import re
import requests
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from tqdm import tqdm



def get_date(title: str) -> str:
    months = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre',
              'Novembre', 'Dicembre']
    date = re.split(r'(\d+)', title)[1:4]
    return f'{date[2]}-{str(months.index(date[1].strip()) + 1).zfill(2)}-{date[0].zfill(2)}'

def get_num(title: str) -> str:
    string = re.sub("\(.*?\)", "", title)
    return string.split(' ')[-1]

class Law:
    def __init__(self, title, codice_redazionale, data_gazzetta, numero_gazzetta, vigore_inizio, vigore_fine,
                 description, text, links):
        self.title = title
        self.type = re.split(r'(\d+)', self.title)[0].strip()
        self.date = get_date(self.title)
        self.num = get_num(self.title)
        self.codice_redazionale = codice_redazionale
        self.data_gazzetta = data_gazzetta
        self.numero_gazzetta = numero_gazzetta
        self.permalink = None
        self.vigore_inizio = vigore_inizio
        self.vigore_fine = vigore_fine
        self.description = description
        self.articles = []
        self.links = []

    def __repr__(self):
        return f'{self.title}'

    def __str__(self):
        return f'{self.title}'


def get_title(item):
    return re.sub(r"\s+", " ", item.text).strip()


def get_codice_redazionale(item):
    return re.findall(r'\d{2}[A-Z]\d{5}', item['href'])[0]


def get_data_pubblicazione(item):
    return re.findall(r'\d{4}-\d{2}-\d{2}', item['href'])[0]


def get_next_page(_soup):
    page_links = _soup.find_all('a', attrs={'class': 'page-link text'})
    for link in page_links:
        if link.text == 'Pagina Successiva':
            return link['href']


def get_laws_by_year(year: int) -> []:
    print(f'Getting laws for year {year}')
    search_url = f'https://www.normattiva.it/ricerca/elencoPerData/anno/{year}'
    s = requests.Session()
    result_page = s.get(search_url)
    soup = BeautifulSoup(result_page.text, 'html.parser')
    results = []
    page_number = 0

    while len(soup.find_all('a', attrs={'title': 'Dettaglio atto'})) > 0:
        result_page = s.get(f'https://www.normattiva.it/ricerca/elencoPerData/{page_number}')
        soup = BeautifulSoup(result_page.text, 'html.parser')

        for item in soup.find_all('a', attrs={'title': 'Dettaglio atto'}):
            results.append(
                Law(get_title(item), get_codice_redazionale(item), get_data_pubblicazione(item), None, None, None,
                        None, None, None))

        page_number += 1

    print(f'{len(results)} laws found for year {year}')

    return results


def get_law_permalink(s, law: Law) -> str:
    query = {
        'atto.dataPubblicazioneGazzetta': law.data_gazzetta,
        'atto.codiceRedazionale': law.codice_redazionale,
    }
    result = s.get(f'https://www.normattiva.it/do/atto/vediPermalink?', params=query)
    soup = BeautifulSoup(result.text, 'html.parser')
    return soup.find_all('a')[1]['href']


def download_law(_law: Law) -> Law:
    law = _law
    s = requests.Session()
    query = {
        'atto.dataPubblicazioneGazzetta': law.data_gazzetta,
        'atto.codiceRedazionale': law.codice_redazionale,
        'tipoDettaglio': 'originario'
    }

    result_page = s.get(f'https://www.normattiva.it/atto/caricaDettaglioAtto?',  params=query)
    soup = BeautifulSoup(result_page.text, 'html.parser')
    law.description = re.sub("\s\s+", " ", re.sub("\(.*?\)","", soup.find('h3').text)).strip()
    law.permalink = get_law_permalink(s, law)
    art_raw = soup.find('div', attrs={'id': 'albero'}).find('ul').find_all('a', attrs={'class': 'numero_articolo'})
    art_url = [re.search(r'\((.*?)\)', art['onclick']).group(1).replace("'", '') for art in art_raw]

    for url in art_url:
        result_page = s.get(f'https://www.normattiva.it{url}')
        soup = BeautifulSoup(result_page.text, 'html.parser')
        law.articles.append(soup.find('pre', attrs={'class': 'nero'}).text)
        for url in soup.find('pre', attrs={'class': 'nero'}).find_all('a'):
            if url['href'][:9] != '/uri-res/':
                continue
            result_page = s.get(f'https://www.normattiva.it{url["href"]}')
            soup = BeautifulSoup(result_page.text, 'html.parser')
            data_gazzetta = soup.find('input', attrs={'name': 'atto.dataPubblicazioneGazzetta'})['value']
            codice_gazzetta = soup.find('input', attrs={'name': 'atto.codiceRedazionale'})['value']
            law.links.append({'data_gazzetta': data_gazzetta, 'codice_gazzetta': codice_gazzetta})

    return law


########################################################################################################################
########################################################################################################################
########################################################################################################################

from multiprocessing import Pool

if __name__ == '__main__':
    law_list = get_laws_by_year(2015)
    with Pool() as p:
        laws = p.map(download_law, law_list)
    for law in tqdm(law_list):
        downlaw = download_law(law)
        print('=======================================================================================================')
        print(f'TITLE:\t\t\t\t{downlaw.title}')
        print(f'TYPE:\t\t\t\t{downlaw.type}')
        print(f'DATE:\t\t\t\t{downlaw.date}')
        print(f'NUM:\t\t\t\t{downlaw.num}')
        print(f'PERMALINK:\t\t\t{downlaw.permalink}')
        print(f'DESCRIPTION:\t\t{downlaw.description}')
        print(f'CODICE GAZZETTA:\t{downlaw.codice_redazionale}')
        print(f'DATA GAZZETTA:\t\t{downlaw.data_gazzetta}')
        print(f'ARTICLES:\t\t\t{len(downlaw.articles)}')
        print(f'LINKS:\t\t\t\t{len(downlaw.links)}')


        for link in downlaw.links:
            print(link)

        for article in downlaw.articles:
            print(article)

        print('=======================================================================================================')
        print('\n\n')

