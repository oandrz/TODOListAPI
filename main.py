import os

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "just secret")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRE", 'sqlite:///tasks.db')
db = SQLAlchemy()
db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.execute(db.select(User).where(User.id == user_id)).scalar_one_or_none()

@login_manager.unauthorized_handler
def unauthorized():
    return jsonify(status_code=404, response={"message": "User is unauthorized"}), 404


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    is_done = db.Column(db.Boolean, default=False)

    # To provide string representation used for debugging
    def __repr__(self):
        return f'<Task {self.title}>'

    def as_dictionary(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))


with app.app_context():
    db.create_all()

@app.route('/add-task', methods=['POST'])
@login_required
def add_task():
    if request.method == 'POST':
        task_title = request.form["task"]
        new_task = Task(title=task_title)
        db.session.add(new_task)
        db.session.commit()

        return jsonify(status_code=200, response={"message": "Successfully Add Task"}), 200
    return jsonify(status_code=404, response={"message": "Page Not Found"}), 400


@app.route('/task')
@login_required
def get_tasks():
    tasks = db.session.execute(db.select(Task)).scalars().all()

    if len(tasks) == 0:
        return jsonify(status_code=404, error={"message": "We don't find any task "}), 200

    response = jsonify(status_code=200, tasks=[task.as_dictionary() for task in tasks])
    return response, 200


@app.route('/remove-task/<task_id>')
@login_required
def delete_task(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    db.session.delete(task)
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Delete Task"})
    return response, 200


@app.route('/mark-done/<task_id>', methods=['PATCH'])
@login_required
def mark_task_done(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    task.is_done = True
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Update Task"})
    return response, 200


@app.route('/edit-task/<task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    task.title = request.form["task"]
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Update Task"})
    return response, 200

@app.route('/register', methods=["POST"])
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

@app.route('/login', methods=["POST"])
def login():
    email = request.form['email']
    password = request.form['password']

    user = db.session.execute(db.select(User).where(User.email == email)).scalar_one_or_none()

    if not user:
        return jsonify(status_code=404, error={"message": "User Not Found"}), 404
    elif not check_password_hash(user.password, password):
        return jsonify(status_code=400, error={"message": "Wrong Password"}), 400
    else:
        login_user(user)
        return jsonify(status_code=200, response={"message": "Successfully Login"}), 200


@app.route('/logout')
def logout():
    logout_user()
    return jsonify(status_code=200, response={"message": "Successfully Logout"}), 200

if __name__ == "__main__":
    app.run(debug=True)
