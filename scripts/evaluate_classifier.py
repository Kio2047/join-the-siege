import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report
import joblib

# Paths
VAL_PATH = "data/validation"
MODEL_PATH = "models"

# Load model files
embedder_name = open(os.path.join(MODEL_PATH, "embedder.txt")).read().strip()
embedder = SentenceTransformer(embedder_name)
clf = joblib.load(os.path.join(MODEL_PATH, "classifier.joblib"))
label_encoder = joblib.load(os.path.join(MODEL_PATH, "label_encoder.joblib"))

# Load validation data
texts, labels = [], []
for filename in os.listdir(VAL_PATH):
    if filename.endswith(".csv"):
        df = pd.read_csv(os.path.join(VAL_PATH, filename))
        texts.extend(df["text"].tolist())
        labels.extend(df["label"].tolist())

# Encode and predict
print("Embedding validation text...")
X_val = embedder.encode(texts, convert_to_tensor=False, show_progress_bar=True)

print("Predicting...")
y_true = label_encoder.transform(labels)
y_pred = clf.predict(X_val)

# Report
print("Evaluation Report:")
print(classification_report(y_true, y_pred, target_names=label_encoder.classes_))
