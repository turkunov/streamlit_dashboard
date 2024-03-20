import urllib3
import re
from bs4 import BeautifulSoup
import pandas as pd

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
    'Accept-Encoding': 'utf-8'
}

def holidays_lookup():
    """
    Получение актуальных праздников в виде pd.DataFrame
    """
    http = urllib3.PoolManager()
    lookup_url = 'https://www.calend.ru/holidays/russtate/'
    resp = http.request(
        method='GET',
        url=lookup_url,
        headers=headers
    )
    soup = BeautifulSoup(resp.data.decode('utf-8', 'ignore'), "html.parser")
    list_items = soup.find_all('li', {'class': 'full'})

    hol_df = pd.DataFrame([
        {'holiday': item.find('a', {'href': re.compile('.*/holidays/.*')}).get_text(),
         'date': item.find('a', {'href': re.compile('/day/\d+\-\d+\-\d+/')})['href'].replace('/day/','').rstrip('/')}
        for item in list_items
    ])
    hol_df['date'] = pd.to_datetime(hol_df['date'])
    return hol_df
    