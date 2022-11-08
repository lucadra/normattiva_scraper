import requests
import json
import os
import sys
import time
import pandas as pd
import numpy as np
import re
from bs4 import BeautifulSoup

LIST_BY_DATE_URL = 'https://www.normattiva.it/ricerca/elencoPerData'

years = range(1861, 2022)
year = 2014

date_search_url = f'https://www.normattiva.it/ricerca/elencoPerData/anno/{year}'
root_url = 'https://www.normattiva.it'

if __name__ == '__main__':
    result_page = requests.get(date_search_url)
    soup = BeautifulSoup(result_page.text, 'html.parser')
    result_list = soup.find_all('a', attrs={'title': 'Dettaglio atto'})

    for item in result_list:
        href = item['href']
        title = re.sub(r"\s+", " ", item.text).strip()

        item_current = requests.get(root_url + href)
        soup_current = BeautifulSoup(item_current.text, 'html.parser')

        href_original = soup_current.find('a', text='Mostra Atto Originario')['href']

        item_original = requests.get(root_url + href_original)
        soup_original = BeautifulSoup(item_original.text, 'html.parser')

        item_vigore = [element.text for element in soup_original.find('div', attrs={'class': 'vigore'}).findChildren('span') if len(element.text) < 11]

        item_description_raw = soup_original.find('h3').text
        item_description = re.sub(r"\s+", " ", item_description_raw).strip()
        item_id = re.findall(r'\d{2}[A-Z]\d{5}', item_description)[0]

        item_gazzetta = soup_original.find('div', attrs={'class': 'riferimento'}).findChildren('a', recursive=True)[0].text
        item_gazzetta_date = '-'.join(re.findall(r'\d{2}-\d{2}-\d{4}', item_gazzetta)[0].split('-')[::-1])
        #extract date from item_gazzetta string (GU n.57 del 10-03-2015) => 2015-03-10

        item_text = soup_original.find('div', attrs={'id': 'testo'}).findChildren('pre', recursive=False)[0]
        next_article = soup_original.find('a', attrs={'class': 'btn', 'href': 'javascript:'})['onclick']
        next_article_href = next_article[next_article.find('(') + 1:next_article.rfind(')')]

        item_links = [element['href'] for element in item_text.findChildren('a', recursive=False)]



        print('########################################################################################################')
        print('TITLE:\t\t\t' + title)
        print('HREF:\t\t\t' + href)
        print('HREF_ORIGINAL:\t' + href_original)
        print('LINKS:\t\t\t' + str(item_links))
        print('VIGORE:\t\t\t' + str(item_vigore))
        print('DESCRIPTION:\t' + item_description)
        print('ID\t\t\t\t' + item_id)
        print('GAZZETTA:\t\t' + item_gazzetta)
        print('GAZZETTA_DATE:\t' + item_gazzetta_date)
        print('NEXT_ARTICLE:\t' + next_article_href)
        #print(item_text.text)

        print('\n')


