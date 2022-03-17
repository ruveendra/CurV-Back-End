from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

from src.constances.http_status_code import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, \
    HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT

import validators
from src.database import User, db
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity

user = Blueprint("user", __name__, url_prefix="/api/v1/user")


@user.route('/', methods=['POST', 'GET'])
def user_register():
    if request.method == "POST":

        username = request.json['username']
        email = request.json['email']
        password = request.json['password']

        if len(password) < 6:
            return jsonify({
                'error': "Password is too short"
            }), HTTP_400_BAD_REQUEST

        if len(username) < 3:
            return jsonify({
                'error': "Username is too short"
            }), HTTP_400_BAD_REQUEST

        if not username.isalnum() or " " in username:
            return jsonify({
                'error': "Username should be alphanumeric, also no spaces"
            }), HTTP_400_BAD_REQUEST

        if not validators.email(email):
            return jsonify({
                'error': "Invalid Email"
            }), HTTP_400_BAD_REQUEST

        if not User.query.filter_by(email=email).first() is None:
            return jsonify({
                'error': "Email is taken"
            }), HTTP_409_CONFLICT

        if not User.query.filter_by(username=username).first() is None:
            return jsonify({
                'error': "username is taken"
            }), HTTP_409_CONFLICT

        pwd_hash = generate_password_hash(password)

        user = User(username=username, password=pwd_hash, email=email)
        db.session.add(user)
        db.session.commit()

        return jsonify({
            'message': "User Created",
            'user': {
                'username': username, 'email': email
            }
        }), HTTP_201_CREATED

    else:
        users = User.query.filter_by(status=1)

        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'api_key': user.api_key,
                'status': user.status
            })
        return jsonify({
            'data': data
        }), HTTP_200_OK


@user.get("/<int:id>")
@jwt_required()
def get_user(id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=id, status=1).first()

    if not user:
        return jsonify({
            'message': "User not found"
        }), HTTP_404_NOT_FOUND

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'api_key': user.api_key,
        'status': user.status
    }), HTTP_200_OK


@user.put('/<int:id>')
@user.patch('/<int:id>')
@jwt_required()
def edit_user(id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=id).first()

    if not user:
        return jsonify({
            'message': "User not found"
        }), HTTP_404_NOT_FOUND

    username = request.json['username']
    email = request.json['email']

    if not username.isalnum() or " " in username:
        return jsonify({
            'error': "Username should be alphanumeric, also no spaces"
        }), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({
            'error': "Invalid Email"
        }), HTTP_400_BAD_REQUEST

    if not User.query.filter_by(email=email).first() is None:
        return jsonify({
            'error': "Email is taken"
        }), HTTP_409_CONFLICT

    if not User.query.filter_by(username=username).first() is None:
        return jsonify({
            'error': "username is taken"
        }), HTTP_409_CONFLICT

    if not user:
        return jsonify({
            'message': "No user found"
        }), HTTP_400_BAD_REQUEST

    user.username = username
    user.email = email
    db.session.commit()

    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'api_key': user.api_key,
        'status': user.status
    }), HTTP_200_OK


@user.delete('/<int:id>')
@jwt_required()
def delete_user(id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=id).first()

    if not user:
        return jsonify({
            'message': "User not found"
        }), HTTP_404_NOT_FOUND

    user.status = 0
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT
