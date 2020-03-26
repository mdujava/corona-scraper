#!/usr/bin/env python
import requests
import gspread
import datetime
import json
import traceback
import os
import syslog
from oauth2client.service_account import ServiceAccountCredentials
from lxml import html


#log in onece
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

def updateData(config = None):
    today = datetime.datetime.today()

    cacheDirName  = os.path.expandvars('$XDG_CACHE_HOME')
    cacheFileName = os.path.join(cacheDirName, config['CACHE_FILE'])

    newData = config['NEW_DATA']()

    newData.append(today.strftime('%s'))

    if newData is None:
        raise Exception('No data')
    if newData[0] is None or int(newData[1]) == 0:
        raise Exception('Invalid data: {}, {}'.format(newData[0], newData[1]))

    skip = False
    skipTime = False

    try:
        with open(cacheFileName, 'r') as cacheFile:
            cacheData = json.loads(cacheFile.read())
            if cacheData[0] == newData[0] and cacheData[1] == newData[1]:
                syslog.syslog("no change in {}.".format(config['CACHE_FILE']))
                skip = True
                if int(cacheData[2]) + 3550 > int(newData[2]):
                    skipTime = True
    except:
        pass

    if not skipTime:
        with open(cacheFileName, 'w') as cacheFile:
            cacheFile.seek(0)
            cacheFile.write(json.dumps(newData))
            cacheFile.truncate()

    ss = client.open(config['SPREADSHEET_NAME'])

    ws = ss.worksheet(config['WORKSHEET_NAME'])

    searchDate = today.strftime(config['DATE_FORMAT'])
    todayCell = ws.find(searchDate)

    if not skipTime:
        ws.update_cell(todayCell.row, config['COLUMN_DATE_UPDATED'], today.strftime(config['UPDATE_FORMAT']))

    if not skip:
        ws.update_cell(todayCell.row, config['COLUMN_DATE_ON_WEB'], newData[0])
        ws.update_cell(todayCell.row, config['COLUMN_CASES_ON_WEB'], newData[1])


def getNewDataCz():
    ret = [None, None]

    page = requests.get('https://onemocneni-aktualne.mzcr.cz/covid-19')
    tree = html.fromstring(page.content)

    counter = tree.get_element_by_id("count-sick")

    date = counter.getprevious() \
           .getchildren()[0]

    ret[0] = date.text.strip().replace(u'\xa0', ' ')

    ret[1] = counter.text.replace(" ", "")

    return ret

def getNewDataSk():
    ret = [None, None]

    page = requests.get('https://virus-korona.sk/api.php')

    decodedJson = json.loads(page.text)

    ret[1] = decodedJson['tiles']['k26']['data']['d'][-1]['v']
    ret[0] = decodedJson['tiles']['k26']['updated']

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
              'NEW_DATA'            : getNewDataCz,
              }

    updateData(config)

def slovak():
    config = {'COLUMN_CASES_ON_WEB' : 3,
              'COLUMN_DATE_ON_WEB'  : 7,
              'COLUMN_DATE_UPDATED' : 8,
              'DATE_FORMAT'         : '%d.%m.%Y',
              'UPDATE_FORMAT'       : '%d.%m.%Y, %H:%M',
              'CACHE_FILE'          : 'covid-sk',
              'SPREADSHEET_NAME'    : 'SK Covid-19',
              'WORKSHEET_NAME'      : 'Data',
              'NEW_DATA'            : getNewDataSk,
              }

    updateData(config)

if __name__ == "__main__":
    syslog.syslog("Starting ...")
    try:
        slovak()
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, traceback.print_exc())

    try:
        czech()
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, traceback.print_exc())
    syslog.syslog("Finished ...")
