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

import cPickle as pickle
import sys

if len(sys.argv) <= 1:
    print "must supply a pickle name"
    sys.exit()

from scrabble import *
from kddload import *          # this will take awhile

paper_features = [
	  lambda a,p: int(p.Year)
	, lambda a,p: len(p.Author)
	# new:
	, lambda a,p: len(p.CoAuthor)
	, lambda a,p: len(p.Voc)
	, lambda a,p: len(p.Journal.Paper) if p.Journal else 0
	, lambda a,p: len(p.Journal.Author) if p.Journal else 0
	, lambda a,p: len(p.Journal.Voc) if p.Journal else 0
	, lambda a,p: len(p.Conference.Paper) if p.Conference else 0
	, lambda a,p: len(p.Conference.Author) if p.Conference else 0
	, lambda a,p: len(p.Conference.Voc) if p.Conference else 0
]

direct_features = [
	  lambda a,p: common_neighbours(a,p, relate('CoAuthor','Author'))
	, lambda a,p: jaccard          (a,p, relate('CoAuthor','Author'))
	, lambda a,p: preferential     (a,p, relate('CoAuthor','Author'))
	, lambda a,p: adamic_adar      (a,p, relate('CoAuthor','Author'))

	, lambda a,p: common_neighbours(a,p, relate('Voc',default={'of'})) # len(a.Voc & p.Voc)
	, lambda a,p: jaccard          (a,p, relate('Voc',default={'of'}))
	, lambda a,p: preferential     (a,p, relate('Voc',default={'of'}))
	, lambda a,p: adamic_adar      (a,p, relate('Voc',default={'of'}), lambda x: lenint(Voc[x]))

	, lambda a,p: sum(map(len, a.Voc & p.Voc))
	, lambda a,p: len(a.Voc ^ p.Voc)
	, lambda a,p: sum(select(a.PrefVoc, p.Voc).values())

	, lambda a,p: average([Scrabble(w) for w in p.Voc]) if p.Voc else 0
]

indirect_features = [
	  lambda a,p: lifted(common_neighbours, a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,           a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,      a, p.Author-{a}) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       a, p.Author-{a}) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,           a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,      a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       a, p.Author-{a}, relate('CoAuthor')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,           a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,      a, p.Author-{a}, relate('Journal')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       a, p.Author-{a}, relate('Journal','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       a, p.Author-{a}, relate('Journal','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(jaccard,           a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(preferential,      a, p.Author-{a}, relate('Conference')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       a, p.Author-{a}, relate('Conference','Paper')) if len(p.Author) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       a, p.Author-{a}, relate('Conference','Author')) if len(p.Author) > 1 else 0

	, lambda a,p: lifted(common_neighbours, p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(jaccard,           p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(preferential,      p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       p, a.Paper-{p}) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       p, a.Paper-{p}, relate('Author','Journal')) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       p, a.Paper-{p}, relate('Author','Conference')) if len(a.Paper) > 1 else 0

	, lambda a,p: lifted(common_neighbours, p, a.Paper-{p}, relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0 #new
	, lambda a,p: lifted(jaccard,           p, a.Paper-{p}, relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0 #new
	, lambda a,p: lifted(preferential,      p, a.Paper-{p}, relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0 #new
	, lambda a,p: lifted(adamic_adar,       p, a.Paper-{p}, relate('Voc',default={'of'}), lambda x: lenint(Voc[x])) if len(a.Paper) > 1 else 0 #upd
]

linksemantic_features = [
	  lambda a,p: min([ len(l.Name)         for l in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: max([ len(l.Name)         for l in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: min([ len(l.Affiliation)  for l in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: max([ len(l.Affiliation)  for l in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: min([ned(lnk.Name, a.Name) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: max([ned(lnk.Name, a.Name) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: min([ned(lnk.Affiliation, a.Affiliation) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: max([ned(lnk.Affiliation, a.Affiliation) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: min([lcstr(lnk.Name, a.Name) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: max([lcstr(lnk.Name, a.Name) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: min([lcstr(lnk.Affiliation, a.Affiliation) for lnk in (a.PaperAuthor & p.PaperAuthor)])
	, lambda a,p: max([lcstr(lnk.Affiliation, a.Affiliation) for lnk in (a.PaperAuthor & p.PaperAuthor)])
]

link_features = [
	  lambda a,p: common_neighbours(a, p, relate('PaperAuthor')) # len(a.PaperAuthor & p.PaperAuthor)
	, lambda a,p: jaccard          (a, p, relate('PaperAuthor')) #new - 0.963!!!
	, lambda a,p: preferential     (a, p, relate('PaperAuthor')) #new
]

derived_direct_features = [
	  lambda a,p: common_neighbours(a,p.Journal, relate('Paper')) if p.Journal else 0
	, lambda a,p: pseudojaccard    (a,p.Journal, relate('Paper')) if p.Journal else 0#new
	, lambda a,p: preferential     (a,p.Journal, relate('Paper')) if p.Journal else 0#new
	, lambda a,p: adamic_adar      (a,p.Journal, relate('Paper','Author')) if p.Journal else 0#new

	, lambda a,p: common_neighbours(a,p.Conference, relate('Paper')) if p.Conference else 0
	, lambda a,p: pseudojaccard    (a,p.Conference, relate('Paper')) if p.Conference else 0#new
	, lambda a,p: preferential     (a,p.Conference, relate('Paper')) if p.Conference else 0#new
	, lambda a,p: adamic_adar      (a,p.Conference, relate('Paper','Author')) if p.Conference else 0#new

	, lambda a,p: common_neighbours(a,p.Journal, relate('CoAuthor','Author')) if p.Journal else 0
	, lambda a,p: pseudojaccard    (a,p.Journal, relate('CoAuthor','Author')) if p.Journal else 0 #new
	, lambda a,p: preferential     (a,p.Journal, relate('CoAuthor','Author')) if p.Journal else 0 #new
	, lambda a,p: adamic_adar      (a,p.Journal, relate('CoAuthor','Author')) if p.Journal else 0 #new
	, lambda a,p: adamic_adar      (a,p.Journal, relate('CoAuthor','Author'), relate('Paper')) if p.Journal else 0 #new 

	, lambda a,p: common_neighbours(a,p.Conference, relate('CoAuthor','Author')) if p.Conference else 0
	, lambda a,p: pseudojaccard    (a,p.Conference, relate('CoAuthor','Author')) if p.Conference else 0#new
	, lambda a,p: preferential     (a,p.Conference, relate('CoAuthor','Author')) if p.Conference else 0#new
	, lambda a,p: adamic_adar      (a,p.Conference, relate('CoAuthor','Author')) if p.Conference else 0#new
	, lambda a,p: adamic_adar      (a,p.Conference, relate('CoAuthor','Author'), relate('Paper')) if p.Conference else 0#new

	, lambda a,p: common_neighbours(a,p.Journal,relate('Voc',default={'of'})) 
	, lambda a,p: jaccard          (a,p.Journal,relate('Voc',default={'of'}))
	, lambda a,p: preferential     (a,p.Journal,relate('Voc',default={'of'}))
	, lambda a,p: adamic_adar      (a,p.Journal,relate('Voc',default={'of'}), lambda x: lenint(Voc[x]))

	, lambda a,p: common_neighbours(a,p.Conference,relate('Voc',default={'of'}))
	, lambda a,p: jaccard          (a,p.Conference,relate('Voc',default={'of'}))
	, lambda a,p: preferential     (a,p.Conference,relate('Voc',default={'of'}))
	, lambda a,p: adamic_adar      (a,p.Conference,relate('Voc',default={'of'}), lambda x: lenint(Voc[x]))

]
 
derived_indirect_features = [
	#all these are new
	  lambda a,p: lifted(common_neighbours, p.Journal, a.Paper-{p}, relate('Author')) if len(a.Paper) > 1 and p.Journal else 0
	, lambda a,p: lifted(pseudojaccard,     p.Journal, a.Paper-{p}, relate('Author')) if len(a.Paper) > 1 and p.Journal else 0
	, lambda a,p: lifted(preferential,      p.Journal, a.Paper-{p}, relate('Author')) if len(a.Paper) > 1 and p.Journal else 0
	, lambda a,p: lifted(adamic_adar,       p.Journal, a.Paper-{p}, relate('Author','Paper')) if len(a.Paper) > 1 and p.Journal else 0
	#, lambda a,p: lifted(adamic_adar,       p.Journal, a.Paper-{p}, relate('Author','Journal')) if len(a.Paper) > 1 and p.Journal else 0
	#, lambda a,p: lifted(adamic_adar,       p.Journal, a.Paper-{p}, relate('Author','Conference')) if len(a.Paper) > 1 and p.Journal else 0

	, lambda a,p: lifted(common_neighbours, p.Conference, a.Paper-{p}, relate('Author')) if len(a.Paper) > 1 and p.Conference else 0
	, lambda a,p: lifted(pseudojaccard,     p.Conference, a.Paper-{p}, relate('Author')) if len(a.Paper) > 1 and p.Conference else 0
	, lambda a,p: lifted(preferential,      p.Conference, a.Paper-{p}, relate('Author')) if len(a.Paper) > 1 and p.Conference else 0
	, lambda a,p: lifted(adamic_adar,       p.Conference, a.Paper-{p}, relate('Author','Paper')) if len(a.Paper) > 1 and p.Conference else 0
	#, lambda a,p: lifted(adamic_adar,       p.Conference, a.Paper-{p}, relate('Author','Journal')) if len(a.Paper) > 1 and p.Conference else 0
	#, lambda a,p: lifted(adamic_adar,       p.Conference, a.Paper-{p}, relate('Author','Conference')) if len(a.Paper) > 1 and p.Conference else 0

	#next are all upd
	, lambda a,p: lifted(common_neighbours, p.Journal,a.Paper-{p},relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(jaccard,           p.Journal,a.Paper-{p},relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(preferential,      p.Journal,a.Paper-{p},relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       p.Journal,a.Paper-{p},relate('Voc',default={'of'}), lambda x: lenint(Voc[x])) if len(a.Paper) > 1 else 0

	, lambda a,p: lifted(common_neighbours, p.Conference,a.Paper-{p},relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(jaccard,           p.Conference,a.Paper-{p},relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(preferential,      p.Conference,a.Paper-{p},relate('Voc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       p.Conference,a.Paper-{p},relate('Voc',default={'of'}), lambda x: lenint(Voc[x])) if len(a.Paper) > 1 else 0
]

# all new
more_derived_features = [
	  lambda a,p: lifted(common_neighbours, p.Journal, a.CoAuthor, relate('Paper')) if len(a.Paper) > 1 and p.Journal else 0
	, lambda a,p: lifted(pseudojaccard,     p.Journal, a.CoAuthor, relate('Paper')) if len(a.Paper) > 1 and p.Journal else 0
	, lambda a,p: lifted(preferential,      p.Journal, a.CoAuthor, relate('Paper')) if len(a.Paper) > 1 and p.Journal else 0
	, lambda a,p: lifted(adamic_adar,       p.Journal, a.CoAuthor, relate('Paper','Author')) if len(a.Paper) > 1 and p.Journal else 0

	, lambda a,p: lifted(common_neighbours, p.Conference, a.CoAuthor, relate('Paper')) if len(a.Paper) > 1 and p.Conference else 0
	, lambda a,p: lifted(pseudojaccard,     p.Conference, a.CoAuthor, relate('Paper')) if len(a.Paper) > 1 and p.Conference else 0
	, lambda a,p: lifted(preferential,      p.Conference, a.CoAuthor, relate('Paper')) if len(a.Paper) > 1 and p.Conference else 0
	, lambda a,p: lifted(adamic_adar,       p.Conference, a.CoAuthor, relate('Paper','Author')) if len(a.Paper) > 1 and p.Conference else 0
]

#certainly new
cheat_features = [
	  lambda a,p: Train[a].DeletedPaper.count(p)+Train[a].ConfirmedPaper.count(p) if a in Train else Valid[a].Paper.count(p)
]

#last minute
keyword_bigram_features = [
	  lambda a,p: lifted(common_neighbours, p, a.Paper-{p}, relate('KeyVoc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(jaccard,           p, a.Paper-{p}, relate('KeyVoc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(preferential,      p, a.Paper-{p}, relate('KeyVoc',default={'of'})) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(adamic_adar,       p, a.Paper-{p}, relate('KeyVoc',default={'of'}), lambda x: lenint(Voc[x])) if len(a.Paper) > 1 else 0 

	, lambda a,p: lifted(common_neighbours, p, a.Paper-{p}, relate('Bigram',default=set())) if len(a.Paper) > 1 else 0
	, lambda a,p: lifted(preferential,      p, a.Paper-{p}, relate('Bigram',default=set())) if len(a.Paper) > 1 else 0 
]

feature_set = paper_features + direct_features + indirect_features + linksemantic_features + link_features + derived_direct_features + derived_indirect_features + more_derived_features + cheat_features + keyword_bigram_features

raw_train, labels = train_data()
raw_test = test_data()

print "featurizing trainset..."
train = [(a.Id, p.Id) for a,p in raw_train], extract_verbose(feature_set,raw_train), labels
print "featurizing testset..."
test  = [(a.Id, p.Id) for a,p in raw_test],  extract_verbose(feature_set,raw_test)

print "pickling..."
with open(sys.argv[1], 'wb') as outfile:
    pickle.dump((train,test), outfile)

