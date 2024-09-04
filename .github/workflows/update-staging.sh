name: 💿 CI Staging
on:
  push:
    branches:
      - "staging"
jobs:
  build-dev:
    name: 🏗 Update staging from server
    runs-on: self-hosted
    env:
      CONTEXT: .
    steps:
      - name: 🎉 Update staging
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.CI_AIRFLOW_HOST }}
          username: ${{ secrets.CI_AIRFLOW_USER }}
          key: ${{ secrets.CI_AIRFLOW_KEY }}
          script: sh /opt/dags/update-staging.sh