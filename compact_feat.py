'''
   compacts a feature file by storing it as numpy arrays
   - also removes duplicates, and infinities
'''

import kddutil
import cPickle as pickle
import numpy as np
import sys

if len(sys.argv) <= 2:
    print "pickelino pickelouto"
    sys.exit()

print "reading"
with open(sys.argv[1],"rb") as infile:
    train, test = pickle.load(infile)

print "numpyifying"

id, feat, lab = kddutil.notrash(*train)
feat = kddutil.bound(feat, min=-10000, max=+10000)
train = np.array(id, np.int32), np.array(feat, np.float16), np.array(lab, np.bool)

id, feat = kddutil.notrash(*test)
feat = kddutil.bound(feat, min=-10000, max=+10000)
test = np.array(id, np.int32), np.array(feat, np.float16)

print "writing"
with open(sys.argv[2],"wb") as outfile:
    pickle.dump((train,test), outfile)

