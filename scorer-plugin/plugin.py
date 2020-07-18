import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.ircmsgs as ircmsgs
import supybot.log as log
import requests
import re
import json
import os
import sys
import mwapi
import logging
import time
from concurrent import futures as cfutures
from editquality.feature_lists.enwiki import damaging
from revscoring.extractors import api
from revscoring.errors import TextDeleted, RevisionNotFound
from revscoring.scoring.models import GradientBoosting, Classifier
import faulthandler

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Cynthia')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(dir_path + '/config.json', 'r') as f:
    config = json.load(f)

damaging = damaging

with open(dir_path + '/' + config['models']['damaging'], 'rb') as model_file:
    model = Classifier.load(model_file)

class Cynthia(callbacks.Plugin):
    threaded = True
    """
    Cynthia: Revscoring to Discord plugin
    """
    def __init__(self, irc):

        faulthandler.enable()
        logging.getLogger('mwapi').setLevel(logging.ERROR)

        self.__parent = super(Cynthia, self)
        self.__parent.__init__(irc)
        self.log = log.getPluginLogger('Cynthia')
        
        self.re_edit = re.compile(r'^\x0314\[\[\x0307([^\]]+)\x0314\]\]\x034 ([!NBM]*)\x0310 \x0302https?:\/\/([a-z0-9-.]+)\.(fandom\.com|wikia\.(?:com|org)|(?:wikia|fandom)-dev\.(?:com|us|pl))\/(?:([a-z-]+)\/)?index\.php\?(\S+)\x03 \x035\*\x03 \x0303([^\x03]+)\x03 \x035\*\x03 \(\x02?(\+|-)(\d+)\x02?\) \x0310(.*)$')
        # page, flags, wiki, domain, language, params, user, sign, num, summary

        requests.post(config['discord'][0]['webhook'], data={
            'content': 'Reloaded Cynthia'
        })

        self.executor = cfutures.ProcessPoolExecutor(max_workers=4)

        
    def get_wiki_and_diff(self, msg):
        """
        Returns the wiki URL and diff link parsed to the message
        """
        m = self.re_edit.match(msg)
        if m:
            # ignore non-EN wikis (for now)
            if m.group(5):
                return (None, None)
            if m.group(1).startswith('Board:') or m.group(1).startswith('Message Wall:'):
                return (None, None)
            url = '{0}.{1}'.format(m.group(3), m.group(4))
            params = [a.split('=') for a in m.group(6).split('&')]
            params = {p[0]: p[1] for p in params}
            diff = None
            if 'diff' in params:
                diff = params['diff']
            elif 'oldid' in params:
                diff = params['oldid']
            return ('https://' + m.group(3) + '.' + m.group(4), diff)
        return (None, None)

    def doPrivmsg(self, irc, msg):
        if irc.network == config['irc']['network'] and msg.args[0] == config['irc']['rc']:
            wiki, diff = self.get_wiki_and_diff(msg.args[1])

            if wiki and diff:
                self.executor.submit(perform_scoring, wiki, diff, time.time())
                # self.perform_scoring(wiki, diff)


def perform_scoring(wiki, diff, start_time):
    page_data = requests.get(wiki + '/api.php?action=query&prop=info&revids=' + diff + '&format=json')
    try:
        page_data = page_data.json()
        page_id = next(iter(page_data['query']['pages']))
        ns = page_data['query']['pages'][page_id]['ns']
        if ns not in [0, 2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 500, 828]:
            return
    except Exception:
        return
    features = get_features(wiki, diff)
    if features:
        score = model.score(features)
        print(str(round(score['probability'][True], 2)) + '\t' + str(round(time.time() - start_time, 2)) + '\t'
             + wiki + '/wiki/?diff=' + diff + '')
        # print(features)
        # print(score['prediction'], round(score['probability'][True], 2))
        send_discord(wiki, diff, score, features)


def get_features(wiki, diff):
    session = mwapi.Session(wiki, api_path='/api.php', 
                user_agent='Cynthia - Vandalism detection bot, @noreplyz')
    api_extractor = api.Extractor(session)
    return list(api_extractor.extract(int(diff), damaging))


def send_discord(wiki, diff, score, features):
    for hook in config['discord']:
        if hook['min'] <= round(score['probability'][True], 2) <= hook['max']:
            requests.post(hook['webhook'], data={
                'content': str(round(score['probability'][True], 2)) + ': <' + wiki + '/wiki/?diff=' + diff + '>'
            })

Class = Cynthia

if __name__ == "__main__":
    new = Cynthia("Cynthia")
    print(new)