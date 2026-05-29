import pandas as pd
import numpy as np

class QualityScorer:
    def __init__(self, df, cleaner_report, validator_summary, outlier_summary):
        self.df = df
        self.cleaner_report = cleaner_report
        self.validator_summary = validator_summary
        self.outlier_summary = outlier_summary
        self.total_rows = len(df) if hasattr(df, '__len__') else 0

    def compute(self):
        scores = {}
        weights = {
            'completeness': 30,
            'consistency': 25,
            'duplicate_free': 20,
            'format_validity': 15,
            'outlier_free': 10,
        }

        missing_count = sum(self.cleaner_report.get('missing_before', {}).values())
        total_cells = self.total_rows * len(self.df.columns) if self.total_rows > 0 else 1
        completeness = max(0, 100 - (missing_count / max(total_cells, 1) * 100))
        scores['completeness'] = round(completeness, 1)
        scores['completeness_detail'] = {
            'missing_cells': missing_count,
            'total_cells': total_cells,
            'pct': round(missing_count / max(total_cells, 1) * 100, 2)
        }

        dup_found = self.cleaner_report.get('duplicates_found', 0)
        dup_score = max(0, 100 - (dup_found / max(self.total_rows, 1) * 100))
        scores['duplicate_free'] = round(dup_score, 1)
        scores['duplicate_detail'] = {
            'duplicates_found': dup_found,
            'total_rows': self.total_rows
        }

        total_errors = self.validator_summary.get('total', 0)
        format_score = max(0, 100 - (total_errors / max(total_cells, 1) * 100))
        scores['format_validity'] = round(format_score, 1)
        scores['format_detail'] = {
            'errors': total_errors,
            'total_cells': total_cells
        }

        total_outliers = self.outlier_summary.get('total_outliers', 0)
        outlier_score = max(0, 100 - (total_outliers / max(self.total_rows, 1) * 100))
        scores['outlier_free'] = round(outlier_score, 1)
        scores['outlier_detail'] = {'outliers': total_outliers}

        cross_errors = self.validator_summary.get('cross_errors', 0)
        consistency = max(0, 100 - (cross_errors / max(self.total_rows, 1) * 100))
        scores['consistency'] = round(consistency, 1)
        scores['consistency_detail'] = {
            'cross_errors': cross_errors,
            'total_rows': self.total_rows
        }

        weighted = sum(scores[k] * weights[k] / 100 for k in weights)
        scores['overall'] = round(weighted, 1)

        if scores['overall'] >= 90:
            grade = 'A'
        elif scores['overall'] >= 75:
            grade = 'B'
        elif scores['overall'] >= 60:
            grade = 'C'
        else:
            grade = 'D'
        scores['grade'] = grade
        scores['weights'] = weights

        return scores
