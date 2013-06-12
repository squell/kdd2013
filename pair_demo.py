'''
  a playground for evaluating classifiers
'''

import kddutil 
import kddnumpy
import cPickle as pickle
import sys
import sklearn
import numpy as np
import operator
from sklearn import svm, tree, lda, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes

if len(sys.argv) <= 1:
    print "so what pkl do you want me to read, hm?"
    sys.exit()

randomForest = ensemble.RandomForestClassifier(verbose=10
	, n_estimators=80
	, min_samples_split=10
	, max_depth=14
	, n_jobs=16
	)
randomForest2 = ensemble.RandomForestClassifier(verbose=10
	, n_estimators=80
	, min_samples_split=10
	, max_depth=14
	, n_jobs=5
	)

print "reading"
with open(sys.argv[1]) as infile:
    train, _ = pickle.load(infile)

ids, info, labels = train

print "training points"
randomForest.fit(info, labels)

print "transforming"
info2 = np.append([labels],info.T,0).T
info2 = kddnumpy.transform_pairwise_np(operator.sub, ids, info2)

print "!??"
label2 = info2[:,0]
info2 = info2[:,1:]

print "training pairs"
#randomForest2.fit(info2, label2)
with open("precious.pkl","rb") as infile:
    randomForest2 = pickle.load(infile)

print "predicting (normal resubstitution)"
predictions = randomForest.predict_proba(info)[:,1]
print "+", kddutil.MAP(ids, labels, predictions)
predictions = map(lambda x:-x, predictions)
print "-", kddutil.MAP(ids, labels, predictions)

print "predicting (paired resubstitution)"
predictions = randomForest2.predict_proba(info)[:,1]
print "+", kddutil.MAP(ids, labels, predictions)
predictions = map(lambda x:-x, predictions)
print "-", kddutil.MAP(ids, labels, predictions)

print "predicting (pairwise resubstitution)"
print "*", kddnumpy.MAP(ids, labels, info, operator.sub, randomForest2)

