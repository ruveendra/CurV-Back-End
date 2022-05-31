import json
from decimal import Decimal

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
from src.database import User, db, SensorData, Device, MainSensor, Setting

settings = Blueprint("settings", __name__, url_prefix="/api/v1/settings")


@settings.get('/cost-set')
def set_setting():
    no_units = 170
    data = [
        {
            "range_from": 168,
            "value": 45,
        },
        {
            "range_from": 112,
            "value": 32,
        },
        {
            "range_from": 84,
            "value": 27.75,
        },
        {
            "range_from": 56,
            "value": 10,
        },
        {
            "range_from": 0,
            "value": 7.85,
        }
    ]
    data_json = json.dumps(data)
    tot = 0
    remaining_units = no_units

    for units_range in data:
        print(units_range)
        if units_range["range_from"] < remaining_units:
            units_in_range = remaining_units - units_range["range_from"]
            tot += units_in_range * units_range["value"]
            remaining_units = remaining_units - units_in_range

    print(tot)
    print(remaining_units)

    settings = Setting.query.filter_by(setting="cost_values").first()

    if settings:
        settings.value = data_json
        db.session.commit()
    else:
        setting = Setting(setting="cost_values", value=data_json)
        db.session.add(setting)
        db.session.commit()

    return jsonify({
        "message": "Success"
    }), HTTP_200_OK


@settings.get('/offpeak-set')
def offpeak_setting():
    data = [{
        "offpeak_start": "22",
        "offpeak_end": "06",
    }]
    data_json = json.dumps(data)

    settings = Setting.query.filter_by(setting="off_peak_values").first()

    if settings:
        settings.value = data_json
        db.session.commit()
    else:
        setting = Setting(setting="off_peak_values", value=data_json)
        db.session.add(setting)
        db.session.commit()

    return jsonify({
        "message": "Success"
    }), HTTP_200_OK
