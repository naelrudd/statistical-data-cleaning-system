import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_VERCEL = os.environ.get('VERCEL', False) or os.environ.get('VERCEL_ENV', False)

if IS_VERCEL:
    UPLOAD_FOLDER = '/tmp/uploads'
    EXPORT_FOLDER = '/tmp/exports'
else:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}
MAX_CONTENT_LENGTH = 30 * 1024 * 1024
SECRET_KEY = os.environ.get('SECRET_KEY', 'bps-capstone-secret-key-2026')

ZSCORE_THRESHOLD = 3
IQR_MULTIPLIER = 1.5

VALIDATION_RULES = {
    'gender': {'L', 'P'},
    'age': (0, 120),
}

CROSS_VALIDATION_RULES = [
    {
        'name': 'Student with age > 40',
        'conditions': {'status': 'sekolah'},
        'check': lambda r: r.get('umur', 0) > 40,
        'message': 'Umur {umur} tidak sesuai dengan status sekolah'
    },
    {
        'name': 'Working age < 10',
        'conditions': {'status_kerja': 'bekerja'},
        'check': lambda r: r.get('umur', 100) < 10,
        'message': 'Umur {umur} terlalu muda untuk bekerja'
    },
    {
        'name': 'Married age < 15',
        'conditions': {'status_perkawinan': 'kawin'},
        'check': lambda r: r.get('umur', 0) < 15,
        'message': 'Umur {umur} belum cukup untuk menikah'
    },
    {
        'name': 'Pensioner age < 45',
        'conditions': {'status_kerja': 'pensiun'},
        'check': lambda r: r.get('umur', 100) < 45,
        'message': 'Umur {umur} terlalu muda untuk pensiun'
    },
    {
        'name': 'Child working',
        'conditions': {},
        'check': lambda r: r.get('umur', 100) < 15 and str(r.get('status_kerja', '')).lower() == 'bekerja',
        'message': 'Anak umur {umur} tidak boleh bekerja'
    },
]
