
def cost(a, b):
    """
    function to calculate the edit distance cost between 2 given words.
    useful and insightful url: http://web.stanford.edu/class/cs124/lec/med.pdf
    """
    m = len(a) + 1
    n = len(b) + 1
    # prepare the cost Matrix for house keeping
    table = [[]] * m
    for l in range(m):
        table[l] = [0] * n

    #set the 0 row and col to sequence numbers
    for i in range(m): table[i][0] = i
    for i in range(n): table[0][i] = i

    for i in range(1, m):
        for j in range(1, n):
            d = 0 if a[i-1]==b[j-1] else 1 # assuming substitution is of cost 1
            table[i][j] = min(
                          table[i-1][j-1] + d,
                          table[i-1][j] + 1,
                          table[i][j-1] + 1
                          )

    traceBack("", "",  "",  table, m-1, n-1, a, b)
    return table[m-1][n-1]

def traceBack(r1, r2, r3, m, i, j, s1, s2):
    """
    Awesome explanation from: http://www.csse.monash.edu.au/~lloyd/tildeAlgDS/Dynamic/Edit/
    """
    if i > 0 and j > 0:
        diag = m[i-1][j-1]
        diagCh = '|'
        if s1[i-1] != s2[j-1]:
            diag += 1
            diagCh = ' '

        if m[i][j] == diag:
            traceBack(s1[i-1]+r1, diagCh+r2, s2[j-1]+r3, m, i-1, j-1, s1, s2)
        elif m[i][j] == m[i-1][j]-0 + 1: # delete
            traceBack(s1[i-1]+r1, ' '+r2, '-'+r3, m, i-1, j, s1, s2)
        else:
            traceBack('-'+r1, ' '+r2, s2[j-1]+r3, m, i, j-1, s1, s2) # insertion
    elif i > 0:
        traceBack(s1[i-1]+r1, ' '+r2, '-'+r3, m, i-1, j, s1, s2)
    elif j > 0:
        traceBack('-'+r1, ' '+r2, s2[j-1]+r3, m, i, j-1, s1, s2)
    else:
        print r1+'\n'+r2+'\n'+r3+'\n'


def findEditDistance (a, b):
    if   len(a) == 0: return len(b)
    elif len(b) == 0: return len(a)
    else:
        addCost = findEditDistance(a, b[1:]) + 1
        delCost = findEditDistance(a[1:], b) + 1
        substCost = findEditDistance(a[1:], b[1:])
        if a[0] != b[0]:
            substCost += 1
    return min(addCost, delCost, substCost)
