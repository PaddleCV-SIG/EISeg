import os.path as osp
from eiseg import pjpath
from collections import defaultdict


class TransUI(object):
    def __init__(self, is_trans=False):
        super().__init__()
        self.trans_dict = defaultdict(dict)
        with open(osp.join(pjpath, "config/zh_CN.EN"), 'r') as f:
            texts = f.readlines()
            for txt in texts:
                strs = txt.split("@")
                self.trans_dict[strs[0].strip()] = strs[1].strip()
        self.is_trans = is_trans

    def put(self, zh_CN):
        if self.is_trans == False:
            return zh_CN
        else:
            try:
                return str(self.trans_dict[zh_CN])
            except:
                return zh_CN