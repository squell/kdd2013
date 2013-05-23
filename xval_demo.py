'''
  demo of cross validation
'''

import kddutil 
import cPickle as pickle
import sys
import sklearn
from sklearn import svm, tree, lda, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes

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

print kddutil.evaluate(ensemble.RandomForestClassifier(n_estimators=10), ids, info, labels)
sys.exit()

print "Random Forest"
print kddutil.evaluate(ensemble.RandomForestClassifier(n_estimators=50, min_samples_split=15), ids, info, labels)
print kddutil.evaluate(ensemble.RandomForestClassifier(n_estimators=50, min_samples_split=15), ids, info, labels)
print kddutil.evaluate(ensemble.RandomForestClassifier(n_estimators=50, min_samples_split=15), ids, info, labels)

print "ExtraTree Forest"
print kddutil.evaluate(ensemble.ExtraTreesClassifier(n_estimators=50, min_samples_split=15), ids, info, labels)
print kddutil.evaluate(ensemble.ExtraTreesClassifier(n_estimators=50, min_samples_split=15), ids, info, labels)
print kddutil.evaluate(ensemble.ExtraTreesClassifier(n_estimators=50, min_samples_split=15), ids, info, labels)

print "Gradient Boosting"
print kddutil.evaluate(ensemble.GradientBoostingClassifier(min_samples_split=15, max_depth=7), ids, info, labels)
print kddutil.evaluate(ensemble.GradientBoostingClassifier(min_samples_split=15, max_depth=7), ids, info, labels)
print kddutil.evaluate(ensemble.GradientBoostingClassifier(min_samples_split=15, max_depth=7), ids, info, labels)
