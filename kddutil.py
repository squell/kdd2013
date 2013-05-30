'''
    some functions which are useful even without the kdd-database loaded in memory
'''

#############################################################
# a less useful dictionary
#############################################################

class record (object):
    ''' a simple "coat hanger"

    using a regular dictionary is annoying
    - you dont want to see its representation all the time
    - not hashable 
    - it is nicer to type x.blaabla.werewr than x['blabla']['werewr'] 
    '''
    def __init__(self, d=None):
	self.__dict__ = d or {}
    def setdefault(self, name, val):
	return self.__dict__.setdefault(name, val)
    def get(self, name, val):
	return self.__dict__.get(name, val)
    def keys(self):
	return self.__dict__.keys()
    def values(self):
	return self.__dict__.values()
    def items(self):
	return self.__dict__.items()
    def __getitem__(self, name):
	return self.__dict__[name]
    def __contains__(self, name):
    	return name in self.__dict__
    def __getattr__(self, name):
	return self.__dict__.get(name, set())

#############################################################
# average precision -- assumes you are not trying to cheat
#############################################################

def avg_prec(decide, ranked, expected=None):
    'decide: is sample positive? ranked: ranking produced'
    acc = 0
    TP = 0
    seen = set()
    for P, paper in enumerate(ranked,1):
	if decide(paper) and paper not in seen:
	    TP  += 1
	    acc += TP/float(P)
	    seen.add(paper)
    try:
	return acc / (expected or TP)
    except ZeroDivisionError:
	return 1.0

#############################################################
# functions usable on processed and unprocessed data
#############################################################

def group_by_author(id_set, info_set):
    '''groups the results by author; input:
	list of tuples (having as first item an author/authorid)
	list of values (i.e. the result of a zip())
    returns: dictionary of author/authorid -> list of value
    '''
    xlat = {}
    for id, val in zip(id_set, info_set):
	xlat.setdefault(id[0], []).append(val)
    return xlat

# items with the same score are further sorted on id, then on label(!)
# this may seem strange, but intended so duplicates work correctly

def MAP(train_set, labels, predictions):
    '''calculates MAP for use with a sklearn-classifier
    first argument: raw-train data or a list of tuples of authorid,paperid
    second: list of correct labels
    third: predictions
    '''
    pids = [x[1] for x in train_set]
    xlat = group_by_author(train_set, zip(labels, predictions, pids))
    prec = 0
    N = 0
    for _, scores in xlat.iteritems():
	rank = sorted(scores, key=lambda x:(x[1],x[2],x[0]), reverse=True)
	prec += avg_prec(lambda x:x[0], rank)
	N += 1
    return prec/float(N)

def write_csv(train_set, predictions):
    def getId(obj):
	return obj.Id if type(obj) is record else obj

    authorIds = [(getId(a), ) for a,p in train_set]
    paperIds  = [getId(p) for a,p in train_set]
    table = group_by_author(authorIds, zip(paperIds, predictions))

    csv = open("output.csv", "w")
    print >> csv, "AuthorId, PaperIds"
    for authorId, ranking in table.iteritems():
	ranking = sorted(ranking, key=lambda x:(x[1],x[0]), reverse=True)
	print >> csv, "%d," % authorId,
	for paperId, _ in ranking:
	    print >> csv, paperId,
	print >> csv
    
#############################################################
# combining two sets of features 
# - this saves recomputation
#############################################################

import random

def merge_features(set1, set2):
    '''merge_features(set1, set2), where set1 and set2 be tuples of the form
    (ids, features) or (ids, features, labels) and contain
    exactly the same ids (but perhaps in a different order)
    '''
    set1 = zip(*sorted(zip(*set1)))
    set2 = zip(*sorted(zip(*set2)))
    if set1[0] <> set2[0] or set1[2:] <> set2[2:]:
	raise Exception("datasets differ")
    map(list.extend, set1[1], set2[1])
    set1 = zip(*set1)
    random.shuffle(set1)
    return zip(*set1)

#############################################################
# make sure all data points are within certain boundaries
#############################################################

def bound(data, min=-float('inf'), max=+float('inf')):
    if type(data) in [list,tuple]:
	return [bound(elem, min, max) for elem in data]
    elif data < min:
	return min
    elif data > max:
	return max
    else:
	return data

#############################################################
# splitting already processed data into train/validation sets
# this just uses the hold-out method; CV is overrated :-)
#############################################################

def xval_split(ids, labels, features, ratio=0.2, shuffle=True):
    table = group_by_author(ids, zip(ids, features, labels))
    authors = table.keys()
    if shuffle:
	for a in authors: random.shuffle(table[a])
    random.shuffle(authors)
    N = int(ratio*len(authors))
    train = zip(*[tuple for a in authors[N:] for tuple in table[a]])
    valid = zip(*[tuple for a in authors[:N] for tuple in table[a]])
    return train, valid

def xval_split_k(ids, labels, features, fold=10, shuffle=True):
    table = group_by_author(ids, zip(ids, features, labels))
    authors = table.keys()
    if shuffle:
	for a in authors: random.shuffle(table[a])
        random.shuffle(authors)
    N = int(len(authors)/fold)
    for k in xrange(fold):
	authors = authors[N:] + authors[:N]
	train = zip(*[tuple for a in authors[N:] for tuple in table[a]])
	valid = zip(*[tuple for a in authors[:N] for tuple in table[a]])
	yield train, valid

#############################################################
# demo: how to evaluate a classifier?
# use postprocess in case special treatment of trainset is desired
#############################################################

def evaluate(classifier, ids, features, labels, ratio=0.2, shuffle=True, postprocess=lambda *x: x):
    train, validate = xval_split(ids, labels, features, ratio, shuffle)
    ids, features, labels = postprocess(*train)
    classifier.fit(features, labels)
    ids, features, labels = validate
    return MAP(ids, labels, classifier.predict_proba(features)[:,1])

# calculate the average MAP for each score
def evaluate_k_(classifier, ids, features, labels, fold=3, shuffle=True, postprocess=lambda *x: x):
    score = 0
    for train, validate in xval_split_k(ids, labels, features, fold, shuffle):
	ids, features, labels = postprocess(*train)
	classifier.fit(features, labels)
	ids, features, labels = validate
	score += MAP(ids, labels, classifier.predict_proba(features)[:,1])
    return score/float(fold)

# calculate the overall MAP using scores obtained during folds
def evaluate_k(classifier, ids, features, labels, fold=3, shuffle=True, postprocess=lambda *x: x):
    score = []
    for train, validate in xval_split_k(ids, labels, features, fold, shuffle):
        ids, features, labels = postprocess(*train)
        classifier.fit(features, labels)
        ids, features, labels = validate
        for id,l,p in zip(ids,labels,classifier.predict_proba(features)[:,1]):
            score.append((id,l,p))
    return MAP(*zip(*score))

#############################################################
# turn stored data back into a input for map_score
#############################################################

def stored(ids, features):
    table = dict(zip(ids,features))
    return lambda a,p: table[a.Id,p.Id]

#############################################################
# remove/relabel duplicates from a id,feat,label set
#############################################################

def disambiguate(ids, features, labels):
    'totally remove data which is labelled inconsistently'
    data = zip(ids,features,labels)
    pos = { id for (id,f,l) in data if l }
    neg = { id for (id,f,l) in data if not l }
    uniq = pos^neg
    return zip(*[row for row in data if row[0] in uniq])

def relabel(ids, features, labels):
    'relabel data: 0 = False, 1 = True, 2 = Ambiguous'
    data = zip(ids,features,labels)
    pos = { id for (id,f,l) in data if l }
    neg = { id for (id,f,l) in data if not l }
    uniq = pos^neg
    dupl = pos&neg
    return zip(*[(id,f,int(l) if id in uniq else 2) for (id,f,l) in data])

def majority_vote(ids, features, labels):
    'relabel data: 0 = False, 1 = True, 2 = Ambiguous; minimize ambiguities'
    data = zip(ids,features,labels)
    bal = {}
    for (id,f,l) in data:
	bal[id] = bal.get(id,0) + (2*l-1)
    return zip(*[(id,f,(bal[id]>=0)+(bal[id]==0)) for (id,f,l) in data])

def nodupes(ids, features, labels=None):
    'remove exact duplicates (but not ambiguous labels) -- changes order'
    if labels:
	dct = { (id,l): f for (id,f,l) in zip(ids,features,labels) }
	return zip(*[(id,f,l) for ((id,l),f) in dct.iteritems()])
    else:
	return zip(*dict(zip(ids,features)).iteritems())

def notrash(ids, features, labels=None, assumed=True):
    'remove duplicates; replacing ambiguous with assumed -- changes order'
    if not labels: 
	return nodupes(ids, features)
    dct = {}
    for (id,f,l) in zip(ids,features,labels):
	dct[id] = (f,l if dct[id][1]==l else assumed) if id in dct else (f,l)
    return zip(*[(id,f,l) for (id,(f,l)) in dct.iteritems()])

#############################################################
# square the trainset for pairwise learning
#############################################################

# can be optimized; if the mingle function is known
# for example if mingle=operator.sub, C(x,y) = -C(y,x)

def transform_pairwise(mingle, ids, *vectors):
    'transform pointwise into pairwise input; assumes no duplicates in ids'
    def deepmap(f, xs, ys):
        try:
            return [ deepmap(f,x,y) for (x,y) in zip(xs,ys) ]
        except TypeError:
            return f(xs,ys)

    xlat = group_by_author(ids, zip(ids, *vectors))
    for qid in xlat:
	def pairing(x,y):
	    newid = (qid,x[0][1],y[0][1])
	    return (newid,)+tuple(deepmap(mingle,x[1:],y[1:]))
        orig = xlat[qid]
        xlat[qid] = [ pairing(x,y) for x in orig for y in orig ]
    return zip(*sum(xlat.itervalues(),[]))

#############################################################
# remove duplicates from a id,feat,label set
#############################################################

def memoise(f):
    tab = {}
    def proxy(*args):
	if args in tab:
		return tab[args]
	else:
		tab[args] = x = f(*args)
		return x
    return proxy

#############################################################
# a string cleaner
#############################################################

import re

def sanitize(s):
    return re.sub('[^\w]', ' ', s).strip().lower()

#############################################################
# a parallel map (inspired by ruben)
#############################################################

from multiprocessing import Queue, Process
def multomap(f, work, j=2):
    '''use as a simpe map taking a single list, run j jobs'''
    N = len(work)
    j = min(N,j)
    def submap(start,stop,result):
        result.put(map(f, work[start:stop]))

    queues = map(Queue, [1]*j)
    for (i,q) in enumerate(queues):
        Process(target=submap, args=(N*i/j,N*(i+1)/j,q)).start()

    return sum([q.get() for q in queues], [])

