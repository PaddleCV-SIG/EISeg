import numpy as np
import cv2
import operator
from functools import reduce


# def twoPercentLinear(image, max_out=255, min_out=0):
#     b, g, r = cv2.split(image)
#     def gray_process(gray, maxout = max_out, minout = min_out):
#         high_value = np.percentile(gray, 98)  # 取得98%直方图处对应灰度
#         low_value = np.percentile(gray, 2)
#         truncated_gray = np.clip(gray, a_min=low_value, a_max=high_value) 
#         processed_gray = ((truncated_gray - low_value)/(high_value - low_value)) * (maxout - minout)#线性拉伸嘛
#         return processed_gray
#     r_p = gray_process(r)
#     g_p = gray_process(g)
#     b_p = gray_process(b)
#     result = cv2.merge((b_p, g_p, r_p))
#     return np.uint8(result)


def selec_band(tifarr, rgb):
    C = tifarr.shape[-1] if len(tifarr.shape) == 3 else 1
    if C == 1:
        return sample_norm(cv2.merge([np.uint16(tifarr)] * 3))
    elif C == 2:
        return None
    else:
        return sample_norm(
            cv2.merge([np.uint16(tifarr[:, :, rgb[0]]),
                       np.uint16(tifarr[:, :, rgb[1]]),
                       np.uint16(tifarr[:, :, rgb[2]])]))


# DEBUG：test
def sample_norm(image, NUMS=65536):
    stretched_r = __stretch(image[:, :, 0], NUMS)
    stretched_g = __stretch(image[:, :, 1], NUMS)
    stretched_b = __stretch(image[:, :, 2], NUMS)
    stretched_img = cv2.merge([
        stretched_r / float(NUMS), 
        stretched_g / float(NUMS), 
        stretched_b / float(NUMS)])
    return np.uint8(stretched_img * 255)


# 计算直方图
def __histogram(ima, NUMS):
    bins = list(range(0, NUMS))
    flat = ima.flat
    n = np.searchsorted(np.sort(flat), bins)
    n = np.concatenate([n, [len(flat)]])
    hist = n[1:] - n[:-1]
    return hist


# 直方图均衡化
def __stretch(ima, NUMS):
    hist = __histogram(ima, NUMS)
    lut = []
    for bt in range(0, len(hist), NUMS):
        # 步长尺寸
        step = reduce(operator.add, hist[bt: bt + NUMS]) / (NUMS - 1)
        # 创建均衡的查找表
        n = 0
        for i in range(NUMS):
            lut.append(n / step)
            n += hist[i + bt]
        np.take(lut, ima, out=ima)
        return ima


# 计算缩略图
def get_thumbnail(image, range=2000, max_size=1000):
    h, w = image.shape[:2]
    resize = False
    if h >= range or w >= range:
        if h >= w:
            image = cv2.resize(image, (int(max_size / h * w), max_size))
        else:
            image = cv2.resize(image, (max_size, int(max_size / w * h)))
        resize = True
    return image, resize