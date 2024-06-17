from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from intelligence import gemini_ai

from database import db


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


task_blueprint = Blueprint('task_blueprint', __name__)


@task_blueprint.route('/add-task', methods=['POST'])
@jwt_required()
def add_task():
    task_title = request.form["task"]
    if not task_title:
        return jsonify(status_code=400, response={"message": "Task title is required"}), 400
    new_task = Task(title=task_title, user=current_user)
    db.session.add(new_task)
    db.session.commit()

    return jsonify(status_code=200, response={"message": "Successfully Add Task"}), 200


@task_blueprint.route('/task')
@jwt_required()
def get_tasks():
    tasks = db.session.execute(db.select(Task).where(Task.user_id == current_user.id)).scalars().all()
    response = jsonify(status_code=200, tasks=[task.as_dictionary() for task in tasks])
    return response, 200


@task_blueprint.route('/remove-task/<task_id>')
@jwt_required()
def delete_task(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    db.session.delete(task)
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Delete Task"})
    return response, 200


@task_blueprint.route('/mark-done/<task_id>', methods=['PATCH'])
@jwt_required()
def mark_task_done(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    task.is_done = True
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Update Task"})
    return response, 200


@task_blueprint.route('/edit-task/<task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    task = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar_one_or_none()

    if task is None:
        return jsonify(status_code=404, error={"message": "Task Not Found"}), 404

    task.title = request.form["task"]
    db.session.commit()

    response = jsonify(status_code=200, response={"message": "Successfully Update Task"})
    return response, 200


@task_blueprint.route('/generate-task', methods=['POST'])
@jwt_required()
def generate_task_ai():
    query = f"query:{request.form["query"]}"
    result, status_code = gemini_ai.request_gemini(query)

    # Guard empty task list
    if result is None and status_code == 200:
        return jsonify(status_code=404, error={"message": "We unable to generate task from your query, please try "
                                                          "another query"}), 404
    # Guard if the 'error' field exists in the response
    if 'error' in result:
        return jsonify(status_code=404, error={"message": result['error']}), 404

    response = jsonify(status_code=status_code, response=result)

    return response, status_code
