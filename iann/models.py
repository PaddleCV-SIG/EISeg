import os.path as osp

import paddle

from model.is_hrnet_model import HRNetModel

here = osp.dirname(osp.abspath(__file__))


# class HumanSeg:
#     name = "人像分割"
#
#     def get_model(self):
#         model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
#         para_state_dict = paddle.load(
#             osp.join(here, "weight/human_resnet/model.pdparams")
#         )
#         model.set_dict(para_state_dict)
#         return model
#
#
# class SkySeg:
#     name = "非天空分割"
#
#     def get_model(self):
#         model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
#         para_state_dict = paddle.load(
#             osp.join(here, "weight/sky_resnet/model.pdparams")
#         )
#         model.set_dict(para_state_dict)
#         return model


# class Aorta:
#     name = "主动脉分割"
#
#     def get_model(self):
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
#         para_state_dict = paddle.load("weights/hrnet18s_ocr48_human_f_007.pdparams")
#         model.set_dict(para_state_dict)
#         return model


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
        para_state_dict = paddle.load(
            osp.join(
                here,
                "/home/aistudio/git/paddle/iann/iann/weight/human_resnet/hrnet18s_ocr48_human_f_007.pdparams",
            )
        )
        model.set_dict(para_state_dict)
        return model


models = [HumanNew(), HumanNew()]
