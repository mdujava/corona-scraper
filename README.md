# Setup

## Optional: Set up venv

```
python3 -m venv venv
. ./venv/bin/activate
```

## Install deps

```
pip install -r requiroments.txt
```

## Set up permissions

Create new service account on https://console.cloud.google.com/apis/credentials for `Google Spreadsheet API` and add erite permision on the newly created client_email (see client_secret.json.template)


## Customize data

Edit constants in the main.py as `SPREADSHEET_NAME` nad `WORKSHEET_NAME`

## Run script

`./main.py`

