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

def read_csv(table, force_creation=False):
    global limit
    print "reading", table
    dataset = []
    db[table] = dataset

    for row in csv.DictReader(open(table+".csv", 'rb')):
	if limit == 0: break
	limit -= 1
	obj = record(row)

	# add identifiable items
	if 'Id' in row:
	    row['Id'] = idx = int(row['Id'])
	    #grow dataset if necessary
	    while idx >= len(dataset):
		dataset.extend([None]*(idx+1-len(dataset)))
	    dataset[idx] = obj
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
		    pass
		else:
		    foreign.setdefault(table, set()).add(obj)
	    elif key[-3:] == "Ids":
		# we dont back-reference these #
		del row[key]
		newkey = key[:-3]
		row[newkey] = links = list()
		for subval in val.split():
		    foreign = db[newkey][int(subval)]
		    links.append(foreign)
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

def author_to_paper(author):
    return { link.Paper for link in author.PaperAuthor if link.Paper }

def paper_to_author(paper):
    return { link.Author for link in paper.PaperAuthor if link.Author }

print "creating quick access"

for key in db:
    # convert the train/test set for author-based lookup
    if key in ("Train","Valid"): 
	db[key] = { rec.Author: rec for rec in db[key] }
	continue

    # now that quick direct access is less of an issue, convert list into a dict
    table = db[key] = dict(filter(lambda x: x[1] is not None,  enumerate(db[key])))
    if key == "Author":
	for author in table.values():
	    # precompute several links
	    author.Paper = author_to_paper(author)
	    author.CoAuthor = set.union(set(),*[p.Author for p in author.Paper]) - {None,author}
	    author.Publish  = set.union(set(),*[{p.Journal,p.Conference} for p in author.Paper]) - {None}
	#    if 'Valid' in author:
	#	unconfirmed[author] = {link.Paper for link in author.Valid.Paper}
	#    if 'Train' in author:
	#	confirmed[author] = {link.Paper for link in author.Train.ConfirmedPaper}
	#	rejected [author] = {link.Paper for link in author.Train.RejectedPaper}
    elif key == "Paper":
	for paper in table.values():
	    paper.Author = paper_to_author(paper)
	    paper.CoPaper = set.union(set(),*[a.Paper for a in paper.Author]) - {None,paper}
	    paper.Publish = {p.Journal, p.Conference} - {None}
	    paper.LikePaper = set.union(set(),*[j.Paper for j in paper.Publish]) - {None,paper}

#def validate(author, paper):
#    if paper in confirmed[author]: return True
#    if paper in rejected [author]: return False
#    raise Exception("paper not in trainset")

# dump everything in the module scope; dirty but works!
globals().update(db)
print "done"

#############################################################
# neighbour definitions
#############################################################

def relate(table1, table2=None):
    return lambda rec: rec[table1] if table1 in rec else rec[table2]

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

def lifted(metric, a, bs, G=default_nb):
    big_b = set.union(*[G(b) for b in bs])
    def Gmod(obj):
	return G(obj) if obj is not big_b else big_b
    return metric(a, big_b, Gmod)

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

def path_len(a, b, G=default_nb):
    open   = [(a,0)]
    closed = set()
    for node, D in open:
	if node is b: return D
	closed.add(node)
	open.extend([(x,D+1) for x in G(node) - closed])
    return float("inf")

#############################################################
# average precision
#############################################################

def ap_rank(actual, ranked):
    if not actual: return 1.0
    acc = 0
    TP = 0
    for P, paper in enumerate(ranked,1):
	if paper in actual:
	    TP  += 1
	    acc += TP/float(P)
    return acc / TP

#############################################################
# using a simple score
#############################################################

def map_rank(ranking):
    prec = 0
    N = 0
    for author, challenge in Train.iteritems():
	confirmed = challenge.ConfirmedPaper
	deleted   = challenge.DeletedPaper
	maybe     = confirmed + deleted
	random.shuffle(maybe)
	prec += ap_score(confirmed, ranking(author, maybe))
	N += 1
    return prec/float(N)

def map_score(score):
    def score_to_rank(author,papers):
	return sorted(papers, key=lambda paper: score(author, paper), reverse=True)
    return map_rank(score_to_rank)

#############################################################
# get input for a normal clsssifier
#############################################################

def train_data():
    '''returns (unpreprocessed) train_set, label_set'''
    A = []
    for author, challenge in Train.iteritems():
	confirmed = challenge.ConfirmedPaper
	deleted   = challenge.DeletedPaper
	A.extend([((author, paper),True)  for paper in confirmed])
	A.extend([((author, paper),False) for paper in deleted])
    random.shuffle(A)
    return zip(*A)

def test_data():
    '''returns (unpreprocessed) test_set'''
    return [(author, paper) for author,x in Valid.iteritems() for paper in x]

