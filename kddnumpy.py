'''
    useful functions requiring numpy (not usable with pypy)
'''

import numpy as np

def transform_pairwise_np(mingle, ids, vectors):
    'transform pointwise into pairwise input; assumes no duplicates in ids'

    # performs f (broadcasted) on all pairs of elements of arr
    def cartesian(f, arr):
	return f(np.tile(arr, [arr.shape[0],1]), np.repeat(arr, arr.shape[0], 0))

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

def MAP(ids, vectors, labels, comparer):
    pids = [x[1] for x in ids]
    xlat = group_by_author(ids, zip(labels, vectors))
    prec = 0
    N = 0
    for _, scores in xlat.iteritems():
        rank = sorted(scores, cmp=lambda x,y:comparer(x[1],y[1]), reverse=True)
        prec += avg_prec(lambda x:x[0], rank)
        N += 1
    return prec/float(N)


