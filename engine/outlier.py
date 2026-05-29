import pandas as pd
import numpy as np
from scipy import stats
from config import ZSCORE_THRESHOLD, IQR_MULTIPLIER

class OutlierDetector:
    def __init__(self, df):
        self.df = df.copy()
        self.outliers = {}

    def detect_zscore(self, columns=None):
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns
        for col in columns:
            if col not in self.df.columns:
                continue
            vals = self.df[col].dropna()
            if len(vals) < 4:
                continue
            z = np.abs(stats.zscore(vals, nan_policy='omit'))
            outlier_indices = vals.index[z > ZSCORE_THRESHOLD]
            if len(outlier_indices) > 0:
                self.outliers[col] = {
                    'method': 'zscore',
                    'threshold': ZSCORE_THRESHOLD,
                    'count': len(outlier_indices),
                    'rows': [int(i) + 2 for i in outlier_indices],
                    'values': [float(self.df.loc[i, col]) for i in outlier_indices]
                }
        return self.outliers

    def detect_iqr(self, columns=None):
        if columns is None:
            columns = self.df.select_dtypes(include=[np.number]).columns
        for col in columns:
            if col in self.outliers:
                continue
            if col not in self.df.columns:
                continue
            vals = self.df[col].dropna()
            if len(vals) < 4:
                continue
            q1 = vals.quantile(0.25)
            q3 = vals.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - IQR_MULTIPLIER * iqr
            upper = q3 + IQR_MULTIPLIER * iqr
            outlier_indices = vals[(vals < lower) | (vals > upper)].index
            if len(outlier_indices) > 0:
                self.outliers[col] = {
                    'method': 'iqr',
                    'threshold': IQR_MULTIPLIER,
                    'bounds': {'lower': float(lower), 'upper': float(upper)},
                    'count': len(outlier_indices),
                    'rows': [int(i) + 2 for i in outlier_indices],
                    'values': [float(self.df.loc[i, col]) for i in outlier_indices]
                }
        return self.outliers

    def detect_all(self, columns=None):
        self.detect_zscore(columns)
        self.detect_iqr(columns)
        return self.outliers

    def get_summary(self):
        total = sum(o['count'] for o in self.outliers.values())
        cols = list(self.outliers.keys())
        return {'total_outliers': total, 'columns_affected': cols, 'details': self.outliers}
