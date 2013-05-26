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

info = kddutil.bound(info, max=10000, min=-10000)

print "Random Forest"
classifier = ensemble.RandomForestClassifier(n_estimators=80, min_samples_split=10, max_depth=14, n_jobs=15)
print kddutil.evaluate_k_(classifier, ids, info, labels)
sys.exit()
print "Gradient Boosting"
classifier = ensemble.GradientBoostingClassifier(verbose=True, n_estimators=100, min_samples_split=10, max_depth=3)
print kddutil.evaluate_k_(classifier, ids, info, labels)

