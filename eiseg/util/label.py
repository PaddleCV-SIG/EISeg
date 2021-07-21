import os
import os.path as osp


# def _saveLabel(labelList, path):
#     print("save label", labelList, path)
#     print(osp.exists(osp.dirname(path)), osp.dirname(path))
#     if not path or len(path) == 0 or not osp.exists(osp.dirname(path)):
#         print("save label error")
#         return
#     with open(path, "w", encoding="utf-8") as f:
#         for ml in labelList:
#             print(ml.idx, end=" ", file=f)
#             print(ml.name, end=" ", file=f)
#             for idx in range(3):
#                 print(ml.color[idx], end=" ", file=f)
#             print(file=f)


class Label:
    def __init__(self, idx=None, name=None, color=None):
        self.idx = idx
        self.name = name
        self.color = color

    def __repr__(self):
        return f"{self.idx} {self.name} {self.color}"


class LabeleList(object):
    def __init__(self):
        self.list = []

    def add(self, idx, name, color):
        self.list.append(Label(idx, name, color))

    def remove(self, index):
        del self.list[index]

    def clear(self):
        self.list = []

    def toint(self, seq):
        if isinstance(seq, list):
            for i in range(len(seq)):
                try:
                    seq[i] = int(seq[i])
                except ValueError:
                    print(f"toint ValueError: {seq[i]} {type(seq[i])}")
                    pass
        else:
            seq = int(seq)
        return seq

    def readLabel(self, path):
        if not osp.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            labels = f.readlines()
        labelList = []
        for lab in labels:
            lab = lab.replace("\n", "").strip(" ").split(" ")
            if len(lab) != 2 and len(lab) != 5:
                print(f"{lan} 标签不合法")
                continue
            label = Label(self.toint(lab[0]), str(lab[1]), _toint(lab[2:]))
            labelList.append(label)
        self.list = labelList
        # self.list = _readLabel(path)

    def saveLabel(self, path):
        print("save label", self.list, path)
        print(osp.exists(osp.dirname(path)), osp.dirname(path))
        if not path or len(path) == 0 or not osp.exists(osp.dirname(path)):
            print("save label error")
            return
        with open(path, "w", encoding="utf-8") as f:
            for ml in self.list:
                print(ml.idx, end=" ", file=f)
                print(ml.name, end=" ", file=f)
                for idx in range(3):
                    print(ml.color[idx], end=" ", file=f)
                print(file=f)

        # _saveLabel(self.list, path)

    def __repr__(self):
        s = ""
        for lab in self.list:
            s += str(lab) + ","

    def __getitem__(self, index):
        return self.list[index]

    def __len__(self):
        return len(self.list)
