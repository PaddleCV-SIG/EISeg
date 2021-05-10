import os.path as osp

import paddle

from iann.model.model import get_hrnet_model, get_deeplab_model

here = osp.dirname(osp.abspath(__file__))


class HumanSeg:
    name = "人像分割"

    def get_model(self):
        model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
        para_state_dict = paddle.load(
            osp.join(here, "weight/human_resnet/model.pdparams")
        )
        model.set_dict(para_state_dict)
        return model


class HumanSegCopy:
    name = "人像分割-另一个"

    def get_model(self):
        model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
        para_state_dict = paddle.load(
            osp.join(here, "weight/human_resnet/model.pdparams")
        )
        model.set_dict(para_state_dict)
        return model


models = [HumanSeg(), HumanSegCopy()]
# print(models[1].name)
