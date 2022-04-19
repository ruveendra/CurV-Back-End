import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
from src.database import User, db, SensorData, Device, MainSensor, Setting

analytics = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


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
@analytics.get('/power-consumption-by-device')
@jwt_required()
def power_consumption_by_device():
    group_by = request.json['group_by']
    value = request.json['value']
    user_id = get_jwt_identity()

    sql = "SELECT device_id, {0}(created_at), SUM(sd.kw_sec) FROM sensor_data sd WHERE {0}(sd.created_at) = '{1}' AND "\
          "sd.user_id = '{2}' GROUP BY sd.device_id, {0}(sd.created_at)".format(group_by, value, user_id)
    print(sql)
    data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'device_id': row[0],
            group_by.lower(): row[1],
            'total': row[2],
        })

    return jsonify(response), HTTP_200_OK


# line and bar - Cost and daily power Total --- monthly, yearly-
@analytics.get('/cost-bar-power-total')
@jwt_required()
def cost_bar_power_total():
    group_by = request.json['group_by']
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    user_id = get_jwt_identity()

    sql = "SELECT {0}(created_at), SUM(sd.kw_sec) FROM sensor_data sd WHERE sd.user_id = '{1}' AND '{2}' <= " \
          "sd.created_at <= '{3}' GROUP BY {0}(sd.created_at) ORDER BY {0}(sd.created_at) DESC".format(group_by,
                                                                                                       user_id,
                                                                                                       date_from ,
                                                                                                       date_to)
    data = db.engine.execute(sql)

    def cost_logic(no_units):
        tot = 0
        remaining_units = no_units

        settings = Setting.query.filter_by(setting="cost_values").first()
        data_values = json.loads(settings.value)

        for units_range in data_values:
            print(units_range)
            if units_range["range_from"] < remaining_units:
                units_in_range = remaining_units - units_range["range_from"]
                tot += units_in_range * units_range["value"]
                remaining_units = remaining_units - units_in_range
        return tot

    response = []
    for row in data:
        response.append({
            group_by.lower(): row[0],
            'total': row[1],
            'cost' : cost_logic(row[1])
        })

    return jsonify(response), HTTP_200_OK


# bar peak off-peak usage -- monthly
@analytics.get('/peak-off-peak-usage')
@jwt_required()
def peak_off_peak_usage():

    # group_by = request.json['group_by']

    settings = Setting.query.filter_by(setting="off_peak_values").first()
    data = json.loads(settings.value)

    off_peak_start = data['offpeak_start']
    off_peak_end = data['offpeak_end']

    user_id = get_jwt_identity()

    sql = "SELECT sdmMain.sdmDate, hrgPeak.peakUsage ,hrgOff.offPeakUsage  FROM (SELECT DATE(sdm.created_at) as " \
          "sdmDate FROM	sensor_data sdm WHERE sdm.user_id = '{2}' GROUP BY DATE(sdm.created_at)) AS sdmMain   LEFT " \
          "JOIN (SELECT   DATE(sd.created_at) as date,  SUM(sd.kw_sec) as peakUsage  FROM  sensor_data sd WHERE {0} >" \
          "HOUR(sd.created_at) AND {1} < HOUR(sd.created_at) GROUP BY   DATE(sd.created_at)) AS hrgPeak ON " \
          "hrgPeak.date = sdmMain.sdmDate   LEFT JOIN (SELECT   DATE(sd.created_at) as date,   SUM(sd.kw_sec) as " \
          "offPeakUsage   FROM sensor_data sd   WHERE   {0} < HOUR(sd.created_at) OR {1} > HOUR(sd.created_at)   " \
          "GROUP BY DATE(sd.created_at)) AS hrgOff ON hrgOff.date = sdmMain.sdmDate".format(off_peak_start,
                                                                                            off_peak_end, user_id)

    data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'date': row[0],
            'peakUsage': row[1] if row[1] else 0,
            'offPeakUsage': row[2] if row[2] else 0
        })

    return jsonify(response), HTTP_200_OK


# ----------------------- device dashboard -----------------------------

# line and bar - Cost and daily power device --- monthly, yearly-
@analytics.get('/cost-bar-power-total-device/<int:id>')
@jwt_required()
def cost_and_daily_power_usage(id):
    group_by = request.json['group_by']
    date_from = request.json['date_from']
    date_to = request.json['date_to']
    user_id = get_jwt_identity()

    device_id = Device.query.filter_by(id=id).first()

    sql = "SELECT {0}(created_at), SUM(sd.kw_sec) FROM sensor_data sd WHERE sd.user_id = '{1}' AND '{2}' <= " \
          "sd.created_at <= '{3}' AND sd.device_id = '{4}' GROUP BY {0}(sd.created_at) ORDER BY {0}(sd.created_at) " \
          "DESC".format(group_by, user_id, date_from, date_to, device_id.device_id)

    data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            group_by.lower(): row[0],
            'total': row[1],
        })

    return jsonify(response), HTTP_200_OK


# meter - kwh usage -- Daily (pick a date), monthly (pick a monthly)
@analytics.get('/kwh_device_usage')
@jwt_required()
def kwh_device_usage():
    group_by = request.json['group_by'] # Upper case DAY, MONTH
    device_id = request.json['device_id']

    sql = "SELECT SUM(kw_sec) AS kw, DATE(created_at) as date_1  FROM sensor_data sd WHERE device_id = '{1}' GROUP BY "\
          "{0}(created_at)".format(group_by, device_id)

    data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'kwh': row[0] if row[0] else 0,
            'date': row[1],
        })

    return jsonify(response), HTTP_200_OK


# Active usage and kwh -day
@analytics.get('/device_active_time/<int:id>')
@jwt_required()
def device_active_time(id):
    group_by = request.json['group_by']

    sql = ""
    data = db.engine.execute(sql)

    return jsonify({
        "message": "success"
    }), HTTP_200_OK


# bar peak off-peak usage -- monthly
@analytics.get('/peak-off-peak-usage-device')
@jwt_required()
def peak_off_peak_usage_device():
    # group_by = request.json['group_by']
    # device_id = request.json['device_id']

    settings = Setting.query.filter_by(setting="off_peak_values").first()
    data = json.loads(settings.value)

    off_peak_start = data['offpeak_start']
    off_peak_end = data['offpeak_end']
    device_id = "FSE89G98"
    user_id = get_jwt_identity()

    sql = "SELECT sdmMain.sdmDate,sdmMain.device_id,hrgPeak.peakUsage, hrgOff.offPeakUsage  FROM (SELECT DATE(" \
          "sdm.created_at) as sdmDate, sdm.device_id FROM	sensor_data sdm WHERE sdm.user_id = '{3}' GROUP BY DATE(sdm.created_at), " \
          "sdm.device_id) AS sdmMain LEFT JOIN (SELECT  DATE(sd.created_at) as date,  " \
          "sd.device_id as sdDeviceId,  SUM(sd.kw_sec) as peakUsage  FROM  sensor_data sd  WHERE  {0} > HOUR(" \
          "sd.created_at) AND {1} < HOUR(sd.created_at)  GROUP BY  sd.device_id, DATE(sd.created_at)) AS hrgPeak ON " \
          "hrgPeak.date = sdmMain.sdmDate AND sdmMain.device_id = hrgPeak.sdDeviceId  LEFT JOIN (SELECT  DATE(" \
          "sd.created_at) as date,  sd.device_id as sdDeviceId,  SUM(sd.kw_sec) as offPeakUsage  FROM " \
          "sensor_data sd   WHERE   {0} < HOUR(sd.created_at) OR {1} > HOUR(sd.created_at) GROUP BY sd.device_id, " \
          "DATE(sd.created_at)) AS hrgOff ON hrgOff.date = sdmMain.sdmDate AND sdmMain.device_id = hrgOff.sdDeviceId " \
          "WHERE sdmMain.device_id = '{2}'".format(off_peak_start, off_peak_end, device_id, user_id)

    data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'date': row[0],
            'device_id': row[1],
            'peakUsage': row[2] if row[2] else 0,
            'offPeakUsage': row[3] if row[3] else 0
        })

    return jsonify(response), HTTP_200_OK
