
def findRectangle_O_N_N(histogram, left, right):
    if left >= right: return 0
    minHeight = histogram[left]
    pivot = left

    i = left+1
    while i < right:
        if histogram[i] < minHeight:
            minHeight = histogram[i]
            pivot = i
        i += 1

    return max( minHeight * (right-left),
                findRectangle_O_N_N(histogram, left, pivot),
                findRectangle_O_N_N(histogram, pivot+1, right))

def largestRectangleArea(height):
        stack = []  # Store the position of bars with non-decreasing height
        maxArea = 0
        height.append(-1)   # Append a pseudo bar at the end so that, after
                            # the while loop, the one and the only on bar
                            # left in the stack will definitely be this
                            # pseudo bar.

        index = 0
        # In this loop, we are using the stack to find out the largest zone
        # for each bar (to say i), in which bar i is the shortest one.
        while index < len(height):
            if len(stack) == 0:
                # This is the first bar. OR all of its previous bars are
                # higher than this one.
                stack.append(index)
                index += 1
            elif height[index] >= height[stack[-1]]:
                stack.append(index)
                index += 1
            else:
                preBasin = stack.pop()
                if len(stack) == 0:
                    # From beginning to index-1 position, the preBasin has
                    # the shortest bar.
                    maxArea = max(maxArea, height[preBasin] * index)
                else:
                    # From stack[-1] position to index-1 position, the
                    # preBasin has the shortest bar.
                    maxArea = max(maxArea, height[preBasin] * (index-stack[-1]-1) )

        return maxArea


histogram = [6, 2, 5, 4, 5, 2, 6]
print findRectangle_O_N_N(histogram, 0, len(histogram)), largestRectangleArea(histogram)

h = [4,8,3,5,3,0]
print findRectangle_O_N_N(h, 0, len(h)), largestRectangleArea(h)

h1 = [3, 5, 6]
print findRectangle_O_N_N(h1, 0, len(h1)), largestRectangleArea(h1)