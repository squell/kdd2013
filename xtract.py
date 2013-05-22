#! /usr/bin/python -O -i

'''
 a demo on using kddload to get features
'''

from kddload import *          # this will take awhile
import cPickle as pickle
import sys

if len(sys.argv) <= 1:
    print "must supply a pickle name"
    sys.exit()

from scrabble import Scrabble

feature_set = features(
	  lambda a,p: len(p.Journal.Paper & a.Paper) if p.Journal else 0
	, lambda a,p: len(p.Conference.Paper & a.Paper) if p.Conference else 0
	, lambda a,p: len(p.Conference.Paper & a.Paper) if p.Conference else 0

	, lambda a,p: len(a.Paper)
	, lambda a,p: len(p.Author)
	, lambda a,p: int(p.Year)

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Journal','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Journal','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard, a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Conference','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Conference','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(jaccard, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}, relate('Author','Journal')) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}, relate('Author','Conference')) if len(a.Paper) > 1 else 0

	, lambda a,p: len(a.Voc & p.Voc)
	, lambda a,p: sum(select(a.PrefVoc, p.Voc).values())

	, lambda a,p: average([Scrabble(w) for w in p.Voc]) if p.Voc else 0
	)


raw_train, labels = train_data(shuffle=False)
raw_test = test_data(shuffle=False)

print "featurizing trainset..."
train = [(a.Id, p.Id) for a,p in raw_train], feature_set(raw_train), labels
print "featurizing testset..."
test  = [(a.Id, p.Id) for a,p in raw_test],  feature_set(raw_test)

print "pickling..."
with open(sys.argv[1], 'wb') as outfile:
    pickle.dump((train,test), outfile)


