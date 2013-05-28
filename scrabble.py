def Scrabble(w):
    'gives the scrabble value for a word :)'
    def value(c):
    	distrib = ["EAIONRTLSU", "DG", "BCMP", "FHVWY", "K", "", "", "JX", "", "QZ"]
	for w, letters in enumerate(distrib, 1):
	    if c in letters: return w
	return 0
    return sum(map(value, w.upper()))

def ed(word1,word2):
    'simple edit distance: count only inserts en deletions'
    D = [(0,None)]+list(enumerate(word2,1))
    for c in word1:
        olw = nlw = float('inf')
        for i, pair in enumerate(D):
            w, c2 = pair
            olw, w = w, min(w+1, nlw+1, olw if c==c2 else float('inf'))
            nlw = w
            D[i] = (nlw,c2)
    return D[-1][0]

def ed_name(word1,word2):
    'ed, but specialized for names: recognize . as an abbreviation'
    D = [(0,None)]+list(enumerate(word2,1))
    for c in word1:
        olw = nlw = float('inf')
        for i, pair in enumerate(D):
            w, c2 = pair
            olw, w = w, min(w+int(c2<>'.'), nlw+int(c<>'.'), olw if c==c2 else float('inf'))
            nlw = w
            D[i] = (nlw,c2)
    return D[-1][0]

def ed_bi(word1,word2):
    'pure bigram edit distance'
    D = [(0,None)]+list(enumerate(word2,1))
    def match(i,j):
	bi1 = word1[j-1:j+1]
	bi2 = word2[i-1:i+1]
	return len(bi1) == 2 and word1[j-1:j+1] == word2[i-1:i+1]
    for j, c in enumerate(word1):
        olw = nlw = float('inf')
        for i, pair in enumerate(D):
            w, c2 = pair
            olw, w = w, min(w+1, nlw+1, olw if match(j,i) else olw+1)
            nlw = w
            D[i] = (nlw,c2)
    return D[-1][0]

