import math
import numpy as np
from math import ceil


class Grids:
    def __init__(self, grid_size=512, overlap=12):
        # 1
        self.grid_size = grid_size
        self.overlap = overlap
        # 2
        self.rawimg = None  # 保存原始的遥感图像或者医疗图像（多通道）
        self.detimg = None  # 宫格初始图像
        self.gridInit = False  # 是否初始化了宫格
        self.imagesGrid = []  # 图像宫格
        self.masksGrid = []  # 标签宫格
        self.gridCount = None  # (row count, col count)
        self.gridIndex = None  # (current row, current col, current idx)

    # TODO: 合入init
    def reInit(self):
        self.rawimg = None
        self.detimg = None
        self.gridInit = False
        self.imagesGrid = []
        self.masksGrid = []
        self.gridCount = None
        self.gridIndex = None

    def createGrids(self, img):
        self.detimg = img.copy()
        h, w = self.detimg.shape[:2]
        grid_row_count = math.ceil(h / self.grid_size)
        grid_col_count = math.ceil(w / self.grid_size)
        self.gridCount = (grid_row_count, grid_col_count)
        self.imagesGrid = self.slideOut(grid_row_count, grid_col_count)
        self.masksGrid = [None] * len(self.imagesGrid)
        self.gridInit = True
        return grid_row_count, grid_col_count

    def slideOut(self, row, col):
        """
        根据输入的图像[H, W, C]和行列数以及索引输出对应图像块
        index (list)
        """
        bimg = self.detimg
        H, W = bimg.shape[:2]
        c_size = [ceil(H / row), ceil(W / col)]
        # 扩展不够的以及重叠部分
        h_new = row * c_size[0] + self.overlap
        w_new = col * c_size[1] + self.overlap
        # 新图
        tmp = np.zeros((h_new, w_new, bimg.shape[-1]))
        tmp[: bimg.shape[0], : bimg.shape[1], :] = bimg
        H, W = tmp.shape[:2]
        cell_h = c_size[0]
        cell_w = c_size[1]
        # 开始分块
        result = []
        for i in range(row):
            for j in range(col):
                start_h = i * cell_h
                end_h = start_h + cell_h + self.overlap
                start_w = j * cell_w
                end_w = start_w + cell_w + self.overlap
                result.append(tmp[start_h:end_h, start_w:end_w, :])
        # for r in result:
        #     print(r.shape)
        return result

    def splicingList(self):
        """
        将slide的out进行拼接，raw_size保证恢复到原状
        """
        imgs = self.masksGrid
        raw_size = self.detimg.shape[:2]
        h, w = None, None
        for i in range(len(imgs)):
            if imgs[i] is not None:
                h, w = imgs[i].shape[:2]
                break
        if h is None and w is None:
            return False
        row = ceil(raw_size[0] / h)
        col = ceil(raw_size[1] / w)
        # print('row, col:', row, col)
        result_1 = np.zeros((h * row, w * col), dtype=np.uint8)
        result_2 = result_1.copy()
        k = 0
        for i in range(row):
            for j in range(col):
                # print('h, w:', h, w)
                if imgs[k] is not None:
                    start_h = (i * h) if i == 0 else (i * (h - self.overlap))
                    end_h = start_h + h
                    start_w = (j * w) if j == 0 else (j * (w - self.overlap))
                    end_w = start_w + w
                    # 单区自己，重叠取或
                    if (i + j) % 2 == 0:
                        result_1[start_h:end_h, start_w:end_w] = imgs[k]
                    else:
                        result_2[start_h:end_h, start_w:end_w] = imgs[k]
                k += 1
                # print('r, c, k:', i_r, i_c, k)
        result = np.where(result_2 != 0, result_2, result_1)
        return result[: raw_size[0], : raw_size[1]]
