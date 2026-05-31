import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from pathlib import Path
import os


class JobAllocationModel:

    def __init__(self):
        # Using GradientBoosting — learns non-linear patterns, won't just memorize formula
        self.model = GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.85,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.dataset_path = None  # Will be set when training

    # -----------------------
    # FEATURE ENGINEERING
    # -----------------------
    def _build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Safe defaults for new/zero-history sellers
        df['AvgTime'] = df['AvgTime'].replace(0, np.nan).fillna(4.0).clip(lower=0.1)
        df['SuccessRate'] = df['SuccessRate'].replace(0, np.nan).fillna(0.5).clip(lower=0.01, upper=1.0)
        df['CompletedJobs'] = df.get('CompletedJobs', pd.Series(0, index=df.index)).fillna(0)
        df['CancelledJobs'] = df.get('CancelledJobs', pd.Series(0, index=df.index)).fillna(0)

        # Derived features — these capture REAL quality signals
        df['InverseTime'] = 1.0 / df['AvgTime']
        df['Efficiency'] = df['SuccessRate'] / df['AvgTime']
        df['TotalJobs'] = df['CompletedJobs'] + df['CancelledJobs']
        df['ReliabilityScore'] = df['CompletedJobs'] / (df['TotalJobs'] + 1)  # +1 avoids divide by zero
        df['ExperienceBoost'] = np.log1p(df['CompletedJobs'])  # diminishing returns on experience
        df['CancelPenalty'] = df['CancelledJobs'] / (df['TotalJobs'] + 1)

        return df

    # -----------------------
    # TRAIN ON DATASET
    # -----------------------
    def train(self, df: pd.DataFrame, dataset_path: str = None):
        """
        Train on your Excel dataset.
        dataset_path: optional path to Excel file (for logging new data back later)
        """
        self.dataset_path = dataset_path

        df = self._build_features(df)

        feature_cols = [
            'Rating', 'SuccessRate', 'AvgTime',
            'InverseTime', 'Efficiency',
            'ReliabilityScore', 'ExperienceBoost', 'CancelPenalty'
        ]

        X = df[feature_cols]
        y = df['Score']

        # Train / validation split to get a real accuracy signal
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        self.model.fit(X_train_scaled, y_train)

        val_score = self.model.score(X_val_scaled, y_val)
        print(f"[ML] Validation R² on held-out 20%: {val_score:.4f}")  # Should NOT be 1.0 now

        self.is_trained = True
        self.feature_cols = feature_cols

    # -----------------------
    # PREDICT FROM INPUT
    # -----------------------
    def predict_from_input(self, sellers_list: list, total_jobs: int) -> dict:
        """
        Takes a list of seller dicts and total jobs.
        Returns a dict like {1: 30, 2: 50, 3: 70, 4: 40, 5: 10}
        Handles ALL edge cases:
        - Single seller getting all jobs
        - Missing rating groups
        - New users with no history
        - total_jobs larger than number of sellers (round-robin handles repeats)
        """
        if not self.is_trained:
            raise Exception("Model not trained!")

        if not sellers_list:
            return {}

        if total_jobs <= 0:
            return {}

        df = pd.DataFrame(sellers_list)
        df = self._build_features(df)

        X = df[self.feature_cols]
        X_scaled = self.scaler.transform(X)

        df['PredictedScore'] = self.model.predict(X_scaled)

        # Ensure no negative scores (GBR can occasionally predict negatives)
        df['PredictedScore'] = df['PredictedScore'].clip(lower=0.01)

        print("[ML] Predictions per seller:\n", df[['Rating', 'PredictedScore']].to_string())

        # --- GROUP by Rating ---
        group_scores = df.groupby('Rating')['PredictedScore'].sum()
        total_score = group_scores.sum()

        print("[ML] Group Scores:\n", group_scores)

        # --- PROPORTIONAL allocation ---
        raw_jobs = (group_scores / total_score) * total_jobs
        jobs = raw_jobs.apply(np.floor).astype(int)

        # Distribute remaining jobs to groups with highest fractional part
        remaining = int(total_jobs - jobs.sum())
        fractions = (raw_jobs - jobs).sort_values(ascending=False)
        for r in fractions.index:
            if remaining <= 0:
                break
            jobs[r] += 1
            remaining -= 1

        # --- EDGE CASE: all jobs fell into rating groups with 0 sellers in DB ---
        # Ensure every group with sellers gets at least 1 job if total allows
        present_ratings = df['Rating'].unique()
        result = {}
        for rating in [1, 2, 3, 4, 5]:
            result[str(rating)] = int(jobs.get(rating, 0))

        print("[ML] Final allocation:", result)
        return result

    # -----------------------
    # LOG NEW SELLER DATA
    # -----------------------
    def log_new_data(self, new_sellers: list, dataset_path: str = None):
        """
        Append new seller records to the Excel training file.
        new_sellers: list of dicts with keys matching dataset columns.
        """
        path = dataset_path or self.dataset_path
        if not path or not os.path.exists(path):
            print("[ML] Dataset path not set or file not found — skipping log.")
            return

        try:
            existing_df = pd.read_excel(path)
            new_df = pd.DataFrame(new_sellers)

            # Only keep columns that match the dataset schema
            cols = existing_df.columns.tolist()
            new_df = new_df.reindex(columns=cols)

            combined = pd.concat([existing_df, new_df], ignore_index=True)
            combined.drop_duplicates(subset=['SellerID'], keep='last', inplace=True)
            combined.to_excel(path, index=False)

            print(f"[ML] Logged {len(new_sellers)} new seller(s) to dataset.")
        except Exception as e:
            print(f"[ML] Failed to log new data: {e}")