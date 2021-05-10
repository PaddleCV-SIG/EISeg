import numpy as np
import paddle
import paddle.nn as nn
import paddle.nn.functional as F
import iann.util.util as U


class NormalizedFocalLossSigmoid(nn.Layer):
    def __init__(self, axis=-1, alpha=0.25, gamma=2,
                 from_logits=False, batch_axis=0,
                 weight=None, size_average=True, detach_delimeter=True,
                 eps=1e-12, scale=1.0,
                 ignore_label=-1):
        super(NormalizedFocalLossSigmoid, self).__init__()
        self._axis = axis
        self._alpha = alpha
        self._gamma = gamma
        self._ignore_label = ignore_label
        self._weight = weight if weight is not None else 1.0
        self._batch_axis = batch_axis

        self._scale = scale
        self._from_logits = from_logits
        self._eps = eps
        self._size_average = size_average
        self._detach_delimeter = detach_delimeter
        self._k_sum = 0

    def forward(self, pred, label, sample_weight=None):
        one_hot = label > 0
        sample_weight = label != self._ignore_label
        sample_weight = sample_weight.astype('float32')

        if not self._from_logits:
            pred = F.sigmoid(pred)

        x = sample_weight * 0.5
        y = (1 - self._alpha) * sample_weight
        alpha = paddle.where(one_hot, x, y)
        pt = paddle.where(one_hot, pred, 1 - pred)
        sample_weight = sample_weight.astype('bool')
        pt = paddle.where(sample_weight, pt, paddle.ones_like(pt))
        beta = (1 - pt) ** self._gamma
        sample_weight = sample_weight.astype('float32')
        sw_sum = paddle.sum(sample_weight, axis=(-2, -1), keepdim=True)
        beta_sum = paddle.sum(beta, axis=(-2, -1), keepdim=True)
        mult = sw_sum / (beta_sum + self._eps)

        if self._detach_delimeter:
            mult = mult.detach()

        beta = beta * mult
        ignore_area = paddle.sum((label == self._ignore_label).astype('float32'), axis=tuple(range(1, len(label.shape)))).numpy()
        sample_mult = paddle.mean(mult, axis=tuple(range(1, len(mult.shape)))).numpy()
        if np.any(ignore_area == 0):
            self._k_sum = 0.9 * self._k_sum + 0.1 * sample_mult[ignore_area == 0].mean()
        loss = -alpha * beta * paddle.log(paddle.mean(pt + self._eps))
        loss = self._weight * (loss * sample_weight)

        if self._size_average:
            bsum = paddle.sum(sample_weight, axis=U.get_dims_with_exclusion(len(sample_weight.shape), self._batch_axis))
            loss = paddle.sum(loss, axis=U.get_dims_with_exclusion(len(loss.shape), self._batch_axis)) / (
                    bsum + self._eps)
        else:
            loss = paddle.sum(loss, axis=U.get_dims_with_exclusion(len(loss.shape), self._batch_axis))

        return self._scale * loss


class FocalLoss(nn.Layer):
    def __init__(self, axis=-1, alpha=0.25, gamma=2,
                 from_logits=False, batch_axis=0,
                 weight=None, num_class=None,
                 eps=1e-9, size_average=True, scale=1.0):
        super(FocalLoss, self).__init__()
        self._axis = axis
        self._alpha = alpha
        self._gamma = gamma
        self._weight = weight if weight is not None else 1.0
        self._batch_axis = batch_axis

        self._scale = scale
        self._num_class = num_class
        self._from_logits = from_logits
        self._eps = eps
        self._size_average = size_average

    def forward(self, pred, label, sample_weight=None):
        if not self._from_logits:
            pred = F.sigmoid(pred)

        one_hot = label > 0
        pt = paddle.where(one_hot, pred, 1 - pred)
        t = label != -1
        alpha = paddle.where(one_hot, self._alpha * t, (1 - self._alpha) * t)
        beta = (1 - pt) ** self._gamma

        loss = -alpha * beta * paddle.log(paddle.min(pt + self._eps, paddle.ones(1, dtype='float32')))
        sample_weight = label != -1

        loss = self._weight * (loss * sample_weight)

        if self._size_average:
            tsum = paddle.sum(label == 1, axis=U.get_dims_with_exclusion(len(label.shape), self._batch_axis))
            loss = paddle.sum(loss, axis=U.get_dims_with_exclusion(len(loss.shape), self._batch_axis)) / (
                    tsum + self._eps)
        else:
            loss = paddle.sum(loss, axis=U.get_dims_with_exclusion(len(loss.shape), self._batch_axis))

        return self._scale * loss


class SigmoidBinaryCrossEntropyLoss(nn.Layer):
    def __init__(self, from_sigmoid=False, weight=None, batch_axis=0, ignore_label=-1):
        super(SigmoidBinaryCrossEntropyLoss, self).__init__()
        self._from_sigmoid = from_sigmoid
        self._ignore_label = ignore_label
        self._weight = weight if weight is not None else 1.0
        self._batch_axis = batch_axis

    def forward(self, pred, label):
        label = label.reshape(pred.shape)
        sample_weight = label != self._ignore_label
        label = paddle.where(sample_weight, label, paddle.zeros_like(label))

        if not self._from_sigmoid:
            loss = F.relu(pred) - pred * label + F.softplus(-paddle.abs(pred))
        else:
            eps = 1e-12
            loss = -(paddle.log(pred + eps) * label + paddle.log(1. - pred + eps) * (1. - label))
        loss = self._weight * (loss * sample_weight)
        return paddle.mean(loss, axis=U.get_dims_with_exclusion(len(loss.shape), self._batch_axis))

