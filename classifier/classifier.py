#from revscoring.features import wikitext, revision_oriented, temporal
#from revscoring.languages import english
from revscoring.scoring.models import GradientBoosting, Classifier
from revscoring.utilities.util import read_observations
from editquality.feature_lists.enwiki import damaging

import json

'''
features = [
	# Catches long key mashes like kkkkkkkkkkkk
	wikitext.revision.diff.longest_repeated_char_added,
	# Measures the size of the change in added words
	wikitext.revision.diff.words_added,
	# Measures the size of the change in removed words
	wikitext.revision.diff.words_removed,
	# Measures the proportional change in "badwords"
	english.badwords.revision.diff.match_prop_delta_sum,
	# Measures the proportional change in "informals"
	english.informals.revision.diff.match_prop_delta_sum,
	# Measures the proportional change meaningful words
	english.stopwords.revision.diff.non_stopword_prop_delta_sum,
	# Is the user anonymous
	revision_oriented.revision.user.is_anon,
	# Is the user a bot or a sysop
	revision_oriented.revision.user.in_group({'bot', 'sysop'}),
	# How long ago did the user register?
	temporal.revision.user.seconds_since_registration
]
'''
features = damaging

def processFeatures(a):
	if a == 'True': return True
	if a == 'False': return False
	try:
		return float(a)
	except ValueError:
		print('diff link is not a float')
	return None



training_features = []
testing_features = []
testing_features_2 = []

with open('damaging-labels.json') as f:
	content = json.load(f)
	with open('../feature-gen/20k-features.tsv') as f1:
		for line in f1.readlines()[:10000]:
			i = [x.strip() for x in line.split('\t')]
			diff = i[0]
			ftr = [processFeatures(a) for a in i[1:]]
			training_features.append((ftr, True if content[diff] else False))
		f1.seek(0)
		for line in f1.readlines()[10001:]:
			i = [x.strip() for x in line.split('\t')]
			diff = i[0]
			ftr = [processFeatures(a) for a in i[1:]]
			testing_features.append((ftr, True if content[diff] else False))
			testing_features_2.append((ftr, True if content[diff] else False, diff))

is_reverted = GradientBoosting(features, labels=[True, False], version="live demo!", 
							   learning_rate=0.01, max_features="log2", 
							   n_estimators=700, max_depth=5,
							   population_rates=None, scale=True, center=True, verbose=1)

is_reverted.train(training_features)
is_reverted.test(testing_features)
print(is_reverted.info.format())

with open('damaging-2020.model', 'wb') as model_file:
    is_reverted.dump(model_file)

# with open('damaging-2020.model', 'rb') as model_file:
#     is_reverted = Classifier.load(model_file)

reverted_obs = [(rev_features, diff) for rev_features, reverted, diff in testing_features_2 if reverted]
non_reverted_obs = [(rev_features, diff) for rev_features, reverted, diff in testing_features_2 if not reverted]

for rev_features, diff in reverted_obs[:20]:
    score = is_reverted.score(rev_features)
    print(True, str(diff), 
          score['prediction'], round(score['probability'][True], 2))

for rev_features, diff in non_reverted_obs[:20]:
    score = is_reverted.score(rev_features)
    print(False, str(diff), 
          score['prediction'], round(score['probability'][True], 2))
'''
with open('../feature-gen/20k-features.tsv') as f1:
	for line in f1.readlines()[500:999]:
		feature_values = list(api_extractor.extract(rev_id, features))
		score = is_reverted.score(feature_values)
		print(True, line., 
          score['prediction'], round(score['probability'][True], 2))
'''