import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

class JobAllocationModel:

    def __init__(self):
        self.model = LinearRegression()
        self.scaler = StandardScaler()
        self.is_trained = False

    # -----------------------
    # TRAIN ON DATASET
    # -----------------------
    def train(self, df):

        df['InverseTime'] = 1 / df['AvgTime']
        df['Efficiency'] = df['SuccessRate'] / df['AvgTime']

        X = df[['Rating', 'SuccessRate', 'AvgTime', 'InverseTime', 'Efficiency']]
        y = df['Score']

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

        self.is_trained = True

    # -----------------------
    # PREDICT FROM DICTIONARY
    # -----------------------
    def predict_from_input(self, sellers_list, total_jobs=20):

        if not self.is_trained:
            raise Exception("Model not trained!")

        # Convert input list → DataFrame
        df = pd.DataFrame(sellers_list)

        df['AvgTime'] = df['AvgTime'].replace(0, 4)
        df['SuccessRate'] = df['SuccessRate'].replace(0, 0.6)

        # Feature engineering
        df['InverseTime'] = 1 / df['AvgTime']
        df['Efficiency'] = df['SuccessRate'] / df['AvgTime']

        X = df[['Rating', 'SuccessRate', 'AvgTime', 'InverseTime', 'Efficiency']]
        X_scaled = self.scaler.transform(X)

        df['PredictedScore'] = self.model.predict(X_scaled)

        # Group scores by rating
        group_scores = df.groupby('Rating')['PredictedScore'].sum()
        total_score = group_scores.sum()

        # Job allocation
        raw_jobs = (group_scores / total_score) * total_jobs
        jobs = raw_jobs.astype(int)

        remaining = total_jobs - jobs.sum()

        fractions = (raw_jobs - jobs).sort_values(ascending=False)

        for r in fractions.index:
            if remaining <= 0:
                break
            jobs[r] += 1
            remaining -= 1

        return jobs.to_dict()