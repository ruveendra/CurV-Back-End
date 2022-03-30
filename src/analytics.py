from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST
from src.database import User, db, SensorData, Device, MainSensor

analytics = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")


# ----------------------- main dashboard -----------------------------

# Line - Power usage for each device --- ,week, monthly, yearly-
@analytics.get('/power_usage_for_each_device')
@jwt_required()
def power_usage_for_each_device():
    group_by = request.json['group_by']

    sql = ""
    data = db.engine.execute(sql)

    return jsonify({
        "message": "success"
    }), HTTP_200_OK


# pie - Pie chart device usage ---Daily (pick a date), monthly (pick a monthly), Yearly (pick a year) -
@analytics.get('/power-consumption-by-device')
@jwt_required()
def power_consumption_by_device():
    group_by = request.json['group_by']
    value = request.json['value']

    sql = "SELECT device_id, {0}(created_at), SUM(sd.kw_sec) FROM sensor_data sd WHERE {0}(sd.created_at) = '{1}' " \
          "GROUP BY sd.device_id, {0}(created_at)".format(group_by, value)
    print(sql)
    data = db.engine.execute(sql)

    response = []
    for row in data:
        response.append({
            'device_id': row[0],
            'month': row[1],
            'total': row[2],
        })

    return jsonify(response), HTTP_200_OK


# line and bar - Cost and daily power Total --- monthly, yearly-
@analytics.get('/cost-and-daily-power-total')
@jwt_required()
def cost_and_daily_power_total():
    group_by = request.json['group_by']

    sql = ""
    data = db.engine.execute(sql)

    return jsonify({
        "message": "success"
    }), HTTP_200_OK


# bar peak off-peak usage -- monthly
@analytics.get('/peak-off-peak-usage')
@jwt_required()
def peak_off_peak_usage():
    # group_by = request.json['group_by']

    off_peak_start = "22"
    off_peak_end = "06"

    sql = "SELECT sdmMain.sdmDate, hrgPeak.peakUsage ,hrgOff.offPeakUsage  FROM (SELECT DATE(sdm.created_at) as " \
          "sdmDate FROM	sensor_data sdm GROUP BY DATE(sdm.created_at)) AS sdmMain   LEFT JOIN (SELECT   DATE(" \
          "sd.created_at) as date,   SUM(sd.kw_sec) as peakUsage   FROM   sensor_data sd   WHERE   {0} >" \
          "HOUR(sd.created_at) AND {1} < HOUR(sd.created_at)   GROUP BY   DATE(sd.created_at)) AS hrgPeak ON " \
          "hrgPeak.date = sdmMain.sdmDate   LEFT JOIN (SELECT   DATE(sd.created_at) as date,   SUM(sd.kw_sec) as " \
          "offPeakUsage   FROM sensor_data sd   WHERE   {0} < HOUR(sd.created_at) OR {1} > HOUR(sd.created_at)   " \
          "GROUP BY DATE(sd.created_at)) AS hrgOff ON hrgOff.date = sdmMain.sdmDate".format(off_peak_start,
                                                                                            off_peak_end)

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
@analytics.get('/cost_and_daily_power_usage/<int:id>')
@jwt_required()
def cost_and_daily_power_usage(id):
    group_by = request.json['group_by']

    sql = ""
    data = db.engine.execute(sql)

    return jsonify({
        "message": "success"
    }), HTTP_200_OK


# meter - kwh usage -- daily, monthly
@analytics.get('/kwh_device_usage/<int:id>')
@jwt_required()
def kwh_device_usage(id):
    group_by = request.json['group_by']

    sql = ""
    data = db.engine.execute(sql)

    return jsonify({
        "message": "success"
    }), HTTP_200_OK


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

    off_peak_start = "22"
    off_peak_end = "06"
    device_id = "FSE89G98"

    sql = "SELECT sdmMain.sdmDate,sdmMain.device_id,hrgPeak.peakUsage, hrgOff.offPeakUsage  FROM (SELECT DATE(" \
          "sdm.created_at) as sdmDate, sdm.device_id FROM	sensor_data sdm GROUP BY DATE(sdm.created_at), " \
          "sdm.device_id) AS sdmMain LEFT JOIN (SELECT  DATE(sd.created_at) as date,  " \
          "sd.device_id as sdDeviceId,  SUM(sd.kw_sec) as peakUsage  FROM  sensor_data sd  WHERE  {0} > HOUR(" \
          "sd.created_at) AND {1} < HOUR(sd.created_at)  GROUP BY  sd.device_id, DATE(sd.created_at)) AS hrgPeak ON " \
          "hrgPeak.date = sdmMain.sdmDate AND sdmMain.device_id = hrgPeak.sdDeviceId  LEFT JOIN (SELECT  DATE(" \
          "sd.created_at) as date,  sd.device_id as sdDeviceId,  SUM(sd.kw_sec) as offPeakUsage  FROM " \
          "sensor_data sd   WHERE   {0} < HOUR(sd.created_at) OR {1} > HOUR(sd.created_at) GROUP BY sd.device_id, " \
          "DATE(sd.created_at)) AS hrgOff ON hrgOff.date = sdmMain.sdmDate AND sdmMain.device_id = hrgOff.sdDeviceId " \
          "WHERE sdmMain.device_id = '{2}'".format(off_peak_start, off_peak_end, device_id)

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
