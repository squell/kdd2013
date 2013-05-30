'''
  a playground for evaluating classifiers
'''

import kddutil 
import cPickle as pickle
import sys

if len(sys.argv) <= 2:
    print "usage: in.pkl out.pkl"
    sys.exit()

print "reading"
with open(sys.argv[1],'rb') as infile:
    train, test = pickle.load(infile)

print "dusting off trainset"
ids, info, labels = kddutil.notrash(*train)
info = kddutil.bound(info, max=10000, min=-10000)
print "pairing"
train = kddutil.transform_pairwise(lambda x,y:x-y, ids, info, labels)

print "dusting off testset"
ids, info = kddutil.notrash(*test)
info = kddutil.bound(info, max=10000, min=-10000)
print "pairing"
test = kddutil.transform_pairwise(lambda x,y:x-y, ids, info)

print "writing"
with open(sys.argv[2],'wb') as outfile:
    pickle.dump((train,test), outfile)

