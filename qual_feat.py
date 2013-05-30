'''
  estimate the quality of features in a pickle file by showing the MAP if they
  are used stand-alone
'''

from kddutil import *
import cPickle as pickle
import sys

if len(sys.argv) <= 1:
    print "so what pkl do you want me to read, hm?"
    sys.exit()

with open(sys.argv[1]) as infile:
    train, _ = pickle.load(infile)

ids, info, labels = notrash(*train)

for i in xrange(len(info[0])):
    print "%.4f,\t%.4f" % (MAP(ids,labels,[+x[i] for x in info]), MAP(ids,labels,[-x[i] for x in info]))

