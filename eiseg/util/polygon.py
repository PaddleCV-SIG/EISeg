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

    # plt.imshow(label)
    # plt.savefig("./temp.png")
    # print("contours", contours[1])
    # opencv3返回为3个参数，其中第二个是边界；opencv4和2只返回2个参数，其中第一个是边界
    cv2_v = cv2.__version__.split('.')[0]
    boundary = contours[1][0] if cv2_v == 3 else contours[0][0]
    for p in boundary:
        # print("+_+_+", p)
        if count == sample:
            points.append(p[0])
            count = 0
        else:
            count += 1
    return points
