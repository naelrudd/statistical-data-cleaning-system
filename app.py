import os, uuid
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from werkzeug.utils import secure_filename
from engine import DataParser, DataCleaner, DataValidator, OutlierDetector, QualityScorer, DataExporter
from config import UPLOAD_FOLDER, EXPORT_FOLDER, ALLOWED_EXTENSIONS, TEMP_FOLDER, IS_VERCEL
from r2_storage import r2

app = Flask(__name__)
app.config.from_object('config')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

sessions = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def store_upload(file, session_id):
    ext = os.path.splitext(file.filename)[1]
    safe_name = f"{session_id}{ext}"
    local_path = os.path.join(UPLOAD_FOLDER, safe_name)
    file.save(local_path)
    if r2.enabled:
        r2.upload(local_path, f"uploads/{safe_name}")
    return local_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Invalid file type. Use .xlsx, .xls, or .csv', 'error')
            return redirect(request.url)

        session_id = str(uuid.uuid4())
        filepath = store_upload(file, session_id)

        parser = DataParser(filepath)
        df = parser.parse()
        info = parser.get_info()

        sessions[session_id] = {
            'filepath': filepath,
            'df': df,
            'original_df': df.copy(),
            'info': info,
            'cleaner_report': {},
            'validator_summary': {},
            'outlier_summary': {},
            'quality_scores': {},
            'missing_strategy': None,
        }

        return redirect(url_for('dashboard', session_id=session_id))
    return render_template('upload.html')

@app.route('/dashboard/<session_id>')
def dashboard(session_id):
    session = sessions.get(session_id)
    if not session:
        flash('Session not found', 'error')
        return redirect(url_for('index'))
    r2_enabled = 'true' if r2.enabled else 'false'
    return render_template('dashboard.html', session_id=session_id, info=session['info'], r2_enabled=r2_enabled)

@app.route('/api/<session_id>/info')
def api_info(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session['info'])

@app.route('/api/<session_id>/preview')
def api_preview(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    df = session['df']
    head = df.head(20).fillna('').to_dict(orient='records')
    cols = list(df.columns)
    return jsonify({'columns': cols, 'rows': head, 'total': len(df)})

@app.route('/api/<session_id>/clean', methods=['POST'])
def api_clean(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    data = request.get_json() or {}
    strategy = data.get('strategy', 'drop')
    fill_value = data.get('fill_value')
    column_strategy = data.get('column_strategy')
    remove_dups = data.get('remove_duplicates', True)
    dup_subset = data.get('dup_subset')

    df = session['original_df'].copy()
    cleaner = DataCleaner(df)
    cleaner.clean_whitespace()
    cleaner.detect_missing()

    if strategy == 'drop':
        cleaner.handle_missing(strategy='drop')
    else:
        cleaner.handle_missing(strategy='fill', fill_value=fill_value, column_strategy=column_strategy)

    if remove_dups:
        cleaner.remove_duplicates(subset=dup_subset if dup_subset else None)

    session['df'] = cleaner.df
    session['cleaner_report'] = cleaner.get_report()
    session['missing_strategy'] = strategy

    return jsonify({'report': cleaner.get_report(), 'rows': len(cleaner.df)})

@app.route('/api/<session_id>/validate', methods=['POST'])
def api_validate(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    data = request.get_json() or {}
    code_patterns = data.get('code_patterns', {})

    validator = DataValidator(session['df'])
    validator.validate_format()
    validator.validate_cross()
    if code_patterns:
        validator.validate_codes(code_patterns)

    session['validator_summary'] = validator.get_summary()
    session['format_errors'] = validator.format_errors
    session['cross_errors'] = validator.cross_errors

    return jsonify({
        'summary': validator.get_summary(),
        'format_errors': validator.format_errors,
        'cross_errors': validator.cross_errors
    })

@app.route('/api/<session_id>/outliers', methods=['POST'])
def api_outliers(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    data = request.get_json() or {}
    columns = data.get('columns')

    detector = OutlierDetector(session['df'])
    detector.detect_all(columns)
    session['outlier_summary'] = detector.get_summary()

    return jsonify(detector.get_summary())

@app.route('/api/<session_id>/quality')
def api_quality(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    scorer = QualityScorer(
        session['df'],
        session.get('cleaner_report', {}),
        session.get('validator_summary', {}),
        session.get('outlier_summary', {})
    )
    scores = scorer.compute()
    session['quality_scores'] = scores

    return jsonify(scores)

@app.route('/api/<session_id>/charts')
def api_charts(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    exporter = DataExporter(
        session['df'],
        session.get('quality_scores', {}),
        session.get('cleaner_report', {}),
        session.get('validator_summary', {}),
        session.get('outlier_summary', {})
    )
    charts = exporter.generate_charts()
    return jsonify({'charts': charts})

@app.route('/export/<session_id>/excel')
def export_excel(session_id):
    session = sessions.get(session_id)
    if not session:
        flash('Session not found', 'error')
        return redirect(url_for('index'))

    out_path = os.path.join(EXPORT_FOLDER, f"cleaned_{session_id}.xlsx")
    exporter = DataExporter(
        session['df'],
        session.get('quality_scores', {}),
        session.get('cleaner_report', {}),
        session.get('validator_summary', {}),
        session.get('outlier_summary', {})
    )
    exporter.export_cleaned(out_path)

    if r2.enabled:
        r2.upload(out_path, f"exports/cleaned_{session_id}.xlsx")
        url = r2.presigned_url(f"exports/cleaned_{session_id}.xlsx")
        return redirect(url)

    return send_file(out_path, as_attachment=True, download_name='cleaned_data.xlsx')

@app.route('/export/<session_id>/report')
def export_report(session_id):
    session = sessions.get(session_id)
    if not session:
        flash('Session not found', 'error')
        return redirect(url_for('index'))

    scorer = QualityScorer(
        session['df'],
        session.get('cleaner_report', {}),
        session.get('validator_summary', {}),
        session.get('outlier_summary', {})
    )
    scores = scorer.compute()

    exporter = DataExporter(
        session['df'],
        scores,
        session.get('cleaner_report', {}),
        session.get('validator_summary', {}),
        session.get('outlier_summary', {})
    )
    html = exporter.generate_report_html()

    out_path = os.path.join(EXPORT_FOLDER, f"report_{session_id}.html")
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    if r2.enabled:
        r2.upload(out_path, f"exports/report_{session_id}.html")
        url = r2.presigned_url(f"exports/report_{session_id}.html")
        return redirect(url)

    return send_file(out_path, as_attachment=True, download_name='validation_report.html')

if __name__ == '__main__':
    app.run(debug=not IS_VERCEL, port=5000)
