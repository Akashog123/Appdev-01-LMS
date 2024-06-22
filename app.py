from flask import Flask 
from Dependancies.database import db
from Dependancies.chartsApi import api

app = None

def create_app():
    app = Flask(__name__)
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///lib_ma_sys_db.sqlite3"
    pdf_folder = 'static\\pdf_folder'
    thumbnail_folder = 'static\\thumbnail_folder'
    app.config['pdf_folder'] = pdf_folder
    app.config['thumbnail_folder'] = thumbnail_folder
    db.init_app(app)
    api.init_app(app)
    app.app_context().push()
    return app

app = create_app()
from Dependancies.controllers import *

if __name__ == "__main__":
    app.run()