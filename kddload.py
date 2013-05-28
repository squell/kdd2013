import sys
import csv
import math
import random
from kddutil import *

#############################################################
# read in a huge amount of data; create forward and backward
# links contained in the .csv on the fly as direct ref's
#############################################################

db = dict()

def read_csv(table, force_creation=False, missing=None):
    print "reading", table
    dataset = []
    db[table] = dataset

    def identify(dataset, idx, obj):
	#grow dataset if necessary
	while idx >= len(dataset):
	    dataset.extend([None]*(idx+1-len(dataset)))
	dataset[idx] = obj
	return obj

    for row in csv.DictReader(open(table+".csv", 'rb')):
	obj = record(row)

	# add identifiable items
	if 'Id' in row:
	    row['Id'] = idx = int(row['Id'])
	    identify(dataset, idx, obj)
	elif force_creation:
	    dataset.append(obj)

	# convert references in row into pythonesque
	for key, val in row.items():
	    if key[-2:] == "Id" and len(key) > 2:
		del row[key]
		newkey = key[:-2]
		try:
		    row[newkey] = foreign = db[newkey][int(val)]
		except IndexError:
		    #print "invalid foreign key:", table, newkey, val
		    row[newkey] = foreign = None
		if not foreign: 
		    #print "null foreign key:", table, newkey, val
		    row[newkey] = foreign = missing and missing()
		    if missing: foreign.Id = int(val)
		    identify(db[newkey], int(val), foreign)
		if foreign:
		    foreign.setdefault(table, set()).add(obj)
	    elif key[-3:] == "Ids":
		# we dont back-reference these #
		del row[key]
		newkey = key[:-3]
		row[newkey] = links = [] # must allow for duplicates
		for subval in val.split():
		    foreign = db[newkey][int(subval)]
		    links.append(foreign)
		    if not foreign: 
			raise "warning foreign key:", newkey

read_csv("Conference")
read_csv("Journal")
read_csv("Author")
read_csv("Paper",missing=record)
read_csv("PaperAuthor",missing=record)

db['DeletedPaper'] = db['Paper']
db['ConfirmedPaper'] = db['Paper']
read_csv("Train", True)
read_csv("Valid", True)

#############################################################
# make the data-format nicer to use
#############################################################

print "creating quick access"

def enable(fn):
    'use this as a decorator (see below)'
    print fn.__doc__
    fn()
    return fn

for key in db:
    # convert the train/test set for author-based lookup
    if key in ("Train","Valid"): 
	db[key] = { rec.Author: rec for rec in db[key] }
	continue

    # now that quick direct access is less of an issue, convert list into a dict
    table = db[key] = dict(filter(lambda x: x[1] is not None,  enumerate(db[key])))

for author in db['Author'].values():
    if author.Train:
	author.Train = author.Train.pop()
	author.ConfirmedPaper = set(author.Train.ConfirmedPaper)
	author.DeletedPaper = set(author.Train.DeletedPaper)
    if author.Valid:
	author.Valid = author.Valid.pop()
	author.CandidatePaper = set(author.Valid.Paper)

def hardwire(table, relation, foreign):
    tmp = { link[foreign] for link in table.get(relation,[]) if foreign in link }
    tmp -= {None}
    return tmp

def hardwire_union(table, relation, foreign):
    tmp = { item for link in table.get(relation,[]) for item in link.get(foreign,[]) if item }
    tmp -= {None}
    return tmp

@enable
def annotate_papers():
    'joining Paper->Author'
    for paper in db['Paper'].itervalues():
	# hop-0
	paper.Author = hardwire(paper, 'PaperAuthor', 'Author')
	# hop-1; expensive!
	#paper.CoPaper = hardwire_union(paper, 'Author', 'Paper')
	# hop-1; but REALLY expensive!
	#paper.LikePaper = hardwire_union(paper, 'xxx', 'Paper')

# we may not have to scan /all/ authors, just the ones in the trainset.
@enable
def annotate_authors(restrict=False, excluded_papers=lambda x: set()):
    'joining Author->Paper->{CoAuthor,Journal,Conference}'
    if restrict:
	selection = db['Train'].keys()+db['Valid'].keys()
    else:
	selection = db['Author'].itervalues()
    for author in selection:
	# hop-0 
	author.Paper = hardwire(author, 'PaperAuthor', 'Paper') - excluded_papers(author)
	# hop-1
	author.CoAuthor = hardwire_union(author, 'Paper', 'Author')
	author.Journal  = hardwire(author, 'Paper', 'Journal')
	author.Conference = hardwire(author, 'Paper', 'Conference')

@enable
def annotate_journals():
    'joining {Journal,Conference}->Author'
    for pub in db['Journal'].itervalues():
	pub.Author = hardwire_union(pub, 'Paper', 'Author')
    for pub in db['Conference'].itervalues():
	pub.Author = hardwire_union(pub, 'Paper', 'Author')

@enable
def make_word_cloud(restrict=False, excluded_papers=lambda x: x.ConfirmedPaper|x.DeletedPaper|x.CandidatePaper, normalize=str.lower):
    'creating word counts'
    if restrict:
	selection = db['Train'].keys()+db['Valid'].keys()
    else:
	selection = db['Author'].itervalues()

    F = db['Voc'] = {}
    for pub in db['Journal'].values()+db['Conference'].values():
	if pub.FullName:
	    pub.Voc = set(normalize(pub.FullName or "").split())
	for w in pub.Voc: F[w] = F.get(w,0)+1
    for paper in db['Paper'].itervalues():
	if paper.Title:
	    paper.Voc = set(normalize(paper.Title or "").split())
	for w in paper.Voc: F[w] = F.get(w,0)+1

    for author in selection:
	admissable = author.Paper - excluded_papers(author)
	author.Voc = { w for paper in admissable for w in paper.Voc }
	author.PrefVoc = {}
	for paper in admissable:
	    for w in paper.Voc:
		author.PrefVoc[w] = author.PrefVoc.get(w,0)+1

# dump everything in the module scope; dirty but works!
globals().update(db)
print "done"

#############################################################
# neighbour definitions
#############################################################

def relate(*options, **kwarg):
    def nb(rec):
	for table in options:
	    if table in rec: return rec[table]
	#return set()
	try:
	    return kwarg['default']
	except KeyError:
	    raise Exception("dead-end encountered!", rec)
    return nb

default_nb = relate('Paper', 'Author')

# compute multiple joins -- better to precompute this!!
def nb_nb(G1, G2):
    return lambda rec: set.union(*(G2(z) for z in G1(rec)))

def collapse(table1, table2=None):
    R = relate(table1, table2)
    return nb_nb(R,R)

#############################################################
# averaging utilities
#############################################################

def average(nums):
    return float(sum(nums))/len(nums)

def median(nums):
    return sorted(nums)[len(nums)/2]

def geometric(nums):
    return math.pow(reduce(lambda x,y: x*y, nums, 1.0), 1.0/len(nums))

def harmonic(nums):
    return len(nums)/sum(map(lambda x:1.0/x, nums))

#############################################################
# aggregating functions
#############################################################

def combined(metric, a, bs, G=default_nb, H=None, aggregate=average):
    if H:
	return aggregate([ metric(a,b,G,H) for b in bs ])
    else:
	return aggregate([ metric(a,b,G) for b in bs ])

def combined2(metric, xs, bs, G=default_nb, aggregate=average):
    return aggregate([ metric(a,b,G) for a in xs for b in bs ])

def lifted(metric, a, bs, G=default_nb, H=None):
    big_b = set.union(*[G(b) for b in bs])
    def Gmod(obj):
	return G(obj) if obj is not big_b else big_b
    if H:
	return metric(a, big_b, Gmod, H)
    else:
	return metric(a, big_b, Gmod)

def lifted2(metric, xs, bs, G=default_nb):
    big_a = set.union(*[G(a) for a in xs])
    big_b = set.union(*[G(b) for b in bs])
    def Gmod(obj):
	if obj is not big_a and obj is not big_b:
	    return G(obj)
	else:
	    return obj
    return metric(big_a, big_b, Gmod)

#############################################################
# metrics defined using a neighbor function
#############################################################

def common_neighbours(a, b, G=default_nb):
    return len(G(a) & G(b))

def jaccard(a, b, G=default_nb):
    return len(G(a) & G(b)) / float(len(G(a) | G(b)))

# approximates jaccard if little overlap or large neighboursets
def pseudojaccard(a, b, G=default_nb):
    return len(G(a) & G(b)) / float(len(G(a)) + len(G(b)))

def adamic_adar(a, b, G=default_nb, H=None):
    try:
	return sum([1.0/math.log(len((H or G)(z))) for z in G(a) & G(b)])
    except ZeroDivisionError:
	return float("inf")

def preferential(a, b, G=default_nb):
    return len(G(a))*len(G(b))

# this is slow; obviously
def path_hit(a, bs, G=default_nb, max=6):
    if type(bs) is not set: bs = {bs}
    D = 0
    open   = [(a,D)]
    closed = {a}
    while open and D <= max:
	node, D = open.pop(0)
        if node in bs: return D
	new = G(node) - closed
        closed |= new
        open.extend([(x,D+1) for x in new])
    return max+1

# a small hack to fake neighbour-sets
class lenint (int):
    def __len__(self): return self

# a simple function which generalizes the "[]" on dictionaries
def select(dct, vals, op=None):
    if type(vals) is dict:
	return { x: op(dct[x],vals[x]) for x in vals if x in dct }
    elif type(vals) is set:
	return { x: dct[x] for x in vals if x in dct }
    elif type(vals) is list:
	return [ dct[x] for x in vals ]
    else:
    	return dct[vals]

#############################################################
# not sure if python has this -- run multiple functions
# on the same arguments
#############################################################

def multi(fs, *args, **kwargs):
    return [f(*args, **kwargs) for f in fs]

def holistic(metric, a, b, Gs):
    return [metric(a,b,G) for G in Gs]

#############################################################
# create ranking using a rank/score function
#############################################################

def map_rank(ranking):
    'ranking: function of author, paper -> ranking of paper'
    prec = 0
    N = 0
    for author, challenge in Train.iteritems():
	confirmed = set(challenge.ConfirmedPaper)
	deleted   = set(challenge.DeletedPaper)
	maybe     = list(confirmed | deleted)
	random.shuffle(maybe)
	prec += avg_prec(lambda p: p in confirmed, ranking(author, maybe))
	N += 1
    return prec/float(N)

def map_score(score):
    'score: function of author, paper -> value'
    def score_to_rank(author,papers):
	return sorted(papers, key=lambda paper: score(author, paper), reverse=True)
    return map_rank(score_to_rank)

#############################################################
# get input for a normal clsssifier
#############################################################

def train_data(shuffle=True, selection=None):
    '''returns zip(author_set, paper_set), label_set '''
    A = []
    for author, challenge in (selection or Train.iteritems()):
	confirmed = [((author,p),True)  for p in challenge.ConfirmedPaper]
	deleted   = [((author,p),False) for p in challenge.DeletedPaper]
	entries = confirmed+deleted
	if shuffle: random.shuffle(entries)
	A.extend(entries)
    return zip(*A)

def xvalidation_data(split=0.2, shuffle=True):
    '''returns trainset, trainlabels, validset, validlabels'''
    authors = Train.keys()
    random.shuffle(authors)
    N = int(len(authors)*split)
    train, trainlabel = train_data(shuffle, selection=authors[N:])
    test , testlabel  = train_data(shuffle, selection=authors[:N])
    return train, trainlabel, test, testlabel

def test_data(shuffle=True):
    '''similar to train_data
    returns zip(authorset, paperset) or
    returns zip(authorset, paperset), proccessed  if argument is given
    '''
    A = [(row.Author, p) for row in Valid.itervalues() for p in row.Paper]
    if shuffle: random.shuffle(A)
    return A

def extract_features(method, rawset, n_jobs=None):
    '''apply the method (a function or list of functions) for every item'''
    if callable(method):
	extract = lambda item: (method(*item),)
    else:
	extract = lambda item: multi(method, *item)
    if not n_jobs:
	return [extract(item) for item in rawset]
    else:
	return multomap(extract, rawset, j=n_jobs)

