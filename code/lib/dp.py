
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
    return table[m-1][n-1]

def recursiveCost(a, b, m, n):
    if n == len(b): return len(b)-m
    if m == len(a): return len(a)-n

    if a[m] == b[n]: return recursiveCost(a, b, m+1, n+1)
    if a[m] != b[n]:
        return 1 + min(
                       recursiveCost(a, b, m, n+1),
                       recursiveCost(a, b, m+1, n),
                       recursiveCost(a, b, m+1, n+1)
                    );
