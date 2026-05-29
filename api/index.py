import os, sys, uuid, io, base64, re, json
from datetime import datetime
from flask import Flask, render_template as _rt, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

VERCEL = os.environ.get('VERCEL_ENV', '')
TEMPLATE_DIR = os.path.join(BASE, 'templates')
STATIC_DIR = os.path.join(BASE, 'static')
UPLOAD_DIR = '/tmp/statclean/uploads' if VERCEL else os.path.join(BASE, 'uploads')
EXPORT_DIR = '/tmp/statclean/exports' if VERCEL else os.path.join(BASE, 'exports')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs('/tmp/statclean', exist_ok=True)

# Detect if templates are available on filesystem
TEMPLATES_AVAILABLE = os.path.isdir(TEMPLATE_DIR)

app = Flask(__name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR)
app.secret_key = os.environ.get('SECRET_KEY', 'bps-capstone-secret-key-2026')
app.config['MAX_CONTENT_LENGTH'] = 30 * 1024 * 1024

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# ==================== EMBEDDED TEMPLATES (fallback) ====================
BASE_HTML = '''<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>{% block title %}StatClean{% endblock %}</title><script src=https://cdn.jsdelivr.net/npm/chart.js@4></script><style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,Tahoma,Geneva,Verdana,sans-serif;background:#f0f2f5;color:#333;min-height:100vh}
nav{background:#1565C0;color:#fff;padding:1rem 2rem;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 8px rgba(0,0,0,.15)}
nav h1{font-size:1.4rem;font-weight:600}nav h1 span{font-weight:300;opacity:.8}
nav a{color:#fff;text-decoration:none;margin-left:1.5rem;font-size:.9rem}
nav a:hover{text-decoration:underline}
.container{max-width:1200px;margin:0 auto;padding:2rem}
.card{background:#fff;border-radius:10px;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.card h3{color:#1565C0;margin-bottom:1rem;font-weight:600}
.btn{display:inline-block;padding:.6rem 1.4rem;border:none;border-radius:6px;font-size:.9rem;font-weight:500;cursor:pointer;text-decoration:none;transition:all .2s}
.btn-primary{background:#1565C0;color:#fff}.btn-primary:hover{background:#0D47A1}
.btn-success{background:#2E7D32;color:#fff}.btn-success:hover{background:#1B5E20}
.btn-warning{background:#f57f17;color:#fff}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.5rem}
.grid-4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:1.5rem}
.stat-card{background:#fff;border-radius:10px;padding:1.5rem;text-align:center;box-shadow:0 2px 4px rgba(0,0,0,.08)}
.stat-card .number{font-size:2.2rem;font-weight:700;color:#1565C0}
.stat-card .label{font-size:.85rem;color:#666;margin-top:.3rem}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th,td{padding:.6rem;text-align:left;border-bottom:1px solid #e0e0e0}
th{background:#f5f5f5;font-weight:600;position:sticky;top:0}
.table-wrap{max-height:400px;overflow-y:auto;border:1px solid #e0e0e0;border-radius:6px}
.badge{display:inline-block;padding:.2rem .6rem;border-radius:12px;font-size:.75rem;font-weight:600}
.badge-success{background:#e8f5e9;color:#2e7d32}.badge-danger{background:#ffebee;color:#c62828}
.step-indicator{display:flex;justify-content:center;gap:.5rem;margin-bottom:2rem}
.step{padding:.5rem 1rem;background:#e0e0e0;border-radius:20px;font-size:.8rem;color:#666}
.step.active{background:#1565C0;color:#fff}.step.done{background:#2E7D32;color:#fff}
select,input[type=text]{padding:.5rem;border:1px solid #ccc;border-radius:4px;font-size:.9rem;width:100%}
label{display:block;margin-bottom:.3rem;font-weight:500;font-size:.85rem}
.form-group{margin-bottom:1rem}.flex{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap}
.loading{display:none;text-align:center;padding:2rem}.loading.active{display:block}
.spinner{border:3px solid #e0e0e0;border-top:3px solid #1565C0;border-radius:50%;width:40px;height:40px;animation:spin .8s linear infinite;margin:0 auto}
@keyframes spin{to{transform:rotate(360deg)}}
.mt-2{margin-top:1rem}.mt-3{margin-top:1.5rem}.text-center{text-align:center}
@media(max-width:768px){.grid-2,.grid-3,.grid-4{grid-template-columns:1fr}}
</style></head><body>
<nav><h1>StatClean <span>| Data Cleaning System</span></h1><div><a href=/ >Home</a><a href=/upload>Upload</a></div></nav>
<div class=container>{% block content %}{% endblock %}</div></body></html>'''

def render(template_name, **ctx):
    if TEMPLATES_AVAILABLE:
        try: return _rt(template_name, **ctx)
        except: pass
    from jinja2 import Template
    templates = {
        'index.html': INDEX_HTML,
        'upload.html': UPLOAD_HTML,
        'dashboard.html': DASHBOARD_HTML,
    }
    tmpl_str = templates.get(template_name)
    if not tmpl_str:
        return _rt(template_name, **ctx)
    t = Template(tmpl_str)
    return t.render(**ctx)

INDEX_HTML = '''{% extends "base.html" %}
{% block content %}
<div class=text-center style="padding:3rem 0">
<h1 style="font-size:2.5rem;color:#1565C0;margin-bottom:1rem">Statistical Data Cleaning System</h1>
<p style="font-size:1.1rem;color:#555;max-width:700px;margin:0 auto 2rem">Web-based automated preprocessing and validation system for statistical data. Upload your Excel or CSV files for automatic cleaning, validation, and quality scoring.</p>
<a href=/upload class="btn btn-primary" style="font-size:1.1rem;padding:.8rem 2.5rem">Get Started</a></div>
<div class=grid-3 style="margin-top:2rem">
<div class="card text-center"><div style="font-size:2.5rem;margin-bottom:.5rem">📤</div><h3>Upload</h3><p style="color:#666;font-size:.9rem">Upload .xlsx, .xls, or .csv files</p></div>
<div class="card text-center"><div style="font-size:2.5rem;margin-bottom:.5rem">🧹</div><h3>Auto Clean</h3><p style="color:#666;font-size:.9rem">Missing values, duplicates, format validation</p></div>
<div class="card text-center"><div style="font-size:2.5rem;margin-bottom:.5rem">📊</div><h3>Quality Report</h3><p style="color:#666;font-size:.9rem">Visual dashboard with charts and scores</p></div></div>
{% endblock %}'''

UPLOAD_HTML = '''{% extends "base.html" %}
{% block content %}
<div class="card text-center" style="padding:3rem">
<h3>Upload Dataset</h3><p style="color:#666;margin-bottom:1.5rem">Formats: .xlsx, .xls, .csv (Max 30MB)</p>
<form method=POST enctype=multipart/form-data>
<div style="border:2px dashed #ccc;border-radius:10px;padding:3rem;margin-bottom:1.5rem" onclick="document.getElementById('f').click()">
<div style="font-size:3rem;margin-bottom:.5rem">📁</div><p style="color:#888">Click to select file</p></div>
<input type=file name=file id=f accept=.xlsx,.xls,.csv style=display:none required>
<button type=submit class="btn btn-primary" style="font-size:1.1rem;padding:.8rem 3rem">Upload & Process</button></form></div>{% endblock %}'''

DASHBOARD_HTML = '''{% extends "base.html" %}
{% block content %}
<input type=hidden id=sid value="{{ session_id }}">
<div class=step-indicator><div class="step active" id=st1>1. Preview</div><div class=step id=st2>2. Clean</div><div class=step id=st3>3. Validate</div><div class=step id=st4>4. Quality</div><div class=step id=st5>5. Export</div></div>
<div class=card><div class="flex" style="justify-content:space-between"><h3>Dataset: {{ info.filename }}</h3><div class=flex><span class="badge badge-success">{{ info.rows }} rows</span><span class="badge badge-success">{{ info.columns }} cols</span></div></div></div>
<div class=grid-4>
<div class=stat-card><div class=number id=sRows>{{ info.rows }}</div><div class=label>Total Rows</div></div>
<div class=stat-card><div class="number" id=sMissing>-</div><div class=label>Missing Values</div></div>
<div class=stat-card><div class="number" id=sErrors>-</div><div class=label>Errors Found</div></div>
<div class=stat-card><div class="number" id=sScore>-</div><div class=label>Quality Score</div></div></div>
<div class=card><h3>Data Preview</h3><div class=table-wrap id=preview><div class="loading active"><div class=spinner></div></div></div></div>

<div class="flex mt-2" style=gap:1rem>
<button class="btn btn-primary" onclick=runPipeline()>Run Full Pipeline</button>
<button class="btn btn-success" onclick=runCleaning()>1. Clean</button>
<button class="btn btn-warning" onclick=runValidation()>2. Validate</button>
</div>

<div id=cleanSection style=display:none class="card mt-3"><h3>Cleaning Results</h3><div id=cleanResult></div></div>
<div id=valSection style=display:none class="card mt-3"><h3>Validation Results</h3><div id=valResult></div></div>
<div id=outSection style=display:none class="card mt-3"><h3>Outlier Detection</h3><div id=outResult></div></div>
<div id=qualSection style=display:none class="card mt-3"><h3>Quality Score</h3><div class=grid-2><div id=gauge class=text-center style=padding:2rem></div><div id=qualDetails></div></div></div>
<div id=chartSection style=display:none class="card mt-3"><h3>Visualizations</h3><div id=chartContainer></div></div>
<div id=exportSection style=display:none class="card mt-3"><h3>Export</h3><div class=flex style=gap:1rem><a class="btn btn-success" href=/export/{{ session_id }}/excel>Download Cleaned Excel</a><a class="btn btn-warning" href=/export/{{ session_id }}/report>Download Report</a></div></div>

<script>
const sid=document.getElementById('sid').value;loadPreview();
async function loadPreview(){const r=await(await fetch('/api/'+sid+'/preview')).json();let h='<table><thead><tr>';r.columns.forEach(c=>h+='<th>'+esc(c)+'</th>');h+='</tr></thead><tbody>';r.rows.forEach(row=>{h+='<tr>';r.columns.forEach(c=>h+='<td>'+esc(row[c])+'</td>');h+='</tr>'});h+='</tbody></table>';document.getElementById('preview').innerHTML=h}
async function runPipeline(){await runCleaning();await runValidation();await loadQuality();await loadCharts();document.getElementById('exportSection').style.display='block';document.getElementById('st5').classList.add('done')}
async function runCleaning(){const r=await(await fetch('/api/'+sid+'/clean',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({strategy:'drop',remove_duplicates:true})})).json();const rep=r.report;document.getElementById('cleanSection').style.display='block';document.getElementById('st2').classList.add('done');const mc=Object.values(rep.missing_before||{}).reduce((a,b)=>a+b,0);document.getElementById('sMissing').textContent=mc;document.getElementById('sRows').textContent=r.rows;document.getElementById('st3').classList.add('active');let h='<div class=grid-3><div class=stat-card><div class=number>'+mc+'</div><div class=label>Missing</div></div><div class=stat-card><div class=number>'+rep.duplicates_found+'</div><div class=label>Duplicates</div></div><div class=stat-card><div class=number>'+(rep.duplicates_removed||0)+'</div><div class=label>Removed</div></div></div>';document.getElementById('cleanResult').innerHTML=h;document.getElementById('st3').classList.remove('active');return r}
async function runValidation(){const r=await(await fetch('/api/'+sid+'/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).json();document.getElementById('valSection').style.display='block';document.getElementById('st3').classList.add('done');const t=r.summary.total;document.getElementById('sErrors').textContent=t;let h='<div class=grid-3><div class=stat-card><div class=number style=color:#c62828>'+t+'</div><div class=label>Errors</div></div><div class=stat-card><div class=number>'+r.summary.cross_errors+'</div><div class=label>Cross-Validations</div></div></div>';if(r.format_errors){h+='<h4>Format Errors</h4><div class=table-wrap style=max-height:200px><table><tr><th>Column</th><th>Errors</th></tr>';for(const[c,errs]of Object.entries(r.format_errors))h+='<tr><td>'+c+'</td><td>'+errs.length+'</td></tr>';h+='</table></div>'}document.getElementById('valResult').innerHTML=h;document.getElementById('outSection').style.display='block';return r}
async function loadQuality(){const r=await(await fetch('/api/'+sid+'/quality')).json();const o=r.overall||0;document.getElementById('sScore').textContent=o+'%';document.getElementById('st4').classList.add('done');let h='<canvas id=gChart width=280 height=280></canvas>';document.getElementById('gauge').innerHTML=h;new Chart(document.getElementById('gChart'),{type:'doughnut',data:{labels:['Score','Remaining'],datasets:[{data:[o,100-o],backgroundColor:['#1565C0','#e0e0e0'],borderWidth:0}]},options:{cutout:'70%',plugins:{legend:{display:false}}}});let d='<table><tr><th>Dimension</th><th>Score</th></tr>';['completeness','consistency','duplicate_free','format_validity','outlier_free'].forEach(k=>{const lb={'completeness':'Completeness','consistency':'Consistency','duplicate_free':'No Duplicates','format_validity':'Format Validity','outlier_free':'No Outliers'};d+='<tr><td>'+(lb[k]||k)+'</td><td>'+(r[k]||0)+'</td></tr>'});d+='</table>';document.getElementById('qualDetails').innerHTML=d;document.getElementById('chartSection').style.display='block';return r}
async function loadCharts(){const r=await(await fetch('/api/'+sid+'/charts')).json();if(r.charts&&r.charts.summary)document.getElementById('chartContainer').innerHTML='<img src="data:image/png;base64,'+r.charts.summary+'" style=max-width:100%;border-radius:8px>';document.getElementById('st5').classList.add('active')}
function esc(s){if(s===null||s===undefined)return '';const d=document.createElement('div');d.textContent=String(s);return d.innerHTML}
</script>{% endblock %}'''

sessions = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== IMPORTS ====================
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ==================== CORE ENGINE ====================
class DataParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.df = None
    def parse(self):
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext == '.csv':
            self.df = pd.read_csv(self.filepath, encoding='utf-8')
        else:
            self.df = pd.read_excel(self.filepath, engine='openpyxl')
        self.df.columns = [str(c).strip().lower() for c in self.df.columns]
        return self.df
    def get_info(self):
        if self.df is None: return {}
        return {'filename': self.filename, 'rows': len(self.df), 'columns': len(self.df.columns),
                'col_names': list(self.df.columns), 'dtypes': {c: str(self.df[c].dtype) for c in self.df.columns}}

class DataCleaner:
    def __init__(self, df):
        self.df = df.copy()
        self.report = {'missing_before': {}, 'missing_after': {}, 'duplicates_found': 0, 'duplicates_removed': 0, 'missing_handled': {}}
    def detect_missing(self):
        self.df = self.df.replace({'': None, '-': None, 'n/a': None, 'na': None, 'none': None, 'null': None, 'N/A': None, 'NULL': None}, np.nan)
        for col in self.df.columns:
            c = int(self.df[col].isna().sum())
            if c > 0: self.report['missing_before'][col] = c
        return self.report['missing_before']
    def handle_missing(self, strategy='drop', column_strategy=None):
        self.detect_missing()
        if strategy == 'drop':
            b = len(self.df); self.df = self.df.dropna(); a = len(self.df)
            self.report['missing_handled'] = {'strategy': 'drop', 'rows_dropped': b - a}
        elif strategy == 'fill':
            for col in self.df.columns:
                if self.df[col].isna().sum() == 0: continue
                cs = (column_strategy or {}).get(col, 'auto')
                if cs == 'auto':
                    cs = 'mode' if self.df[col].dtype in ('object', 'category') else 'mean'
                if cs == 'mean': self.df[col] = self.df[col].fillna(self.df[col].mean())
                elif cs == 'median': self.df[col] = self.df[col].fillna(self.df[col].median())
                elif cs == 'mode':
                    mv = self.df[col].mode()
                    if len(mv) > 0: self.df[col] = self.df[col].fillna(mv[0])
            self.report['missing_handled'] = {'strategy': 'fill'}
    def detect_duplicates(self, subset=None):
        dupes = self.df.duplicated(subset=subset, keep=False)
        self.report['duplicates_found'] = int(dupes.sum()); return dupes
    def remove_duplicates(self, subset=None):
        self.detect_duplicates(subset)
        b = len(self.df); self.df = self.df.drop_duplicates(subset=subset)
        self.report['duplicates_removed'] = b - len(self.df)
    def clean_whitespace(self):
        for col in self.df.select_dtypes(include='object').columns:
            self.df[col] = self.df[col].astype(str).str.strip()
            self.df[col] = self.df[col].replace({'': None, 'nan': None, 'none': None})
    def get_report(self): return self.report

VALIDATION_RULES = {'gender': {'L', 'P'}, 'age': (0, 120)}
CROSS_VALIDATION_RULES = [
    {'name': 'Student age > 40', 'conditions': {'status': 'sekolah'}, 'check': lambda r: r.get('umur', 0) > 40, 'message': 'Umur {umur} tidak sesuai status sekolah'},
    {'name': 'Working age < 10', 'conditions': {'status_kerja': 'bekerja'}, 'check': lambda r: r.get('umur', 100) < 10, 'message': 'Umur {umur} terlalu muda untuk bekerja'},
    {'name': 'Married age < 15', 'conditions': {'status_perkawinan': 'kawin'}, 'check': lambda r: r.get('umur', 0) < 15, 'message': 'Umur {umur} belum cukup menikah'},
    {'name': 'Pensioner age < 45', 'conditions': {'status_kerja': 'pensiun'}, 'check': lambda r: r.get('umur', 100) < 45, 'message': 'Umur {umur} terlalu muda pensiun'},
    {'name': 'Child working', 'conditions': {}, 'check': lambda r: r.get('umur', 100) < 15 and str(r.get('status_kerja', '')).lower() == 'bekerja', 'message': 'Anak umur {umur} tidak boleh bekerja'},
]

class DataValidator:
    def __init__(self, df):
        self.df = df.copy(); self.errors = {}; self.cross_errors = []; self.format_errors = {}
    def validate_format(self):
        for col, rule in VALIDATION_RULES.items():
            if col not in self.df.columns: continue
            col_errors = []
            if isinstance(rule, set):
                for idx, val in self.df[col].items():
                    if pd.notna(val) and str(val).strip() not in rule:
                        col_errors.append({'row': int(idx) + 2, 'value': str(val), 'rule': f"Must be: {', '.join(rule)}"})
            elif isinstance(rule, tuple):
                lo, hi = rule
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                for idx, val in self.df[col].items():
                    if pd.notna(val) and (val < lo or val > hi):
                        col_errors.append({'row': int(idx) + 2, 'value': str(val), 'rule': f"Range {lo}-{hi}"})
            if col_errors: self.format_errors[col] = col_errors
        return self.format_errors
    def validate_cross(self):
        self.cross_errors = []
        for rule in CROSS_VALIDATION_RULES:
            for idx, row in self.df.iterrows():
                match = all(str(row.get(k, '')).strip().lower() == v.lower() for k, v in rule['conditions'].items())
                if match:
                    try:
                        if rule['check'](row):
                            self.cross_errors.append({'row': int(idx) + 2, 'rule': rule['name'], 'message': rule['message'].format(**row.to_dict())})
                    except: pass
        return self.cross_errors
    def get_summary(self):
        total = sum(len(e) for e in self.format_errors.values()) + len(self.cross_errors)
        return {'format_errors': {c: len(e) for c, e in self.format_errors.items()}, 'cross_errors': len(self.cross_errors), 'total': total}

class OutlierDetector:
    def __init__(self, df):
        self.df = df.copy(); self.outliers = {}
    def detect_all(self, columns=None):
        if columns is None: columns = self.df.select_dtypes(include=[np.number]).columns
        for col in columns:
            if col not in self.df.columns: continue
            vals = self.df[col].dropna()
            if len(vals) < 4: continue
            z = np.abs(scipy_stats.zscore(vals, nan_policy='omit'))
            o_idx = vals.index[z > 3]
            if len(o_idx) == 0:
                q1, q3 = vals.quantile(0.25), vals.quantile(0.75)
                iqr = q3 - q1
                o_idx = vals[(vals < q1 - 1.5*iqr) | (vals > q3 + 1.5*iqr)].index
            if len(o_idx) > 0:
                self.outliers[col] = {'count': len(o_idx), 'rows': [int(i)+2 for i in o_idx], 'values': [float(self.df.loc[i, col]) for i in o_idx[:10]]}
        return self.outliers
    def get_summary(self):
        return {'total_outliers': sum(o['count'] for o in self.outliers.values()), 'details': self.outliers}

class QualityScorer:
    def __init__(self, df, cleaner_report, validator_summary, outlier_summary):
        self.df = df; self.cr = cleaner_report; self.vs = validator_summary; self.os = outlier_summary
        self.total_rows = max(len(df), 1); self.total_cells = max(self.total_rows * max(len(df.columns), 1), 1)
    def compute(self):
        mc = sum(self.cr.get('missing_before', {}).values())
        completeness = max(0, 100 - mc / self.total_cells * 100)
        dup = self.cr.get('duplicates_found', 0)
        dup_score = max(0, 100 - dup / self.total_rows * 100)
        te = self.vs.get('total', 0)
        fmt_score = max(0, 100 - te / self.total_cells * 100)
        to = self.os.get('total_outliers', 0)
        out_score = max(0, 100 - to / self.total_rows * 100)
        ce = self.vs.get('cross_errors', 0)
        consistency = max(0, 100 - ce / self.total_rows * 100)
        overall = round(completeness*0.3 + consistency*0.25 + dup_score*0.2 + fmt_score*0.15 + out_score*0.1, 1)
        grade = 'A' if overall >= 90 else 'B' if overall >= 75 else 'C' if overall >= 60 else 'D'
        return {'overall': overall, 'grade': grade, 'completeness': round(completeness,1), 'consistency': round(consistency,1),
                'duplicate_free': round(dup_score,1), 'format_validity': round(fmt_score,1), 'outlier_free': round(out_score,1)}

class DataExporter:
    def __init__(self, df, scores, cr, vs, os_):
        self.df = df; self.scores = scores; self.cr = cr; self.vs = vs; self.os = os_
    def export_cleaned(self, path): self.df.to_excel(path, index=False, engine='openpyxl')
    def generate_charts(self):
        charts = {}
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        md = self.cr.get('missing_before', {})
        if md:
            axes[0,0].bar(list(md.keys()), list(md.values()), color='orange')
            axes[0,0].set_title('Missing Values per Column')
            plt.setp(axes[0,0].xaxis.get_majorticklabels(), rotation=45, ha='right')
        else: axes[0,0].text(0.5, 0.5, 'No Missing Values', ha='center', va='center'); axes[0,0].set_title('Missing Values')
        fe = self.vs.get('format_errors', {})
        if fe:
            axes[0,1].bar(list(fe.keys()), list(fe.values()), color='red')
            axes[0,1].set_title('Format Errors per Column')
            plt.setp(axes[0,1].xaxis.get_majorticklabels(), rotation=45, ha='right')
        else: axes[0,1].text(0.5, 0.5, 'No Format Errors', ha='center', va='center'); axes[0,1].set_title('Format Errors')
        te = self.vs.get('total', 0); tr = len(self.df)
        axes[1,0].pie([max(1, tr-te), te], labels=['Valid', 'Invalid'], autopct='%1.1f%%', colors=['#4CAF50','#f44336'])
        axes[1,0].set_title('Valid vs Invalid')
        keys = ['completeness','consistency','duplicate_free','format_validity','outlier_free']
        labels = ['Completeness','Consistency','No Dupes','Format','No Outliers']
        axes[1,1].bar(labels, [self.scores.get(k,0) for k in keys], color='#2196F3')
        axes[1,1].set_title('Quality Scores'); axes[1,1].set_ylim(0,100)
        plt.setp(axes[1,1].xaxis.get_majorticklabels(), rotation=45, ha='right')
        plt.tight_layout()
        buf = io.BytesIO(); fig.savefig(buf, format='png', dpi=100); buf.seek(0)
        charts['summary'] = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig); return charts
    def generate_report_html(self):
        charts = self.generate_charts()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        tr = len(self.df); rb = tr + self.cr.get('duplicates_removed',0)
        mh = sum(self.cr.get('missing_before', {}).values())
        return f'''<html><head><meta charset=utf-8><title>Validation Report</title><style>
body{{font-family:Arial,sans-serif;margin:40px}}h1{{color:#1565C0}}.score{{font-size:48px;color:#4CAF50}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#1565C0;color:#fff}}.card{{background:#f5f5f5;padding:15px;margin:10px 0;border-radius:5px}}
img{{max-width:100%}}</style></head><body>
<h1>Data Quality Report</h1><p>Generated: {now}</p>
<h2>Overall Score: {self.scores.get("overall",0)} / 100 (Grade: {self.scores.get("grade","N/A")})</h2>
<div class=card><h3>Processing Summary</h3>
<table><tr><th>Metric</th><th>Value</th></tr>
<tr><td>Rows (original)</td><td>{rb}</td></tr>
<tr><td>Rows (final)</td><td>{tr}</td></tr>
<tr><td>Duplicates Removed</td><td>{self.cr.get("duplicates_removed",0)}</td></tr>
<tr><td>Missing Values Handled</td><td>{mh}</td></tr>
<tr><td>Format Errors</td><td>{self.vs.get("total",0)}</td></tr>
<tr><td>Outliers Detected</td><td>{self.os.get("total_outliers",0)}</td></tr>
</table></div><img src="data:image/png;base64,{charts["summary"]}" alt=Charts></body></html>'''

# ==================== CLOUD RF R2 ====================
r2_enabled = False
try:
    import boto3
    from botocore.config import Config
    aid = os.environ.get('R2_ACCOUNT_ID', '')
    ak = os.environ.get('R2_ACCESS_KEY', '')
    sk = os.environ.get('R2_SECRET_KEY', '')
    if aid and ak and sk:
        r2_client = boto3.client('s3', endpoint_url=f'https://{aid}.r2.cloudflarestorage.com',
            aws_access_key_id=ak, aws_secret_access_key=sk,
            config=Config(signature_version='s3v4'), region_name='auto')
        r2_enabled = True
except: pass

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_route():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return render('upload.html')
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Invalid file type. Use .xlsx, .xls, or .csv', 'error')
            return render('upload.html')
        session_id = str(uuid.uuid4())
        ext = os.path.splitext(file.filename)[1]
        fp = os.path.join(UPLOAD_DIR, f"{session_id}{ext}")
        file.save(fp)
        if r2_enabled:
            try: r2_client.upload_file(fp, os.environ.get('R2_BUCKET', 'statclean'), f"uploads/{session_id}{ext}")
            except: pass
        parser = DataParser(fp); df = parser.parse(); info = parser.get_info()
        sessions[session_id] = {'filepath': fp, 'df': df, 'original_df': df.copy(), 'info': info,
            'cleaner_report': {}, 'validator_summary': {}, 'outlier_summary': {}, 'quality_scores': {}}
        return redirect(url_for('dashboard', session_id=session_id))
    return render('upload.html')

@app.route('/dashboard/<session_id>')
def dashboard(session_id):
    s = sessions.get(session_id)
    if not s: flash('Session not found', 'error'); return redirect(url_for('index'))
    return render('dashboard.html', session_id=session_id, info=s['info'])

@app.route('/api/<session_id>/preview')
def api_preview(session_id):
    s = sessions.get(session_id)
    if not s: return jsonify({'error': 'Not found'}), 404
    head = s['df'].head(20).fillna('').to_dict(orient='records')
    return jsonify({'columns': list(s['df'].columns), 'rows': head, 'total': len(s['df'])})

@app.route('/api/<session_id>/clean', methods=['POST'])
def api_clean(session_id):
    s = sessions.get(session_id)
    if not s: return jsonify({'error': 'Not found'}), 404
    data = request.get_json() or {}
    df = s['original_df'].copy()
    cleaner = DataCleaner(df); cleaner.clean_whitespace(); cleaner.detect_missing()
    strategy = data.get('strategy', 'drop')
    if strategy == 'drop': cleaner.handle_missing(strategy='drop')
    else: cleaner.handle_missing(strategy='fill', column_strategy=data.get('column_strategy'))
    if data.get('remove_duplicates', True): cleaner.remove_duplicates(subset=data.get('dup_subset'))
    s['df'] = cleaner.df; s['cleaner_report'] = cleaner.get_report()
    return jsonify({'report': cleaner.get_report(), 'rows': len(cleaner.df)})

@app.route('/api/<session_id>/validate', methods=['POST'])
def api_validate(session_id):
    s = sessions.get(session_id)
    if not s: return jsonify({'error': 'Not found'}), 404
    validator = DataValidator(s['df']); validator.validate_format(); validator.validate_cross()
    s['validator_summary'] = validator.get_summary()
    return jsonify({'summary': validator.get_summary(), 'format_errors': validator.format_errors, 'cross_errors': validator.cross_errors})

@app.route('/api/<session_id>/outliers', methods=['POST'])
def api_outliers(session_id):
    s = sessions.get(session_id)
    if not s: return jsonify({'error': 'Not found'}), 404
    detector = OutlierDetector(s['df']); detector.detect_all()
    s['outlier_summary'] = detector.get_summary()
    return jsonify(detector.get_summary())

@app.route('/api/<session_id>/quality')
def api_quality(session_id):
    s = sessions.get(session_id)
    if not s: return jsonify({'error': 'Not found'}), 404
    scorer = QualityScorer(s['df'], s.get('cleaner_report',{}), s.get('validator_summary',{}), s.get('outlier_summary',{}))
    scores = scorer.compute(); s['quality_scores'] = scores
    return jsonify(scores)

@app.route('/api/<session_id>/charts')
def api_charts(session_id):
    s = sessions.get(session_id)
    if not s: return jsonify({'error': 'Not found'}), 404
    exporter = DataExporter(s['df'], s.get('quality_scores',{}), s.get('cleaner_report',{}), s.get('validator_summary',{}), s.get('outlier_summary',{}))
    charts = exporter.generate_charts()
    return jsonify({'charts': charts})

@app.route('/export/<session_id>/excel')
def export_excel(session_id):
    s = sessions.get(session_id)
    if not s: flash('Session not found', 'error'); return redirect(url_for('index'))
    out_path = os.path.join(EXPORT_DIR, f"cleaned_{session_id}.xlsx")
    exporter = DataExporter(s['df'], s.get('quality_scores',{}), s.get('cleaner_report',{}), s.get('validator_summary',{}), s.get('outlier_summary',{}))
    exporter.export_cleaned(out_path)
    if r2_enabled:
        try:
            r2_client.upload_file(out_path, os.environ.get('R2_BUCKET','statclean'), f"exports/cleaned_{session_id}.xlsx")
            url = r2_client.generate_presigned_url('get_object', Params={'Bucket': os.environ.get('R2_BUCKET','statclean'), 'Key': f"exports/cleaned_{session_id}.xlsx"}, ExpiresIn=3600)
            return redirect(url)
        except: pass
    return send_file(out_path, as_attachment=True, download_name='cleaned_data.xlsx')

@app.route('/export/<session_id>/report')
def export_report(session_id):
    s = sessions.get(session_id)
    if not s: flash('Session not found', 'error'); return redirect(url_for('index'))
    scorer = QualityScorer(s['df'], s.get('cleaner_report',{}), s.get('validator_summary',{}), s.get('outlier_summary',{}))
    exporter = DataExporter(s['df'], scorer.compute(), s.get('cleaner_report',{}), s.get('validator_summary',{}), s.get('outlier_summary',{}))
    html = exporter.generate_report_html()
    out_path = os.path.join(EXPORT_DIR, f"report_{session_id}.html")
    with open(out_path, 'w', encoding='utf-8') as f: f.write(html)
    if r2_enabled:
        try:
            r2_client.upload_file(out_path, os.environ.get('R2_BUCKET','statclean'), f"exports/report_{session_id}.html")
            url = r2_client.generate_presigned_url('get_object', Params={'Bucket': os.environ.get('R2_BUCKET','statclean'), 'Key': f"exports/report_{session_id}.html"}, ExpiresIn=3600)
            return redirect(url)
        except: pass
    return send_file(out_path, as_attachment=True, download_name='validation_report.html')
