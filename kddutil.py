'''
    some functions which are useful even without the kdd-database loaded in memory
'''

import random

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
# average precision
#############################################################

def avg_prec(decide, ranked):
    'decide: is sample positive? ranked: ranking produced'
    acc = 0
    TP = 0
    for P, paper in enumerate(ranked,1):
	if decide(paper):
	    TP  += 1
	    acc += TP/float(P)
    try:
	return acc / TP
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

def MAP(train_set, labels, predictions):
    '''calculates MAP for use with a sklearn-classifier
    first argument: raw-train data or a list of tuples of authorid,paperid
    second: list of correct labels
    third: predictions
    '''
    xlat = group_by_author(train_set, zip(labels, predictions))
    prec = 0
    N = 0
    for _, scores in xlat.iteritems():
	rank = sorted(scores, key=lambda x:x[1], reverse=True)
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
	ranking = sorted(ranking, key=lambda x:x[1], reverse=True)
	print >> csv, "%d," % authorId,
	for paperId, _ in ranking:
	    print >> csv, paperId,
	print >> csv
    
#############################################################
# combining two sets of features 
# - this saves recomputation
#############################################################

def merge_features(set1, set2):
    '''merge_features(set1, set2), where set1 and set2 be tuples of the form
    (ids, features) or (ids, features, labels) and contain
    exactly the same ids (but perhaps in a different order)
    '''
    set1 = zip(*set1)
    set2 = zip(*set2)
    table = {}
    for row in set1:
	table[row[0]] = list(row[1:])
    for row in set2:
	table[row[0]].append(row[1:])
    return zip(*[[key]+row for key, row in table.iteritems()])

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

#############################################################
# demo: how to evaluate a classifier?
#############################################################

def evaluate(classifier, ids, features, labels, ratio=0.2, shuffle=True):
    train, validate = xval_split(ids, labels, features, ratio, shuffle)
    ids, features, labels = train
    classifier.fit(features, labels)
    ids, features, labels = validate
    return MAP(ids, labels, classifier.predict_proba(features)[:,1])

#############################################################
# turn stored data back into a input for map_score
#############################################################

def stored(ids, features):
    table = dict(zip(ids,features))
    return lambda a,p: table[a.Id,p.Id]
