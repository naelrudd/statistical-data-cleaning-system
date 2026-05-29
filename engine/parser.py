import pandas as pd
import os

class DataParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.df = None
        self.filename = os.path.basename(filepath)

    def parse(self):
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext == '.csv':
            self.df = pd.read_csv(self.filepath, encoding='utf-8')
        elif ext in ('.xlsx', '.xls'):
            self.df = pd.read_excel(self.filepath, engine='openpyxl')
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        self.df.columns = [str(c).strip().lower() for c in self.df.columns]
        return self.df

    def get_info(self):
        if self.df is None:
            return {}
        return {
            'filename': self.filename,
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'col_names': list(self.df.columns),
            'dtypes': {c: str(self.df[c].dtype) for c in self.df.columns},
        }
