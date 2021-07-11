import cv2
import matplotlib.pyplot as plt
import numpy as np


def get_polygon(label, sample=2):
    contours, _ = cv2.findContours(
        image=label, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_TC89_KCOS
    )
    # out = contours[0]
    out = cv2.approxPolyDP(contours[0], sample, True)
    points = []
    for p in out:
        points.append(p[0])
    return points


label = cv2.imread("tool/mask.png", cv2.IMREAD_GRAYSCALE) * 255
points = get_polygon(label)
print(len(points))
mask = np.zeros_like(label)
for p in points:
    mask[p[1], p[0]] = 255
plt.imshow(mask)
plt.show()