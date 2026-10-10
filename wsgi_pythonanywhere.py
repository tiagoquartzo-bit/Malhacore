import sys
import os

# Caminho base do projeto no ambiente do PythonAnywhere
app_dir = os.path.expanduser('~/06.MalhaCore')
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Converte aplicação ASGI (FastAPI) em WSGI para compatibilidade com PythonAnywhere
from asgiref.wsgi import WsgiToAsgi
from main import app as asgi_app

application = WsgiToAsgi(asgi_app)
