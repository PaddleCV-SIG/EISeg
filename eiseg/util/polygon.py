from enum import Enum

import cv2
import numpy as np
import math


class Instructions(Enum):
    No_Instruction = 0
    Polygon_Instruction = 1


def get_polygon(label, sample="Dynamic"):
    results = cv2.findContours(
        image=label, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_TC89_KCOS
    )  # 获取内外边界，用RETR_TREE更好表示
    cv2_v = cv2.__version__.split(".")[0]
    contours = results[1] if cv2_v == "3" else results[0]  # 边界
    hierarchys = results[2] if cv2_v == "3" else results[1]  # 隶属信息
    if len(contours) != 0:  # 可能出现没有边界的情况
        polygons = []
        relas = []
        for contour, hierarchy in zip(contours, hierarchys[0]):
            # opencv实现边界简化
            epsilon = 0.0005 * cv2.arcLength(contour, True) if sample == "Dynamic" else sample
            if not isinstance(epsilon, float) and not isinstance(epsilon, int):
                epsilon = 0
            # print("epsilon:", epsilon)
            out = cv2.approxPolyDP(contour, epsilon, True)
            # 自定义边界简化  TODO:感觉这一块还需要再优化
            out = approx_poly_DP(out)
            # 判断自己，如果是子对象就不管自己是谁
            if hierarchy[2] == -1:
                own = None
            else:
                if hierarchy[0] == -1 and hierarchy[1] == -1:
                    own = 0
                elif hierarchy[0] != -1 and hierarchy[1] == -1:
                    own = hierarchy[0] - 1
                else:
                    own = hierarchy[1] + 1
            rela = (own,  # own
                    hierarchy[-1] if hierarchy[-1] != -1 else None)  # parent
            polygon = []
            for p in out:
                polygon.append(p[0])
            polygons.append(polygon)  # 边界
            relas.append(rela)  # 关系
        for i in range(len(relas)):
            if relas[i][1] != None:  # 有父母
                for j in range(len(relas)):
                    if relas[j][0] == relas[i][1]:  # i的父母就是j（i是j的内圈）
                        min_i, min_o = _find_min_point(polygons[i], polygons[j])
                        # 改变顺序
                        s_pj = polygons[j][: min_o]
                        polygons[j] = polygons[j][min_o:]
                        polygons[j].extend(s_pj)
                        s_pi = polygons[i][: min_i]
                        polygons[i] = polygons[i][min_i:]
                        polygons[i].extend(s_pi)
                        # 连接
                        j_connect = polygons[j][0].copy()
                        i_connect = polygons[i][0].copy()
                        polygons[j].append(j_connect)  # 外圈闭合
                        polygons[j].extend(polygons[i])  # 连接内圈
                        polygons[j].append(i_connect)  # 内圈闭合
                        polygons[i] = None
        polygons = list(filter(None, polygons))  # 清除加到外圈的内圈多边形
        return polygons
    else:
        print("没有标签范围，无法生成边界")
        return None


def _find_min_point(i_list, o_list):
    min_dis = 1e7
    idx_i = -1
    idx_o = -1
    for i in range(len(i_list)):
        for o in range(len(o_list)):
            dis = math.sqrt((i_list[i][0] - o_list[o][0]) ** 2 + \
                            (i_list[i][1] - o_list[o][1]) ** 2)
            if dis <= min_dis:
                min_dis = dis
                idx_i = i
                idx_o = o
    return idx_i, idx_o


# 根据三点坐标计算夹角
def _cal_ang(p1, p2, p3):
    eps = 1e-12
    a = math.sqrt((p2[0] - p3[0]) * (p2[0] - p3[0]) + (p2[1] - p3[1]) * (p2[1] - p3[1]))
    b = math.sqrt((p1[0] - p3[0]) * (p1[0] - p3[0]) + (p1[1] - p3[1]) * (p1[1] - p3[1]))
    c = math.sqrt((p1[0] - p2[0]) * (p1[0] - p2[0]) + (p1[1] - p2[1]) * (p1[1] - p2[1]))
    ang = math.degrees(math.acos((b**2 - a**2 - c**2) / (-2 * a * c + eps)))  # p2对应
    return ang


# 计算两点距离
def _cal_dist(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


# 边界点简化
def approx_poly_DP(contour, min_dist=10, ang_err=5):
    # print(contour.shape)  # N, 1, 2
    cs = [contour[i][0] for i in range(contour.shape[0])]
    ## 1. 先删除夹角接近180度的点
    i = 0
    while i < len(cs):
        try:
            last = (i - 1) if (i != 0) else (len(cs) - 1)
            next = (i + 1) if (i != len(cs) - 1) else 0
            ang_i = _cal_ang(cs[last], cs[i], cs[next])
            if abs(ang_i) > (180 - ang_err):
                del cs[i]
            else:
                i += 1
        except:
            i += 1
    ## 2. 再删除两个相近点与前后两个点角度接近的点
    i = 0
    while i < len(cs):
        try:
            j = (i + 1) if (i != len(cs) - 1) else 0
            if _cal_dist(cs[i], cs[j]) < min_dist:
                last = (i - 1) if (i != 0) else (len(cs) - 1)
                next = (j + 1) if (j != len(cs) - 1) else 0
                ang_i = _cal_ang(cs[last], cs[i], cs[next])
                ang_j = _cal_ang(cs[last], cs[j], cs[next])
                # print(ang_i, ang_j)  # 角度值为-180到+180
                if abs(ang_i - ang_j) < ang_err:
                    # 删除距离两点小的
                    dist_i = _cal_dist(cs[last], cs[i]) + _cal_dist(cs[i], cs[next])
                    dist_j = _cal_dist(cs[last], cs[j]) + _cal_dist(cs[j], cs[next])
                    if dist_j < dist_i:
                        del cs[j]
                    else:
                        del cs[i]
                else:
                    i += 1
            else:
                i += 1
        except:
            i += 1
    res = np.array(cs).reshape([-1, 1, 2])
    return res