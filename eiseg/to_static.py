import argparse
# import tkinter as tk
# from inference import utils
import paddle

# from interactive_demo.app import InteractiveDemoApp
from model.is_hrnet_model import HRNetModel
from model.is_hrnet_edge_model import HRNetEdgeModel
import os
from paddleseg.utils import logger
import yaml


def main():
    # args, cfg = parse_args()
    # 小模型部分
    # model = HRNetModel(width=18, ocr_width=48, small=True, with_aux_output=True, use_rgb_conv=False,
    # use_leaky_relu=True, use_disks=True, with_prev_mask=True, norm_radius=5, cpu_dist_maps=False)
    # 通用
    # para_state_dict = paddle.load('weights/hrnet18s_ocr48_cocolvis.pdparams')
    # 人像
    # para_state_dict = paddle.load('weights/hrnet18s_ocr48_human_f_007.pdparams')

    # 大模型部分，有mask
    model = HRNetEdgeModel(width=18, ocr_width=64, small=False, with_aux_output=True, use_leaky_relu=True,
                           use_rgb_conv=False, use_disks=True, norm_radius=5,
                           with_prev_mask=False, with_edge=True, with_finenet=True)
    # 通用
    para_state_dict = paddle.load('weights/cocolvis_hrnet18_ocr64_border_nonmask_edge_finenet_1iter_032.pdparams')
    # 人像
    # para_state_dict = paddle.load('weights/hrnet18_ocr64_mask_self_f_human_034.pdparams')

    model.set_dict(para_state_dict)
    print('Loaded trained params of model successfully')
    model.eval()
    new_net = paddle.jit.to_static(
        model,
        input_spec=[
            paddle.static.InputSpec(
                shape=[None, 3, None, None], dtype='float32'),
            paddle.static.InputSpec(
                shape=[None, 3, None, None], dtype='float32')
        ])

    paddle.jit.save(new_net, 'static_weights/static_hrnet18_ocr64_edgeflow')

    yml_file = os.path.join('static_weights', 'static_hrnet18_ocr64_edgeflow.yaml')
    with open(yml_file, 'w') as file:
        # transforms = cfg.export_config.get('transforms', [{
        #     'type': 'Normalize'
        # }])
        data = {
            'Deploy': {
                # 'transforms': transforms,
                'model': 'static_hrnet18_ocr64_edgeflow.pdmodel',
                'params': 'static_hrnet18_ocr64_edgeflows.pdiparams'
            }
        }
        yaml.dump(data, file)

    logger.info(f'Model is saved in model_dir.')
    # root = tk.Tk()
    # root.minsize(960, 480)
    # app = InteractiveDemoApp(root, args, model)
    # root.deiconify()
    # app.mainloop()




if __name__ == '__main__':
    main()
