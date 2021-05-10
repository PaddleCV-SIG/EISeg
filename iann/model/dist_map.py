import paddle
import paddle.nn as nn
import numpy as np

from iann.cython_dict import get_dist_maps


class DistMaps(nn.Layer):
    def __init__(self, norm_radius, spatial_scale=1.0, cpu_mode=True):
        super(DistMaps, self).__init__()
        self.spatial_scale = spatial_scale
        self.norm_radius = norm_radius
        self.cpu_mode = cpu_mode

    def get_coord_features(self, points, batchsize, rows, cols):
        if self.cpu_mode:
            coords = []
            for i in range(batchsize):
                norm_delimeter = self.spatial_scale * self.norm_radius
                middle = get_dist_maps(
                    points[i].numpy().astype("float32"), rows, cols, norm_delimeter
                )
                coords.append(middle)
            coords = paddle.to_tensor(np.stack(coords, axis=0)).astype("float32")

        else:
            num_points = points.shape[1] // 2
            points = points.reshape([-1, 2])

            invalid_points = paddle.max(points, axis=1, keepdim=False)[0] < 0
            row_array = paddle.arange(start=0, end=rows, step=1, dtype="float32")
            col_array = paddle.arange(start=0, end=cols, step=1, dtype="float32")
            coord_rows, coord_cols = paddle.meshgrid(row_array, col_array)

            coords = paddle.unsqueeze(
                paddle.stack([coord_rows, coord_cols], axis=0), axis=0
            ).tile([points.shape[0], 1, 1, 1])
            add_xy = (points * self.spatial_scale).reshape(
                [points.shape[0], points.shape[1], 1, 1]
            )
            coords = coords - add_xy
            coords = coords / (self.norm_radius * self.spatial_scale)
            coords = coords * coords
            coords[:, 0] += coords[:, 1]
            coords = coords[:, :1]
            coords[invalid_points, :, :, :] = 1e6
            coords = coords.reshape([-1, num_points, 1, rows, cols])
            coords = paddle.min(coords, axis=1)
            coords = coords.reshape([-1, 2, rows, cols])

        coords = paddle.tanh(paddle.sqrt(coords) * 2)
        return coords

    def forward(self, x, coords):
        return self.get_coord_features(coords, x.shape[0], x.shape[2], x.shape[3])
