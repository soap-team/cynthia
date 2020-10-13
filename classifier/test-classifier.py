#from revscoring.features import wikitext, revision_oriented, temporal
#from revscoring.languages import english
from revscoring.extractors import api
from revscoring.scoring.models import GradientBoosting, Classifier
from revscoring.utilities.util import read_observations
from editquality.feature_lists.enwiki import damaging
old_damaging = damaging
from feature_lists.fandom import damaging


import json, re, sys, mwapi, logging

logging.getLogger('mwapi').setLevel(logging.ERROR) # silence 1.19 warnings

# Extract features for the diff using mwapi, and returns a list of features
def get_features(wiki, diff, featurelist):
    session = mwapi.Session('https://' + wiki, api_path='/api.php', 
                user_agent='Cynthia testing')
    api_extractor = api.Extractor(session)
    return list(api_extractor.extract(int(diff), featurelist))

with open('damaging-2020-3.model', 'rb') as model_file:
    v3_model = Classifier.load(model_file)
with open('damaging-2020-2.model', 'rb') as model_file:
    v2_model = Classifier.load(model_file)
with open('damaging-2020.model', 'rb') as model_file:
    v1_model = Classifier.load(model_file)

print(v3_model.info.format())

print('Loaded classifier - enter links:')

for line in sys.stdin:
    cmpts = re.match(r'(https:\/\/)?(.*?)\/wiki\/\?diff=(\d+)', line)
    if not cmpts:
        print('Not a link, try again')
        continue
    try:
        diff_features = get_features(cmpts.group(2), cmpts.group(3), damaging)
        diff_v1features = get_features(cmpts.group(2), cmpts.group(3), old_damaging)
    except Exception as e:
        print('Error: ' + str(repr(e)))

    v3_score = v3_model.score(diff_features)
    v2_score = v2_model.score(diff_features)
    v1_score = v1_model.score(diff_v1features)
    print('v1: ' + str(v1_score['probability'][True]))
    print('v2: ' + str(v2_score['probability'][True]))
    print('v3: ' + str(v3_score['probability'][True]))


# print(stats['thresholds'].format())

# reverted_obs = [(rev_features, diff) for rev_features, reverted, diff in testing_features_2 if reverted]
# non_reverted_obs = [(rev_features, diff) for rev_features, reverted, diff in testing_features_2 if not reverted]

# for rev_features, diff in reverted_obs[:20]:
#     score = is_reverted.score(rev_features)
#     print(True, str(diff), 
#           score['prediction'], round(score['probability'][True], 2))

# for rev_features, diff in non_reverted_obs[:20]:
#     score = is_reverted.score(rev_features)
#     print(False, str(diff), 
#       score['prediction'], round(score['probability'][True], 2))
# '''
# with open('../feature-gen/20k-features.tsv') as f1:
#     for line in f1.readlines()[500:999]:
#         feature_values = list(api_extractor.extract(rev_id, features))
#         score = is_reverted.score(feature_values)
#         print(True, line., 
#           score['prediction'], round(score['probability'][True], 2))
# '''