import random
import string
from sqlalchemy import and_
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date

from src.constances.http_status_code import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_201_CREATED, \
    HTTP_409_CONFLICT, HTTP_204_NO_CONTENT
from src.database import User, db, Device, SensorData

devices = Blueprint("devices", __name__, url_prefix="/api/v1/devices")


@devices.route('/', methods=['POST', 'GET'])
@jwt_required()
def handle_devices():
    current_user = get_jwt_identity()
    if request.method == "POST":

        device_id = request.json['device_id']
        device_name = request.json['device_name']
        user_id = get_jwt_identity()

        if not device_id:
            return jsonify({
                'error': "No device id found"

            }), HTTP_400_BAD_REQUEST

        if not device_name:
            return jsonify({
                'error': "No device name found"

            }), HTTP_400_BAD_REQUEST

        # if not Device.query.filter(Device.device_id == device_id) is None:
        #     return jsonify({'error': "Device ID is taken"}), HTTP_409_CONFLICT

        if not Device.query.filter(and_(Device.device_name == device_name, Device.user_id == user_id)).first() is None:
            return jsonify({
                'error': "Device name is taken"

            }), HTTP_409_CONFLICT

        new_device = Device(device_id=device_id, device_name=device_name, device_status=0, device_switch=1,
                            status=1, user_id=user_id)
        db.session.add(new_device)
        db.session.commit()

        return jsonify({
            'message': "Device Created",

        }), HTTP_201_CREATED

    else:

        devices = Device.query.filter_by(user_id=current_user)
        # devices = db.engine.execute("SELECT * FROM device")

        data = []
        for device in devices:
            data.append({
                'id': device.id,
                'device_id': device.device_id,
                'device_name': device.device_name,
                'device_status': device.device_status,
                'device_switch': device.device_switch,
                'status': device.status,
            })

        return jsonify({
            'data': data

        }), HTTP_200_OK


@devices.get("/<int:id>")
@jwt_required()
def get_device(id):
    current_user = get_jwt_identity()

    device = Device.query.filter_by(user_id=current_user, id=id).first()

    if not device:
        return jsonify({
            'message': "device not found"

        }), HTTP_404_NOT_FOUND

    return jsonify({
        'id': device.id,
        'device_id': device.device_id,
        'device_name': device.device_name,
        'device_status': device.device_status,
        'device_switch': device.device_switch,
        'status': device.status,

    }), HTTP_200_OK


@devices.put('/<int:id>')
@devices.patch('/<int:id>')
@jwt_required()
def edit_device(id):
    current_user = get_jwt_identity()
    device = Device.query.filter_by(user_id=current_user, id=id).first()

    if not device:
        return jsonify({
            'message': "Device not found"

        }), HTTP_404_NOT_FOUND

    for key in request.json:
        setattr(device, key, request.json[key])

    db.session.commit()
    return jsonify({
        'id': device.id,
        'device_id': device.device_id,
        'device_name': device.device_name,
        'device_status': device.device_status,
        'device_switch': device.device_switch,
        'status': device.status,
        }), HTTP_200_OK


@devices.delete('/<int:id>')
@jwt_required()
def delete_device(id):
    current_user = get_jwt_identity()
    device = Device.query.filter_by(user_id=current_user, id=id).first()

    if not device:
        return jsonify({
            'message': "Device not found"

        }), HTTP_404_NOT_FOUND

    device.status = 0
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT


@devices.get('/get-usage-day')
@jwt_required()
def get_usage():
    # type = request.args.get('type')
    # start = request.args.get('start')
    # end = request.args.get('end')

    start = '2022-03-01'
    end = '2022-03-31'

    sql = "SELECT * FROM sensor_data WHERE created_at >= '{}' AND created_at <= '{}' AND user_id = 1".format(start,end)

    # data = SensorData.query.filter(SensorData.created_at >= start, SensorData.created_at >= end)
    sensor_data = db.engine.execute(sql)

    data = []
    device_id = 0
    ampere = 0
    power = 0

    for item in sensor_data:
        power = float(power) + item.kw_sec

    return jsonify({
        'power': power

    }), HTTP_200_OK


@devices.get('/device-switch/<int:id>')
@jwt_required()
def device_switch(id):

    status = request.json['status']

    if status == 'true' or status == 'True':
        switch_status = True

    elif status == 'false' or status == 'False':
        switch_status = False
    else:
        return jsonify({
            "error": "Please sent True or False only"
        }), HTTP_400_BAD_REQUEST

    device = Device.query.filter_by(id=id).first()

    if device:
        device.device_switch = switch_status
        db.session.commit()
        status = "Updated Successfully"
        status_code = HTTP_200_OK
    else:
        status = "Updated Unsuccessful -Device Not Found"
        status_code = HTTP_404_NOT_FOUND

    return jsonify({
        "message": status
    }), status_code


@devices.get('/preview')
@jwt_required()
def add_new_device():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()

    characters = string.digits + string.ascii_letters
    picked_chars = ''.join(random.choices(characters, k=8))

    return jsonify({
        "api_key": user.api_key,
        "new_device_id": picked_chars

    }), HTTP_200_OK


@devices.get('/get-online-status/<int:id>')
@jwt_required()
def check_online_status(id):
    user_id = get_jwt_identity()
    device = Device.query.filter_by(id=id).first()
    status = device.device_status
    device.device_status = False
    db.session.commit()

    return jsonify({
        "status": status,

    }), HTTP_200_OK


# ------ ESP8266 Endpoint -------
@devices.get('/set-online-status')
def set_device_online_status():
    api_key = request.args.get('api_key')
    device_id = request.args.get('device_id')
    status = request.args.get('status')

    user = User.query.filter_by(api_key=api_key).first()
    device = Device.query.filter_by(device_id=device_id).first()

    if status == 'true' or status == 'True':
        online_status = True

    elif status == 'false' or status == 'False':
        online_status = False
    else:
        return jsonify({
            "error": "Please sent True or False only"
        }), HTTP_400_BAD_REQUEST

    if not user:
        return jsonify({
            'error': "Authentication failed"

        }), HTTP_400_BAD_REQUEST

    if not device:
        return jsonify({
            'error': "No device found"

        }), HTTP_400_BAD_REQUEST

    if not status:
        return jsonify({
            'error': "No value for status found"

        }), HTTP_400_BAD_REQUEST

    device = Device.query.filter_by(device_id=device_id).first()

    if device:
        device.device_status = online_status
        db.session.commit()

        return jsonify({
            "message": "Update Successful"

        }), HTTP_200_OK

    else:
        return jsonify({
            "message": "success"

        }), HTTP_200_OK


# ------ ESP8266 Endpoint -------
@devices.get("/read-switch-status")
def read_device_switch():
    api_key = request.args.get('api_key')
    device_id = request.args.get('device_id')

    user = User.query.filter_by(api_key=api_key).first()
    device = Device.query.filter_by(device_id=device_id).first()

    if not user:
        return jsonify({
            'error': "Authentication failed"

        }), HTTP_400_BAD_REQUEST

    if not device:
        return jsonify({
            'error': "No device found"

        }), HTTP_400_BAD_REQUEST

    return jsonify({
        "data": device.device_switch

    }), HTTP_200_OK


@devices.get('/real-time-stats/<int:id>')
@jwt_required()
def real_time_stats(id):

    user_id = get_jwt_identity()
    device = Device.query.filter_by(id=id).first()

    if not device:
        return jsonify({
            'error': "No device found"

        }), HTTP_400_BAD_REQUEST

    today = date.today()

    sql = "SELECT *, (SELECT SUM(kw_sec) FROM sensor_data as sd WHERE sd.created_at >='{}')  as kw_sum FROM " \
          "sensor_data WHERE device_id='{}' ORDER BY created_at DESC LIMIT 1".format(today, device.device_id )

    sensor_data = db.engine.execute(sql).first()
    power = sensor_data.voltage * sensor_data.ampere

    return jsonify({
        'voltage': sensor_data.voltage if sensor_data.voltage else 0,
        'ampere': sensor_data.ampere if sensor_data.ampere else 0,
        'power': power if power else 0,
        'kwh': sensor_data.kw_sum if sensor_data.kw_sum else 0

    }), HTTP_200_OK