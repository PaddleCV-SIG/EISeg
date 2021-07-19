import numpy as np


def percent_linear(image):
    '''
        线性拉伸，输入图像为[H,W,C]，类型为uint8
    '''
    H, W, C = image.shape
    def gray_process(gray, maxout=255, minout=0):
        truncated_down = np.percentile(gray, 2)
        truncated_up = np.percentile(gray, (98))
        gray_new = (gray - truncated_down) / (truncated_up - truncated_down) * \
                   (maxout - minout) + minout
        gray_new[gray_new < minout] = minout
        gray_new[gray_new > maxout] = maxout
        return gray_new
    result = None
    for i_c in range(C):
        if i_c == 0:
            result = gray_process(image[:, :, i_c])[:, :, np.newaxis]
        else:
            result = np.concatenate([result, gray_process(image[:, :, i_c])[:, :, np.newaxis]], \
                                    axis=-1)
    return np.uint8(result.reshape([H, W, C]))