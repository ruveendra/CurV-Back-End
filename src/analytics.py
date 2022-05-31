import json
from datetime import datetime
from cerberus import Validator
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_caching import Cache
from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
from src.database import User, db, SensorData, Device, MainSensor, Setting, Jobtbl
from flask import current_app as app

analytics = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")

cache = Cache()

# ----------------------- main dashboard -----------------------------

# Line - Power usage for each device --- ,week, monthly, yearly-
# @analytics.get('/power_usage_for_each_device')
# @jwt_required()
# def power_usage_for_each_device():
#     group_by = request.json['group_by']
#
#     sql = ""
#     data = db.engine.execute(sql)
#
#     return jsonify({
#         "message": "success"
#     }), HTTP_200_OK


# pie - Pie chart device usage ---Daily (pick a date), monthly (pick a monthly), Yearly (pick a year) -
@analytics.post('/power-consumption-by-device')
@jwt_required()
def power_consumption_by_device():
    # group_by = request.json['group_by']
    # value = request.json['value']

    date_from = request.json['date_from']
    date_to = request.json['date_to']

    user_id = get_jwt_identity()

    convert = lambda s: datetime.strptime(s, '%Y-%m-%d')

    SCHEMA = {
        "date_from": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        },
        "date_to": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        }
    }

    v = Validator(SCHEMA)

    if not v.validate(request.json):
        return jsonify(v.errors), HTTP_400_BAD_REQUEST

    # sql = "SELECT device_id, {0}(created_at), SUM(sd.kw_sec) FROM sensor_data sd WHERE {0}(sd.created_at) = '{1}'
    # AND " \ "sd.user_id = '{2}' GROUP BY sd.device_id, {0}(sd.created_at)".format(group_by, value, user_id)
    # print(sql)

    sql = "SELECT device_id, SUM(sd.kw_sec) FROM sensor_data sd WHERE sd.created_at BETWEEN '{0}' AND '{1}' AND " \
          "sd.user_id = '{2}' GROUP BY sd.device_id".format(date_from, date_to, user_id)


    # with app.app_context():
    cache = Cache(config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 5
    })
    cache.init_app(app)

    data = cache.get(sql)

    if data is not None:
        data = json.loads(data)
        return jsonify(data), HTTP_200_OK
    else:
        data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'device_id': row[0],
            'total': row[1],
        })

    cache.set(sql, json.dumps(response), timeout=5)
    return jsonify({
        "data": response
    }), HTTP_200_OK


# line and bar - Cost and daily power Total --- monthly, yearly-
@analytics.post('/cost-bar-power-total')
@jwt_required()
def cost_bar_power_total():
    group_by = request.json['group_by']
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    user_id = get_jwt_identity()

    convert = lambda s: datetime.strptime(s, '%Y-%m-%d')
    SCHEMA = {
        "group_by": {
            "type": "string",
            "required": True,
            'empty': False,
            'allowed': ['DAY', 'MONTH', 'YEAR']
        },
        "date_from": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        },
        "date_to": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        }
    }

    v = Validator(SCHEMA)

    if not v.validate(request.json):
        return jsonify(v.errors), HTTP_400_BAD_REQUEST

    group_by_dict = {
        'YEAR': "%%Y",
        'MONTH': "%%Y-%%m",
        'DAY': "%%Y-%%m-%%d"
    }

    sql = 'SELECT DATE_FORMAT(sd.created_at,"' + group_by_dict[group_by] + '") as MONTH, SUM(sd.kw_sec) as TOTAL FROM ' \
                                                                           'sensor_data sd WHERE sd.user_id = "' + str(
        user_id) + '" AND sd.created_at BETWEEN "' + date_from + '" AND ' \
                                                                 '"' + date_to + '" GROUP BY DATE_FORMAT(sd.created_at,"' + \
          group_by_dict[group_by] + '") '

    # print(sql)
    # data = db.engine.execute(sql)

    cache = Cache(config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 5
    })
    cache.init_app(app)

    data = cache.get(sql)

    if data is not None:
        data = json.loads(data)
        return jsonify(data), HTTP_200_OK
    else:
        data = db.engine.execute(sql)

    def cost_logic(no_units):
        tot = 0
        remaining_units = no_units
        # print(no_units)
        settings = Setting.query.filter_by(setting="cost_values").first()
        data_values = json.loads(settings.value)

        for units_range in data_values:
            # print(units_range)
            if int(units_range["range_from"]) < remaining_units:
                units_in_range = remaining_units - units_range["range_from"]
                tot += units_in_range * units_range["value"]
                remaining_units = remaining_units - units_in_range
        return tot

    response = []
    for row in data:
        response.append({
            group_by.lower(): row[0],
            'total': row[1],
            'cost': cost_logic(row[1])
        })

    return jsonify({
        "data": response
    }), HTTP_200_OK


# bar peak off-peak usage -- monthly
@analytics.post('/peak-off-peak-usage')
@jwt_required()
def peak_off_peak_usage():
    # group_by = request.json['group_by']
    date_from = request.json['date_from']
    date_to = request.json['date_to']

    settings = Setting.query.filter_by(setting="off_peak_values").first()
    data = json.loads(settings.value)
    off_peak_start = data[0]['offpeak_start']
    off_peak_end = data[0]['offpeak_end']

    user_id = get_jwt_identity()

    convert = lambda s: datetime.strptime(s, '%Y-%m-%d')
    SCHEMA = {
        "date_from": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        },
        "date_to": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        }
    }

    sql = "SELECT sdmMain.sdmDate, hrgPeak.peakUsage ,hrgOff.offPeakUsage  FROM (SELECT DATE_FORMAT(sdm.created_at, '%%Y-%%m-%%d') as " \
          "sdmDate FROM	sensor_data sdm WHERE sdm.user_id = '{2}' AND sdm.created_at BETWEEN '{3}' AND '{4}' GROUP BY DATE_FORMAT(sdm.created_at, '%%Y-%%m-%%d')) AS sdmMain   LEFT " \
          "JOIN (SELECT   DATE(sd.created_at) as date,  SUM(sd.kw_sec) as peakUsage  FROM  sensor_data sd WHERE {0} >" \
          "HOUR(sd.created_at) AND {1} < HOUR(sd.created_at) GROUP BY   DATE(sd.created_at)) AS hrgPeak ON " \
          "hrgPeak.date = sdmMain.sdmDate   LEFT JOIN (SELECT   DATE(sd.created_at) as date,   SUM(sd.kw_sec) as " \
          "offPeakUsage   FROM sensor_data sd   WHERE   {0} < HOUR(sd.created_at) OR {1} > HOUR(sd.created_at) " \
          "GROUP BY DATE(sd.created_at)) AS hrgOff ON hrgOff.date = sdmMain.sdmDate".format(off_peak_start,
                                                                                            off_peak_end, user_id,
                                                                                            date_from, date_to)

    # data = db.engine.execute(sql)

    cache = Cache(config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 5
    })
    cache.init_app(app)

    data = cache.get(sql)

    if data is not None:
        data = json.loads(data)
        return jsonify(data), HTTP_200_OK
    else:
        data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'date': row[0],
            'peakUsage': row[1] if row[1] else 0,
            'offPeakUsage': row[2] if row[2] else 0
        })

    return jsonify({
        "data": response
    }), HTTP_200_OK


# ----------------------- device dashboard -----------------------------

# line and bar - Cost and daily power device --- monthly, yearly-
@analytics.post('/cost-bar-power-total-device/<int:id>')
@jwt_required()
def cost_and_daily_power_usage(id):
    group_by = request.json['group_by']
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    user_id = get_jwt_identity()

    convert = lambda s: datetime.strptime(s, '%Y-%m-%d')
    SCHEMA = {
        "group_by": {
            "type": "string",
            "required": True,
            'empty': False,
            'allowed': ['DAY', 'MONTH', 'YEAR']
        },
        "date_from": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        },
        "date_to": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        }
    }

    v = Validator(SCHEMA)

    if not v.validate(request.json):
        return jsonify(v.errors), HTTP_400_BAD_REQUEST

    device_id = Device.query.filter_by(id=id).first()

    group_by_dict = {
        'YEAR': "%%Y",
        'MONTH': "%%Y-%%m",
        'DAY': "%%Y-%%m-%%d"
    }

    sql = "SELECT DATE_FORMAT(sd.created_at, '{0}'), SUM(sd.kw_sec) FROM sensor_data sd WHERE sd.user_id = '{1}' AND " \
          "sd.created_at BETWEEN '{2}' AND '{3}' AND sd.device_id = '{4}' GROUP BY DATE_FORMAT(sd.created_at, '{0}') " \
          " ORDER BY DATE_FORMAT(sd.created_at, '{0}') DESC".format(group_by_dict[group_by], user_id, date_from,
                                                                    date_to,
                                                                    device_id.device_id)

    # data = db.engine.execute(sql)

    cache = Cache(config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 5
    })
    cache.init_app(app)

    data = cache.get(sql)

    if data is not None:
        data = json.loads(data)
        return jsonify(data), HTTP_200_OK
    else:
        data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            group_by.lower(): row[0],
            'total': row[1],
        })

    return jsonify({
        "data": response
    }), HTTP_200_OK


# meter - kwh usage -- Daily (pick a date), monthly (pick a monthly)
@analytics.post('/kwh_device_usage')
@jwt_required()
def kwh_device_usage():
    group_by = request.json['group_by']  # Upper case DAY, MONTH
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    device_id = request.json['device_id']

    convert = lambda s: datetime.strptime(s, '%Y-%m-%d')
    SCHEMA = {
        "group_by": {
            "type": "string",
            "required": True,
            'empty': False,
            'allowed': ['DAY', 'MONTH', 'YEAR']
        },
        "device_id": {
            "type": "string",
            "required": True,
            'empty': False
        },
        "date_from": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        },
        "date_to": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        }
    }

    v = Validator(SCHEMA)

    if not v.validate(request.json):
        return jsonify(v.errors), HTTP_400_BAD_REQUEST

    group_by_dict = {
        'YEAR': "%%Y",
        'MONTH': "%%Y-%%m",
        'DAY': "%%Y-%%m-%%d"
    }

    # sql = 'SELECT SUM(kw_sec) AS kw, DATE_FORMAT(sd.created_at, "'+group_by_dict[group_by]+'") as date_1 FROM
    # sensor_data sd WHERE device_id = "{1}" AND ' \ 'sd.created_at BETWEEN "{2}" AND "{3}" GROUP BY DATE_FORMAT(
    # sd.created_at, "'+group_by_dict[group_by]+'")'.format(device_id,date_from, date_to)

    sql = 'SELECT SUM(kw_sec) AS kw, DATE_FORMAT(sd.created_at, "' + group_by_dict[
        group_by] + '") as date_1 FROM sensor_data sd WHERE device_id = "' + device_id + '" AND ' \
                                                                                         'sd.created_at BETWEEN "' + date_from + '" AND "' + date_to + '" GROUP BY DATE_FORMAT(sd.created_at, "' + \
          group_by_dict[group_by] + '")'

    # data = db.engine.execute(sql)
    # print(data)

    cache = Cache(config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 5
    })
    cache.init_app(app)

    data = cache.get(sql)

    if data is not None:
        data = json.loads(data)
        return jsonify(data), HTTP_200_OK
    else:
        data = db.engine.execute(sql)


    response = []
    for row in data:
        response.append({
            'kwh': row[0] if row[0] else 0,
            'date': row[1],
        })

    return jsonify({
        "data": response
    }), HTTP_200_OK


# bar peak off-peak usage -- monthly
@analytics.post('/peak-off-peak-usage-device')
@jwt_required()
def peak_off_peak_usage_device():
    # group_by = request.json['group_by']
    # device_id = request.json['device_id']

    date_from = request.json['date_from']
    date_to = request.json['date_to']

    settings = Setting.query.filter_by(setting="off_peak_values").first()
    data = json.loads(settings.value)

    off_peak_start = data[0]['offpeak_start']
    off_peak_end = data[0]['offpeak_end']

    device_id = request.json['device_id']
    user_id = get_jwt_identity()

    convert = lambda s: datetime.strptime(s, '%Y-%m-%d')
    SCHEMA = {
        "device_id": {
            "type": "string",
            "required": True,
            'empty': False
        },
        "date_from": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        },
        "date_to": {
            "type": "datetime",
            'coerce': convert,
            "required": True,
            'empty': False
        }
    }
    v = Validator(SCHEMA)

    if not v.validate(request.json):
        return jsonify(v.errors), HTTP_400_BAD_REQUEST

    sql = "SELECT sdmMain.sdmDate,sdmMain.device_id,hrgPeak.peakUsage, hrgOff.offPeakUsage  FROM (SELECT DATE_FORMAT(" \
          "sdm.created_at, '%%Y-%%m-%%d') as sdmDate, sdm.device_id FROM	sensor_data sdm WHERE sdm.user_id = '{3}'  " \
          "AND sdm.created_at BETWEEN '{4}' AND '{5}' GROUP BY DATE_FORMAT(sdm.created_at, '%%Y-%%m-%%d'), " \
          "sdm.device_id) AS sdmMain LEFT JOIN (SELECT  DATE(sd.created_at) as date,  " \
          "sd.device_id as sdDeviceId,  SUM(sd.kw_sec) as peakUsage  FROM  sensor_data sd  WHERE  {0} > HOUR(" \
          "sd.created_at) AND {1} < HOUR(sd.created_at)  GROUP BY  sd.device_id, DATE(sd.created_at)) AS hrgPeak ON " \
          "hrgPeak.date = sdmMain.sdmDate AND sdmMain.device_id = hrgPeak.sdDeviceId  LEFT JOIN (SELECT  DATE(" \
          "sd.created_at) as date,  sd.device_id as sdDeviceId,  SUM(sd.kw_sec) as offPeakUsage  FROM " \
          "sensor_data sd   WHERE   {0} < HOUR(sd.created_at) OR {1} > HOUR(sd.created_at) GROUP BY sd.device_id, " \
          "DATE(sd.created_at)) AS hrgOff ON hrgOff.date = sdmMain.sdmDate AND sdmMain.device_id = hrgOff.sdDeviceId " \
          "WHERE sdmMain.device_id = '{2}'".format(off_peak_start, off_peak_end, device_id, user_id, date_from, date_to)

    # data = db.engine.execute(sql)

    cache = Cache(config={
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 5
    })
    cache.init_app(app)

    data = cache.get(sql)

    if data is not None:
        data = json.loads(data)
        return jsonify(data), HTTP_200_OK
    else:
        data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'date': row[0],
            'device_id': row[1],
            'peakUsage': row[2] if row[2] else 0,
            'offPeakUsage': row[3] if row[3] else 0
        })

    return jsonify({
        "data": response
    }), HTTP_200_OK


