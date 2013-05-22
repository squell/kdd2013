#! /usr/bin/python -O -i

'''
  demo of cross validation
'''

import kddutil 
import cPickle as pickle
import sys
import sklearn
from sklearn import svm, tree, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes

if len(sys.argv) <= 1:
    print "so what pkl do you want me to read, hm?"
    sys.exit()

classifier = ensemble.RandomForestClassifier(
		  verbose=10
		 , oob_score=True
		, n_estimators=50
		, n_jobs=4
		 , criterion='entropy'
		 , compute_importances=True
		#, random_state=1 #
		, min_samples_split=10 #
		)

with open(sys.argv[1]) as infile:
    train, _ = pickle.load(infile)

ids, info, labels = train

info = kddutil.bound(info, max=10000)

print kddutil.evaluate(classifier, ids, info, labels)

