import datetime
import json
import uuid

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from redis import Redis
from rq import Queue
from datetime import datetime

from src.constances.http_status_code import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_204_NO_CONTENT
from src.database import db, Jobtbl, Predictions
from src.machine_learing_prediction import machine_learning_worker

prediction = Blueprint("prediction", __name__, url_prefix="/api/v1/prediction")


@prediction.get('/')
# @jwt_required()
def machine_learning_prediction():
    # user_id = get_jwt_identity()
    user_id = 1

    myuuid = str(uuid.uuid4())

    job_create = Jobtbl(queue_jobID=myuuid, job_status="PENDING", user_id=user_id, created_at=datetime.now())

    db.session.add(job_create)
    db.session.commit()

    print(job_create)
    # Tell RQ what Redis connection to use
    redis_conn = Redis()
    q = Queue(connection=redis_conn)  # no args implies the default queue

    job = q.enqueue(machine_learning_worker, user_id, job_id=myuuid)

    return jsonify({
        'job_id': job.id
    }),  HTTP_200_OK


@prediction.get('/get-status')
# @jwt_required()
def get_status():
    # user_id = get_jwt_identity()
    user_id = 1

    job_tbl = Jobtbl.query.filter_by(user_id=user_id).order_by(Jobtbl.created_at.desc()).limit(1).first()

    print(job_tbl)

    if not job_tbl:
        return jsonify({
            'status': None,
            'end_time': None,
        }),  HTTP_204_NO_CONTENT

    return jsonify({
        'status': job_tbl.job_status,
        'end_time': job_tbl.job_end_time,
    }), HTTP_200_OK


@prediction.get('/get-predicted-data')
# @jwt_required()
def get_predicted_data():
    # user_id = get_jwt_identity()
    user_id = 1

    predict_tbl = Predictions.query.filter_by(user_id=user_id).order_by(Predictions.id.desc()).limit(1).first()

    date_values = json.loads(predict_tbl.value)

    if not predict_tbl:
        return jsonify({
            'status': None,
            'end_time': None,
        }),  HTTP_204_NO_CONTENT

    return jsonify({
        "data": date_values
    }), HTTP_200_OK

