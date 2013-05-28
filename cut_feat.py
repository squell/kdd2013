'''
    reduce a feature-pickle file by selecting features
'''

from kddutil import *
import cPickle as pickle
import sys

if len(sys.argv) <= 3:
    print "pickel-in pickel-out selection [selection....]"
    sys.exit()

print "reading"
with open(sys.argv[1],"rb") as infile:
    train, test = pickle.load(infile)

selected = map(int, sys.argv[3:])
print "selected: ", selected

ids, features, labels = train
features = map(lambda feat: [row for (i,row) in enumerate(feat,1) if i in selected], features)
train = ids, features, labels

ids, features = test
features = map(lambda feat: [row for (i,row) in enumerate(feat,1) if i in selected], features)
test = ids, features

print "writing"
with open(sys.argv[2],"wb") as outfile:
    pickle.dump((train,test), outfile)

