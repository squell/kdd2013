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

randomForest = ensemble.RandomForestClassifier(verbose=False
	, n_estimators=80
	, min_samples_split=10
	, max_depth=14
	, n_jobs=15
	)

randomForestRegress = ensemble.RandomForestClassifier(verbose=True
	, n_estimators=80
	, min_samples_split=10
	, max_depth=14
	, n_jobs=15
	)

gradBoost = ensemble.GradientBoostingClassifier(verbose=True
	, n_estimators=100
	, min_samples_split=10
	, max_depth=7
	)

with open(sys.argv[1]) as infile:
    train, _ = pickle.load(infile)

if type(train[1][0]) == list:
    ids, info, labels = kddutil.notrash(*train)
    info = kddutil.bound(info, max=10000, min=-10000)
else:
    ids, info, labels = train
    print "assuming compacted data; skip preprocessing"

print "Random Forest"
print kddutil.evaluate_k(randomForest, ids, info, labels)

#print "Gradient Boosting"
#print kddutil.evaluate(gradBoost, ids, info, labels)

