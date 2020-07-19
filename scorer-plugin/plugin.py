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
import logging
import time
from concurrent import futures as cfutures
from .scoring_handler import ScoringHandler

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Cynthia')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

# Load config
dir_path = os.path.dirname(os.path.realpath(__file__))
with open(dir_path + '/config.json', 'r') as f:
    config = json.load(f)

scoring_handler = ScoringHandler(config)

class Cynthia(callbacks.Plugin):
    threaded = True
    """
    Cynthia: Revscoring to Discord plugin
    """
    def __init__(self, irc):
        self.__parent = super(Cynthia, self)
        self.__parent.__init__(irc)
        self.log = log.getPluginLogger('Cynthia')
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + '/config.json', 'r') as f:
            config = json.load(f)

        scoring_handler = ScoringHandler(config)

        logging.getLogger('mwapi').setLevel(logging.ERROR)
        
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
            else:
                return (None, None)
            return ('https://' + m.group(3) + '.' + m.group(4), diff)
        return (None, None)

    def doPrivmsg(self, irc, msg):
        if irc.network == config['irc']['network'] and msg.args[0] == config['irc']['rc']:
            wiki, diff = self.get_wiki_and_diff(msg.args[1])

            if wiki and diff:
                self.executor.submit(scoring_handler.perform_scoring, wiki, diff, time.time())
                # scoring_handler.perform_scoring(wiki, diff, time.time())

Class = Cynthia

if __name__ == "__main__":
    new = Cynthia("Cynthia")
    print(new)