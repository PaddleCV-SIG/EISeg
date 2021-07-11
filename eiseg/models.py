import os.path as osp
from abc import ABC, abstractmethod

import paddle

from model.is_hrnet_model import HRNetModel
from util import MODELS

here = osp.dirname(osp.abspath(__file__))


class EISegModel:
    @abstractmethod
    def __init__(self):
        pass

    def load_param(self, param_path):
        params = self.get_param(param_path)
        if params:
            self.model.set_dict(params)
            self.model.eval()
            return self.model
        else:
            return None

    def get_param(self, param_path):
        if not osp.exists(param_path):
            return None
        params = paddle.load(param_path)
        pkeys = params.keys()
        mkeys = self.model.named_parameters()
        if len(pkeys) != len(list(mkeys)):
            return None
        for p, m in zip(pkeys, mkeys):
            if p != m[0]:
                return None
        return params


@MODELS.add_component
class HRNet18s_OCR48(EISegModel):
    __name__ = "HRNet18s_OCR48"

    def __init__(self):
        self.model = HRNetModel(
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


@MODELS.add_component
class HRNet18_OCR64(EISegModel):
    __name__ = "HRNet18_OCR64"

    def __init__(self):
        self.model = HRNetModel(
            width=18,
            ocr_width=64,
            small=False,
            with_aux_output=True,
            use_leaky_relu=True,
            use_rgb_conv=False,
            use_disks=True,
            norm_radius=5,
            with_prev_mask=True,
            cpu_dist_maps=False,  # 目前打包cython有些问题，先默认用False
        )


# print(MODELS.keys())
# print(MODELS.get("test", None))

# @MODELS.add_component
# class HRNet18s_OCR48:
#     __name__ = "HRNet18s_OCR48"
#
#     def load_params(self, params_path):
#         model = HRNetModel(
#             width=18,
#             ocr_width=48,
#             small=True,
#             with_aux_output=True,
#             use_rgb_conv=False,
#             use_leaky_relu=True,
#             use_disks=True,
#             with_prev_mask=True,
#             norm_radius=5,
#             cpu_dist_maps=False,
#         )
#         para_state_dict = paddle.load(params_path)
#         if checkParamsAndNet(model, para_state_dict):
#             model.set_dict(para_state_dict)
#             model.eval()
#             return model
#         else:
#             return None


# @MODELS.add_component
# class HRNet18_OCR64:
#     __name__ = "HRNet18_OCR64"
#
#     def load_params(self, params_path):
#         model = HRNetModel(
#             width=18,
#             ocr_width=64,
#             small=False,
#             with_aux_output=True,
#             use_leaky_relu=True,
#             use_rgb_conv=False,
#             use_disks=True,
#             norm_radius=5,
#             with_prev_mask=True,
#             cpu_dist_maps=False,  # 目前打包cython有些问题，先默认用False
#         )
#         para_state_dict = paddle.load(params_path)
#         if checkParamsAndNet(model, para_state_dict):
#             model.set_dict(para_state_dict)
#             model.eval()
#             return model
#         else:
#             return None


# models = [HRNet18s_OCR48(), HRNet18_OCR64()]
# print(MODELS)


# def findModelByName(model_name):
#     for idx, mt in enumerate(models):
#         if model_name == mt.name:
#             return models[idx], idx
#     return None, -1
