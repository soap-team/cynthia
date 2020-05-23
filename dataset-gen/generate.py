import requests
import json
import configparser
from bs4 import BeautifulSoup
import re

"""
Generate a JSON file with diffs
"""
class DatasetGenerator():
    def __init__(self):
        self.ua = 'cynthia/1.0, SOAP ML Project Bot'
        self.loggedin = False
        self.session = self.login()
        self.re_like_rollback = re.compile('(revert|vandal|undo|undid)', re.I)
        self.re_rollback = re.compile('^Reverted edits by \[\[')

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
            wiki_data = (cells[1].find('a')['href'].replace('http://', 'https://'), int(cells[3].getText().strip()))
            # print(wiki_data)
            wikis.append(wiki_data)
        return list(wikis)
    
    """
    Filter lc to match edit requirements and is English
    """
    def filtered_lc(self, lc, min_edits, max_edits):
        return list(filter(lambda d: d[1] >= min_edits and d[1] <= max_edits and re.search(r'\.com/$', d[0]), lc))

    """
    Get a list of user contributions
    """
    def contribs(self, wiki, user, limit):
        res = self.session.get(wiki + 'api.php', params={
            'action': 'query',
            'list': 'usercontribs',
            'ucuser': user,
            'uclimit': limit,
            'format': 'json'
        })
        try:
            return res.json()['query']['usercontribs']
        except (json.decoder.JSONDecodeError, KeyError) as e:
            print('Failed to get contribs for ' + wiki)
            return []
    
    # https://mario.fandom.com/api.php?action=query&prop=revisions&revids=288644&rvprop=ids|comment&rvdiffto=prev&format=json
    def get_prev_diff(self, wiki, curr_diff):
        res = self.session.get(wiki + 'api.php', params={
            'action': 'query',
            'prop': 'revisions',
            'revids': curr_diff,
            'rvprop': 'ids|comment',
            'format': 'json'
        })
        pages = res.json()['query']['pages']
        for page in pages:
            return pages[page]['revisions'][0]['parentid']
        
        return None

    """
    Filter contribs to match various rules
    Return diff list
    """
    def filter_contribs(self, contribs, wiki):
        def is_vandalism(contrib):
            if re.match(self.re_like_rollback, contrib['comment']):
                return True
            return False
        return list(filter(is_vandalism, contribs))

if __name__ == '__main__':
    soap_member = 'Noreplyz'
    client = DatasetGenerator()

    # Get LC
    lc = client.lc(soap_member, '1000')
    filtered_lc = client.filtered_lc(lc, 1, 20)

    # Loop through wikis and get contribs
    reverted = []
    for wiki, edits in filtered_lc:
        contribs = client.contribs(wiki, soap_member, 100)
        filtered_contribs = client.filter_contribs(contribs, wiki)
        for fc in filtered_contribs:
            # For each filtered edit, get previous
            reverted.append((wiki, client.get_prev_diff(wiki, fc['revid'])))
            print(wiki + 'wiki/?diff=' + str(client.get_prev_diff(wiki, fc['revid'])))
