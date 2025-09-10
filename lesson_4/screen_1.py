import numpy as np

A1 = np.array([[1, 2, 4],
               [7, 5, -2],
               [-2, 1, 3]
               ])

B1 = np.array([[-1, 0, 3],
               [2, -6, 1],
               [-7, 1, 5]
               ])

C1 = np.array([[-2, 3],
               [4,0],
               [7, -1]
               ])

A2 = np.array([[0, 3, 4],
               [-7, 1, -2],
               [2, -1, 3]
               ])

B2 = np.array([[1, 2, 4],
               [7, 0, -2],
               [-3, -2, 5]
               ])

C2 = np.array([[-3, 2],
               [0, 4],
               [-1, 7]
               ])

A3 = np.array([[5, 2, 9],
               [7, 0, -2],
               [-2, 3 ,0]
               ])

B3 = np.array([[1, -2, 1],
               [7, 5, -2],
               [-2, 8,3]
               ])

C3 = np.array([[-2, 3],
               [4, 5],
               [0, -1]
               ])

A4 = np.array([[1, -2, 8],
               [7, 5, -2],
               [-2, 3, 0]
               ])

B4 = np.array([[0, 2, 4],
               [1, -3, -2],
               [-2, 1, 3]
               ])

C4 = np.array([[0, 3],
               [5, -4],
               [7, -1]
               ])

A5 = np.array([[9, 2, 4],
               [7, 5, -5],
               [6, -2, 3]
               ])

B5 = np.array([[8, 2, 4],
               [0, 1, -3],
               [-2, 1, 6]
               ])

C5 = np.array([[-2, 0],
               [4, 8],
               [1, -1]
               ])

print(A1 + B1)
print(A2 + B2)
print(A3 + B3)
print(A4 + B4)
print(A5 + B5)

print(B1 - A1)
print(B2 - A2)
print(B3 - A3)
print(B4 - A4)
print(B5 - A5)

print(A1 @ C1)
print(A2 @ C2)
print(A3 @ C3)
print(A4 @ C4)
print(A5 @ C5)

print(A1 @ B1 @ C1)
print(A2 @ B2 @ C2)
print(A3 @ B3 @ C3)
print(A4 @ B4 @ C4)
print(A5 @ B5 @ C5)