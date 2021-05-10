import paddle
import paddle.nn as nn
from paddleseg.models import OCRNet
from paddleseg.models.backbones import HRNet_W32
import paddleseg.transforms as T

import iann.util.util as U
from iann.util.util import SyncBatchNorm
from .dist_map import DistMaps
from .modeling.hrnet_ocr import HighResolutionNet
from .modeling.deeplab_v3 import DeepLabV3Plus
from .modeling.basic_blocks import SepConvHead
from .modeling.shufflenet import ShuffleNetV2


def get_hrnet_model(
    width=48,
    ocr_width=256,
    small=False,
    norm_radius=260,
    use_rgb_conv=True,
    with_aux_output=False,
    cpu_dist_maps=False,
    norm_layer=SyncBatchNorm,
    is_ritm=False,
):
    model = DistMapsHRNetModel(
        feature_extractor=HighResolutionNet(
            width=width,
            ocr_width=ocr_width,
            small=small,
            num_classes=1,
            norm_layer=norm_layer,
        ),
        use_rgb_conv=use_rgb_conv,
        with_aux_output=with_aux_output,
        norm_layer=norm_layer,
        norm_radius=norm_radius,
        cpu_dist_maps=cpu_dist_maps,
        is_ritm=is_ritm,
    )

    return model


class DistMapsHRNetModel(nn.Layer):
    def __init__(
        self,
        feature_extractor,
        use_rgb_conv=True,
        with_aux_output=False,
        norm_layer=nn.BatchNorm2D,
        norm_radius=260,
        cpu_dist_maps=False,
        is_ritm=True,
    ):
        super(DistMapsHRNetModel, self).__init__()
        self.with_aux_output = with_aux_output
        self.is_ritm = is_ritm
        self.normalization = T.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        )

        if use_rgb_conv and self.is_ritm:
            self.rgb_conv = nn.Sequential(
                nn.Conv2D(in_channels=6, out_channels=8, kernel_size=1),
                nn.LeakyReLU(negative_slope=0.2),
                norm_layer(8),
                nn.Conv2D(in_channels=8, out_channels=3, kernel_size=1),
            )
        elif use_rgb_conv and not self.is_ritm:
            self.rgb_conv = nn.Sequential(
                nn.Conv2D(in_channels=5, out_channels=8, kernel_size=1),
                nn.LeakyReLU(negative_slope=0.2),
                norm_layer(8),
                nn.Conv2D(in_channels=8, out_channels=3, kernel_size=1),
            )
        else:
            self.rgb_conv = None

        self.dist_maps = DistMaps(
            norm_radius=norm_radius, spatial_scale=1.0, cpu_mode=cpu_dist_maps
        )
        self.feature_extractor = feature_extractor

    def prepare_input(self, image):
        prev_mask = None

        prev_mask = image[:, 3:, :, :]
        image = image[:, :3, :, :]

        return image, prev_mask

    def get_coord_features(self, image, prev_mask, points):

        coord_features = self.dist_maps(image, points)

        if prev_mask is not None:
            coord_features = paddle.concat((prev_mask, coord_features), axis=1)

        return coord_features

    def forward(self, image, points):
        if not self.is_ritm:
            coord_features = self.dist_maps(image, points)
        else:
            image, prev_mask = self.prepare_input(image)
            coord_features = self.get_coord_features(image, prev_mask, points)

        if self.rgb_conv is not None:

            x = self.rgb_conv(paddle.concat((image, coord_features), axis=1))

        else:
            c1, c2 = paddle.chunk(coord_features, 2, axis=1)
            c3 = paddle.ones_like(c1)
            coord_features = paddle.concat([c1, c2, c3], axis=1)
            x = 0.8 * image * coord_features + 0.2 * image
        feature_extractor_out = self.feature_extractor(x)
        instance_out = feature_extractor_out[0]
        instance_out = nn.functional.interpolate(
            instance_out, size=image.shape[2:], mode="bilinear", align_corners=True
        )
        outputs = {"instances": instance_out}
        if self.with_aux_output:
            instance_aux_out = feature_extractor_out[1]
            instance_aux_out = nn.functional.interpolate(
                instance_aux_out,
                size=image.shape[2:],
                mode="bilinear",
                align_corners=True,
            )
            outputs["instances_aux"] = instance_aux_out
        return outputs

    def load_weights(self, path_to_weights):
        model_state_dict = self.state_dict()
        para_state_dict = paddle.load(path_to_weights)
        keys = model_state_dict.keys()
        num_params_loaded = 0
        for k in keys:
            if k not in para_state_dict:
                print("{} is not in pretrained model".format(k))
            elif list(para_state_dict[k].shape) != list(model_state_dict[k].shape):
                print(
                    "[SKIP] Shape of pretrained params {} doesn't match.(Pretrained: {}, Actual: {})".format(
                        k, para_state_dict[k].shape, model_state_dict[k].shape
                    )
                )
            else:
                model_state_dict[k] = para_state_dict[k]
                num_params_loaded += 1
        self.set_dict(model_state_dict)
        print("load model success")

    def get_trainable_params(self):
        backbone_params = nn.ParameterList()
        other_params = nn.ParameterList()
        other_params_keys = []
        nonbackbone_keywords = [
            "rgb_conv",
            "aux_head",
            "cls_head",
            "conv3x3_ocr",
            "ocr_distri_head",
        ]

        for name, param in self.named_parameters():
            if not param.stop_gradient:
                if any(x in name for x in nonbackbone_keywords):
                    other_params.append(param)
                    other_params_keys.append(name)
                else:
                    backbone_params.append(param)
        print("Nonbackbone params:", sorted(other_params_keys))
        return backbone_params, other_params


def get_deeplab_model(
    backbone="resnet18",
    deeplab_ch=256,
    aspp_dropout=0.5,
    norm_layer=nn.BatchNorm2D,
    backbone_norm_layer=None,
    use_rgb_conv=True,
    cpu_dist_maps=False,
    norm_radius=260,
    is_ritm=False,
):
    model = DistMapsModel(
        feature_extractor=DeepLabV3Plus(
            backbone=backbone,
            ch=deeplab_ch,
            project_dropout=aspp_dropout,
            norm_layer=norm_layer,
            backbone_norm_layer=backbone_norm_layer,
        ),
        head=SepConvHead(
            1,
            in_channels=deeplab_ch,
            mid_channels=deeplab_ch // 2,
            num_layers=2,
            norm_layer=norm_layer,
        ),
        use_rgb_conv=use_rgb_conv,
        norm_layer=norm_layer,
        norm_radius=norm_radius,
        cpu_dist_maps=cpu_dist_maps,
        is_ritm=is_ritm,
    )

    return model


class DistMapsModel(nn.Layer):
    def __init__(
        self,
        feature_extractor,
        head,
        norm_layer=nn.BatchNorm2D,
        use_rgb_conv=True,
        cpu_dist_maps=False,
        norm_radius=260,
        is_ritm=True,
    ):
        super(DistMapsModel, self).__init__()
        self.is_ritm = is_ritm

        if use_rgb_conv and self.is_ritm:
            self.rgb_conv = nn.Sequential(
                nn.Conv2D(in_channels=6, out_channels=8, kernel_size=1),
                nn.LeakyReLU(negative_slope=0.2),
                norm_layer(8),
                nn.Conv2D(in_channels=8, out_channels=3, kernel_size=1),
            )

        elif use_rgb_conv and not self.is_ritm:
            self.rgb_conv = nn.Sequential(
                nn.Conv2D(in_channels=5, out_channels=8, kernel_size=1),
                nn.LeakyReLU(negative_slope=0.2),
                norm_layer(8),
                nn.Conv2D(in_channels=8, out_channels=3, kernel_size=1),
            )
        else:
            self.rgb_conv = None

        self.dist_maps = DistMaps(
            norm_radius=norm_radius, spatial_scale=1.0, cpu_mode=cpu_dist_maps
        )
        self.feature_extractor = feature_extractor
        self.head = head

    def prepare_input(self, image):
        prev_mask = None

        prev_mask = image[:, 3:, :, :]
        image = image[:, :3, :, :]

        return image, prev_mask

    def get_coord_features(self, image, prev_mask, points):

        coord_features = self.dist_maps(image, points)

        if prev_mask is not None:
            coord_features = paddle.concat((prev_mask, coord_features), axis=1)
        return coord_features

    def forward(self, image, points):

        if not self.is_ritm:
            coord_features = self.dist_maps(image, points)
        else:
            image, prev_mask = self.prepare_input(image)
            coord_features = self.get_coord_features(image, prev_mask, points)

        if self.rgb_conv is not None:

            x = self.rgb_conv(paddle.concat((image, coord_features), axis=1))

        if self.rgb_conv is not None:
            x = self.rgb_conv(paddle.concat((image, coord_features), axis=1))
        else:
            c1, c2 = paddle.chunk(coord_features, 2, axis=1)
            c3 = paddle.ones_like(c1)
            coord_features = paddle.concat((c1, c2, c3), axis=1)
            x = 0.8 * image * coord_features + 0.2 * image

        backbone_features = self.feature_extractor(x)
        instance_out = self.head(backbone_features[0])
        instance_out = nn.functional.interpolate(
            instance_out, size=image.shape[2:], mode="bilinear", align_corners=True
        )

        return {"instances": instance_out}

    def load_weights(self, path_to_weights):
        model_state_dict = self.state_dict()
        para_state_dict = paddle.load(path_to_weights)
        keys = model_state_dict.keys()
        num_params_loaded = 0
        for k in keys:
            if k not in para_state_dict:
                print("{} is not in pretrained model".format(k))
            elif list(para_state_dict[k].shape) != list(model_state_dict[k].shape):
                print(
                    "[SKIP] Shape of pretrained params {} doesn't match.(Pretrained: {}, Actual: {})".format(
                        k, para_state_dict[k].shape, model_state_dict[k].shape
                    )
                )
            else:
                model_state_dict[k] = para_state_dict[k]
                num_params_loaded += 1
        self.set_dict(model_state_dict)
        print("load model success")

    def get_trainable_params(self):
        backbone_params = nn.ParameterList()
        other_params = nn.ParameterList()
        other_params_keys = []

        for name, param in self.named_parameters():
            if not param.stop_gradient:
                if "backbone" in name:
                    backbone_params.append(param)
                else:
                    other_params.append(param)
                    other_params_keys.append(name)
        print("Nonbackbone params:", sorted(other_params_keys))
        return backbone_params, other_params


def get_shufflenet_model(
    norm_radius=260,
    use_rgb_conv=True,
    cpu_dist_maps=True,
    norm_layer=nn.BatchNorm2D,
    is_ritm=False,
):
    model = ShuffleNetV2Model(
        feature_extractor=ShuffleNetV2(num_classes=1),
        use_rgb_conv=use_rgb_conv,
        norm_layer=norm_layer,
        norm_radius=norm_radius,
        cpu_dist_maps=cpu_dist_maps,
        is_ritm=is_ritm,
    )

    return model


class ShuffleNetV2Model(nn.Layer):
    def __init__(
        self,
        feature_extractor,
        use_rgb_conv=True,
        norm_layer=nn.BatchNorm2D,
        norm_radius=260,
        cpu_dist_maps=False,
        is_ritm=True,
    ):
        super(ShuffleNetV2Model, self).__init__()
        self.is_ritm = is_ritm
        self.normalization = T.Normalize(
            mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        )

        if use_rgb_conv and self.is_ritm:
            self.rgb_conv = nn.Sequential(
                nn.Conv2D(in_channels=6, out_channels=8, kernel_size=1),
                nn.LeakyReLU(negative_slope=0.2),
                norm_layer(8),
                nn.Conv2D(in_channels=8, out_channels=3, kernel_size=1),
            )
        elif use_rgb_conv and not self.is_ritm:
            self.rgb_conv = nn.Sequential(
                nn.Conv2D(in_channels=5, out_channels=8, kernel_size=1),
                nn.LeakyReLU(negative_slope=0.2),
                norm_layer(8),
                nn.Conv2D(in_channels=8, out_channels=3, kernel_size=1),
            )
        else:
            self.rgb_conv = None

        self.dist_maps = DistMaps(
            norm_radius=norm_radius, spatial_scale=1.0, cpu_mode=cpu_dist_maps
        )
        self.feature_extractor = feature_extractor

    def prepare_input(self, image):
        prev_mask = None
        prev_mask = image[:, 3:, :, :]
        image = image[:, :3, :, :]

        return image, prev_mask

    def get_coord_features(self, image, prev_mask, points):

        coord_features = self.dist_maps(image, points)

        if prev_mask is not None:
            coord_features = paddle.concat((prev_mask, coord_features), axis=1)

        return coord_features

    def forward(self, image, points):
        if not self.is_ritm:
            coord_features = self.dist_maps(image, points)
        else:
            image, prev_mask = self.prepare_input(image)
            coord_features = self.get_coord_features(image, prev_mask, points)

        if self.rgb_conv is not None:
            x = self.rgb_conv(paddle.concat((image, coord_features), axis=1))
        else:
            c1, c2 = paddle.chunk(coord_features, 2, axis=1)
            c3 = paddle.ones_like(c1)
            coord_features = paddle.concat([c1, c2, c3], axis=1)
            x = 0.8 * image * coord_features + 0.2 * image

        feature_extractor_out = self.feature_extractor(x)
        instance_out = feature_extractor_out[0]
        instance_out = nn.functional.interpolate(
            instance_out, size=image.shape[2:], mode="bilinear", align_corners=True
        )
        outputs = {"instances": instance_out}
        # if self.with_aux_output:
        #     instance_aux_out = feature_extractor_out[1]
        #     instance_aux_out = nn.functional.interpolate(instance_aux_out, size=image.shape[2:],
        #                                                  mode='bilinear', align_corners=True)
        #     outputs['instances_aux'] = instance_aux_out
        return outputs

    def load_weights(self, path_to_weights):
        model_state_dict = self.state_dict()
        para_state_dict = paddle.load(path_to_weights)
        keys = model_state_dict.keys()
        num_params_loaded = 0

        for k in keys:
            if k not in para_state_dict:
                print("{} is not in pretrained model".format(k))
            elif list(para_state_dict[k].shape) != list(model_state_dict[k].shape):
                print(
                    "[SKIP] Shape of pretrained params {} doesn't match.(Pretrained: {}, Actual: {})".format(
                        k, para_state_dict[k].shape, model_state_dict[k].shape
                    )
                )
            else:
                model_state_dict[k] = para_state_dict[k]
                num_params_loaded += 1

        self.set_dict(model_state_dict)
        print("load model success")

    def get_trainable_params(self):
        backbone_params = nn.ParameterList()
        other_params = nn.ParameterList()
        other_params_keys = []
        nonbackbone_keywords = ["rgb_conv", "head"]
        for name, param in self.named_parameters():
            if not param.stop_gradient:
                if any(x in name for x in nonbackbone_keywords):
                    other_params.append(param)
                    other_params_keys.append(name)
                else:
                    backbone_params.append(param)
        print("Nonbackbone params:", sorted(other_params_keys))
        return backbone_params, other_params
