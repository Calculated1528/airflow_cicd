import json
import logging
import requests
import pandas as pd

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable
from datetime import datetime, timedelta
from base.db_connector import *

DAG_ID = 'dag_category_catalog_report'

catalog_query_path = sql_file_path(DAG_ID, 'catalog')
report_query_path = sql_file_path(DAG_ID, 'report')

def format_json(x:int) -> str:
    json_data = {
        "text": f"airflow: {x} categories are not synced between catalog_service and report_service",
    }
    return json_data

def sendSlack(url, payload, token) -> None:
    headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {token}'}
    payloadJson = json.dumps(payload)
    try:
        response = requests.post(url, headers=headers, data=payloadJson)
    except requests.exceptions.RequestException as error:
        logging.error("Request to Slack failed")
        print ("Request to Slack failed", error)

def fetch_and_send() ->None:
    slack_token = Variable.get("slack_authorization_bearer")
    slackUrl = Variable.get("slack-billz2-looker-webhook")

    catalog_db = DatabaseConnector('pg_prod_billz_catalog_service_v2')
    report_db = DatabaseConnector('pg_prod_billz_report_service')
    catalog_result = catalog_db.execute_query(catalog_query_path)
    catalog_df = pd.DataFrame(catalog_result, columns=['cat_category_id'])
    report_result = report_db.execute_query(report_query_path)
    report_df = pd.DataFrame(report_result, columns=['rep_category_id'])

    common_df = pd.merge(left=catalog_df,
                      right=report_df,
                      left_on=['cat_category_id'],
                      right_on=['rep_category_id'],
                      how='left')
    result = common_df[common_df['rep_category_id'].isnull()].shape[0]
    if result == 0 or result is None:
        logging.info("No data returned from query or the returned value is zero.")
        return False
    json_data = format_json(result)

    logging.info("Sending message to Slack")
    sendSlack(slackUrl, json_data, slack_token)
    catalog_db.close()
    report_db.close()
    logging.info("Dag done")
    return


def task_id(dag_id):
    return 'fetch_and_send_' + dag_id



# DAG definition
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 23, 7, 0),
    'retries': 1,
    'retry_delay': timedelta(minutes=60),
    'execution_timeout': timedelta(minutes=5)
}

dag = DAG(DAG_ID,
          default_args=default_args,
          max_active_runs=1,
          concurrency=1,
          schedule_interval='@hourly',
          catchup=False,
          description="n categories are not synced between catalog_service and report_service")

t1 = PythonOperator(
    task_id=task_id(DAG_ID),
    python_callable=fetch_and_send,
    execution_timeout=timedelta(minutes=5),
    dag=dag)

