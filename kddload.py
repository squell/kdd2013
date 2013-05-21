import sys
import csv
import math
import random

class record (object):
    ''' a simple "coat hanger"

    using a regular dictionary is annoying
    - you dont want to see its representation all the time
    - not hashable 
    - it is nicer to type x.blaabla.werewr than x['blabla']['werewr'] 
    '''
    def __init__(self, d={}):
	self.__dict__ = d
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

db = dict()

limit = int(sys.argv[1]) if len(sys.argv) > 1 else -1

def read_csv(table, force_creation=False, missing=None):
    global limit
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
	if limit == 0: break
	limit -= 1
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
		    identify(db[newkey], int(val), foreign)
		if foreign:
		    foreign.setdefault(table, set()).add(obj)
	    elif key[-3:] == "Ids":
		# we dont back-reference these #
		del row[key]
		newkey = key[:-3]
		row[newkey] = links = set()
		for subval in val.split():
		    foreign = db[newkey][int(subval)]
		    links.add(foreign)
		    if not foreign: 
			raise "warning foreign key:", newkey

read_csv("Conference")
read_csv("Journal")
read_csv("Author")
read_csv("Paper")
read_csv("PaperAuthor")

db['DeletedPaper'] = db['Paper']
db['ConfirmedPaper'] = db['Paper']
read_csv("Train", True)
read_csv("Valid", True)

print "creating quick access"

def enable(fn):
    'use this as a decorator (see below)'
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
	author.ConfirmedPaper = author.Train.ConfirmedPaper
	author.DeletedPaper = author.Train.DeletedPaper
    if author.Valid:
	author.Valid = author.Valid.pop()
	author.CandidatePaper = author.Valid.Paper

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
    for paper in db['Paper'].values():
	# hop-0
	paper.Author = hardwire(paper, 'PaperAuthor', 'Author')
	paper.Publish = {paper.Journal, paper.Conference} - {None}
	# hop-1; expensive!
	#paper.CoPaper = hardwire_union(paper, 'Author', 'Paper')
	# hop-1; but REALLY expensive!
	#paper.LikePaper = hardwire_union(paper, 'Publish', 'Paper')

@enable
def annotate_authors(excluded_papers=lambda x: set()):
    for author in db['Author'].values():
	# hop-0 
	author.Paper = hardwire(author, 'PaperAuthor', 'Paper') - excluded_papers(author)
	# hop-1
	author.CoAuthor = hardwire_union(author, 'Paper', 'Author')
	author.Journal  = hardwire(author, 'Paper', 'Journal')
	author.Conference = hardwire(author, 'Paper', 'Conference')
	author.Publish = hardwire_union(author, 'Paper', 'Publish')

print "creating word counts"

@enable
def make_word_cloud(excluded_papers=lambda x: x.ConfirmedPaper|x.DeletedPaper|x.CandidatePaper, normalize=str.lower):
    F = db['Voc'] = {}
    for paper in db['Paper'].values():
    	paper.Voc = set(map(normalize, paper.Title.split()))
	for w in paper.Voc: F[w] = F.get(w,0)+1
    for author in db['Author'].values():
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

def relate(table1, table2=None):
    return lambda rec: rec[table1] if table1 in rec else rec[table2]

# similar to the above, but multiple args 
def relates(*options):
    def nb(rec):
	for table in options:
	    if table in rec: return rec[table]
	raise Exception("dead-end encountered!", rec)
    return nb

default_nb = relate('Paper', 'Author')

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

def geometric(nums):
    return math.pow(reduce(lambda x,y: x*y, nums, 1.0), 1.0/len(nums))

def harmonic(nums):
    return len(nums)/sum(map(lambda x:1.0/x, nums))

#############################################################
# aggregating functions
#############################################################

def combined(metric, a, bs, G=default_nb, aggregate=average):
    return aggregate([ metric(a,b,G) for b in bs ])

def combined2(metric, xs, bs, G=default_nb, aggregate=average):
    return aggregate([ metric(a,b,G) for a in xs for b in bs ])

def lifted(metric, a, bs, G=default_nb):
    big_b = set.union(*[G(b) for b in bs])
    def Gmod(obj):
	return G(obj) if obj is not big_b else big_b
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

def adamic_adar(a, b, G=default_nb):
    try:
	return sum([1.0/math.log(len(G(z))) for z in G(a) & G(b)])
    except ZeroDivisionError:
	return float("inf")

def preferential(a, b, G=default_nb):
    return len(G(a))*len(G(b))

# this is slow; obviously
def path_len(a, b, G=default_nb):
    open   = [(a,0)]
    closed = set()
    for node, D in open:
	if node is b: return D
	closed.add(node)
	open.extend([(x,D+1) for x in G(node) - closed])
    return float("inf")

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
# create ranking using a rank/score function
#############################################################

def map_rank(ranking):
    'ranking: function of author, paper -> ranking of paper'
    prec = 0
    N = 0
    for author, challenge in Train.iteritems():
	confirmed = challenge.ConfirmedPaper
	deleted   = challenge.DeletedPaper
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

def features(*list_of_functions):
    '''Some syntactic sugar'''
    return lambda x: extract_features(list_of_functions, x)

def train_data(shuffle=True):
    '''returns zip(author_set, paper_set), label_set
    where train_set is a list of of (author, paper) tuples if no argument given.

    return zip(authorset, paper_set), processed, labelset
    if an argument is given, where trainset is obtained by applying argument
    '''
    A = []
    for author, challenge in Train.iteritems():
	confirmed = challenge.ConfirmedPaper
	deleted   = challenge.DeletedPaper
	A.extend([((author,paper),True)  for paper in confirmed])
	A.extend([((author,paper),False) for paper in deleted])
    if shuffle: random.shuffle(A)
    return zip(*A)

def test_data(shuffle=True):
    '''similar to train_data
    returns zip(authorset, paperset) or
    returns zip(authorset, paperset), proccessed  if argument is given
    '''
    A = [(row.Author, p) for row in Valid.itervalues() for p in row.Paper]
    if shuffle: random.shuffle(A)
    return A

def extract_features(method, rawset):
    '''you could implement this yourself'''
    if callable(method):
	return [(method(*item),) for item in rawset]
    else:
	return [multi(method, *item) for item in rawset]

def group_by_author(train_set, labels, predictions):
    '''groups the results by author; use answers or papers as labels
    input:
	list of tuples (having as first item an author/authorid)
	list of labels
	list of predicted values
    returns: dictionary of author/authorid -> list of (label,score)
    '''
    xlat = {}
    # re-combine results for each author
    for train, label, score in zip(train_set, labels, predictions):
	xlat.setdefault(train[0], []).append((label,score))
    return xlat

def MAP(train_set, labels, predictions):
    '''calculates MAP for use with a sklearn-classifier
    first argument: raw-train data or a list of tuples of authorid,paperid
    second: list of correct labels
    third: predictions
    '''
    xlat = group_by_author(train_set, labels, predictions)
    prec = 0
    N = 0
    for _, scores in xlat.iteritems():
	rank = sorted(scores, key=lambda x:x[0], reverse=True)
	prec += avg_prec(lambda x:x[1], rank)
	N += 1
    return prec/float(N)

def write_csv(train_set, predictions):
    def getId(obj):
	return obj.Id if type(obj) is record else obj

    authorIds = [(getId(a), ) for a,p in train_set]
    paperIds  = [getId(p) for a,p in train_set]
    table = group_by_author(authorIds, paperIds, predictions)

    csv = open("output.csv", "w")
    print >> csv, "AuthorId, PaperIds"
    for authorId, ranking in table.iteritems():
	ranking = sorted(ranking, key=lambda x:x[1], reverse=True)
	print >> csv, "%d," % authorId,
	for paperId, _ in ranking:
	    print >> csv, paperId,
	print >> csv
    
