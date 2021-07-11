from enum import Enum

import cv2
import matplotlib.pyplot as plt


class Instructions(Enum):
    No_Instruction = 0
    Polygon_Instruction = 1
    # Moving = 2


def get_polygon(label, sample=2):
    contours = cv2.findContours(
        image=label, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_TC89_KCOS
    )
    points = []
    count = 0

    plt.imshow(label)
    plt.savefig("./temp.png")
    print("contours", contours[1])
    for p in contours[1][0]:  # 0索引显示的边界
        print("+_+_+", p)
        if count == sample:
            points.append(p[0])
            count = 0
        else:
            count += 1
    return points
