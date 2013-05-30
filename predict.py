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

randomForest = ensemble.RandomForestClassifier(verbose=True
        , n_estimators=80
        , min_samples_split=10
        , max_depth=14
        , n_jobs=12
        )

gradBoost = ensemble.GradientBoostingClassifier(verbose=True
        , n_estimators=100
        , min_samples_split=10
        , max_depth=5
        )

classifier = randomForest

with open(sys.argv[1]) as infile:
    train, test = pickle.load(infile)

train_ids, train_set, labels = kddutil.notrash(*train)
test_ids, test_set = kddutil.notrash(*test)

train_set = kddutil.bound(train_set, max=10000, min=-10000)
test_set  = kddutil.bound(test_set,  max=10000, min=-10000)

classifier.fit(train_set, labels)

predictions = classifier.predict_proba(test_set)[:,1]

print "writing to output.csv"
kddutil.write_csv(test_ids, predictions)

