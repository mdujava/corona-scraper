#!/usr/bin/env python
import requests
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from lxml import html

def update_data(config = None):
    if config is None:
        return

    new_data = config['NEW_DATA']()

    if new_data is None:
        raise Exception('No data')
    if new_data[0] is None or int(new_data[1]) == 0:
        raise Exception('Invalid data: {}, {}'.format(new_data[0], new_data[1]))

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    ss = client.open(config['SPREADSHEET_NAME'])

    ws = ss.worksheet(config['WORKSHEET_NAME'])

    today = datetime.datetime.today()
    search_date = today.strftime('%-m/%-d/%Y')
    today_cell = ws.find(search_date)

    ws.update_cell(today_cell.row, config['COLUMN_DATE_ON_WEB'], new_data[0])
    ws.update_cell(today_cell.row, config['COLUMN_CASES_ON_WEB'], new_data[1])


def get_new_data_cz():
    ret = [None, None]

    page = requests.get('https://onemocneni-aktualne.mzcr.cz/covid-19')
    tree = html.fromstring(page.content)

    counter = tree.get_element_by_id("count-sick")

    #prev span with date of update
    #date in <strong>
    date = counter.getprevious() \
           .getchildren()[0]

    ret[0] = date.text.strip().replace(u'\xa0', ' ')

    #select last box
    #select number
    #item = counter.getchildren()[2] \
    #       .getchildren()[1]

    ret[1] = counter.text.replace(" ", "")
    return ret

def get_new_data_sk():
    ret = [None, None]

    page = requests.get('https://www.korona.gov.sk/')
    tree = html.fromstring(page.content)

    counter = tree.find_class("covd-counter")[0]

    #prev span with date of update
    #date in <strong>
    date = counter.getprevious() \
           .getchildren()[0]

    ret[0] = date.text.strip()

    #select last box
    #select number
    item = counter.getchildren()[2] \
           .getchildren()[1]

    ret[1] = item.text
    return ret

def czech():
    config = {'COLUMN_CASES_ON_WEB' : 3,
              'COLUMN_DATE_ON_WEB'  : 6,
              'SPREADSHEET_NAME'    : 'CZ Covid-19',
              'WORKSHEET_NAME'      : 'Data',
              'NEW_DATA'            : get_new_data_cz,
              }

    update_data(config)

def slovak():
    config = {'COLUMN_CASES_ON_WEB' : 3,
              'COLUMN_DATE_ON_WEB'  : 6,
              'COLUMN_DATE_UPDATED' : 7,
              'SPREADSHEET_NAME'    : 'SK Covid-19',
              'WORKSHEET_NAME'      : 'Data',
              'NEW_DATA'            : get_new_data_sk,
              }

    update_data(config)

if __name__ == "__main__":
    try:
        slovak()
    except Exception as e:
        print(e)

    try:
        czech()
    except Exception as e:
        print(e)
