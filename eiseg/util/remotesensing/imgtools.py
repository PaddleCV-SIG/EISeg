import numpy as np
import cv2


def twoPercentLinear(image, max_out=255, min_out=0):
    b, g, r = cv2.split(image)
    def gray_process(gray, maxout = max_out, minout = min_out):
        high_value = np.percentile(gray, 98)  # 取得98%直方图处对应灰度
        low_value = np.percentile(gray, 2)
        truncated_gray = np.clip(gray, a_min=low_value, a_max=high_value) 
        processed_gray = ((truncated_gray - low_value)/(high_value - low_value)) * (maxout - minout)#线性拉伸嘛
        return processed_gray
    r_p = gray_process(r)
    g_p = gray_process(g)
    b_p = gray_process(b)
    result = cv2.merge((b_p, g_p, r_p))
    return np.uint8(result)


def selec_band(tifarr, rgb):
    C = tifarr.shape[-1] if len(tifarr.shape) == 3 else 1
    if C == 1:
        return cv2.merge([_sample_norm(tifarr)] * 3)
    elif C == 2:
        return None
    else:
        return cv2.merge([_sample_norm(tifarr[:,:,rgb[0]]), 
                          _sample_norm(tifarr[:,:,rgb[1]]), 
                          _sample_norm(tifarr[:,:,rgb[2]])])


# DEBUG：test
def _sample_norm(image):
    imax = np.max(image)
    imin = np.min(image)
    return np.uint8(((image - imin) / (imax - imin)) * 255)