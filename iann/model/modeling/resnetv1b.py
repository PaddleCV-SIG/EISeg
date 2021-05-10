import paddle
import paddle.nn as nn

from iann.util.util import SyncBatchNorm


def is_bn(norm_layer, planes):
    if isinstance(norm_layer, nn.BatchNorm2D):
        bn = norm_layer(planes, use_global_stats=True)
    else:
        bn = norm_layer(planes)
    return bn


class BasicBlockV1b(nn.Layer):
    expansion = 1

    def __init__(
        self,
        inplanes,
        planes,
        stride=1,
        dilation=1,
        downsample=None,
        previous_dilation=1,
        norm_layer=SyncBatchNorm,
    ):
        super(BasicBlockV1b, self).__init__()
        self.conv1 = nn.Conv2D(
            inplanes,
            planes,
            kernel_size=3,
            stride=stride,
            padding=dilation,
            bias_attr=False,
        )
        self.bn1 = is_bn(norm_layer, planes)
        self.conv2 = nn.Conv2D(
            planes,
            planes,
            kernel_size=3,
            stride=1,
            padding=previous_dilation,
            dilation=previous_dilation,
            bias_attr=False,
        )
        self.bn2 = is_bn(norm_layer, planes)
        self.relu = nn.ReLU()
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            residual = self.downsample(x)
        out = out + residual
        out = self.relu(out)
        return out


class BottleneckV1b(nn.Layer):
    expansion = 4

    def __init__(
        self,
        inplanes,
        planes,
        stride=1,
        dilation=1,
        downsample=None,
        previous_dilation=1,
        norm_layer=SyncBatchNorm,
        use_global_stats=True,
    ):
        super(BottleneckV1b, self).__init__()
        self.conv1 = nn.Conv2D(inplanes, planes, kernel_size=1, bias_attr=False)
        self.bn1 = is_bn(norm_layer, planes)

        self.conv2 = nn.Conv2D(
            planes,
            planes,
            kernel_size=3,
            stride=stride,
            padding=dilation,
            dilation=dilation,
            bias_attr=False,
        )
        self.bn2 = is_bn(norm_layer, planes)

        self.conv3 = nn.Conv2D(
            planes, planes * self.expansion, kernel_size=1, bias_attr=False
        )
        self.bn3 = is_bn(norm_layer, planes * self.expansion)

        self.relu = nn.ReLU()
        self.downsample = downsample
        self.stride = stride

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)
        out = self.relu(out)

        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out = out + residual
        out = self.relu(out)

        return out
