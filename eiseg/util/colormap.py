import os.path as osp
import random

#
# def toint(seq):
#     return [int(x) for x in seq]


class ColorMask(object):
    def __init__(self, color_path, shuffle=False):
        with open(color_path, "r") as f:
            colors = f.readlines()
        self.colors = [[int(x) for x in c[:-2].split(",")] for c in colors]

    def __len__(self):
        return len(self.colors)

    def get_color(self, labelList):
        diffs = [0 for _ in range(len(self))]
        for colorIdx in range(len(self)):
            for lab in labelList:
                lab = lab.color
                print(lab)
                if self.colors[colorIdx] == lab:
                    diffs[colorIdx] = 0
                else:
                    for idx in range(3):
                        print(idx)
                        diffs[colorIdx] += abs(self.colors[colorIdx][idx] - lab[idx])
        f = lambda i: diffs[i]
        colorIdx = max(range(len(self)), key=f)
        return self.colors[colorIdx]
