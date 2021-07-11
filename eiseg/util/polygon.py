from enum import Enum

import cv2
import matplotlib.pyplot as plt


class Instructions(Enum):
    No_Instruction = 0
    Polygon_Instruction = 1


def get_polygon(label, sample=2):
    contours = cv2.findContours(
        image=label, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_TC89_KCOS
    )
    points = []
    count = 0

    # plt.imshow(label)
    # plt.savefig("./temp.png")
    # print("contours", contours[1])

    cv2_v = cv2.__version__.split(".")[0]
    contours = contours[1] if cv2_v == "3" else contours[0]
    print(f"Totally {len(contours[1])} contours")
    polygons = []
    for contour in contours:
        polygon = []
        for p in contour:
            if count == sample:
                polygon.append(p[0])
                count = 0
            else:
                count += 1
        polygons.append(polygon)
    return polygons
