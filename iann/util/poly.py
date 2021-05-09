import cv2
import matplotlib.pyplot as plt
import numpy as np

lab = cv2.imread("../../dzq.png", cv2.IMREAD_UNCHANGED)

plt.imshow(lab)
plt.show()

poly, hierarchy = cv2.findContours(lab, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

result = np.zeros_like(lab)
print(result.shape)
print(poly)
for p in poly[0]:
    p = p[0]
    print(p[0], p[1])
    result[p[1], p[0]] = 1

plt.imshow(result)
plt.show()
