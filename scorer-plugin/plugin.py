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
import concurrent.futures
from editquality.feature_lists.enwiki import damaging
from revscoring.extractors import api
from revscoring.errors import TextDeleted, RevisionNotFound
from revscoring.scoring.models import GradientBoosting, Classifier

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Cynthia')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Cynthia(callbacks.Plugin):
    threaded = True
    """
    Cynthia: Revscoring to Discord plugin
    """
    def __init__(self, irc):
        import platform

        logging.getLogger('mwapi').setLevel(logging.ERROR)

        self.__parent = super(Cynthia, self)
        self.__parent.__init__(irc)
        self.log = log.getPluginLogger('Cynthia')
        self.log.info(platform.python_version())

        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + '/config.json', 'r') as f:
            self.config = json.load(f)
        
        self.re_edit = re.compile(r'^\x0314\[\[\x0307([^\]]+)\x0314\]\]\x034 ([!NBM]*)\x0310 \x0302https?:\/\/([a-z0-9-.]+)\.(fandom\.com|wikia\.(?:com|org)|(?:wikia|fandom)-dev\.(?:com|us|pl))\/(?:([a-z-]+)\/)?index\.php\?(\S+)\x03 \x035\*\x03 \x0303([^\x03]+)\x03 \x035\*\x03 \(\x02?(\+|-)(\d+)\x02?\) \x0310(.*)$')
        # page, flags, wiki, domain, language, params, user, sign, num, summary
            
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

        self.damaging = damaging
        self.wikis = ['disney',
                      'villains',
                      'adoptme',
                      'dbz-dokkanbattle',
                      'marvel',
                      'dc',
                      'fategrandorder',
                      'animalcrossing',
                      'fallout',
                      'leagueoflegends',
                      'drama',
                      'harrypotter',
                      'doblaje',
                      'bokunoheroacademia',
                      'vsbattles',
                      'warframe',
                      'yugioh',
                      'spongebob',
                      'gta',
                      'noreply',
                      'bokunoheroacademia',
                      'a-bizarre-day-roblox',
                      'powerlisting',
                      'avatar',
                      'hero',
                      'logos',
                      'youtube',
                      'marvelcinematicuniverse',
                      'hypixel-skyblock',
                      'battle-cats',
                      'muppet',
                      'parody',
                      'wingsoffire',
                      'ttte',
                      'finalfantasy',
                      'miraculousladybug',
                      'megamitensei',
                      'towerofgod',
                      'battlefordreamisland',
                      'tardis',
                      'roblox',
                      'pokemon',
                      'witcher',
                      'memory-alpha',
                      'thelastofus',
                      'kamenrider',
                      'freddy-fazbears-pizza',
                      'cardfight',
                      'sonic',
                      'plantsvszombies',
                      'forgottenrealms',
                      'dragonball',
                      'xenoblade',
                      'ben10',
                      'minecraft',
                      'dragon-adventures',
                      'rogue-lineage',
                      'ninjago']
        with open(dir_path + '/' + self.config['models']['damaging'], 'rb') as model_file:
            self.model = Classifier.load(model_file)
        requests.post(self.config['discord'][0]['webhook'], data={
            'content': 'Reloaded Cynthia'
        })

        
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
            # if m.group(3) not in self.wikis:
            #     return (None, None)
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

    def get_features(self, wiki, diff):
        session = mwapi.Session(wiki, api_path='/api.php', 
                    user_agent='Cynthia - Vandalism detection bot, @noreplyz')
        api_extractor = api.Extractor(session)
        return list(api_extractor.extract(int(diff), self.damaging))

    def score(self, features):
        return self.model.score(features)

    def send_discord(self, wiki, diff, score, features):
        for hook in self.config['discord']:
            if hook['min'] <= round(score['probability'][True], 2) <= hook['max']:
                requests.post(hook['webhook'], data={
                    'content': str(round(score['probability'][True], 2)) + ': <' + wiki + '/wiki/?diff=' + diff + '>'
                })

    def perform_scoring(self, wiki, diff, start_time):
        page_data = requests.get(wiki + '/api.php?action=query&prop=info&revids=' + diff + '&format=json')
        try:
            page_data = page_data.json()
            page_id = next(iter(page_data['query']['pages']))
            ns = page_data['query']['pages'][page_id]['ns']
            if ns not in [0, 2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 500, 828]:
                return
        except Exception:
            return
        features = self.get_features(wiki, diff)
        if features:
            score = self.score(features)
            self.log.info(str(round(score['probability'][True], 2)) + ', ' + wiki + '/wiki/?diff=' + diff + ', ' + str(round(time.time() - start_time, 2)) + ' seconds')
            # print(features)
            # print(score['prediction'], round(score['probability'][True], 2))
            self.send_discord(wiki, diff, score, features)

    def doPrivmsg(self, irc, msg):
        if irc.network == self.config['irc']['network'] and msg.args[0] == self.config['irc']['rc']:
            start_time = time.time()
            wiki, diff = self.get_wiki_and_diff(msg.args[1])

            if wiki and diff:
                self.executor.submit(self.perform_scoring, wiki, diff, start_time)
                

Class = Cynthia

if __name__ == "__main__":
    new = Cynthia("Cynthia")
    print(new)