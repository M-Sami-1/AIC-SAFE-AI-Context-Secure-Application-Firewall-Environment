from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

import config
from aic_safe.runtime import enforce_project_venv, log_run
from aic_safe.middleware.intent_classifier import ToolIntentClassifier
from dataset.build_dataset import build_dataset


def train(version: str, limit: int | None = None) -> dict:
    enforce_project_venv()
    try:
        import joblib
        import pandas as pd
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
    except ImportError as exc:
        raise RuntimeError("Training requires pandas, scikit-learn, and joblib. Install requirements.txt.") from exc

    dataset_path = config.DATASET_DIR / "dataset.csv"
    if not dataset_path.exists():
        build_dataset()
    df = pd.read_csv(dataset_path)
    if limit:
        df = balanced_limit(df, limit)

    x_train, x_test, y_train, y_test = train_test_split(
        df["prompt"],
        df["attack_class"],
        test_size=0.25,
        random_state=config.RANDOM_SEED,
        stratify=df["attack_class"] if df["attack_class"].nunique() > 1 else None,
    )
    classifier = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            (
                "logreg",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=config.RANDOM_SEED,
                    solver="liblinear",
                ),
            ),
        ]
    )
    classifier.fit(x_train, y_train)
    predictions = classifier.predict(x_test)
    accuracy = float(accuracy_score(y_test, predictions))
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)

    rule_intent = ToolIntentClassifier(use_classifier=False)
    df["tool_intent"] = df["prompt"].apply(lambda prompt: rule_intent.classify(prompt).tool_intent)
    ix_train, ix_test, iy_train, iy_test = train_test_split(
        df["prompt"],
        df["tool_intent"],
        test_size=0.25,
        random_state=config.RANDOM_SEED,
        stratify=df["tool_intent"] if df["tool_intent"].nunique() > 1 else None,
    )
    intent_classifier = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            (
                "logreg",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=config.RANDOM_SEED,
                    solver="liblinear",
                ),
            ),
        ]
    )
    intent_classifier.fit(ix_train, iy_train)
    intent_predictions = intent_classifier.predict(ix_test)
    intent_accuracy = float(accuracy_score(iy_test, intent_predictions))
    intent_report = classification_report(iy_test, intent_predictions, output_dict=True, zero_division=0)

    output_dir = config.MODEL_DIR / version
    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(classifier, output_dir / "classifier.joblib")
    joblib.dump(intent_classifier, output_dir / "intent_classifier.joblib")
    metadata = {
        "version": version,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": config.RANDOM_SEED,
        "rows": int(len(df)),
        "accuracy": accuracy,
        "intent_accuracy": intent_accuracy,
        "report": report,
        "intent_report": intent_report,
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    log_run(
        "models.train_tfidf",
        "success",
        {
            "version": version,
            "limit": limit,
            "rows": int(len(df)),
            "accuracy": accuracy,
            "intent_accuracy": intent_accuracy,
            "model_path": str(output_dir / "classifier.joblib"),
            "intent_model_path": str(output_dir / "intent_classifier.joblib"),
        },
    )
    return metadata


def balanced_limit(df, limit: int):
    import pandas as pd

    if limit >= len(df):
        return df
    groups = list(df.groupby("attack_class", sort=True))
    per_group = max(1, limit // len(groups))
    samples = []
    for _, group in groups:
        samples.append(group.sample(n=min(len(group), per_group), random_state=config.RANDOM_SEED))
    limited = pd.concat(samples)
    remaining = limit - len(limited)
    if remaining > 0:
        rest = df.drop(index=limited.index)
        limited = pd.concat(
            [limited, rest.sample(n=min(remaining, len(rest)), random_state=config.RANDOM_SEED)]
        )
    return limited.sample(frac=1.0, random_state=config.RANDOM_SEED).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v2_week12", choices=["v1_week6", "v2_week12"])
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    metadata = train(args.version, args.limit)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
