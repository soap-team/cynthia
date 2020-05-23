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
        try:
            res = self.session.get(wiki + 'api.php', params={
                'action': 'query',
                'list': 'usercontribs',
                'ucuser': user,
                'uclimit': limit,
                'format': 'json'
            })
        except (requests.exceptions.SSLError) as e:
            print('Failed to get contribs for ' + wiki)
            return []
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
    
    # https://mario.fandom.com/api.php?action=query&prop=revisions&revids=288644&rvprop=ids|comment&rvdiffto=next&format=json
    # Returns true if the edit does not have a revert after it
    # false if the edit is reverted
    def is_good_next_diff(self, wiki, curr_diff):
        try:
            res = self.session.get(wiki + 'api.php', params={
                'action': 'query',
                'prop': 'revisions',
                'revids': curr_diff,
                'rvprop': 'ids|comment',
                'rvdiffto': 'next',
                'format': 'json'
            })
            pages = res.json()['query']['pages']
        except (json.decoder.JSONDecodeError, KeyError) as e:
            print('Failed to get diff ' + wiki + ', ' + str(curr_diff))
            return False
        
        for page in pages:
            hasDiff = pages[page]['revisions'][0]['diff']['to']
            if int(hasDiff) == 0:
                return True # Good
            elif re.match(self.re_like_rollback, pages[page]['revisions'][0]['comment']):
                return False
            return True        
        return False

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


def get_split_3():
    data_users = []
    for username in data_users:
        client = DatasetGenerator()

        # Get LC
        lc = client.lc(username, '1000')
        filtered_lc = client.filtered_lc(lc, 1, 20)

        # Loop through wikis and get contribs
        reverted = []
        for wiki, edits in filtered_lc:
            contribs = client.contribs(wiki, username, 100)
            filtered_contribs = client.filter_contribs(contribs, wiki)
            contribs_per_wiki = 3
            for fc in filtered_contribs:
                # For each filtered edit, get previous
                reverted.append((wiki, client.get_prev_diff(wiki, fc['revid'])))
                with open(username + '.txt', 'a') as log:
                    log.write(wiki + 'wiki/?diff=' + str(client.get_prev_diff(wiki, fc['revid'])) + '\n')

                # only get a number of contribs per wiki
                contribs_per_wiki -= 1
                if contribs_per_wiki == 0:
                    break

def get_split_1():
    client = DatasetGenerator()
    with open('potentially-good-recent.txt') as f:
        diffs = f.readlines()

    diffs = [s.strip() for s in diffs] 
    print(diffs)

    for diff in diffs:
        if client.is_good_next_diff(re.findall(r'^(https?:\/\/.*\.(com|org)\/)', diff)[0][0], re.findall(r'\d+$', diff)[0]):
            with open('data/good-recent.txt', 'a') as log:
                log.write(diff + '\n')
        else:
            print(diff + ' is bad')

def get_split_2():
    client = DatasetGenerator()
    with open('data/admin-reverts.txt') as f:
        diffs = f.readlines()

    diffs = [s.strip() for s in diffs] 
    print(diffs)

    for diff in diffs:
        wiki = re.findall(r'^(https?:\/\/.*\.(com|org)\/)', diff)[0][0]
        try:
            prev = client.get_prev_diff(wiki, re.findall(r'\d+$', diff)[0])
        except KeyError:
            prev = None
        if prev:
            with open('data/bad-admin-reverted.txt', 'a') as log:
                log.write(wiki + 'wiki/?diff=' + str(prev) + '\n')
        else:
            print(diff + ' is bad')
            

if __name__ == '__main__':
    get_split_2()