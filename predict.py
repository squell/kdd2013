'''
  train a classifier and create predictions for uploading 
  (output.csv)
'''

import cPickle as pickle
import sys
import sklearn
from sklearn import svm, tree, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes
import kddutil

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
    train, test = pickle.load(infile)

train_ids, train_set, labels = train
test_ids, test_set = test

train_set = kddutil.bound(train_set, max=100000)
test_set  = kddutil.bound(test_set, max=100000)

classifier.fit(train_set, labels)

predictions = classifier.predict_proba(test_set)[:,1]

print "writing to output.csv"
kddutil.write_csv(test_ids, predictions)

