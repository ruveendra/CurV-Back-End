from flask import Blueprint, request, jsonify

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
from src.database import User, db, SensorData, Device

sensor = Blueprint("sensor", __name__, url_prefix="/api/v1/sensor")


@sensor.get('/')
def data_sensor():
    api_key = request.args.get('api_key')
    device_id = request.args.get('device_id')
    ampere = request.args.get('ampere')

    user = User.query.filter_by(api_key=api_key).first()
    device = Device.query.filter_by(device_id=device_id).first()

    if not user:
        return jsonify({'error': "No user found"}), HTTP_400_BAD_REQUEST

    if not device:
        return jsonify({'error': "No device found"}), HTTP_400_BAD_REQUEST

    if not ampere:
        return jsonify({'error': "No value for ampere found"}), HTTP_400_BAD_REQUEST

    sensor_data = SensorData(data=ampere, device_id=device_id, user_id=user.id)
    db.session.add(sensor_data)
    db.session.commit()

    return jsonify({
        "message":"success"
    }), HTTP_200_OK