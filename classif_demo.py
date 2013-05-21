#! /usr/bin/python -O -i

'''
 a demo on using kddload to train a (overfitted) classifier
'''

import sklearn
from sklearn import svm, tree, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes


classifier = ensemble.RandomForestClassifier(
		  verbose=10
		, oob_score=True
		, n_estimators=10#50
		, n_jobs=4
		, criterion='entropy'
		, compute_importances=False
		)

from scrabble import Scrabble

feature_set = [
	  lambda a,p: len(p.Journal.Paper & a.Paper) if p.Journal else 0
	, lambda a,p: len(p.Conference.Paper & a.Paper) if p.Conference else 0
	, lambda a,p: len(p.Conference.Paper & a.Paper) if p.Conference else 0
	, lambda a,p: len(a.Paper)
	, lambda a,p: len(p.Author)
	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: int(p.Year)
	, lambda a,p: len(a.Voc & p.Voc)
	, lambda a,p: average([Scrabble(w) for w in p.Voc]) if p.Voc else 0
	]

# this will take awhile
from kddload import *

raw_data, train_data, labels = train_data(feature_set)

classifier.fit(train_data, labels)

predictions = classifier.predict_proba(train_data)[:,1]

print MAP(raw_data, labels, predictions)

