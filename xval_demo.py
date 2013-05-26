'''
  a playground for evaluating classifiers
'''

import kddutil 
import cPickle as pickle
import sys
import sklearn
from sklearn import svm, tree, lda, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes

if len(sys.argv) <= 1:
    print "so what pkl do you want me to read, hm?"
    sys.exit()

randomForest = ensemble.RandomForestClassifier(verbose=True
	, n_estimators=80
	, min_samples_split=10
	, max_depth=14
	, n_jobs=15
	)

gradBoost = ensemble.GradientBoostingClassifier(verbose=True
	, n_estimators=100
	, min_samples_split=10
	, max_depth=5
	)

with open(sys.argv[1]) as infile:
    train, _ = pickle.load(infile)

# filter out entries which are marked both as positive AND negative
ids, info, labels = kddutil.uniq(*train)

info = kddutil.bound(info, max=10000, min=-10000)

print "Random Forest"
print kddutil.evaluate_k_(randomForest, ids, info, labels)

print "Gradient Boosting"
print kddutil.evaluate_k_(gradBoost, ids, info, labels)

