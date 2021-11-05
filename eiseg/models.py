import os.path as osp
from abc import ABC, abstractmethod

import paddle
import paddle.inference as paddle_infer
from model.is_hrnet_model import HRNetModel
from util import MODELS

here = osp.dirname(osp.abspath(__file__))


class EISegModel:
    @abstractmethod
    def __init__(self,
                 model_path="eiseg/static_hrnet18_ocr64_cocolvis.pdmodel",
                 param_path="eiseg/static_hrnet18_ocr64_cocolvis.pdiparams",
                 use_gpu=False):
        model_path, param_path = self.check_param(model_path, param_path)
        try:
            config = paddle_infer.Config(model_path, param_path)
        except:
            ValueError(" 模型和参数不匹配，请检查模型和参数是否加载错误")
        if not use_gpu:
            config.enable_mkldnn()
            if paddle.fluid.core.supports_bfloat16():
                config.enable_mkldnn_bfloat16()
            config.switch_ir_optim(True)
            config.set_cpu_math_library_num_threads(10)
        else:
            config.enable_use_gpu(500, 0)
            config.switch_ir_optim()
            config.enable_memory_optim()
            config.enable_tensorrt_engine(
                workspace_size=1 << 30, 
                precision_mode=paddle_infer.PrecisionType.Float32,
                max_batch_size=1, min_subgraph_size=5, 
                use_static=False, use_calib_mode=False)
        self.model = paddle_infer.create_predictor(config)
        print("加载模型成功")

    def check_param(self, model_path, param_path):
        if model_path is None or not osp.exists(model_path):
            raise Exception(f"模型路径{model_path}不存在。请指定正确的模型路径")
        if param_path is None or not osp.exists(param_path):
            raise Exception(f"权重路径{param_path}不存在。请指定正确的权重路径")
        return model_path, param_path


# ModelsNick = {"HRNet18s_OCR48": ["轻量级模型", 0],
#               "HRNet18_OCR64": ["高精度模型", 1]}

# @MODELS.add_component
# class HRNet18s_OCR48(EISegModel):
#     __name__ = "HRNet18s_OCR48"

#     def create_model(self):
#         self.model = HRNetModel(
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


# @MODELS.add_component
# class HRNet18_OCR64(EISegModel):
#     __name__ = "HRNet18_OCR64"

#     def create_model(self):
#         self.model = HRNetModel(
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