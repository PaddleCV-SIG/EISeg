import os
import argparse
import random
from easydict import EasyDict as edict
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import paddle
import paddle.nn as nn
import paddleseg.transforms as T
from paddleseg.utils import logger
from model.model import get_hrnet_model, DistMapsHRNetModel, get_deeplab_model, get_shufflenet_model
from model.modeling.hrnet_ocr import HighResolutionNet
from albumentations import (
    Compose, ShiftScaleRotate, PadIfNeeded, RandomCrop,
    RGBShift, RandomBrightnessContrast, RandomRotate90, HorizontalFlip
)
from data.points_sampler import MultiPointSampler
#from data.points_sampler_ritm import MultiPointSampler
from data.davis import DavisDataset
from model.loss import *
from util.util import *
from paddleseg.utils import get_sys_env, logger
from visualdl import LogWriter


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--max_iters', type=int, default=1001,
                        help='The number of the starting epoch from which training will continue. '
                             '(it is important for correct logging and learning rate)')

    parser.add_argument('--workers', type=int, default=4,
                        metavar='N', help='Dataloader threads.')

    parser.add_argument('--batch_size', type=int, default=4,
                        help='You can override model batch size by specify positive number.')

    parser.add_argument('--weights', type=str, default=None,
                        help='Model weights will be loaded from the specified path if you use this argument.')

    parser.add_argument('--use_vdl', type=bool, default=False,
                        help='Whether to use visual dl.')

    return parser.parse_args()


def main():
    env_info = get_sys_env()
    info = ['{}: {}'.format(k, v) for k, v in env_info.items()]
    info = '\n'.join(['', format('Environment Information', '-^48s')] + info +
                     ['-' * 48])
    logger.info(info)

    place = 'gpu' if env_info['Paddle compiled with cuda'] and env_info[
        'GPUs used'] else 'cpu'

    paddle.set_device(place)
    nranks = paddle.distributed.ParallelEnv().nranks
    local_rank = paddle.distributed.ParallelEnv().local_rank
    cfg = parse_args()
    model_cfg = edict()
    model_cfg.crop_size = (320, 480)
    model_cfg.input_normalization = {
        'mean': [.485, .456, .406],
        'std': [.229, .224, .225]
    }
    model_cfg.num_max_points = 10
    model_cfg.input_transform = T.Compose([T.Normalize(mean=model_cfg.input_normalization['mean'],
                                                       std=model_cfg.input_normalization['std'])], to_rgb=False)

    nn.initializer.set_global_initializer(nn.initializer.Normal(), nn.initializer.Constant())

    #model = get_hrnet_model(width=18, ocr_width=64, with_aux_output=True, is_ritm=True)
    #model = get_shufflenet_model()
    #model.load_weights('/mnt/haoyuying/ritm_paddle_mac/pretrained/shufflenet_humanseg.pdparams')
    model = get_deeplab_model(backbone='resnet18', is_ritm=True)
    #model.load_weights('human_best/resnet18_ritm_95.5/model.pdparams')
    #model.load_weights('/mnt/haoyuying/fbrs_interactive_segmentation/pretrained_models/hrnetv2_w18_imagenet_model.pdparams')
    backbone_params, other_params = model.get_trainable_params()
    #model.load_weights('/mnt/haoyuying/fbrs_paddle/output_1/iter_11000_89.04/model.pdparams')

    if nranks > 1:
        if not paddle.distributed.parallel.parallel_helper._is_parallel_ctx_initialized():
            paddle.distributed.init_parallel_env()
            ddp_net = paddle.DataParallel(model)
        else:
            ddp_net = paddle.DataParallel(model)
        train(ddp_net, cfg, model_cfg, max_iters=cfg.max_iters, backbone_params=backbone_params,
              other_params=other_params)
    else:
        train(model, cfg, model_cfg, max_iters=cfg.max_iters, backbone_params=backbone_params,
              other_params=other_params)

def train(model, cfg, model_cfg, max_iters, save_epoch=10, save_dir='hand', backbone_params=None,
          other_params=None):
    local_rank = paddle.distributed.ParallelEnv().local_rank
    cfg.batch_size = 16 if cfg.batch_size < 1 else cfg.batch_size
    cfg.val_batch_size = cfg.batch_size
    cfg.input_normalization = model_cfg.input_normalization
    crop_size = model_cfg.crop_size

    log_iters = 10
    save_interval = 1000
    num_masks = 1

    train_augmentator = Compose([
        UniformRandomResize(scale_range=(0.75, 1.40)),
        HorizontalFlip(),
        PadIfNeeded(min_height=crop_size[0], min_width=crop_size[1], border_mode=0),
        RandomCrop(*crop_size),
        RandomBrightnessContrast(brightness_limit=(-0.25, 0.25), contrast_limit=(-0.15, 0.4), p=0.75),
        RGBShift(r_shift_limit=10, g_shift_limit=10, b_shift_limit=10, p=0.75)
    ], p=1.0)

    val_augmentator = Compose([
        PadIfNeeded(min_height=crop_size[0], min_width=crop_size[1], border_mode=0),
        RandomCrop(*crop_size)
    ], p=1.0)

    def scale_func(image_shape):
        return random.uniform(0.75, 1.25)

    points_sampler = MultiPointSampler(model_cfg.num_max_points, prob_gamma=0.7,
                                       merge_objects_prob=0.15,
                                       max_num_merged_objects=2)
    trainset = DavisDataset(
        'iann/train/datasets/egoHands',
        num_masks=num_masks,
        augmentator=train_augmentator,
        points_from_one_object=False,
        input_transform=model_cfg.input_transform,
        min_object_area=80,
        keep_background_prob=0.0,
        image_rescale=scale_func,
        points_sampler=points_sampler,
        samples_scores_path=None,
        samples_scores_gamma=1.25
    )

    valset = DavisDataset(
        'iann/train/datasets/egoHands',
        augmentator=val_augmentator,
        num_masks=num_masks,
        points_from_one_object=False,
        input_transform=model_cfg.input_transform,
        min_object_area=80,
        image_rescale=scale_func,
        points_sampler=points_sampler
    )

    batch_sampler = paddle.io.DistributedBatchSampler(
        trainset, batch_size=cfg.batch_size, shuffle=True, drop_last=True)

    loader = paddle.io.DataLoader(
        trainset,
        batch_sampler=batch_sampler,
        return_list=True,
    )

    val_batch_sampler = paddle.io.DistributedBatchSampler(
        valset, batch_size=cfg.batch_size, shuffle=True, drop_last=True)

    val_loader = paddle.io.DataLoader(
        valset,
        batch_sampler=val_batch_sampler,
        return_list=True,
    )

    if cfg.use_vdl:
        from visualdl import LogWriter
        log_writer = LogWriter(save_dir)

    iters_per_epoch = len(batch_sampler)

    optimizer1 = paddle.optimizer.Adam(learning_rate=5e-5, parameters=other_params)
    optimizer2 = paddle.optimizer.Adam(learning_rate=5e-6, parameters=backbone_params)
    instance_loss = NormalizedFocalLossSigmoid(alpha=0.5, gamma=2)
    instance_aux_loss = SigmoidBinaryCrossEntropyLoss()
    model.train()
#     with open('mobilenet_model.txt', 'w') as f:
#         for keys, values in model.state_dict().items():
#             f.write(keys +'\t'+str(values.shape)+"\n")
    iters = 0
    avg_loss = 0.0
    while iters < max_iters:
        for data in loader:
            iters += 1
            if iters > max_iters:
                break
            if len(data) == 3:
                images, points, masks = data
            else:
                images, points = data
                masks = None
            if masks is not None:
                batch_size, num_points, c, h, w = masks.shape
                masks = masks.reshape([batch_size * num_points, c, h, w])

            output = batch_forward(model, images, masks, points)
            #output = model(images, points)
#             print('instance', output['instances'])
#             print('mask', masks)
            
            loss = instance_loss(output['instances'], masks)
            if 'instances_aux' in output.keys():
                aux_loss = instance_aux_loss(output['instances_aux'], masks)
                total_loss = loss + 0.4 * aux_loss
            else:
                total_loss = loss
            avg_loss += total_loss.numpy()[0]
            total_loss.backward()
            optimizer1.step()
            optimizer2.step()
            lr = optimizer1.get_lr()
            if isinstance(optimizer1._learning_rate, paddle.optimizer.lr.LRScheduler):
                optimizer1._learning_rate.step()
            if isinstance(optimizer2._learning_rate, paddle.optimizer.lr.LRScheduler):
                optimizer2._learning_rate.step()
            model.clear_gradients()

            if iters % log_iters == 0:
                avg_loss /= log_iters
                logger.info('Epoch={}, Step={}/{}, loss={:.4f}, lr={}'.format(
                    (iters - 1) // iters_per_epoch + 1, iters, max_iters, avg_loss, lr))
                if cfg.use_vdl:
                    log_writer.add_scalar('Train/loss', avg_loss, iters)
                    log_writer.add_scalar('Train/lr', lr, iters)
                avg_loss = 0.0
            if (iters % save_interval == 0 or iters == max_iters) and local_rank == 0:
                model.eval()
                total_len = len(val_loader)
                val_iou = 0
                for val_num, val_data in enumerate(val_loader):
                    if len(data) == 3:
                        val_images, val_points, val_masks = val_data
                    else:
                        val_images, val_points = val_data
                        val_masks = None
                    if val_masks is not None:
                        val_batch_size, val_num_points, val_c, val_h, val_w = val_masks.shape
                        val_masks = val_masks.reshape([val_batch_size * val_num_points, val_c, val_h, val_w])
                        
                    val_output = batch_forward(model, val_images, val_masks, val_points, is_train=False)['instances']
                        
                    #val_output = model(val_images, val_points)['instances']
#                     print('max', paddle.max(val_output))
#                     print('output shape', val_output.shape)
                    val_output = nn.functional.interpolate(val_output, mode='bilinear', align_corners=True,
                                               size=val_masks.shape[2:])
                    val_output = val_output > 0.5
                    iter_iou = get_iou(val_masks.numpy(), val_output.numpy())
                    val_iou += iter_iou
                logger.info('mean iou of iter {} is {}'.format(iters, val_iou / total_len))
                if cfg.use_vdl:
                    log_writer.add_scalar('Eval/miou', val_iou / total_len, iters)

                current_save_dir = os.path.join(save_dir,
                                                "iter_{}".format(iters))
                if not os.path.isdir(current_save_dir):
                    os.makedirs(current_save_dir)
                paddle.save(model.state_dict(),
                            os.path.join(current_save_dir, 'model.pdparams'))
                model.train()


def batch_forward(model, image, gt_mask, points, is_train=True):

    orig_image, orig_gt_mask = image.clone(), gt_mask.clone()
    prev_output = paddle.zeros_like(image, dtype='float32')[:, :1, : :]
    
    #last_click_indx = None
    num_iters = random.randint(1, 3)
    if is_train:
        model.eval()
    with paddle.no_grad():
        for click_indx in range(num_iters):

            net_input = paddle.concat([image, prev_output], axis=1)
#             print(4)
            prev_output = model(net_input, points)['instances']
#             print(5)
            prev_output = nn.functional.sigmoid(prev_output)
#             print(6)
            points = get_next_points(prev_output, orig_gt_mask, points, click_indx + 1)
    if is_train:
        model.train()
    net_input = paddle.concat([image, prev_output], axis=1)

    output = model(net_input, points)
    return output



if __name__ == '__main__':
    main()