import paddle
import paddle.nn as nn
import paddle.nn.functional as F

class Bottleneck(nn.Layer):
    expansion = 4

    def __init__(self, inplanes, planes, stride=1):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Conv2D(inplanes, planes, kernel_size=1, bias_attr=False)
        self.bn1 = nn.BatchNorm2D(planes)
        self.conv2 = nn.Conv2D(planes, planes, kernel_size=3, stride=stride,
                               padding=1, bias_attr=False)
        self.bn2 = nn.BatchNorm2D(planes)
        self.conv3 = nn.Conv2D(planes, planes * 2, kernel_size=1, bias_attr=False)
        self.bn3 = nn.BatchNorm2D(planes * 2)
        self.relu = nn.ReLU()
        self.downsample = nn.Sequential(
            nn.Conv2D(inplanes, planes * 2,
                      kernel_size=1, stride=stride, bias_attr=False),
            nn.BatchNorm2D(planes * 2))
        self.stride = stride

    def forward(self, x):
        residual = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv3(out)
        out = self.bn3(out)

        if self.downsample is not None:
            residual = self.downsample(x)

        out += residual
        out = self.relu(out)

        return out

class FineNet(nn.Layer):
    def __init__(self, inplane, num_class):
        super(FineNet, self).__init__()

        self.atrous1 = nn.Sequential(
            nn.Conv2D(in_channels=inplane, out_channels=32, kernel_size=3, padding=1, bias_attr=False),
            nn.PReLU(),
            nn.BatchNorm2D(32),
            nn.Conv2D(in_channels=32, out_channels=16, kernel_size=1, bias_attr=False),
            nn.PReLU(),
            nn.BatchNorm2D(16))

        self.atrous2 = nn.Sequential(nn.Conv2D(in_channels=inplane, out_channels=32, kernel_size=3, padding=2, dilation=2, bias_attr=False),
            nn.PReLU(),
            nn.BatchNorm2D(32),
            nn.Conv2D(in_channels=32, out_channels=16, kernel_size=1, bias_attr=False),
            nn.PReLU(),
            nn.BatchNorm2D(16))

        self.atrous3 = nn.Sequential(nn.Conv2D(in_channels=inplane, out_channels=32, kernel_size=3, padding=3, dilation=3, bias_attr=False),
            nn.PReLU(),
            nn.BatchNorm2D(32),
            nn.Conv2D(in_channels=32, out_channels=16, kernel_size=1, bias_attr=False),
            nn.PReLU(),
            nn.BatchNorm2D(16))

        self.final_predict = self._predict(3 * 16, num_class)

    def _predict(self, input_channel, num_class):
        layers = []
        layers.append(Bottleneck(input_channel, 32))
        layers.append(nn.Conv2D(64, num_class, kernel_size=3, stride=1, padding=1, bias_attr=False))
        layers.append(nn.BatchNorm2D(num_class))
        return nn.Sequential(*layers)

    def forward(self, inputs, heatmap, coarse, edge=None):
        inputs = F.interpolate(inputs, size=paddle.shape(coarse)[2:])
        heatmap = F.interpolate(heatmap, size=paddle.shape(coarse)[2:])
        coarse = F.sigmoid(coarse)
        if edge is not None:
            edge = F.sigmoid(edge)
            fine_input = paddle.concat([inputs, heatmap,coarse, edge], axis=1)
        else:
            fine_input = paddle.concat([inputs, heatmap,coarse], axis=1)
            
        atrous1_out = self.atrous1(fine_input)
        atrous2_out = self.atrous2(fine_input)
        atrous3_out = self.atrous3(fine_input)

        fine_out = self.final_predict(paddle.concat([atrous1_out, atrous2_out, atrous3_out], axis=1))

        return fine_out