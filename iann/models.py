import os.path as osp

import paddle

from model.is_hrnet_model import HRNetModel
from util import model_path

here = osp.dirname(osp.abspath(__file__))


class HumanNew:
    name = "新人像分割"

    def get_model(self):
        model = HRNetModel(
            width=18,
            ocr_width=48,
            small=True,
            with_aux_output=True,
            use_rgb_conv=False,
            use_leaky_relu=True,
            use_disks=True,
            with_prev_mask=True,
            norm_radius=5,
            cpu_dist_maps=False,
        )
        para_state_dict = paddle.load(model_path("hrnet18s_ocr48_human_f_007"))
        model.set_dict(para_state_dict)
        return model


models = [HumanNew(), HumanNew()]
