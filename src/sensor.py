from datetime import datetime
from decimal import Decimal

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
from src.database import User, db, SensorData, Device, MainSensor

sensor = Blueprint("sensor", __name__, url_prefix="/api/v1/sensor")


@sensor.get('/')
def data_sensor():
    api_key = request.args.get('api_key')
    device_id = request.args.get('device_id')
    ampere = request.args.get('ampere')
    print(ampere)
    user = User.query.filter_by(api_key=api_key).first()
    device = Device.query.filter_by(device_id=device_id).first()

    if not user:
        return jsonify({'error': "No user found"}), HTTP_400_BAD_REQUEST

    if not device:
        return jsonify({'error': "No device found"}), HTTP_400_BAD_REQUEST

    if not ampere:
        return jsonify({'error': "No value for ampere found"}), HTTP_400_BAD_REQUEST

    main_sensor = MainSensor.query.filter_by(user_id=user.id).first()

    power = float(main_sensor.voltage) * float(ampere)
    kilo_watt_per_10_sec = (power * 0.00277778) / 1000

    # data = kilo_watt_per_10_sec * 360
    kilo_watt_round = round(kilo_watt_per_10_sec, 8)

    sensor_data = SensorData(device_id=device_id, voltage=main_sensor.voltage, ampere=ampere,
                             kw_sec=kilo_watt_round, user_id=user.id, created_at=datetime.now())

    db.session.add(sensor_data)
    db.session.commit()

    return jsonify({
        "message": "success"

    }), HTTP_200_OK
