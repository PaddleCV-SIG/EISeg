import os
import os.path as osp
import numpy as np
import cv2
from PIL import Image
from tqdm import tqdm


# 参考paddlex数据准备文档
# https://github.com/PaddlePaddle/PaddleX/blob/release/2.0.0/docs/data/format/README.md

# 语义分割
def Eiseg2Semantic(save_folder, imgs_folder, lab_folder=None, split_rate=0.9):
    """Convert the data marked by eiseg into the semantic segmentation data of paddlex.

    Args:
        save_folder (str): Data save folder.
        imgs_folder (str): Image storage folder.
        lab_folder (str, optional): Label storage folder, 
            if it is none, it will be saved in the current folder by default. Defaults to None.
        split_rate (float, optional): Proportion of training data and validation data. Defaults to 0.9.
    """
    imgs_name = os.listdir(imgs_folder)
    for name in imgs_name:
        pass


# TODO: 实例分割



# TODO: 目标检测