import cv2
import paddle
import paddle.nn as nn
import numpy as np
from datetime import timedelta
from pathlib import Path
import random

from iann.data.berkeley import BerkeleyDataset
from iann.data.grabcut import GrabCutDataset
from iann.data.davis import DavisDataset
from iann.data.sbd import SBDEvaluationDataset

from albumentations import ImageOnlyTransform, DualTransform
from albumentations.augmentations import functional as Func


def toint(seq):
    for idx in range(len(seq)):
        try:
            seq[idx] = int(seq[idx])
        except ValueError:
            pass
    return seq


# TODO: 精简这里的函数，只留推理的


def SyncBatchNorm(*args, **kwargs):
    """In cpu environment nn.SyncBatchNorm does not have kernel so use nn.BatchNorm2D instead"""
    if paddle.distributed.ParallelEnv().nranks == 1:
        return nn.BatchNorm2D(*args, **kwargs)
    else:
        return nn.SyncBatchNorm(*args, **kwargs)


def get_unique_labels(mask):
    return np.nonzero(np.bincount(mask.flatten() + 1))[0] - 1


def get_bbox_from_mask(mask):
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    return rmin, rmax, cmin, cmax


def expand_bbox(bbox, expand_ratio, min_crop_size=None):
    rmin, rmax, cmin, cmax = bbox
    rcenter = 0.5 * (rmin + rmax)
    ccenter = 0.5 * (cmin + cmax)
    height = expand_ratio * (rmax - rmin + 1)
    width = expand_ratio * (cmax - cmin + 1)
    if min_crop_size is not None:
        height = max(height, min_crop_size)
        width = max(width, min_crop_size)

    rmin = int(round(rcenter - 0.5 * height))
    rmax = int(round(rcenter + 0.5 * height))
    cmin = int(round(ccenter - 0.5 * width))
    cmax = int(round(ccenter + 0.5 * width))

    return rmin, rmax, cmin, cmax


def clamp_bbox(bbox, rmin, rmax, cmin, cmax):
    return (
        max(rmin, bbox[0]),
        min(rmax, bbox[1]),
        max(cmin, bbox[2]),
        min(cmax, bbox[3]),
    )


def get_bbox_iou(b1, b2):
    h_iou = get_segments_iou(b1[:2], b2[:2])
    w_iou = get_segments_iou(b1[2:4], b2[2:4])
    return h_iou * w_iou


def get_segments_iou(s1, s2):
    a, b = s1
    c, d = s2
    intersection = max(0, min(b, d) - max(a, c) + 1)
    union = max(1e-6, max(b, d) - min(a, c) + 1)
    return intersection / union


def get_dims_with_exclusion(dim, exclude=None):
    dims = list(range(dim))
    if exclude is not None:
        dims.remove(exclude)
    return dims


def get_iou(gt_mask, pred_mask, ignore_label=-1):
    ignore_gt_mask_inv = gt_mask != ignore_label
    obj_gt_mask = gt_mask == 1

    intersection = np.logical_and(
        np.logical_and(pred_mask, obj_gt_mask), ignore_gt_mask_inv
    ).sum()

    union = np.logical_and(
        np.logical_or(pred_mask, obj_gt_mask), ignore_gt_mask_inv
    ).sum()

    return intersection / union


def get_dataset(dataset_name, cfg):
    if dataset_name == "GrabCut":
        dataset = GrabCutDataset("./datasets/GrabCut")
    elif dataset_name == "Berkeley":
        dataset = BerkeleyDataset("./datasets/Berkeley")
    elif dataset_name == "DAVIS":
        dataset = DavisDataset("./datasets/DAVIS")
    elif dataset_name == "COCO_MVal":
        dataset = DavisDataset("./datasets/COCO_MVal")
    elif dataset_name == "SBD":
        dataset = SBDEvaluationDataset("./datasets/SBD")
    elif dataset_name == "SBD_Train":
        dataset = SBDEvaluationDataset("./datasets/SBD", split="train")
    else:
        dataset = None

    return dataset


def get_time_metrics(all_ious, elapsed_time):
    n_images = len(all_ious)
    n_clicks = sum(map(len, all_ious))

    mean_spc = elapsed_time / n_clicks
    mean_spi = elapsed_time / n_images

    return mean_spc, mean_spi


def compute_noc_metric(all_ious, iou_thrs, max_clicks=20):
    def _get_noc(iou_arr, iou_thr):
        vals = iou_arr >= iou_thr
        return np.argmax(vals) + 1 if np.any(vals) else max_clicks

    noc_list = []
    over_max_list = []
    for iou_thr in iou_thrs:
        scores_arr = np.array(
            [_get_noc(iou_arr, iou_thr) for iou_arr in all_ious], dtype=np.int
        )

        score = scores_arr.mean()
        over_max = (scores_arr == max_clicks).sum()

        noc_list.append(score)
        over_max_list.append(over_max)

    return noc_list, over_max_list


def get_results_table(
    noc_list,
    over_max_list,
    brs_type,
    dataset_name,
    mean_spc,
    elapsed_time,
    n_clicks=20,
    model_name=None,
):
    table_header = (
        f'|{"BRS Type":^13}|{"Dataset":^11}|'
        f'{"NoC@80%":^9}|{"NoC@85%":^9}|{"NoC@90%":^9}|'
        f'{">="+str(n_clicks)+"@85%":^9}|{">="+str(n_clicks)+"@90%":^9}|'
        f'{"SPC,s":^7}|{"Time":^9}|'
    )
    row_width = len(table_header)

    header = f"Eval results for model: {model_name}\n" if model_name is not None else ""
    header += "-" * row_width + "\n"
    header += table_header + "\n" + "-" * row_width

    eval_time = str(timedelta(seconds=int(elapsed_time)))
    table_row = f"|{brs_type:^13}|{dataset_name:^11}|"
    table_row += f"{noc_list[0]:^9.2f}|"
    table_row += f"{noc_list[1]:^9.2f}|" if len(noc_list) > 1 else f'{"?":^9}|'
    table_row += f"{noc_list[2]:^9.2f}|" if len(noc_list) > 2 else f'{"?":^9}|'
    table_row += f"{over_max_list[1]:^9}|" if len(noc_list) > 1 else f'{"?":^9}|'
    table_row += f"{over_max_list[2]:^9}|" if len(noc_list) > 2 else f'{"?":^9}|'
    table_row += f"{mean_spc:^7.3f}|{eval_time:^9}|"

    return header, table_row


def get_eval_exp_name(args):
    if ":" in args.checkpoint:
        model_name, checkpoint_prefix = args.checkpoint.split(":")
        model_name = model_name.split("/")[-1]

        return f"{model_name}_{checkpoint_prefix}"
    else:
        return Path(args.checkpoint).stem


def get_next_points(pred, gt, points, click_indx, pred_thresh=0.49):
    assert click_indx > 0
    pred = pred.numpy()[:, 0, :, :]
    gt = gt.numpy()[:, 0, :, :] > 0.5

    fn_mask = np.logical_and(gt, pred < pred_thresh)
    fp_mask = np.logical_and(np.logical_not(gt), pred > pred_thresh)

    fn_mask = np.pad(fn_mask, ((0, 0), (1, 1), (1, 1)), "constant").astype(np.uint8)
    fp_mask = np.pad(fp_mask, ((0, 0), (1, 1), (1, 1)), "constant").astype(np.uint8)
    num_points = points.shape[1] // 2
    points = points.clone()

    for bindx in range(fn_mask.shape[0]):
        fn_mask_dt = cv2.distanceTransform(fn_mask[bindx], cv2.DIST_L2, 5)[1:-1, 1:-1]
        fp_mask_dt = cv2.distanceTransform(fp_mask[bindx], cv2.DIST_L2, 5)[1:-1, 1:-1]

        fn_max_dist = np.max(fn_mask_dt)
        fp_max_dist = np.max(fp_mask_dt)

        is_positive = fn_max_dist > fp_max_dist
        dt = fn_mask_dt if is_positive else fp_mask_dt
        inner_mask = dt > max(fn_max_dist, fp_max_dist) / 2.0
        indices = np.argwhere(inner_mask)
        if len(indices) > 0:
            coords = indices[np.random.randint(0, len(indices))]
            if is_positive:
                points[bindx, num_points - click_indx, 0] = float(coords[0])
                points[bindx, num_points - click_indx, 1] = float(coords[1])
                # points[bindx, num_points - click_indx, 2] = float(click_indx)
            else:
                points[bindx, 2 * num_points - click_indx, 0] = float(coords[0])
                points[bindx, 2 * num_points - click_indx, 1] = float(coords[1])
                # points[bindx, 2 * num_points - click_indx, 2] = float(click_indx)

    return points


class UniformRandomResize(DualTransform):
    def __init__(
        self,
        scale_range=(0.9, 1.1),
        interpolation=cv2.INTER_LINEAR,
        always_apply=False,
        p=1,
    ):
        super().__init__(always_apply, p)
        self.scale_range = scale_range
        self.interpolation = interpolation

    def get_params_dependent_on_targets(self, params):
        scale = random.uniform(*self.scale_range)
        height = int(round(params["image"].shape[0] * scale))
        width = int(round(params["image"].shape[1] * scale))
        return {"new_height": height, "new_width": width}

    def apply(
        self, img, new_height=0, new_width=0, interpolation=cv2.INTER_LINEAR, **params
    ):
        return Func.resize(
            img, height=new_height, width=new_width, interpolation=interpolation
        )

    def apply_to_keypoint(self, keypoint, new_height=0, new_width=0, **params):
        scale_x = new_width / params["cols"]
        scale_y = new_height / params["rows"]
        return Func.keypoint_scale(keypoint, scale_x, scale_y)

    def get_transform_init_args_names(self):
        return "scale_range", "interpolation"

    @property
    def targets_as_params(self):
        return ["image"]
