import requests
import json
import os
import mwapi
import time
from editquality.feature_lists.enwiki import damaging
from revscoring.extractors import api
from revscoring.scoring.models import Classifier

class ScoringHandler:
    """
    Handles revscoring for incoming edits, and sends
    filtered results to Discord.
    """

    def __init__(self, config):
        self.config = config

        # Load classifier
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + '/' + config['models']['en-damaging'], 'rb') as model_file:
            self.model = Classifier.load(model_file)

    # Check if page is in a scoreable namespace.
    def is_scoreable_namespace(self, wiki, diff):
        page_data = requests.get(wiki + '/api.php?action=query&prop=info&revids=' + diff + '&format=json')
        try:
            page_data = page_data.json()
            page_id = next(iter(page_data['query']['pages']))
            ns = page_data['query']['pages'][page_id]['ns']
            if ns not in [0, 2, 3, 4, 5, 8, 9, 10, 11, 14, 15, 500, 828]:
                return False
            return True
        except Exception:
            return False

    # Get verbose information (title and user) on a particular diff
    def get_verbose_info(self, wiki, diff):
        page_data = requests.get(wiki + '/api.php?action=query&prop=revisions&rvprop=user&revids=' + diff + '&format=json')
        try:
            page_data = page_data.json()
            page_id = next(iter(page_data['query']['pages']))
            return (page_data['query']['pages'][page_id]['title'], page_data['query']['pages'][page_id]['revisions'][0]['user'])
        except Exception:
            return (None, None)

    def _fill_embed(self, embed, to_parse):
        for s in to_parse:
            embed['description'] = embed['description'].replace(*s)
            embed['footer']['text'] = embed['footer']['text'].replace(*s)
            for k in range(len(embed['fields'])):
                embed['fields'][k]['value'] = embed['fields'][k]['value'].replace(*s)
        return embed

    # Send data to multiple Discord webhooks
    def send_discord(self, wiki, diff, score, features):
        for hook in self.config['discord']:
            if hook['min'] <= round(score['probability'][True], 2) <= hook['max']:
                to_parse = ( \
                    ("$wiki", wiki),
                    ("$diff", diff),
                    ("$score", str(round(score['probability'][True], 2)))
                )
                if 'verbose' in hook and hook['verbose']:
                    page, user = self.get_verbose_info(wiki, diff)
                    page = page.replace(' ', '_')
                    user = user.replace(' ', '_')
                    to_parse = (
                        ("$wiki", wiki),
                        ("$diff", diff),
                        ("$score", str(round(score['probability'][True], 2))),
                        ("$user", user),
                        ("$page", page)
                    )
                if 'embed' in hook:
                    embeds = self._fill_embed(hook['embed'], to_parse)
                    headers = {'Content-Type': 'application/json'}
                    a = requests.post(hook['webhook'], headers=headers, data=json.dumps({
                        'embeds': [embeds]
                    }))
                else:
                    content = hook['content']
                    for s in to_parse:
                        content = content.replace(*s)
                    requests.post(hook['webhook'], data={
                        'content': content
                    })

    # Extract features for the diff using mwapi, and returns a list of features
    def get_features(self, wiki, diff):
        session = mwapi.Session(wiki, api_path='/api.php', 
                    user_agent=self.config['user_agent'])
        api_extractor = api.Extractor(session)
        return list(api_extractor.extract(int(diff), damaging))

    # Perform scoring
    def perform_scoring(self, wiki, diff, model, start_time):
        if not self.is_scoreable_namespace(wiki, diff):
            return {
                'error': 'Not a scorable namespace',
                'probability': -1
            }
        features = self.get_features(wiki, diff)
        if features:
            score = self.model.score(features)
            # print(str(round(score['probability'][True], 2)) + '\t' + str(round(time.time() - start_time, 2)) + '\t'
            #      + wiki + '/wiki/?diff=' + diff + '')
            return {
                'probability': score['probability'][True]
            }
        else:
            return {
                'error': 'Could not extract features',
                'probability': -1
            }
            # self.send_discord(wiki, diff, score, features)