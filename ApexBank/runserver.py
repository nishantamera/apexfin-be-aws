import os
from waitress import serve
from ApexBank.wsgi import application

this_files_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(this_files_dir)

if __name__ == '__main__':
    serve(application, host = '0.0.0.0', port = '8001')
