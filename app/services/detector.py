import os
import cv2
import threading
import queue
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from collections import deque
from app.core.config import settings

# --- POSE DETECTION ---
class MoveNetMultiPose:
    def __init__(self, model_url="https://tfhub.dev/google/movenet/multipose/lightning/1"):
        self.model = hub.load(model_url)
        self.input_size = 256

    @tf.function
    def _infer(self, inp):
        return self.model.signatures['serving_default'](inp)['output_0']

    def detect(self, frame):
        square = cv2.resize(frame, (self.input_size, self.input_size), interpolation=cv2.INTER_AREA)
        rgb    = cv2.cvtColor(square, cv2.COLOR_BGR2RGB)
        inp    = tf.cast(rgb, tf.int32)[tf.newaxis, ...]
        poses  = self._infer(inp).numpy()[0]
        return poses

    def keypoints_to_features(self, poses, orig_size):
        h, w = orig_size
        feats = []
        for p in poses:
            kpts   = p[:51].reshape(17,3)
            coords = []
            for y,x,s in kpts:
                coords += [0.0,0.0] if s < 0.2 else [x*w, y*h]
            feats.extend(coords)
        return np.array(feats, dtype=np.float32)

# --- TRANSFORMER BLOCK & MODEL ---
class TransformerBlock(tf.keras.layers.Layer):
    def __init__(self, d_model, num_heads, ff_dim, rate=0.1):
        super().__init__()
        self.att   = tf.keras.layers.MultiHeadAttention(num_heads, key_dim=d_model, dropout=rate)
        self.ffn   = tf.keras.Sequential([
            tf.keras.layers.Dense(ff_dim, activation='relu'),
            tf.keras.layers.Dense(d_model),
        ])
        self.norm1 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
        self.norm2 = tf.keras.layers.LayerNormalization(epsilon=1e-6)
        self.drop1 = tf.keras.layers.Dropout(rate)
        self.drop2 = tf.keras.layers.Dropout(rate)

    def call(self, x, training=False):
        attn = self.att(x, x, training=training)
        x    = self.norm1(x + self.drop1(attn, training=training))
        x2   = self.ffn(x)
        return self.norm2(x + self.drop2(x2, training=training))

class ViolenceTransformer(tf.keras.Model):
    def __init__(self, seq_len, feature_dim, d_model=128, num_heads=4, ff_dim=256, num_layers=2):
        super().__init__()
        self.seq_len = seq_len
        self.proj    = tf.keras.layers.Dense(d_model)
        self.pos_emb = tf.keras.layers.Embedding(input_dim=seq_len, output_dim=d_model)
        self.blocks  = [TransformerBlock(d_model, num_heads, ff_dim) for _ in range(num_layers)]
        self.pool    = tf.keras.layers.GlobalAveragePooling1D()
        self.fc      = tf.keras.layers.Dense(64, activation='relu')
        self.drop    = tf.keras.layers.Dropout(0.3)
        self.out     = tf.keras.layers.Dense(1, activation='sigmoid')

    def call(self, x, training=False):
        pos = tf.range(self.seq_len)
        x   = self.proj(x) + self.pos_emb(pos)[tf.newaxis, ...]
        for blk in self.blocks:
            x = blk(x, training=training)
        x = self.pool(x)
        x = self.drop(self.fc(x), training=training)
        return self.out(x)

# --- VIOLENCE DETECTOR CLASS ---
class ViolenceDetector:
    def __init__(
        self,
        camera_index,
        seq_len=1,
        max_people=2,
        warning_th=settings.WARNING_THRESHOLD,
        urgent_th=settings.URGENT_THRESHOLD,
        smoothing_window=settings.SMOOTHING_WINDOW
    ):
        self.cam        = camera_index
        self.seq_len    = seq_len
        self.max_people = max_people
        self.warning_th = warning_th
        self.urgent_th  = urgent_th
        self.smooth_w   = smoothing_window

        self.pose = MoveNetMultiPose()
        feat_dim = max_people * 17 * 2
        self.model = ViolenceTransformer(seq_len, feat_dim)

        # warm‐up & compile
        dummy = tf.zeros((1, seq_len, feat_dim))
        self.model(dummy, training=False)
        self.model.compile('adam', 'binary_crossentropy', ['accuracy'], jit_compile=True)

        self.frame_q  = queue.Queue(maxsize=1)
        self.seq_buf  = deque(maxlen=seq_len)
        self.pred_buf = deque(maxlen=smoothing_window)

    def train_or_load(self, normal_dir: str, violent_dir: str, model_path: str):
        if os.path.exists(model_path):
            print(f"[INFO] Loading model from {model_path}")
            self.model = tf.keras.models.load_model(model_path)
            return

        print("[INFO] No model found → training now.")
        X, y = [], []
        for fn, label, folder in [*[(fn, 0, normal_dir) for fn in os.listdir(normal_dir)], *[(fn, 1, violent_dir) for fn in os.listdir(violent_dir)]]:
            img = cv2.imread(os.path.join(folder, fn))
            if img is None:
                continue
            poses = self.pose.detect(img)
            feats = self.pose.keypoints_to_features(poses[:self.max_people], img.shape[:2])
            X.append(feats)
            y.append(label)

        X = np.array(X).reshape(-1, self.seq_len, X[0].shape[0])
        y = np.array(y)
        print(f"[INFO] Dataset loaded: {X.shape[0]} samples")

        self.model.fit(X, y, epochs=10, batch_size=16)
        self.model.save(model_path)
        print(f"[INFO] Model trained & saved to {model_path}")

    @tf.function
    def _infer(self, seq):
        return self.model(seq, training=False)

    def _capture(self):
        cap = cv2.VideoCapture(self.cam, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if not self.frame_q.full():
                self.frame_q.put(frame)
        cap.release()

    def _process(self):
        while True:
            frame = self.frame_q.get()
            h, w = frame.shape[:2]
            poses = self.pose.detect(frame)
            feat  = self.pose.keypoints_to_features(poses[:self.max_people], (h, w))
            self.seq_buf.append(feat)

            label, color = "Gathering…", (0, 255, 255)
            if len(self.seq_buf) == self.seq_len:
                arr   = np.stack(self.seq_buf, axis=0)[None, ...]
                score = float(self._infer(tf.constant(arr))[0,0].numpy())
                print(f"[DEBUG] Frame score: {score:.4f}")
                self.pred_buf.append(score)
                avg   = np.mean(self.pred_buf)

                if avg >= self.urgent_th:
                    label, color = f"🚨 URGENT VIOLENCE ({avg:.2f})", (0,0,255)
                elif avg >= self.warning_th:
                    label, color = f"⚠️ Warning ({avg:.2f})", (0,165,255)
                else:
                    label, color = f"✔ Normal ({avg:.2f})", (0,255,0)

            out = frame.copy()
            cv2.putText(out, label, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
            cv2.imshow(f"Camera {self.cam} Detection", out)
            if cv2.waitKey(1) & 0xFF == 27:
                break
        cv2.destroyAllWindows()

    def run(self, normal_dir: str, violent_dir: str, model_path: str):
        self.train_or_load(normal_dir, violent_dir, model_path)
        threading.Thread(target=self._capture, daemon=True).start()
        self._process()
