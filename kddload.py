import sys
import csv

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
	return self.setdefault(name, set())

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
	    idx = int(row['Id'])
	    #grow dataset if necessary
	    while idx >= len(dataset):
		dataset.extend([None]*(idx+1-len(dataset)))
	    dataset[idx] = obj
	    del row['Id']
	elif force_creation:
	    dataset.append(obj)

	# convert references in row into pythonesque
	for key, val in row.items():
	    if key[-2:] == "Id":
		newkey = key[:-2]
		row[newkey] = foreign = db[newkey][int(val)]
		if not foreign: 
		    #print "invalid/empty foreign key:", newkey
		    pass
		else:
		    foreign.setdefault(table, set()).add(obj)
		del row[key]
	    elif key[-3:] == "Ids":
		# we dont back-reference these #
		newkey = key[:-3]
		row[newkey] = links = list()
		for subval in val.split():
		    foreign = db[newkey][int(subval)]
		    links.append(foreign)
		    if not foreign: 
			raise "warning foreign key:", newkey
		del row[key]

read_csv("Conference")
read_csv("Journal")
read_csv("Author")
limit = 100000
read_csv("Paper")
limit = 10000
read_csv("PaperAuthor")

db['DeletedPaper'] = db['Paper']
db['ConfirmedPaper'] = db['Paper']
read_csv("Train", True)
read_csv("Valid", True)

def author_to_paper(author):
    return { link.Paper for link in author.PaperAuthor }

def paper_to_author(paper):
    return { link.Author for link in paper.PaperAuthor }

def nbs(node):
    return { link.Paper if link.Paper is not node else link.Author for link in node.PaperAuthor }

print "creating quick access"

test = dict()
confirmed = dict()
rejected = dict()

for key in db:
    # leave these as-is
    if key in ("Train","Valid"): 
	continue

    # now that quick direct access is less of an issue, convert list into a dict
    table = db[key] = dict(filter(lambda x: x[1] is not None,  enumerate(db[key])))
    if key == "Author":
	for author in table.values():
	    author.Paper = author_to_paper(author)
	    if 'Valid' in author:
		unconfirmed[author] = {link.Paper for link in author.Valid.Paper}
	    if 'Train' in author:
		confirmed[author] = {link.Paper for link in author.Train.ConfirmedPaper}
		rejected [author] = {link.Paper for link in author.Train.RejectedPaper}
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

def common_neighbours(a, b, G):
    return len(G(a) & G(b))

def jaccard(a, b, G):
    return len(G(a) & G(b)) / float(len(G(a) | G(b)))

from math import log
def adamic_adar(a, b, G):
    return sum((1.0/log(len(G(z))) for z in G(a) & G(b)))

# this doesnt work...
#print "pickling"
#import cPickle as pickle
#with open("fridge", 'wb') as outf:
#    pickle.Pickler(outf, -1).dump(db)

