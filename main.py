import os

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt, current_user

application = Flask(__name__)
application.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "just secret")
application.config["JWT_SECRET_KEY"] = os.getenv("SECRET_KEY", "just secret")
application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRE", 'sqlite:///tasks.db')

token_blacklist = set()

db = SQLAlchemy()
db.init_app(application)

jwt = JWTManager(application)

# Override flask jwt default message with custom made
@jwt.unauthorized_loader
def unauthorized(callback):
    return jsonify(status_code=404, response={"message": "User is unauthorized"}), 404

@jwt.revoked_token_loader
def unauthorized(header, payload):
    return jsonify(status_code=404, response={"message": "token revoked"}), 404

@jwt.expired_token_loader
def expired_token(header, payload):
    return jsonify(status_code=404, response={"message": "token expired"}), 404

@jwt.user_identity_loader
def user_identity_lookup(user_id):
    return user_id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return db.session.execute(db.select(User).where(User.id == identity)).scalar_one_or_none()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return len(token_blacklist) > 0 and jti in token_blacklist

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    is_done = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='tasks')

    # To provide string representation used for debugging
    def __repr__(self):
        return f'<Task {self.title}>'

    def as_dictionary(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    tasks = db.relationship("Task", back_populates='user')

with application.app_context():
    db.create_all()

@application.route('/add-task', methods=['POST'])
@jwt_required()
def add_task():
    task_title = request.form["task"]
    new_task = Task(title=task_title, user=current_user)
    db.session.add(new_task)
    db.session.commit()

    return jsonify(status_code=200, response={"message": "Successfully Add Task"}), 200


@application.route('/task')
@jwt_required()
def get_tasks():
    tasks = db.session.execute(db.select(Task).where(Task.user_id == current_user.id)).scalars().all()

    response = jsonify(status_code=200, tasks=[task.as_dictionary() for task in tasks])
    return response, 200


@application.route('/remove-task/<task_id>')
@jwt_required()
def delete_task(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    db.session.delete(task)
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Delete Task"})
    return response, 200


@application.route('/mark-done/<task_id>', methods=['PATCH'])
@jwt_required()
def mark_task_done(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    task.is_done = True
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Update Task"})
    return response, 200


@application.route('/edit-task/<task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    task.title = request.form["task"]
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Update Task"})
    return response, 200

@application.route('/register', methods=["POST"])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

    if user:
        return jsonify(status_code=400, error={"message": "Email Already Exist"}), 400
    else:
        new_user = User(
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8),
            name=name
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify(status_code=200, response={"message": "Successfully Register"}), 200

@application.route('/login', methods=["POST"])
def login():
    email = request.form['email']
    password = request.form['password']

    user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

    if not user:
        return jsonify(status_code=404, error={"message": "User Not Found"}), 404
    elif not check_password_hash(user.password, password):
        return jsonify(status_code=400, error={"message": "Wrong Password"}), 400
    else:
        access_token = create_access_token(identity=user.id)
        response = {
            "message": "Successfully Login",
            "token": access_token
        }
        return jsonify(status_code=200, response=response), 200


@application.route('/logout')
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    token_blacklist.add(jti)
    return jsonify(status_code=200, response={"message": "Successfully Logout"}), 200

if __name__ == "__main__":
    application.run(debug=True)
