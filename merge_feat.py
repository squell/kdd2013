'''
  estimate the quality of features in a pickle file
'''

from kddutil import *
import cPickle as pickle
import sys

if len(sys.argv) <= 3:
    print "pickel1 pickle2 pickle_out"
    sys.exit()

print "reading #1"
with open(sys.argv[1],"rb") as infile:
    train1, test1 = pickle.load(infile)
print "reading #2"
with open(sys.argv[2],"rb") as infile:
    train2, test2 = pickle.load(infile)
print "writing #1+#2"
with open(sys.argv[3],"wb") as outfile:
    pickle.dump((merge_features(train1,train2),merge_features(test1,test2)), outfile)

