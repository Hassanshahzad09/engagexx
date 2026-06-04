"""
EngageX Seller Rating Prediction ML Pipeline

This script trains and evaluates a complete seller rating prediction system using
Random Forest, XGBoost, and Decision Tree classifiers.

Run from the BackEnd folder:
    python mlservice/seller_rating_ml_pipeline.py

Install ML dependencies first if needed:
    pip install -r requirements-ml.txt
"""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path
from typing import Dict, Iterable, Tuple


def ensure_dependencies() -> None:
    missing = []
    required_modules = {
        "pandas": "pandas",
        "numpy": "numpy",
        "matplotlib": "matplotlib",
        "seaborn": "seaborn",
        "sklearn": "scikit-learn",
        "xgboost": "xgboost",
        "joblib": "joblib",
    }

    for module_name, package_name in required_modules.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        packages = " ".join(missing)
        raise SystemExit(
            "\nMissing ML dependencies.\n"
            f"Install them with:\n\n    pip install {packages}\n\n"
            "Or from BackEnd folder:\n\n    pip install -r requirements-ml.txt\n"
        )


ensure_dependencies()

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, cross_val_score, learning_curve, train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="viridis")


FEATURE_COLUMNS = [
    "TrustScore",
    "SuccessRate",
    "CompletionRatio",
    "ProofValidityRate",
    "SpeedScore",
    "AuditRetentionRate",
    "PerformanceScore",
    "FinalReputationScore",
    "AvgCompletionTime",
    "AssignedTasks",
    "CompletedTasks",
    "ApprovedTasks",
    "RejectedTasks",
]

TARGET_COLUMN = "Rating"
DROP_COLUMNS = ["SellerID", "RatingLabel"]
RATING_LABELS = {
    1: "1 Star",
    2: "2 Star",
    3: "3 Star",
    4: "4 Star",
    5: "5 Star",
}


def print_section(title: str) -> None:
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def save_and_maybe_show(output_dir: Path, filename: str, show_plots: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_dir / filename, dpi=180, bbox_inches="tight")
    if show_plots:
        plt.show()
    plt.close()


def load_and_explore_data(csv_path: Path, output_dir: Path, show_plots: bool) -> pd.DataFrame:
    print_section("1. LOAD AND EXPLORE THE DATA")
    df = pd.read_csv(csv_path)

    print(f"Dataset path: {csv_path}")
    print(f"Dataset shape: {df.shape}")
    print("\nData types:")
    print(df.dtypes)
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nNull values:")
    print(df.isnull().sum())
    print("\nRating class distribution:")
    print(df[TARGET_COLUMN].value_counts().sort_index())

    plt.figure(figsize=(9, 5))
    sns.countplot(data=df, x=TARGET_COLUMN, palette="viridis")
    plt.title("Seller Rating Distribution", fontsize=16, fontweight="bold")
    plt.xlabel("Rating")
    plt.ylabel("Number of Sellers")
    save_and_maybe_show(output_dir, "01_rating_distribution.png", show_plots)

    numeric_df = df.select_dtypes(include=[np.number])
    plt.figure(figsize=(14, 10))
    sns.heatmap(numeric_df.corr(), cmap="coolwarm", annot=False, linewidths=0.4)
    plt.title("Feature Correlation Heatmap", fontsize=16, fontweight="bold")
    save_and_maybe_show(output_dir, "02_correlation_heatmap.png", show_plots)

    return df


def preprocess_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
    print_section("2. PREPROCESSING")

    missing_columns = [column for column in FEATURE_COLUMNS + [TARGET_COLUMN] if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {missing_columns}")

    model_df = df.drop(columns=[column for column in DROP_COLUMNS if column in df.columns]).copy()
    print(f"Dropped columns: {[column for column in DROP_COLUMNS if column in df.columns]}")

    if model_df.isnull().sum().sum() > 0:
        print("Missing values found. Filling numeric missing values with column median.")
        numeric_columns = model_df.select_dtypes(include=[np.number]).columns
        model_df[numeric_columns] = model_df[numeric_columns].fillna(model_df[numeric_columns].median())
    else:
        print("No missing values found.")

    X = model_df[FEATURE_COLUMNS]
    y = model_df[TARGET_COLUMN].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"Training rows: {X_train_scaled.shape[0]}")
    print(f"Testing rows: {X_test_scaled.shape[0]}")
    print("StandardScaler applied to all input features.")

    return X_train_scaled, X_test_scaled, y_train.to_numpy(), y_test.to_numpy(), scaler


def get_models() -> Dict[str, object]:
    return {
        "Random Forest": RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300,
            learning_rate=0.1,
            max_depth=7,
            random_state=42,
            use_label_encoder=False,
            eval_metric="mlogloss",
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            class_weight="balanced",
        ),
    }


def train_and_evaluate_models(
    models: Dict[str, object],
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    output_dir: Path,
    show_plots: bool,
) -> Tuple[Dict[str, object], pd.DataFrame]:
    print_section("3-5. TRAIN, EVALUATE, AND COMPARE MODELS")

    trained_models: Dict[str, object] = {}
    results = []
    label_encoder = LabelEncoder()
    y_train_xgb = label_encoder.fit_transform(y_train)

    for model_name, model in models.items():
        print_section(f"MODEL: {model_name}")

        if model_name == "XGBoost":
            model.fit(X_train, y_train_xgb)
            train_predictions = label_encoder.inverse_transform(model.predict(X_train))
            test_predictions = label_encoder.inverse_transform(model.predict(X_test))
            cv_scores = cross_val_score(model, X_train, y_train_xgb, cv=5, scoring="accuracy")
        else:
            model.fit(X_train, y_train)
            train_predictions = model.predict(X_train)
            test_predictions = model.predict(X_test)
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")

        train_accuracy = accuracy_score(y_train, train_predictions)
        test_accuracy = accuracy_score(y_test, test_predictions)
        cv_mean = cv_scores.mean()

        print(f"Training Accuracy: {train_accuracy:.4f}")
        print(f"Testing Accuracy:  {test_accuracy:.4f}")
        print(f"5-Fold CV Score:   {cv_mean:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, test_predictions, target_names=[RATING_LABELS[i] for i in range(1, 6)]))

        cm = confusion_matrix(y_test, test_predictions, labels=[1, 2, 3, 4, 5])
        plt.figure(figsize=(7, 5))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=[RATING_LABELS[i] for i in range(1, 6)],
            yticklabels=[RATING_LABELS[i] for i in range(1, 6)],
        )
        plt.title(f"{model_name} Confusion Matrix", fontsize=14, fontweight="bold")
        plt.xlabel("Predicted Rating")
        plt.ylabel("Actual Rating")
        save_and_maybe_show(output_dir, f"confusion_matrix_{model_name.lower().replace(' ', '_')}.png", show_plots)

        trained_models[model_name] = model
        results.append(
            {
                "Model Name": model_name,
                "Train Accuracy": train_accuracy,
                "Test Accuracy": test_accuracy,
                "CV Score": cv_mean,
            }
        )

    comparison_df = pd.DataFrame(results).sort_values("Test Accuracy", ascending=False)
    print_section("MODEL COMPARISON TABLE")
    print(comparison_df.to_string(index=False))
    print(f"\nBest model before tuning: {comparison_df.iloc[0]['Model Name']}")

    plt.figure(figsize=(10, 5))
    comparison_plot = comparison_df.melt(id_vars="Model Name", value_vars=["Train Accuracy", "Test Accuracy", "CV Score"])
    sns.barplot(data=comparison_plot, x="Model Name", y="value", hue="variable")
    plt.title("Model Accuracy Comparison", fontsize=16, fontweight="bold")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1.05)
    save_and_maybe_show(output_dir, "03_model_comparison.png", show_plots)

    return trained_models, comparison_df


def plot_feature_importance(model: RandomForestClassifier, output_dir: Path, show_plots: bool) -> pd.DataFrame:
    print_section("6. RANDOM FOREST FEATURE IMPORTANCE")

    importance_df = pd.DataFrame(
        {
            "Feature": FEATURE_COLUMNS,
            "Importance": model.feature_importances_,
        }
    ).sort_values("Importance", ascending=False)

    print(importance_df.to_string(index=False))

    plt.figure(figsize=(11, 7))
    sns.barplot(data=importance_df, x="Importance", y="Feature", palette="viridis")
    plt.title("Random Forest Feature Importance", fontsize=16, fontweight="bold")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    save_and_maybe_show(output_dir, "04_feature_importance_random_forest.png", show_plots)

    return importance_df


def get_grid_search_config(best_model_name: str) -> Tuple[object, Dict[str, Iterable]]:
    if best_model_name == "Random Forest":
        model = RandomForestClassifier(random_state=42, class_weight="balanced", n_jobs=-1)
        params = {
            "n_estimators": [150, 200, 300],
            "max_depth": [10, 15, 20],
            "min_samples_split": [2, 5, 10],
        }
    elif best_model_name == "XGBoost":
        model = XGBClassifier(random_state=42, use_label_encoder=False, eval_metric="mlogloss")
        params = {
            "n_estimators": [200, 300],
            "learning_rate": [0.05, 0.1, 0.2],
            "max_depth": [5, 7, 9],
        }
    else:
        model = DecisionTreeClassifier(random_state=42, class_weight="balanced")
        params = {
            "max_depth": [6, 10, 14, 18],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf": [1, 2, 4],
        }

    return model, params


def tune_best_model(
    best_model_name: str,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> Tuple[object, str]:
    print_section("7. HYPERPARAMETER TUNING")

    model, params = get_grid_search_config(best_model_name)
    label_encoder = LabelEncoder()

    if best_model_name == "XGBoost":
        y_train_for_grid = label_encoder.fit_transform(y_train)
    else:
        y_train_for_grid = y_train

    grid_search = GridSearchCV(
        estimator=model,
        param_grid=params,
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
        verbose=1,
    )
    grid_search.fit(X_train, y_train_for_grid)

    tuned_model = grid_search.best_estimator_
    if best_model_name == "XGBoost":
        tuned_predictions = label_encoder.inverse_transform(tuned_model.predict(X_test))
    else:
        tuned_predictions = tuned_model.predict(X_test)

    tuned_accuracy = accuracy_score(y_test, tuned_predictions)
    print(f"Best model selected for tuning: {best_model_name}")
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Improved tuned test accuracy: {tuned_accuracy:.4f}")

    return tuned_model, best_model_name


def evaluate_final_model(
    model: object,
    model_name: str,
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    output_dir: Path,
    show_plots: bool,
) -> object:
    print_section("8. FINAL BEST MODEL")

    label_encoder = LabelEncoder()
    if model_name == "XGBoost":
        y_train_encoded = label_encoder.fit_transform(y_train)
        model.fit(X_train, y_train_encoded)
        model.engagex_label_encoder_classes_ = label_encoder.classes_
        final_predictions = label_encoder.inverse_transform(model.predict(X_test))
    else:
        model.fit(X_train, y_train)
        final_predictions = model.predict(X_test)

    final_accuracy = accuracy_score(y_test, final_predictions)
    print(f"Final Model: {model_name}")
    print(f"Final Test Accuracy: {final_accuracy:.4f}")
    print("\nFinal Classification Report:")
    print(classification_report(y_test, final_predictions, target_names=[RATING_LABELS[i] for i in range(1, 6)]))

    train_sizes, train_scores, test_scores = learning_curve(
        model,
        X_train,
        label_encoder.fit_transform(y_train) if model_name == "XGBoost" else y_train,
        cv=5,
        scoring="accuracy",
        n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 5),
    )
    train_mean = train_scores.mean(axis=1)
    test_mean = test_scores.mean(axis=1)

    plt.figure(figsize=(9, 5))
    plt.plot(train_sizes, train_mean, marker="o", label="Training Accuracy")
    plt.plot(train_sizes, test_mean, marker="o", label="Validation Accuracy")
    plt.title(f"Learning Curve - {model_name}", fontsize=16, fontweight="bold")
    plt.xlabel("Training Set Size")
    plt.ylabel("Accuracy")
    plt.legend()
    plt.grid(True)
    save_and_maybe_show(output_dir, "05_learning_curve_best_model.png", show_plots)

    return model


def save_model(model: object, scaler: StandardScaler, output_dir: Path) -> Tuple[Path, Path]:
    print_section("9. SAVE THE MODEL")

    model_path = output_dir / "seller_rating_model.pkl"
    scaler_path = output_dir / "seller_scaler.pkl"
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    print(f"Model saved to: {model_path}")
    print(f"Scaler saved to: {scaler_path}")
    return model_path, scaler_path


def predict_seller_rating(
    trust_score: float,
    success_rate: float,
    completion_ratio: float,
    proof_validity_rate: float,
    speed_score: float,
    audit_retention_rate: float,
    performance_score: float,
    final_reputation_score: float,
    avg_completion_time: float,
    assigned_tasks: int,
    completed_tasks: int,
    approved_tasks: int,
    rejected_tasks: int,
    model_path: str | Path = "ml_outputs/seller_rating_model.pkl",
    scaler_path: str | Path = "ml_outputs/seller_scaler.pkl",
) -> Tuple[int, str]:
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    input_data = pd.DataFrame(
        [
            {
                "TrustScore": trust_score,
                "SuccessRate": success_rate,
                "CompletionRatio": completion_ratio,
                "ProofValidityRate": proof_validity_rate,
                "SpeedScore": speed_score,
                "AuditRetentionRate": audit_retention_rate,
                "PerformanceScore": performance_score,
                "FinalReputationScore": final_reputation_score,
                "AvgCompletionTime": avg_completion_time,
                "AssignedTasks": assigned_tasks,
                "CompletedTasks": completed_tasks,
                "ApprovedTasks": approved_tasks,
                "RejectedTasks": rejected_tasks,
            }
        ],
        columns=FEATURE_COLUMNS,
    )

    scaled_input = scaler.transform(input_data)
    raw_prediction = model.predict(scaled_input)

    if hasattr(model, "engagex_label_encoder_classes_"):
        label_encoder = LabelEncoder()
        label_encoder.classes_ = model.engagex_label_encoder_classes_
        predicted_rating = int(label_encoder.inverse_transform(raw_prediction)[0])
    else:
        predicted_rating = int(raw_prediction[0])

    return predicted_rating, RATING_LABELS[predicted_rating]


def test_prediction_function(model_path: Path, scaler_path: Path) -> None:
    print_section("10. PREDICTION FUNCTION TESTS")

    good_seller = predict_seller_rating(
        trust_score=92,
        success_rate=0.95,
        completion_ratio=0.90,
        proof_validity_rate=0.93,
        speed_score=0.88,
        audit_retention_rate=0.91,
        performance_score=91.5,
        final_reputation_score=88.7,
        avg_completion_time=1.5,
        assigned_tasks=150,
        completed_tasks=135,
        approved_tasks=128,
        rejected_tasks=7,
        model_path=model_path,
        scaler_path=scaler_path,
    )

    bad_seller = predict_seller_rating(
        trust_score=12,
        success_rate=0.25,
        completion_ratio=0.30,
        proof_validity_rate=0.20,
        speed_score=0.15,
        audit_retention_rate=0.10,
        performance_score=21.5,
        final_reputation_score=18.2,
        avg_completion_time=18.0,
        assigned_tasks=40,
        completed_tasks=12,
        approved_tasks=3,
        rejected_tasks=9,
        model_path=model_path,
        scaler_path=scaler_path,
    )

    print(f"Example 1 - Good Seller Prediction: {good_seller[0]} ({good_seller[1]})")
    print(f"Example 2 - Bad Seller Prediction:  {bad_seller[0]} ({bad_seller[1]})")


def run_pipeline(csv_path: Path, output_dir: Path, show_plots: bool) -> None:
    df = load_and_explore_data(csv_path, output_dir, show_plots)
    X_train, X_test, y_train, y_test, scaler = preprocess_data(df)

    models = get_models()
    trained_models, comparison_df = train_and_evaluate_models(
        models,
        X_train,
        X_test,
        y_train,
        y_test,
        output_dir,
        show_plots,
    )

    plot_feature_importance(trained_models["Random Forest"], output_dir, show_plots)

    best_model_name = str(comparison_df.iloc[0]["Model Name"])
    tuned_model, tuned_model_name = tune_best_model(best_model_name, X_train, X_test, y_train, y_test)
    final_model = evaluate_final_model(
        tuned_model,
        tuned_model_name,
        X_train,
        X_test,
        y_train,
        y_test,
        output_dir,
        show_plots,
    )
    model_path, scaler_path = save_model(final_model, scaler, output_dir)
    test_prediction_function(model_path, scaler_path)

    print_section("PIPELINE COMPLETED SUCCESSFULLY")
    print(f"All plots and model files are saved in: {output_dir.resolve()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train EngageX seller rating ML models.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("seller_rating_dataset.csv"),
        help="Path to the seller rating CSV dataset.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml_outputs"),
        help="Directory for saved models and plots.",
    )
    parser.add_argument(
        "--show-plots",
        action="store_true",
        help="Show matplotlib windows while also saving plots.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if not args.csv.exists():
        raise SystemExit(f"CSV file not found: {args.csv}")

    run_pipeline(args.csv, args.output_dir, args.show_plots)
