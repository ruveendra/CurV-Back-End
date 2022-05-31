# import time
import datetime
import json
import time

import pandas as pd
import mysql.connector
from rq.job import Job, get_current_job
from sqlalchemy import create_engine
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
# from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
# from sklearn.metrics import mean_squared_error
import warnings


engine = create_engine('mysql+pymysql://root:XC.Kjs5563@34.222.56.94:3306/smartmeter')

def machine_learning_worker(user_id):

    try:
        job = get_current_job()

        mydb = mysql.connector.connect(
            host="34.222.56.94",
            user="root",
            password="XC.Kjs5563",
            database="smartmeter"
        )
        mycursor = mydb.cursor()

        sql = "UPDATE jobtbl SET job_start_time = '{0}', job_status = 'PROCESSING'  WHERE queue_jobID = '{1}'".format(
            job.started_at, job.id)
        mycursor.execute(sql)
        mydb.commit()

        arima_model(user_id)

        sql = "UPDATE jobtbl SET job_end_time = '{0}', job_status = 'COMPLETED'  WHERE queue_jobID = '{1}'".format(
            datetime.datetime.utcnow(), job.id)
        mycursor.execute(sql)
        mydb.commit()
        mydb.close()

    except Exception as e:
        print(e)
        sql = "UPDATE jobtbl SET  job_status = 'FAILED'  WHERE queue_jobID = '{0}'".format(job.id)
        mycursor.execute(sql)
        mydb.commit()
        mydb.close()

def arima_model(user_id):

    # query = "Select * FROM sensor_data WHERE user_id = 1;"

    query = 'SELECT DATE_FORMAT(sd.created_at,"%%Y-%%m") as month_date, SUM(sd.kw_sec) as TOTAL ' \
          'FROM sensor_data sd WHERE sd.user_id = "' + str(user_id) + '" GROUP BY DATE_FORMAT(sd.created_at,"%%Y-%%m")'
    # print(query)
    df = pd.read_sql_query(query, engine, parse_dates="month_date", index_col="month_date")
    # print(df.head())


    # df = pd.read_csv('Perrin Freres monthly champagne sales millions.csv', parse_dates=['Date'], index_col=['Date'])
    # print(df.head())

    # df = df.fillna(0)
    # df = df.astype({"kva": int})

    # plt.plot(df)
    # plt.show()

    # print(len(df))

    # Aggregation of data to months
    # ts=df['PJM_Load_MW'].resample('M').sum()
    # print(ts.head())
    # plt.plot(ts)
    # plt.show()

    # stationarity check

    # decomposition = sm.tsa.seasonal_decompose(df, model='additive')
    # fig = decomposition.plot()
    # plt.show()

    # adfuller test
    # aftest = adfuller(df)
    # print(f'pvalue of adfuller test is: {aftest[1]}')

    # Train test split

    # print(len(df))

    # train = df[:85]
    # test = df[85:]

    # Buliding arima model

    warnings.filterwarnings("ignore")
    # p = 5, d = 0, q = 4
    # model = ARIMA(train, order=(5, 0, 4)).fit()
    # pred = model.predict(start=len(train), end=len(df) - 1)

    # model evaluation

    # error = np.sqrt(mean_squared_error(test,pred))
    # print(error)

    # print(test.mean, np.sqrt(test.var()))

    # plt.plot(train, label='Train')
    # plt.plot(test, label='Test')
    # plt.plot(pred, color='red')
    # plt.show()

    p = 5
    d = 0
    q = 4

    final_data = ARIMA(df, order=(5, 0, 4)).fit()
    prediction = final_data.predict(start=len(df), end=len(df) + 6)

    tranformed_dict = json.loads(prediction.to_json())
    data= []
    for row in tranformed_dict:
        epoch = int(row)/1000
        data.append ({
            "date": time.strftime('%B', time.localtime(epoch)),
            "value": tranformed_dict[row]
        })

    json_data = json.dumps(data)
    print(json_data)


    mydb = mysql.connector.connect(
        host="34.222.56.94",
        user="root",
        password="XC.Kjs5563",
        database="smartmeter"
    )
    mycursor = mydb.cursor()

    # sql = "SELECT * FROM predictions WHERE user_id = '{0}'".format(user_id)
    # print(sql)
    # predit_tbl = mycursor.execute(sql)
    # print(predit_tbl)


    sql = "INSERT INTO predictions (user_id, value) VALUES ('{0}', '{1}')".format(user_id, json_data)
    # print(sql)
    mycursor.execute(sql)
    mydb.commit()

    # print(type(prediction))
    # print(prediction.to_json())
    #
    # plt.plot(df, label='Test')
    # plt.plot(prediction, color='red')
    # plt.show()
    # #




