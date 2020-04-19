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


# log in onece
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(
          'client_secret.json', scope)
client = gspread.authorize(creds)


def updateData(config=None):
    today = datetime.datetime.today()

    cacheDirName = os.path.expandvars('$XDG_CACHE_HOME')
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
            if (cacheData[0] == newData[0] and
               cacheData[1] == newData[1] and
               cacheData[2] == newData[2] and
               cacheData[3] == newData[3] and
               cacheData[4] == newData[4]):
                syslog.syslog("no change in {}.".format(config['CACHE_FILE']))
                skip = True
                if int(cacheData[-1]) + 3550 > int(newData[-1]):
                    skipTime = True
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, "error: cachefile: {}".format(e))

    if not skipTime:
        with open(cacheFileName, 'w') as cacheFile:
            cacheFile.seek(0)
            cacheFile.write(json.dumps(newData))
            cacheFile.truncate()

    ss = client.open(config['SS_NAME'])

    ws = ss.worksheet(config['WS_NAME'])

    searchDate = today.strftime(config['DATE_FORMAT'])
    todayCell = ws.find(searchDate)

    rowToUpdate = todayCell.row

    if not skipTime:
        syslog.syslog("Writing update time to {}".format(config['SS_NAME']))
        ws.update_cell(rowToUpdate,
                       config['COL_DATE_UPDATED'],
                       today.strftime(config['UPDATE_FORMAT']))

    if not skip:
        syslog.syslog("Writing data to {}".format(config['SS_NAME']))
        if 'OFFSET_OF_DATA' in config:
            rowToUpdate += config['OFFSET_OF_DATA']

        ws.update_cell(rowToUpdate, config['COL_DATE_ON_WEB'], newData[0])
        ws.update_cell(rowToUpdate, config['COL_CASES_ON_WEB'], newData[1])
        if 'COL_TESTS_ON_WEB' in config:
            ws.update_cell(rowToUpdate,
                           config['COL_TESTS_ON_WEB'],
                           newData[2])
        if 'COL_DEATHS_ON_WEB' in config:
            ws.update_cell(rowToUpdate,
                           config['COL_DEATHS_ON_WEB'],
                           newData[3])
        if 'COL_RECOVERED_ON_WEB' in config:
            ws.update_cell(rowToUpdate,
                           config['COL_RECOVERED_ON_WEB'],
                           newData[4])


def getNewDataCz():
    ret = [None, None, None, None, None]

    page = requests.get('https://onemocneni-aktualne.mzcr.cz/covid-19')
    page.raise_for_status()

    tree = html.fromstring(page.content)

    counter_sick = tree.get_element_by_id("count-sick")
    counter_dead = tree.get_element_by_id("count-dead")
    counter_recover = tree.get_element_by_id("count-recover")

    date = counter_sick.getnext()

    counter_tests = tree.get_element_by_id("count-test")

    ret[0] = date.text.strip().replace(u'\xa0', ' ')

    ret[1] = counter_sick.text.replace(" ", "")
    ret[2] = counter_tests.text.replace(" ", "")
    ret[3] = counter_dead.text.replace(" ", "")
    ret[4] = counter_recover.text.replace(" ", "")

    return ret


def getNewDataSk():
    ret = [None, None, None, None, None]

    page = requests.get('https://virus-korona.sk/api.php')
    page.raise_for_status()

    decodedJson = json.loads(page.text)

    ret[0] = decodedJson['tiles']['k5']['updated']
    ret[1] = decodedJson['tiles']['k5']['data']['d'][-1]['v']
    ret[2] = decodedJson['tiles']['k6']['data']['d'][-1]['v']
    ret[3] = decodedJson['tiles']['k8']['data']['d'][-1]['v']
    ret[4] = decodedJson['tiles']['k7']['data']['d'][-1]['v']

    return ret


def czech():
    config = {'COL_CASES_ON_WEB':        3,
              'COL_TESTS_ON_WEB':        10,
              'COL_DEATHS_ON_WEB':       11,
              'COL_RECOVERED_ON_WEB':    12,
              'COL_DATE_ON_WEB':         7,
              'COL_DATE_UPDATED':        8,
              'DATE_FORMAT':             '%d.%m.%Y',
              'UPDATE_FORMAT':           '%d.%m.%Y, %H:%M',
              'CACHE_FILE':              'covid-cz',
              'SS_NAME':                 'CZ Covid-19',
              'WS_NAME':                 'Data',
              'NEW_DATA':                getNewDataCz,
              }

    updateData(config)


def slovak():
    config = {'COL_CASES_ON_WEB':        3,
              'COL_TESTS_ON_WEB':        10,
              'COL_DEATHS_ON_WEB':       11,
              'COL_RECOVERED_ON_WEB':    12,
              'COL_DATE_ON_WEB':         7,
              'COL_DATE_UPDATED':        8,
              'DATE_FORMAT':             '%d.%m.%Y',
              'UPDATE_FORMAT':           '%d.%m.%Y, %H:%M',
              'CACHE_FILE':              'covid-sk',
              'SS_NAME':                 'SK Covid-19',
              'WS_NAME':                 'Data',
              'OFFSET_OF_DATA':          (-1),
              'NEW_DATA':                getNewDataSk,
              }

    updateData(config)


if __name__ == "__main__":
    syslog.syslog("Starting ...")
    try:
        slovak()
    except Exception as e:
        print(e)
        traceback.print_exc()
        syslog.syslog(syslog.LOG_ERR, "error: {}".format(e))

    try:
        czech()
    except Exception as e:
        print(e)
        traceback.print_exc()
        syslog.syslog(syslog.LOG_ERR, "error: {}".format(e))

    syslog.syslog("Finished ...")
