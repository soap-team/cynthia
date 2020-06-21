# https://github.com/wikimedia/editquality/blob/master/ipython/reverted_detection_demo.ipynb
# Modified for Fandom/Wikia.
# Obtains and stores features into a .tsv, given a list of revids
# Rather than a file with just revids, the required file contains links in the form:
# https://community.fandom.com/wiki/?diff=1234
# https://witcher.fandom.com/de/wiki/?diff=1234

import sys, re
import mwapi
from editquality.feature_lists.enwiki import damaging
from revscoring.extractors import api
from revscoring.errors import TextDeleted, RevisionNotFound

with open('20k-revisions.txt') as f:
    revisions = [(re.search('([0-9]+)$', i.strip()).group(1), 
                    re.search('^(https:\/\/.*?)\/wiki\/', i.strip()).group(1)) 
                    for i in f.readlines()]

# print(revisions[:10])

print(damaging)

for rev in revisions[201:]:
    try:
        print(rev)
        session = mwapi.Session(rev[1], api_path='/api.php', 
                    user_agent='Cynthia - Vandalism detection bot, @noreplyz')
        api_extractor = api.Extractor(session)
        print(list(api_extractor.extract(int(rev[0]), damaging)))
    except RevisionNotFound:
        print('Revision not found.')
        continue
    except Exception:
        print('Wiki closed, or other issue.')
        continue