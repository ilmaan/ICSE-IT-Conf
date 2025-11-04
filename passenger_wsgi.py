import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# If you're using a virtual environment, uncomment and set the path:
# virtualenv = os.path.join(os.path.dirname(__file__), 'venv')
# if os.path.exists(virtualenv):
#     activate_this = os.path.join(virtualenv, 'bin', 'activate_this.py')
#     if os.path.exists(activate_this):
#         exec(open(activate_this).read(), {'__file__': activate_this})

# For Python 3.4+ use importlib, for older Python keep imp
try:
    from importlib import util
    spec = util.spec_from_file_location('wsgi', os.path.join(os.path.dirname(__file__), 'ICSE_ET', 'wsgi.py'))
    wsgi = util.module_from_spec(spec)
    spec.loader.exec_module(wsgi)
except ImportError:
    # Fallback for older Python versions
    import imp
    wsgi = imp.load_source('wsgi', os.path.join(os.path.dirname(__file__), 'ICSE_ET', 'wsgi.py'))

application = wsgi.application
