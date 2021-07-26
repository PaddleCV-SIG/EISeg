import numpy as np
from math import ceil


def slide_out(bimg, row, col, c_size=None):
    '''
        根据输入的图像[H, W, C]和行列数以及索引输出对应图像块
        index (list)
    '''
    H, W = bimg.shape[:2]
    if c_size is None:
        c_size = [ceil(H / row), ceil(W / col)]
    # 扩展不够的
    h_new = row * c_size[0]
    w_new = col * c_size[1]
    if h_new != H or w_new != W:
        if len(bimg.shape) == 2:
            tmp = np.zeros((h_new, w_new))
            tmp[:bimg.shape[0], :bimg.shape[1]] = bimg
        else:
            tmp = np.zeros((h_new, w_new, bimg.shape[-1]))
            tmp[:bimg.shape[0], :bimg.shape[1], :] = bimg
    else:
        tmp = bimg
    H, W = tmp.shape[:2]
    cell_h = c_size[0]
    cell_w = c_size[1]
    result = []
    for i in range(row):
        for j in range(col):
            index = [i, j]
            if len(tmp.shape) == 2:
                result.append(tmp[(index[0] * cell_h):((index[0] + 1) * cell_h), \
                                        (index[1] * cell_w):((index[1] + 1) * cell_w)])
            else:
                result.append(tmp[(index[0] * cell_h):((index[0] + 1) * cell_h), \
                                        (index[1] * cell_w):((index[1] + 1) * cell_w), :])
    return result


def splicing_list(imgs, raw_size):
    '''
        将slide的out进行拼接，raw_size保证恢复到原状
    '''
    h, w = imgs[0].shape[:2]
    row = ceil(raw_size[0] / h)
    col = ceil(raw_size[1] / w)
    # print(raw_size[1], w, raw_size[1]/w)
    # print('row, col:', row, col)
    if len(imgs[0].shape) == 2:
        result = np.zeros((h * row, w * col), dtype=np.uint8)
    else:
        result = np.zeros((h * row, w * col, imgs[0].shape[-1]), dtype=np.uint8)
    k = 0
    for i_r in range(row):
        for i_c in range(col):
            # print('h, w:', h, w)
            if len(imgs[k].shape) == 2:
                result[(i_r * h):((i_r + 1) * h), (i_c * w):((i_c + 1) * w)] = imgs[k]
            else:
                result[(i_r * h):((i_r + 1) * h), (i_c * w):((i_c + 1) * w), :] = imgs[k]
            k += 1
            # print('r, c, k:', i_r, i_c, k)
    if len(result.shape) == 2:
        return result[0:raw_size[0], 0:raw_size[1]]
    else:
        return result[0:raw_size[0], 0:raw_size[1], :]