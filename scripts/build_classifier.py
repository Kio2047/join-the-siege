import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import joblib

# Config
TRAIN_PATH = "data/training"
MODEL_PATH = "src/classifier/file_content_classifier/models"
EMBEDDER_NAME = "all-MiniLM-L6-v2"
OUTPUT_CLASSIFIER = os.path.join(MODEL_PATH, "classifier.joblib")
OUTPUT_LABEL_ENCODER = os.path.join(MODEL_PATH, "label_encoder.joblib")
OUTPUT_EMBEDDER = os.path.join(MODEL_PATH, "embedder.txt")


def load_training_data():
    all_texts, all_labels = [], []
    for filename in os.listdir(TRAIN_PATH):
        if not filename.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(TRAIN_PATH, filename))
        all_texts.extend(df["text"].tolist())
        all_labels.extend(df["label"].tolist())
    return all_texts, all_labels


def train_classifier():
    print("Loading training data")
    texts, labels = load_training_data()

    print(f"Loading embedding model: {EMBEDDER_NAME}")
    model = SentenceTransformer(EMBEDDER_NAME)

    print("Generating embeddings")
    X = model.encode(texts, convert_to_tensor=False, show_progress_bar=True)

    print("Encoding labels")
    le = LabelEncoder()
    y = le.fit_transform(labels)

    print("Training classifier")
    clf = LogisticRegression(max_iter=1000, random_state=42, solver="liblinear")
    clf.fit(X, y)

    print("Saving model artifacts")
    os.makedirs(MODEL_PATH, exist_ok=True)
    joblib.dump(clf, OUTPUT_CLASSIFIER)
    joblib.dump(le, OUTPUT_LABEL_ENCODER)
    with open(OUTPUT_EMBEDDER, "w") as f:
        f.write(EMBEDDER_NAME)

    print(f"Saved classifier to {OUTPUT_CLASSIFIER}")


if __name__ == "__main__":
    train_classifier()
