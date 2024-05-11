from flask import jsonify
from flask_jwt_extended import JWTManager

from auth.authentication import User
from auth.shared_auth import token_blacklist
from database import db


jwt = JWTManager()


@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload['jti']
    return len(token_blacklist) > 0 and jti in token_blacklist

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
