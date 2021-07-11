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
    # 这个地方split出来是字符的3，不是数字，改了一下
    cv2_v = cv2.__version__.split(".")[0]
    boundary = contours[1][0] if cv2_v == "3" else contours[0][0]
    for p in boundary:
        if count == sample:
            points.append(p[0])
            count = 0
        else:
            count += 1
    return points
