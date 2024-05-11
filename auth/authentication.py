from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from auth.shared_auth import token_blacklist
from database import db

auth_blueprint = Blueprint('auth_blueprint', __name__)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

    tasks = db.relationship("Task", back_populates='user')


@auth_blueprint.route('/register', methods=["POST"])
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


@auth_blueprint.route('/login', methods=["POST"])
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


@auth_blueprint.route('/logout')
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    token_blacklist.add(jti)
    return jsonify(status_code=200, response={"message": "Successfully Logout"}), 200
