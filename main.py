import requests
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from lxml import html

COLUMN_CASES_ON_WEB = 3
COLUMN_DATE_ON_WEB = 6
COLUMN_DATE_UPDATED = 7

SPREADSHEET_NAME = 'SK Covid-19'
WORKSHEET_NAME = 'Data'

def get_new_data():
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


def main():
    new_data = get_new_data()

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(creds)

    ss = client.open(SPREADSHEET_NAME)

    ws = ss.worksheet(WORKSHEET_NAME)

    today = datetime.datetime.today()
    search_date = today.strftime('%-m/%-d/%Y')
    today_cell = ws.find(search_date)

    ws.update_cell(today_cell.row, COLUMN_DATE_ON_WEB, new_data[0])
    ws.update_cell(today_cell.row, COLUMN_DATE_UPDATED, today.strftime('%d.%m.%Y, %H:%M'))
    ws.update_cell(today_cell.row, COLUMN_CASES_ON_WEB, new_data[1])

if __name__ == "__main__":
    main()
