from flask import Flask, session
import os
from routes import routes_bp
from models import db, User
from config import Config
from flask_migrate import Migrate


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONT_DIR = os.path.join(BASE_DIR, "frond")

app = Flask(
    __name__,
    static_folder=os.path.join(FRONT_DIR, "static"),
    template_folder=FRONT_DIR
)

app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(routes_bp)

app.secret_key = app.config['SECRET_KEY']
print("STATIC_FOLDER:", app.static_folder)
print("TEMPLATE_FOLDER:", app.template_folder)

if __name__ == '__main__':
    app.run(debug=True)

