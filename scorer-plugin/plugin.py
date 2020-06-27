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

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Cynthia')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class Cynthia(callbacks.Plugin):
    """
    Cynthia: Revscoring to Discord plugin
    """
    def __init__(self, irc):
        self.__parent = super(Cynthia, self)
        self.__parent.__init__(irc)
        self.log = log.getPluginLogger('Cynthia')

        with open('config.json', 'r') as f:
            self.config = json.load(f)
        
        self.re_edit = re.compile(ur'^\x0314\[\[\x0307([^\]]+)\x0314\]\]\x034 ([!NBM]*)\x0310 \x0302https?:\/\/([a-z0-9-.]+)\.(fandom\.com|wikia\.(?:com|org)|(?:wikia|fandom)-dev\.(?:com|us|pl))\/(?:([a-z-]+)\/)?index\.php\?(\S+)\x03 \x035\*\x03 \x0303([^\x03]+)\x03 \x035\*\x03 \(\x02?(\+|-)(\d+)\x02?\) \x0310(.*)$')
        # page, flags, wiki, domain, language, params, user, sign, num, summary
        
    def get_wiki_and_diff(self, msg):
        """
        Returns the wiki URL and diff link parsed to the message
        """
        m = self.re_edit.match(msg)
        if m:
            # ignore non-EN wikis (for now)
            if m.group(5):
                return (None, None)
            url = '{0}.{1}'.format(m.group(3), m.group(4))
            params = [a.split('=') for a in m.group(6).split('&')]
            params = {p[0]: p[1] for p in params}
            diff = None
            if 'diff' in params:
                diff = params['diff']
            elif 'oldid' in params:
                diff = params['oldid']
            return (m.group(3) + '.' + m.group(4), diff)

    def doPrivmsg(self, irc, msg):
        if irc.network == self.config['irc']['network'] and msg.args[0] == self.config['irc']['rc']:
            wiki, diff = get_wiki_and_diff(msg.args[1])

            if wiki and diff:
                self.log.info(wiki + diff)

Class = Cynthia

if __name__ == "__main__":
    new = Cynthia("Test")
    print(new)