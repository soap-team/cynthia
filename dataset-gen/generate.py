import requests
import json
import configparser
from bs4 import BeautifulSoup

"""
Generate a JSON file with diffs
"""
class DatasetGenerator():
    def __init__(self):
        self.ua = 'cynthia/1.0, SOAP ML Project Bot'
        self.loggedin = False
        self.session = self.login()

    """
    Authenticate via services. Credentials are stored in 'config.ini'
    """
    def login(self):
        if self.loggedin:
            print('Already logged in')
        
        config = configparser.ConfigParser()
        if len(config.read('config.ini')) == 0:
            print('Please add credentials in config.ini')
            exit()
        
        credentials = {}
        try:
            credentials['username'] = config['fandom']['username']
            credentials['password'] = config['fandom']['password']
        except KeyError:
            print('Incorrect configuration data in config.ini')
            exit()
        
        # Log in a requests.Session
        login_session = requests.Session()
        result = login_session.post('https://services.fandom.com/auth/token', data=credentials)
        cookie = ''
        try:
            cookie = 'access_token=' + result.json()['access_token']
            self.loggedin = True
        except KeyError:
            print('Could not log in, username or password incorrect. Please check config.py')
            exit()

        cj = requests.utils.cookiejar_from_dict(dict(p.split('=') for p in cookie.split('; ')))

        # Place user agent and login cookie
        session = requests.Session()
        session.cookies = cj
        session.headers.update({'User-Agent': self.ua})
        return session
    
    """
    Get LookupContribs data of a particular user
    """
    def lc(self, user, limit):
        response = self.session.get('https://ucp.fandom.com/wiki/Special:LookupContribs', params={
          'target': user,
          'limit': str(limit)
        })
        soup = BeautifulSoup(response.content, 'html.parser')
        try:
            table_rows = soup.find('table', class_='lookup-contribs__table').find('tbody').find_all('tr')
        except:
            print('You do not have valid permissions to view LC data')
            return None

        wikis = []
        for row in table_rows:
            cells = row.find_all('td')
            wiki_data = (cells[1].find('a')['href'], int(cells[3].getText().strip()))
            # print(wiki_data)
            wikis.append(wiki_data)
        return list(wikis)
    
    """
    Filter lc to match edit requirements
    """
    def filtered_lc(self, lc, min_edits, max_edits):
        return list(filter(lambda d: d[1] >= min_edits and d[1] <= max_edits, lc))

    """
    Get a list of user contributions
    """
    def contribs(self, wiki, user, limit):
        response = self.session.get(wiki + 'api.php', params={
            'action': 'query',
            'list': 'usercontribs',
            'ucuser': user,
            'uclimit': limit,
            'format': 'json'
        })

        return response.json()['query']['usercontribs']

    """
    Filter contribs to match regexes
    """
    def filter_contribs(self, contribs):
        pass
    
    """
    Obtain bad diffs - get the previous diff of good edits by VSTF members
    """
    def get_bad_diffs(self, filtered_contribs):
        pass


if __name__ == '__main__':
    client = DatasetGenerator()
    lc = client.lc('Noreplyz', '100')
    print(lc)
    print('----')
    print(client.filtered_lc(lc, 1, 20))
    # print(client.contribs('https://community.fandom.com/', 'Noreplyz', 100))
