from flask import Blueprint, request, jsonify

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
from src.database import User, MainSensor, db, Device

mainsensor = Blueprint("mainsensor", __name__, url_prefix="/api/v1/main-sensor")


@mainsensor.get('/')
def main_sensor():

    api_key = request.args.get('api_key')
    device_id = request.args.get('device_id')
    voltage = request.args.get('voltage')
    ampere = request.args.get('ampere')

    user = User.query.filter_by(api_key=api_key).first()
    device = Device.query.filter_by(device_id=device_id).first()

    if not user:
        return jsonify({'error': "No user found"}), HTTP_400_BAD_REQUEST

    if not device:
        return jsonify({'error': "No device found"}), HTTP_400_BAD_REQUEST

    if not voltage:
        return jsonify({'error': "No value for voltage found"}), HTTP_400_BAD_REQUEST

    if not ampere:
        return jsonify({'error': "No value for ampere found"}), HTTP_400_BAD_REQUEST

    # mainsensor = MainSensor.query.filter_by(device_id=device_id).first()

    # if mainsensor:
        # update
        # mainsensor.voltage = voltage
        # mainsensor.ampere = ampere
        # db.session.commit()
    # else:
        # insert
    mainsensor = MainSensor(device_id=device_id, voltage=voltage, ampere=ampere, user_id=user.id)
    db.session.add(mainsensor)
    db.session.commit()

    return jsonify({
        "message": "success"

    }), HTTP_200_OK