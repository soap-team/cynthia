from app import app
from waitress import serve

serve(app, host='10.116.0.3', port='8080', threads=32, _quiet=True)
