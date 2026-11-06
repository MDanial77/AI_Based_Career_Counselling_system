"""
Machine learning module.

1. Builds a labelled training dataset of student profiles from the career
   database (synthetic, generated from each career's requirements with
   realistic noise, because no public Pakistani student dataset exists).
2. Encodes each profile as a feature vector:
   education level, field of study, interest, overall percentage, skills.
3. Compares four classifiers (Random Forest, K-Nearest Neighbours,
   Decision Tree, Support Vector Machine) with stratified 10-fold
   cross-validation (accuracy, precision, recall, F1).
4. Uses the best model (highest F1 score) to predict career probabilities
   for a real student profile; these are blended into the final ranking.

Run `python train_model.py` to regenerate the dataset and metrics.
"""
import csv
import json
import os
import random
import sqlite3
import threading

try:
    import numpy as np
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC
    from sklearn.tree import DecisionTreeClassifier
    SKLEARN_AVAILABLE = True
except ImportError:  # the app still works without scikit-learn
    SKLEARN_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "career_counseling.db")
ML_DIR = os.path.join(BASE_DIR, "ml")
DATASET_PATH = os.path.join(ML_DIR, "training_dataset.csv")
METRICS_PATH = os.path.join(ML_DIR, "model_metrics.json")

SEED = 42
PROFILES_PER_CAREER = 60

EDUCATION_RANK = {
    "matric": 1, "o level": 1, "intermediate": 2, "a level": 2,
    "bs": 3, "bachelor": 3, "b.com": 3, "llb": 3, "mbbs": 3,
    "ms": 4, "mba": 4, "master": 4, "phd": 5,
}
FIELDS = ["Computer Science", "Engineering", "Medical", "Business",
          "Commerce", "Arts", "Education", "Law", "Sciences", "Other"]
INTERESTS = ["Programming", "Mathematics", "Biology", "Business", "Arts",
             "Teaching", "Technology", "Physics", "Chemistry", "Debate",
             "Public Service"]

_lock = threading.Lock()
_state = {"model": None, "vocab": None, "classes": None, "name": None}


def model_name():
    return _state["name"] or (load_metrics() or {}).get("selected_model", "Random Forest")


def _education_rank(text):
    return EDUCATION_RANK.get(str(text or "").strip().lower(), 3)


def _field(text):
    text = str(text or "").strip().lower()
    for field in FIELDS:
        if field.lower() == text:
            return field
    if "public" in text or text in ("any", ""):
        return "Other"
    return "Other"


def _skills(text):
    return [s.strip().lower() for s in str(text or "").split(",") if s.strip()]


def load_careers(db_path=DB_PATH):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT career_name, education_required, field_required, "
        "minimum_percentage, interest, required_skills FROM Careers"
    ).fetchall()
    connection.close()
    return [dict(r) for r in rows]


# ----------------------------------------------------------
# 1. Dataset generation
# ----------------------------------------------------------

def generate_dataset(careers, per_career=PROFILES_PER_CAREER, seed=SEED):
    rng = random.Random(seed)
    all_skills = sorted({s for c in careers for s in _skills(c["required_skills"])})
    rows = []
    for career in careers:
        required = _skills(career["required_skills"])
        min_rank = _education_rank(career["education_required"])
        minimum = float(career["minimum_percentage"] or 50)
        for _ in range(per_career):
            # Education: meets the requirement, sometimes higher.
            rank = min(min_rank + (1 if rng.random() < 0.25 else 0), 5)
            # Field: usually the career's field, sometimes a different one.
            field = _field(career["field_required"])
            if rng.random() < 0.15:
                field = rng.choice(FIELDS)
            # Interest: usually matches, sometimes not.
            interest = career["interest"] if rng.random() < 0.8 else rng.choice(INTERESTS)
            # Overall percentage around (and above) the career minimum.
            percentage = max(33.0, min(99.0, rng.gauss(minimum + 10, 9)))
            # Skills: a random part of the required skills plus some noise.
            keep = max(1, round(len(required) * rng.uniform(0.4, 1.0)))
            skills = set(rng.sample(required, min(keep, len(required))))
            for _ in range(rng.randint(0, 2)):
                skills.add(rng.choice(all_skills))
            rows.append({
                "education_rank": rank, "field": field, "interest": interest,
                "percentage": round(percentage, 1),
                "skills": "|".join(sorted(skills)),
                "career": career["career_name"],
            })
    return rows, all_skills


def save_dataset(rows, path=DATASET_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------------------------
# 2. Feature encoding
# ----------------------------------------------------------

def encode(education_rank, field, interest, percentage, skills, vocab):
    skills = {str(s).strip().lower() for s in skills}
    vector = [education_rank / 5.0, float(percentage) / 100.0]
    vector += [1.0 if _field(field) == f else 0.0 for f in FIELDS]
    vector += [1.0 if interest == i else 0.0 for i in INTERESTS]
    vector += [1.0 if s in skills else 0.0 for s in vocab]
    return vector


def _matrix(rows, vocab):
    X = [encode(r["education_rank"], r["field"], r["interest"],
                r["percentage"], r["skills"].split("|"), vocab) for r in rows]
    y = [r["career"] for r in rows]
    return np.array(X), np.array(y)


# ----------------------------------------------------------
# 3. Model comparison (10-fold cross-validation)
# ----------------------------------------------------------

def candidate_models():
    return {
        "Random Forest": RandomForestClassifier(
            n_estimators=200, random_state=SEED, n_jobs=-1),
        "K-Nearest Neighbours": make_pipeline(
            StandardScaler(), KNeighborsClassifier(n_neighbors=7)),
        "Decision Tree": DecisionTreeClassifier(random_state=SEED),
        "Support Vector Machine": make_pipeline(
            StandardScaler(), SVC(kernel="rbf", C=10, random_state=SEED)),
    }


def evaluate_models(rows, vocab, folds=10):
    X, y = _matrix(rows, vocab)
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=SEED)
    scoring = {"accuracy": "accuracy", "precision": "precision_macro",
               "recall": "recall_macro", "f1": "f1_macro"}
    results = []
    for name, model in candidate_models().items():
        scores = cross_validate(model, X, y, cv=splitter, scoring=scoring)
        results.append({
            "model": name,
            "accuracy": round(float(scores["test_accuracy"].mean()) * 100, 1),
            "accuracy_std": round(float(scores["test_accuracy"].std()) * 100, 1),
            "precision": round(float(scores["test_precision"].mean()), 3),
            "recall": round(float(scores["test_recall"].mean()), 3),
            "f1": round(float(scores["test_f1"].mean()), 3),
        })
    results.sort(key=lambda r: -r["f1"])
    return {
        "dataset_size": len(rows),
        "classes": len(set(y)),
        "features": int(X.shape[1]),
        "folds": folds,
        "dataset_type": "Synthetic profiles generated from the career database",
        "selected_model": results[0]["model"],
        "results": results,
    }


def train_and_save_metrics():
    """Full pipeline: dataset -> 10-fold evaluation -> metrics file."""
    careers = load_careers()
    rows, vocab = generate_dataset(careers)
    save_dataset(rows)
    metrics = evaluate_models(rows, vocab)
    os.makedirs(ML_DIR, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)
    return metrics


def load_metrics():
    try:
        with open(METRICS_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


# ----------------------------------------------------------
# 4. Prediction with the selected (best-F1) model
# ----------------------------------------------------------

def _ensure_model():
    if not SKLEARN_AVAILABLE:
        return False
    with _lock:
        if _state["model"] is None:
            rows, vocab = generate_dataset(load_careers())
            X, y = _matrix(rows, vocab)
            name = (load_metrics() or {}).get("selected_model", "Random Forest")
            models = candidate_models()
            if name not in models:
                name = "Random Forest"
            model = models[name]
            if not hasattr(model, "predict_proba") or name == "Support Vector Machine":
                # SVM gives no probabilities by itself; calibrate it.
                model = make_pipeline(StandardScaler(), CalibratedClassifierCV(
                    SVC(kernel="rbf", C=10, random_state=SEED), ensemble=False))
            model.fit(X, y)
            _state.update(model=model, vocab=vocab, classes=list(model.classes_),
                          name=name)
    return True


def predict_probabilities(education, field, interest, percentage, skills):
    """Return {career_name: probability} for one student profile."""
    try:
        if not _ensure_model():
            return {}
        vector = encode(_education_rank(education), field, interest,
                        percentage, skills, _state["vocab"])
        probabilities = _state["model"].predict_proba(np.array([vector]))[0]
        return {str(c): float(p) for c, p in zip(_state["classes"], probabilities)}
    except Exception:
        return {}


def reset_model():
    """Forget the trained model so the next prediction retrains on the
    current careers (called after an admin adds, edits or deletes one)."""
    with _lock:
        _state.update(model=None, vocab=None, classes=None, name=None)
