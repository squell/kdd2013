#! /usr/bin/python -O -i

'''
 a demo on using kddload to train a (overfitted) classifier
'''

import sklearn
from sklearn import svm, tree, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes


classifier = ensemble.RandomForestClassifier(
		  verbose=10
		#, oob_score=True
		, n_estimators=50
		, n_jobs=4
		#, criterion='entropy'
		#, compute_importances=False
		, random_state=1 #
		, min_samples_split=10
		)

from scrabble import Scrabble
from kddload import *          # this will take awhile

feature_set = features(
	  lambda a,p: len(p.Journal.Paper & a.Paper) if p.Journal else 0
	, lambda a,p: len(p.Conference.Paper & a.Paper) if p.Conference else 0
	, lambda a,p: len(p.Conference.Paper & a.Paper) if p.Conference else 0

	, lambda a,p: len(a.Paper)
	, lambda a,p: len(p.Author)
	, lambda a,p: int(p.Year)

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Journal','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Journal','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Conference','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Conference','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(jaccard, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}, relate('Author','Journal')) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}, relate('Author','Conference')) if len(a.Paper) > 1 else 0

	, lambda a,p: len(a.Voc & p.Voc)
	, lambda a,p: sum(select(a.PrefVoc, p.Voc).values())

	, lambda a,p: average([Scrabble(w) for w in p.Voc]) if p.Voc else 0
	)

raw_data, labels = train_data()

train            = feature_set(raw_data)
classifier.fit(train, labels)
predictions      = classifier.predict_proba(train)[:,1]
print MAP(raw_data, labels, predictions)

stop(here(now))

raw_data    = test_data()
test        = feature_set(raw_data)
predictions = classifier.predict_proba(test)[:,1]

write_csv(raw_data, predictions)

