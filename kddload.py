import sys
import csv
from math import log, pow

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

limit = -1

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

limit=100000
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

# in case the neighbour function has to operate on two different types of node
def relate(table1, table2=None):
    return lambda rec: rec[table1] if table1 in rec else rec[table2]

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
	    author.Paper = author_to_paper(author)
	#    if 'Valid' in author:
	#	unconfirmed[author] = {link.Paper for link in author.Valid.Paper}
	#    if 'Train' in author:
	#	confirmed[author] = {link.Paper for link in author.Train.ConfirmedPaper}
	#	rejected [author] = {link.Paper for link in author.Train.RejectedPaper}
    elif key == "Paper":
	for paper in table.values():
	    paper.Author = paper_to_author(paper)

def validate(author, paper):
    if paper in confirmed[author]: return True
    if paper in rejected [author]: return False
    raise Exception("paper not in trainset")

# dump everything in the module scope; dirty but works!
globals().update(db)
print "done"

#############################################################
# averaging utilities
#############################################################

default_nb = relate('Paper', 'Author')

def average(nums):
    return float(sum(x))/len(x)

def geometric(nums):
    return pow(reduce(lambda x,y: x*y, nums, 1.0), 1.0/len(nums))

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
	return sum([1.0/log(len(G(z))) for z in G(a) & G(b)])
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

# this doesnt work...
#print "pickling"
#import cPickle as pickle
#with open("fridge", 'wb') as outf:
#    pickle.Pickler(outf, -1).dump(db)

