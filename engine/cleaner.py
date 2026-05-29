import pandas as pd
import numpy as np

class DataCleaner:
    def __init__(self, df):
        self.df = df.copy()
        self.report = {
            'missing_before': {},
            'missing_after': {},
            'duplicates_found': 0,
            'duplicates_removed': 0,
            'missing_handled': {},
        }

    def detect_missing(self):
        missing_map = {
            'null': None, '': None, '-': None, 'n/a': None, 'na': None,
            'none': None, '?': None, 'unknown': None, '-': None
        }
        self.df = self.df.replace(missing_map, np.nan)
        for col in self.df.columns:
            count = int(self.df[col].isna().sum())
            if count > 0:
                self.report['missing_before'][col] = count
        return self.report['missing_before']

    def handle_missing(self, strategy='drop', fill_value=None, column_strategy=None):
        self.detect_missing()
        if strategy == 'drop':
            before = len(self.df)
            self.df = self.df.dropna()
            after = len(self.df)
            self.report['missing_handled'] = {'strategy': 'drop', 'rows_dropped': before - after}
        elif strategy == 'fill':
            for col in self.df.columns:
                if self.df[col].isna().sum() == 0:
                    continue
                col_strat = column_strategy.get(col, 'auto') if column_strategy else 'auto'
                if col_strat == 'auto':
                    if self.df[col].dtype in ('object', 'category'):
                        col_strat = 'mode'
                    else:
                        col_strat = 'mean'
                if col_strat == 'mean':
                    self.df[col] = self.df[col].fillna(self.df[col].mean())
                elif col_strat == 'median':
                    self.df[col] = self.df[col].fillna(self.df[col].median())
                elif col_strat == 'mode':
                    mode_val = self.df[col].mode()
                    if len(mode_val) > 0:
                        self.df[col] = self.df[col].fillna(mode_val[0])
                elif col_strat == 'constant' and fill_value is not None:
                    self.df[col] = self.df[col].fillna(fill_value)
            self.report['missing_handled'] = {'strategy': 'fill', 'column_strategy': column_strategy or 'auto'}

    def detect_duplicates(self, subset=None):
        if subset:
            dupes = self.df.duplicated(subset=subset, keep=False)
        else:
            dupes = self.df.duplicated(keep=False)
        self.report['duplicates_found'] = int(dupes.sum())
        return dupes

    def remove_duplicates(self, subset=None, keep='first'):
        self.detect_duplicates(subset)
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        self.report['duplicates_removed'] = before - len(self.df)

    def clean_whitespace(self):
        for col in self.df.select_dtypes(include='object').columns:
            self.df[col] = self.df[col].astype(str).str.strip()
            self.df[col] = self.df[col].replace({'': None, 'nan': None, 'none': None})

    def get_report(self):
        return self.report
