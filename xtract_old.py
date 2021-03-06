'''
   using kddload to extract features from the dataset; outputs a pickle file

   containing:
     (train, test)

   where train = (ids, features, labels)
         test = (ids, features)
          where ids = [(authorId, paperId), ...]
                features = list of 'feature vectors'
                labels = list of True/False
       
'''

from kddload import *          # this will take awhile
import cPickle as pickle
import sys

if len(sys.argv) <= 1:
    print "must supply a pickle name"
    sys.exit()

from scrabble import *

feature_set2 = [
	  lambda a,p: len(p.Journal.Paper & a.Paper) if p.Journal else 0
	, lambda a,p: len(p.Conference.Paper & a.Paper) if p.Conference else 0
	, lambda a,p: len(p.Journal.Author & a.CoAuthor) if p.Journal else 0
	, lambda a,p: len(p.Conference.Author & a.CoAuthor) if p.Conference else 0

	, lambda a,p: len(a.Paper)
	, lambda a,p: len(p.Author)
	, lambda a,p: int(p.Year)

	, lambda a,p: common_neighbours(a,p, relate('CoAuthor','Author'))
	, lambda a,p: jaccard(a,p, relate('CoAuthor','Author'))
	, lambda a,p: preferential(a,p, relate('CoAuthor','Author'))
	, lambda a,p: adamic_adar(a,p, relate('CoAuthor','Author'))

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,     a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,     a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,     a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Journal','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Journal','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,     a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Conference','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar, a, p.Author-{a}, relate('Conference','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(jaccard,     p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(preferential,p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}, relate('Author','Journal')) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar, p, a.Paper-{p}, relate('Author','Conference')) if len(a.Paper) > 1 else 0

	, lambda a,p: len(a.Voc & p.Voc)

	, lambda a,p: jaccard(a,p,lambda x: x.Voc if 'Voc' in x else {'of'})
	, lambda a,p: preferential(a,p,lambda x: x.Voc if 'Voc' in x else {'of'})
	, lambda a,p: adamic_adar(a,p,lambda x: lenint(Voc[x]) if type(x) is str else x.Voc if 'Voc' in x else {'of'})
	, lambda a,p: sum(select(a.PrefVoc, p.Voc).values())

	, lambda a,p: average([Scrabble(w) for w in p.Voc]) if p.Voc else 0

	, lambda a,p: max([ed(lnk.Name, a.Name) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: max([ed_name(lnk.Name, a.Name) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	]

feature_set2e = [
	  lambda a,p: max([ed_name(lnk.Affiliation, a.Affiliation) for lnk in (a.PaperAuthor & p.PaperAuthor)])

	, lambda a,p: common_neighbours(a,p.Journal,relate('Voc',default={'of'}))
	, lambda a,p: jaccard(a,p.Journal,relate('Voc',default={'of'}))
	, lambda a,p: preferential(a,p.Journal,relate('Voc',default={'of'}))
	, lambda a,p: adamic_adar(a,p.Journal,lambda x: lenint(Voc[x]) if type(x) is str else x.Voc if 'Voc' in x else {'of'})

	, lambda a,p: common_neighbours(a,p.Conference,relate('Voc',default={'of'}))
	, lambda a,p: jaccard(a,p.Conference,relate('Voc',default={'of'}))
	, lambda a,p: preferential(a,p.Conference,relate('Voc',default={'of'}))
	, lambda a,p: adamic_adar(a,p.Conference,lambda x: lenint(Voc[x]) if type(x) is str else x.Voc if 'Voc' in x else {'of'})

	, lambda a,p: lifted(common_neighbours, p.Journal,a.Paper,relate('Voc',default={'of'}))
	, lambda a,p: lifted(jaccard,     p.Journal,a.Paper,relate('Voc',default={'of'}))
	, lambda a,p: lifted(preferential,p.Journal,a.Paper,relate('Voc',default={'of'}))
	, lambda a,p: lifted(adamic_adar, p.Journal,a.Paper,lambda x: lenint(Voc[x]) if type(x) is str else x.Voc if 'Voc' in x else {'of'})

	, lambda a,p: lifted(common_neighbours, p.Conference,a.Paper,relate('Voc',default={'of'}))
	, lambda a,p: lifted(jaccard,     p.Conference,a.Paper,relate('Voc',default={'of'}))
	, lambda a,p: lifted(preferential,p.Conference,a.Paper,relate('Voc',default={'of'}))
	, lambda a,p: lifted(adamic_adar, p.Conference,a.Paper,lambda x: lenint(Voc[x]) if type(x) is str else x.Voc if 'Voc' in x else {'of'})
	]

feature_set2g = [
	  lambda a,p: len(a.PaperAuthor & p.PaperAuthor)
	, lambda a,p: len(a.Voc ^ p.Voc)
	, lambda a,p: lifted(adamic_adar, p,a.Paper,lambda x: lenint(Voc[x]) if type(x) is str else x.Voc if 'Voc' in x else {'of'})
	, lambda a,p: sum(map(len, a.Voc & p.Voc))
	, lambda a,p: min([ len(l.Name)  for l in a.PaperAuthor&p.PaperAuthor])
	, lambda a,p: max([ len(l.Name)  for l in a.PaperAuthor&p.PaperAuthor])
	, lambda a,p: min([ len(l.Affiliation)  for l in a.PaperAuthor&p.PaperAuthor])
	, lambda a,p: max([ len(l.Affiliation)  for l in a.PaperAuthor&p.PaperAuthor])
	]

feature_set = [lambda a,p: 42]

raw_train, labels = train_data()
raw_test = test_data()

print "featurizing trainset..."
train = [(a.Id, p.Id) for a,p in raw_train], extract_features(feature_set,raw_train), labels
print "featurizing testset..."
test  = [(a.Id, p.Id) for a,p in raw_test],  extract_features(feature_set,raw_test)

print "pickling..."
with open(sys.argv[1], 'wb') as outfile:
    pickle.dump((train,test), outfile)

