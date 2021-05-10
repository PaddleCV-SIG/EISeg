import os
import os.path as osp


def toint(seq):
    for idx in range(len(seq)):
        try:
            seq[idx] = int(seq[idx])
        except ValueError:
            pass
    return seq


def saveLabel(labelList, path):
    # labelList = [[1, "人", [0, 0, 0]], [2, "车", [128, 128, 128]]]
    if not path or len(path) == 0 or not osp.exists(osp.basename(path)):
        return
    with open(path, "w", encoding="utf-8") as f:
        for l in labelList:
            for idx in range(2):
                print(l[idx], end=" ", file=f)
            for idx in range(3):
                print(l[2][idx], end=" ", file=f)
            print(file=f)


# saveLabel("label.txt")


def readLabel(path):
    if not path or len(path) == 0 or not osp.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        labels = f.readlines()
    labelList = []
    for lab in labels:
        lab = lab.replace("\n", "").strip(" ").split(" ")
        if len(lab) != 2 and len(lab) != 5:
            print("标签不合法")
            continue
        label = toint(lab[:2])
        label.append(toint(lab[2:]))
        labelList.append(label)

        return labelList


# readLabel("label.txt")
