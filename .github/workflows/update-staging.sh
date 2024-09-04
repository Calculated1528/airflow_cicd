#!/bin/bash
cd /opt/dags/airflow_dags

git pull

cp -r /opt/dags/airflow_dags/* /opt/airflow/dags/

git branch --no-color 2> /dev/null | sed -e '/^[^*]/d' -e "s/* \(.*\)/\1$()/" > /opt/airflow/dags/.version
git rev-parse --short HEAD 2> /dev/null | sed "s/\(.*\)/@\1/" >> /opt/airflow/dags/.version
exit

