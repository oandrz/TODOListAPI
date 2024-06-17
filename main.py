import os

from intelligence import gemini_ai
from flask import Flask
from auth.authorization import jwt
from auth.authentication import auth_blueprint
from database import db
from task.task import task_blueprint

application = Flask(__name__)
application.register_blueprint(auth_blueprint)
application.register_blueprint(task_blueprint)
application.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "just secret")
application.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "just secret")
application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRE", 'sqlite:///tasks.db')

db.init_app(application)
with application.app_context():
    db.create_all()

jwt.init_app(application)

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
