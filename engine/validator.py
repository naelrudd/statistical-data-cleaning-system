import pandas as pd
import re
from config import VALIDATION_RULES, CROSS_VALIDATION_RULES

class DataValidator:
    def __init__(self, df):
        self.df = df.copy()
        self.errors = {}
        self.cross_errors = []
        self.format_errors = {}

    def validate_format(self, rules=None):
        if rules is None:
            rules = VALIDATION_RULES
        self.format_errors = {}
        for col, rule in rules.items():
            if col not in self.df.columns:
                continue
            col_errors = []
            if isinstance(rule, set):
                for idx, val in self.df[col].items():
                    if pd.notna(val) and str(val).strip() not in rule:
                        col_errors.append({
                            'row': int(idx) + 2,
                            'value': str(val),
                            'rule': f"Must be one of: {', '.join(rule)}"
                        })
            elif isinstance(rule, tuple):
                lo, hi = rule
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                for idx, val in self.df[col].items():
                    if pd.notna(val) and (val < lo or val > hi):
                        col_errors.append({
                            'row': int(idx) + 2,
                            'value': str(val),
                            'rule': f"Range {lo}-{hi}"
                        })
            if col_errors:
                self.format_errors[col] = col_errors
        return self.format_errors

    def validate_cross(self, rules=None):
        if rules is None:
            rules = CROSS_VALIDATION_RULES
        self.cross_errors = []
        for rule in rules:
            cond = rule['conditions']
            check_fn = rule['check']
            message_tpl = rule['message']
            rule_name = rule['name']
            for idx, row in self.df.iterrows():
                match = True
                for k, v in cond.items():
                    if k not in row or str(row[k]).strip().lower() != v.lower():
                        match = False
                        break
                if match:
                    try:
                        if check_fn(row):
                            msg = message_tpl.format(**row.to_dict())
                            self.cross_errors.append({
                                'row': int(idx) + 2,
                                'rule': rule_name,
                                'message': msg
                            })
                    except:
                        pass
        return self.cross_errors

    def validate_codes(self, code_columns=None):
        if code_columns is None:
            code_columns = {}
        code_errors = {}
        for col, pattern in code_columns.items():
            if col not in self.df.columns:
                continue
            col_errors = []
            regex = re.compile(pattern)
            for idx, val in self.df[col].items():
                if pd.notna(val):
                    s = str(val).strip()
                    if not regex.match(s):
                        col_errors.append({
                            'row': int(idx) + 2,
                            'value': s,
                            'rule': f"Pattern: {pattern}"
                        })
            if col_errors:
                code_errors[col] = col_errors
        return code_errors

    def get_all_errors(self):
        total = 0
        for col, errs in self.format_errors.items():
            total += len(errs)
        total += len(self.cross_errors)
        return total

    def get_summary(self):
        return {
            'format_errors': {c: len(e) for c, e in self.format_errors.items()},
            'cross_errors': len(self.cross_errors),
            'total': self.get_all_errors(),
        }
