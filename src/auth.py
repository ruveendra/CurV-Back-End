from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from src import app
from src.constances.http_status_code import HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT, HTTP_201_CREATED, \
    HTTP_401_UNAUTHORIZED, HTTP_200_OK, HTTP_404_NOT_FOUND

import validators
from src.database import User, db
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth.post('/login')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')

    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'username': user.username,
                    'email': user.email
                }

            }), HTTP_200_OK

    return jsonify({
        'error': "Wrong login credentials"

    }), HTTP_401_UNAUTHORIZED


@auth.get("/me")
# @jwt_required()
def me():
    url = request.args.get('test')
    apikey = request.args.get('apikey')
    # user_id = get_jwt_identity()

    user = User.query.filter_by(api_key=apikey).first()

    return jsonify({
        # 'username': user.username,
        # 'email': user.email,
        # 'url': url,
        'apikey': apikey

    }), HTTP_200_OK


@auth.get('/token/refresh')
@jwt_required(refresh=True)
def refresh_user_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        'access': access

    }), HTTP_200_OK


@auth.put('/password-change')
@auth.patch('/password-change')
@jwt_required()
def password_change():

    current_password = request.json['current_password']
    new_password = request.json['new_password']
    confirm_new_password = request.json['confirm_new_password']

    if not current_password:
        return jsonify({
            'error': "current password field  empty"

        }), HTTP_400_BAD_REQUEST

    if not new_password:
        return jsonify({
            'error': "new password field  empty"

        }), HTTP_400_BAD_REQUEST

    if not confirm_new_password:
        return jsonify({
            'error': "confirm new password field  empty"

        }), HTTP_400_BAD_REQUEST

    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    print(current_password)
    is_pass_correct = check_password_hash(user.password, current_password)

    if not is_pass_correct:
        return jsonify({
            'error': "current password incorrect"

        }), HTTP_401_UNAUTHORIZED

    if current_password == new_password:
        return jsonify({
            'error': "new password cannot be current password"

        }), HTTP_400_BAD_REQUEST

    if not new_password == confirm_new_password:
        return jsonify({
            'error': "password doesn't match"

        }), HTTP_400_BAD_REQUEST

    pwd_hash = generate_password_hash(new_password)
    user.password = pwd_hash
    db.session.commit()

    return jsonify({
        'message': "password change successfully"

    }), HTTP_200_OK


@auth.put('/user-email-update')
@auth.patch('/user-email-update')
@jwt_required()
def user_email_update():

    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    email = request.json['email']

    if not validators.email(email):
        return jsonify({
            'error': "Invalid Email"

        }), HTTP_400_BAD_REQUEST

    if not User.query.filter_by(email=email).first() is None:
        return jsonify({
            'error': "Email is taken"

        }), HTTP_409_CONFLICT

    if not user:
        return jsonify({
            'message': "No user found"

        }), HTTP_404_NOT_FOUND

    user.email = email
    db.session.commit()

    return jsonify({
        'message': "update successful",

    }), HTTP_200_OK


@auth.put('/user-username-update')
@auth.patch('/user-username-update')
@jwt_required()
def user_update():

    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    username = request.json['username']

    if not username.isalnum() or " " in username:
        return jsonify({
            'error': "Username should be alphanumeric, also no spaces"

        }), HTTP_400_BAD_REQUEST

    if not User.query.filter_by(username=username).first() is None:
        return jsonify({
            'error': "username is taken"

        }), HTTP_409_CONFLICT

    if not user:
        return jsonify({
            'message': "No user found"

        }), HTTP_404_NOT_FOUND

    user.username = username
    db.session.commit()

    return jsonify({
        'message': "Update successful",

    }), HTTP_200_OK