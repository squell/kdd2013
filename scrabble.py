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

def ned(word1,word2):
    'approximate-normalized edit distance'
    try:
        return ed(word1,word2)/float(max(len(word1),len(word2)))
    except ZeroDivisionError:
	return 0.0

def lcs(word1,word2):
    'longest common subsequence'
    D = [(0,c) for c in [None]+list(word2)]
    for c in word1:
        olw = nlw = -float('inf')
        for i, pair in enumerate(D):
            w, c2 = pair
            olw, w = w, max(w, nlw, olw+1 if c==c2 else w)
            nlw = w
            D[i] = (nlw,c2)
    return D[-1][0]

def lcstr(word1,word2):
    'longest common substring'
    D = [(0,c) for c in [None]+list(word2)]
    M = (0,None)
    for c in word1:
        olw = nlw = -float('inf')
        for i, pair in enumerate(D):
            w, c2 = pair
            olw, w = w, (olw+1 if c==c2 else 0)
            nlw = w
            D[i] = (nlw,c2)
	M = max([M]+D, key=lambda x:x[0])
    return M[0]

