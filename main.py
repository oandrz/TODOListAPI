import os

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRE", 'sqlite:///tasks.db')
db = SQLAlchemy()
db.init_app(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    is_done = db.Column(db.Boolean, default=False)

    # To provide string representation used for debugging
    def __repr__(self):
        return f'<Task {self.title}>'

    def as_dictionary(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


@app.route('/add-task', methods=['POST'])
def add_task():
    if request.method == 'POST':
        task_title = request.form["task"]
        new_task = Task(title=task_title)
        db.session.add(new_task)
        db.session.commit()

        return jsonify(status_code=200, response={"message": "Successfully Add Task"}), 200
    return jsonify(status_code=404, response={"message": "Page Not Found"}), 400


@app.route('/task')
def get_tasks():
    tasks = db.session.execute(db.select(Task)).scalars().all()

    if len(tasks) == 0:
        return jsonify(status_code=404, error={"message": "We don't find any task "}), 200

    response = jsonify(status_code=200, tasks=[task.as_dictionary() for task in tasks])
    return response, 200


@app.route('/remove-task/<task_id>')
def delete_task(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    db.session.delete(task)
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Delete Task"})
    return response, 200


if __name__ == "__main__":
    app.run(debug=True)
