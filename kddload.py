import sys
import csv

class record (object):
    def __init__(self, d={}):
	self.__dict__ = d
    def setdefault(self, name, val):
	return self.__dict__.setdefault(name, val)
    def keys(self):
	return self.__dict__.keys()
    def __getitem__(self, name):
	return self.__dict__[name]
    def __contains__(self, name):
    	return name in self.__dict__
    def __getattr__(self, name):
	return self.setdefault(name, set())

db = dict()

def read_csv(table):
    print "reading", table
    dataset = [None]
    db[table] = dataset

    for row in csv.DictReader(open(table+".csv", 'rb')):
	obj = record(row)

	# add identifiable items
	if 'Id' in row:
	    idx = int(row['Id'])
	    #grow dataset if necessary
	    while idx >= len(dataset):
		dataset.extend([None]*len(dataset))
	    dataset[idx] = obj
	    del row['Id']

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
read_csv("Paper")
read_csv("PaperAuthor")

db['DeletedPaper'] = db['Paper']
db['ConfirmedPaper'] = db['Paper']
read_csv("Train")
read_csv("Valid")

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

for key, table in db:
    if key == "Author":
	for node in compact:
	    node.Papers = author_to_paper(node)
	    if 'Valid' in node:
		unconfirmed[node] = {link.Paper for link in node.Valid.Paper}
	    if 'Train' in node:
		confirmed[node] = {link.Paper for link in node.Train.ConfirmedPaper}
		rejected [node] = {link.Paper for link in node.Train.RejectedPaper}
    elif key == "Paper":
	for node in compact:
	    node.Authors = paper_to_author(node)

def validate(author, paper):
    if paper in confirmed[node]: return True
    if paper in rejected[node]:  return False
    raise Exception("paper not in trainset")

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

