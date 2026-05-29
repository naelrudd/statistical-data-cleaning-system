import pandas as pd
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime

class DataExporter:
    def __init__(self, df, quality_scores, cleaner_report, validator_summary, outlier_summary):
        self.df = df
        self.scores = quality_scores
        self.cleaner_report = cleaner_report
        self.validator_summary = validator_summary
        self.outlier_summary = outlier_summary

    def export_cleaned(self, path):
        self.df.to_excel(path, index=False, engine='openpyxl')
        return path

    def generate_charts(self):
        charts = {}
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        missing_data = self.cleaner_report.get('missing_before', {})
        if missing_data:
            cols_m = list(missing_data.keys())
            vals_m = list(missing_data.values())
            axes[0, 0].bar(cols_m, vals_m, color='orange')
            axes[0, 0].set_title('Missing Values per Column')
            axes[0, 0].set_ylabel('Count')
            plt.setp(axes[0, 0].xaxis.get_majorticklabels(), rotation=45, ha='right')
        else:
            axes[0, 0].text(0.5, 0.5, 'No Missing Values', ha='center', va='center')
            axes[0, 0].set_title('Missing Values')

        fmt_errors = self.validator_summary.get('format_errors', {})
        if fmt_errors:
            cols_f = list(fmt_errors.keys())
            vals_f = list(fmt_errors.values())
            axes[0, 1].bar(cols_f, vals_f, color='red')
            axes[0, 1].set_title('Format Errors per Column')
            axes[0, 1].set_ylabel('Count')
            plt.setp(axes[0, 1].xaxis.get_majorticklabels(), rotation=45, ha='right')
        else:
            axes[0, 1].text(0.5, 0.5, 'No Format Errors', ha='center', va='center')
            axes[0, 1].set_title('Format Errors')

        labels = ['Valid', 'Invalid']
        total_errors = self.validator_summary.get('total', 0)
        total_rows = len(self.df)
        sizes = [max(1, total_rows - total_errors), total_errors]
        axes[1, 0].pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#4CAF50', '#f44336'])
        axes[1, 0].set_title('Valid vs Invalid')

        score_keys = ['completeness', 'consistency', 'duplicate_free', 'format_validity', 'outlier_free']
        score_vals = [self.scores.get(k, 0) for k in score_keys]
        score_labels = ['Completeness', 'Consistency', 'No Duplicates', 'Format', 'No Outliers']
        axes[1, 1].bar(score_labels, score_vals, color='#2196F3')
        axes[1, 1].set_title('Quality Scores')
        axes[1, 1].set_ylabel('Score')
        axes[1, 1].set_ylim(0, 100)
        plt.setp(axes[1, 1].xaxis.get_majorticklabels(), rotation=45, ha='right')

        plt.tight_layout()
        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        charts['summary'] = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        return charts

    def generate_report_html(self):
        charts = self.generate_charts()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_rows = len(self.df)
        rows_before = total_rows + self.cleaner_report.get('duplicates_removed', 0)
        rows_removed = self.cleaner_report.get('duplicates_removed', 0)
        missing_handled = sum(self.cleaner_report.get('missing_before', {}).values())

        html = f"""
        <html><head><meta charset="utf-8"><title>Validation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #1565C0; }}
            .score {{ font-size: 48px; color: #4CAF50; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #1565C0; color: white; }}
            .card {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            img {{ max-width: 100%; }}
        </style></head><body>
        <h1>Data Quality Report</h1>
        <p>Generated: {now}</p>
        <h2>Overall Quality Score: {self.scores.get('overall', 0)} / 100 (Grade: {self.scores.get('grade', 'N/A')})</h2>
        <div class="card">
            <h3>Processing Summary</h3>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Rows (original)</td><td>{rows_before}</td></tr>
                <tr><td>Rows (final)</td><td>{total_rows}</td></tr>
                <tr><td>Duplicates Removed</td><td>{rows_removed}</td></tr>
                <tr><td>Missing Values Handled</td><td>{missing_handled}</td></tr>
                <tr><td>Format Errors</td><td>{self.validator_summary.get('total', 0)}</td></tr>
                <tr><td>Outliers Detected</td><td>{self.outlier_summary.get('total_outliers', 0)}</td></tr>
            </table>
        </div>
        <img src="data:image/png;base64,{charts['summary']}" alt="Charts"/>
        </body></html>
        """
        return html
