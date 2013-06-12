'''
  merge the prediction of a classifier as another feature
'''

import cPickle as pickle
import sys
import sklearn
from sklearn import svm, tree, qda, metrics, cross_validation, grid_search, datasets, ensemble, linear_model, naive_bayes
import kddutil

if len(sys.argv) <= 2:
    print "input.pkl output.pkl"
    sys.exit()

randomForest = ensemble.RandomForestClassifier(verbose=True
        , n_estimators=80
        , min_samples_split=10
        , max_depth=14
        , bootstrap=False
        , n_jobs=16
        )

gradBoost = ensemble.GradientBoostingClassifier(verbose=True
        , n_estimators=100
        , min_samples_split=10
        , max_depth=5
        )

classifier = randomForest

print "reading"
with open(sys.argv[1]) as infile:
    train, test = pickle.load(infile)

if type(train[1][0]) == list:
    train_ids, train_set, labels = kddutil.notrash(*train)
    test_ids, test_set = kddutil.notrash(*test)

    train_set = kddutil.bound(train_set, max=10000, min=-10000)
    test_set  = kddutil.bound(test_set,  max=10000, min=-10000)
else:
    print "sorry, dont use this on numpifiyied input!"
    sys.exit()

print "training"
classifier.fit(train_set, labels)

print "writing"
map(list.append, train_set, classifier.predict_proba(train_set)[:,1])
map(list.append, test_set, classifier.predict_proba(test_set)[:,1])

train = train_ids, train_set, labels
test = test_ids, test_set

with open(sys.argv[2],"wb") as outfile:
    pickle.dump((train,test), outfile)

