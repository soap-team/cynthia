# https://github.com/wikimedia/editquality/blob/master/ipython/reverted_detection_demo.ipynb
# Modified for Fandom/Wikia.
# Obtains and stores features into a .tsv, given a list of revids
# Rather than a file with just revids, the required file contains links in the form:
# https://community.fandom.com/wiki/?diff=1234
# https://witcher.fandom.com/de/wiki/?diff=1234

import sys, re
import logging
import mwapi
from concurrent.futures import ProcessPoolExecutor
from feature_lists.fandom import damaging
from revscoring.extractors import api
from revscoring.errors import TextDeleted, RevisionNotFound

logging.getLogger('mwapi').setLevel(logging.ERROR) # silence 1.19 warnings

with open('20k-revisions.txt') as f:
    revisions = [(re.search('([0-9]+)$', i.strip()).group(1), 
                    re.search('^(https:\/\/.*?)\/wiki\/', i.strip()).group(1)) 
                    for i in f.readlines()]

# print(revisions[:10])

print(damaging)

def get_and_store_features(diff, url):
    try:
        print(diff, url)
        session = mwapi.Session(url, api_path='/api.php', 
                    user_agent='Cynthia - Vandalism detection bot, @noreplyz')
        api_extractor = api.Extractor(session)

        with open('20k-features-damaging-2.tsv', 'a') as f:
            # print(diff)
            features = list(api_extractor.extract(int(diff), damaging))
            features = [str(fea) for fea in features]
            f.write(url + '/wiki/?diff=' + diff + '\t' + '\t'.join(features) + '\n')

    except RevisionNotFound:
        print('Revision not found.')
        return
    except Exception:
        print('Wiki closed, or other issue.')
        return

executor = ProcessPoolExecutor(max_workers=4)

for rev in revisions:
    future = executor.submit(get_and_store_features, rev[0], rev[1])