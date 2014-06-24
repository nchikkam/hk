
def cost(a, b):
    """
    function to calculate the edit distance cost between 2 given words.
    useful and insightful url: http://web.stanford.edu/class/cs124/lec/med.pdf
    """
    m = len(a)
    n = len(b)
    # prepare the cost Matrix for house keeping
    c = [[]] * m
    for l in range(m):
        c[l] = [0] * n

    for i in range(m):
        for j in range(n):
            if   i == 0 and j == 0: c[i][j] = 0 if a[i]==b[j] else 1 # edit distance for initial cases
            elif i == 0: c[i][j] = j # base case
            elif j == 0: c[i][j] = i
            else:
                c[i][j] = min(c[i-1][j]+1, c[i][j-1]+1)   # c(i,j) = min{cost(i-1, j), cost(i-1, j-1), cost(i, j-1)};
                temp = 0 if a[i]==b[j] else 1
                c[i][j] = min(c[i][j], c[i-1][j-1]+temp)

    for i in range(m):
        for j in range(n):
            print c[i][j],
        print

    return c[m-1][n-1]