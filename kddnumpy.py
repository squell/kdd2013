'''
    useful functions requiring numpy (not usable with pypy)
'''

import numpy as np

# performs f (broadcasted) on all pairs of elements of arr
def cartesian(f, arr):
    return f(np.tile(arr, [arr.shape[0],1]), np.repeat(arr, arr.shape[0], 0))

def transform_pairwise_np(mingle, ids, vectors):
    'transform pointwise into pairwise input; assumes no duplicates in ids'

    xlat = {}
    for id, val in zip(ids, vectors):
	if id[0] in xlat:
	    xlat[id[0]] = np.append(xlat[id[0]], [val], 0)
	else:
	    xlat[id[0]] = np.array([val])

    N = len(xlat.items())
    M = 0.0
    for qid, orig in xlat.iteritems():
	M += 1.0
	print M/N
	xlat[qid] = cartesian(mingle, orig)

    return np.concatenate(xlat.values())

from kddutil import group_by_author, avg_prec

def MAP(ids, labels, vectors, mingle, classifier):
    pids = [x[1] for x in ids]
    xlat = group_by_author(ids, zip(labels, vectors))
    prec = 0
    N = 0
    def comparer(x,y):
	return int(classifier.predict(mingle(x[1], y[1]))[0])
    for _, scores in xlat.iteritems():
        rank = [x[0] for x in sorted(scores, cmp=comparer, reverse=True)]
        prec += avg_prec(lambda x:x, rank)
        N += 1
    return prec/float(N)


def write_csv(train_set, vectors, mingle, classifier):
    def getId(obj):
        return obj.Id if type(obj) is record else obj

    authorIds = [(getId(a), ) for a,p in train_set]
    paperIds  = [getId(p) for a,p in train_set]
    table = group_by_author(authorIds, zip(paperIds, vectors))

    def comparer(x,y):
	return int(classifier.predict(mingle(x[1], y[1]))[0])

    csv = open("output.csv", "w")
    print >> csv, "AuthorId, PaperIds"
    for authorId, ranking in table.iteritems():
        ranking = sorted(ranking, cmp=comparer, reverse=True)
        print >> csv, "%d," % authorId,
        for paperId, _ in ranking:
            print >> csv, paperId,
        print >> csv

