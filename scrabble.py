def Scrabble(w):
    '''Gives the scrabble value for a word.'''
    def value(c):
    	distrib = ["EAIONRTLSU", "DG", "BCMP", "FHVWY", "K", "", "", "JX", "", "QZ"]
	for w, letters in enumerate(distrib, 1):
	    if c in letters: return w
	return 0
    return sum(map(value, w.upper()))

