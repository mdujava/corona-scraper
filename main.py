#!/usr/bin/env python
import requests
import gspread
import datetime
import json
import traceback
import os
from oauth2client.service_account import ServiceAccountCredentials
from lxml import html

#log in onece
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

def update_data(config = None):
    cacheDirName  = os.path.expandvars('$XDG_CACHE_HOME')
    cacheFileName = os.path.join(cacheDirName, config['CACHE_FILE'])

    new_data = config['NEW_DATA']()

    if new_data is None:
        raise Exception('No data')
    if new_data[0] is None or int(new_data[1]) == 0:
        raise Exception('Invalid data: {}, {}'.format(new_data[0], new_data[1]))

    skip = False

    try:
        with open(cacheFileName, 'r') as cacheFile:
            cacheData = json.loads(cacheFile.read())
            if cacheData[0] == new_data[0] and cacheData[1] == new_data[1]:
                print("no change in {}.".format(config['CACHE_FILE']))
                skip = True
    except:
        pass

    if not skip:
        with open(cacheFileName, 'w') as cacheFile:
            cacheFile.seek(0)
            cacheFile.write(json.dumps(new_data))
            cacheFile.truncate()

    ss = client.open(config['SPREADSHEET_NAME'])

    ws = ss.worksheet(config['WORKSHEET_NAME'])

    today = datetime.datetime.today()
    search_date = today.strftime(config['DATE_FORMAT'])
    today_cell = ws.find(search_date)

    ws.update_cell(today_cell.row, config['COLUMN_DATE_UPDATED'], today.strftime(config['UPDATE_FORMAT']))

    if not skip:
        ws.update_cell(today_cell.row, config['COLUMN_DATE_ON_WEB'], new_data[0])
        ws.update_cell(today_cell.row, config['COLUMN_CASES_ON_WEB'], new_data[1])


def get_new_data_cz():
    ret = [None, None]

    page = requests.get('https://onemocneni-aktualne.mzcr.cz/covid-19')
    tree = html.fromstring(page.content)

    counter = tree.get_element_by_id("count-sick")

    date = counter.getprevious() \
           .getchildren()[0]

    ret[0] = date.text.strip().replace(u'\xa0', ' ')

    ret[1] = counter.text.replace(" ", "")

    return ret

def get_new_data_sk():
    ret = [None, None]

    page = requests.get('https://virus-korona.sk/api.php')

    decoded_json = json.loads(page.text)

    ret[1] = decoded_json['tiles']['k26']['data']['d'][-1]['v']
    ret[0] = decoded_json['tiles']['k26']['updated']

    return ret

def czech():
    config = {'COLUMN_CASES_ON_WEB' : 3,
              'COLUMN_DATE_ON_WEB'  : 7,
              'COLUMN_DATE_UPDATED' : 8,
              'DATE_FORMAT'         : '%d.%m.%Y',
              'UPDATE_FORMAT'       : '%d.%m.%Y, %H:%M',
              'CACHE_FILE'          : 'covid-cz',
              'SPREADSHEET_NAME'    : 'CZ Covid-19',
              'WORKSHEET_NAME'      : 'Data',
              'NEW_DATA'            : get_new_data_cz,
              }

    update_data(config)

def slovak():
    config = {'COLUMN_CASES_ON_WEB' : 3,
              'COLUMN_DATE_ON_WEB'  : 7,
              'COLUMN_DATE_UPDATED' : 8,
              'DATE_FORMAT'         : '%d.%m.%Y',
              'UPDATE_FORMAT'       : '%d.%m.%Y, %H:%M',
              'CACHE_FILE'          : 'covid-sk',
              'SPREADSHEET_NAME'    : 'SK Covid-19',
              'WORKSHEET_NAME'      : 'Data',
              'NEW_DATA'            : get_new_data_sk,
              }

    update_data(config)

if __name__ == "__main__":
    try:
        slovak()
    except Exception as e:
        traceback.print_exc()

    try:
        czech()
    except Exception as e:
        traceback.print_exc()
