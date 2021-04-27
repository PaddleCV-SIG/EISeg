import time
import numpy as np

from inference import clicker
from inference.predictor import get_predictor
from util.vis import draw_with_blend_and_clicks
import paddleseg.transforms as T


class InteractiveController:
    def __init__(self, net, predictor_params, update_image_callback, prob_thresh=0.5):
        self.net = net
        self.prob_thresh = prob_thresh
        self.clicker = clicker.Clicker()
        self.states = []
        self.probs_history = []
        self.object_count = 0
        self._result_mask = None

        self.image = None
        self.image_nd = None
        self.predictor = None
        self.update_image_callback = update_image_callback
        self.predictor_params = predictor_params
        self.reset_predictor()

    def set_image(self, image):
        """设置当前标注的图片

        Parameters
        ----------
        image :
            Description of parameter `image`.
        """
        # TODO: 这里normalize需要按照模型改
        input_transform = T.Compose(
            [T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])],
            to_rgb=False,
        )
        self.image = image
        self.image_nd = input_transform(image)[0]

        self._result_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        self.object_count = 0
        self.reset_last_object(update_image=False)
        self.update_image_callback(reset_canvas=True)

    # def change_alpha(self, alpha_blend):
    #     self.
    def add_click(self, x, y, is_positive):
        """添加一个点
        跑推理，保存历史用于undo
        Parameters
        ----------
        x : type
            Description of parameter `x`.
        y : type
            Description of parameter `y`.
        is_positive : bool
            是否是正点
        """
        self.states.append(
                {
                    "clicker": self.clicker.get_state(),
                    "predictor": self.predictor.get_states(),
                }
            )
        click = clicker.Click(is_positive=is_positive, coords=(y, x))
        self.clicker.add_click(click)
        start = time.time()
        pred = self.predictor.get_prediction(self.clicker)
        end = time.time()
        print("cost time", end - start)

        # TODO: 这里为什么一个历史存两个？
        if self.probs_history:
            self.probs_history.append((self.probs_history[-1][0], pred))
        else:
            self.probs_history.append((np.zeros_like(pred), pred))

        self.update_image_callback()

    def undo_click(self):
        """undo一步点击"""
        if not self.states:  # 如果还没点
            return

        prev_state = self.states.pop()
        self.clicker.set_state(prev_state["clicker"])
        self.predictor.set_states(prev_state["predictor"])
        self.probs_history.pop()
        self.update_image_callback()

    def partially_finish_object(self):
        """部分完成
        保存一个mask的状态，这个状态里不存点，看起来比较
        """

        object_prob = self.current_object_prob
        if object_prob is None:
            return

        self.probs_history.append((object_prob, np.zeros_like(object_prob)))
        self.states.append(self.states[-1])

        self.clicker.reset_clicks()
        self.reset_predictor()
        self.update_image_callback()

    def finish_object(self):
        """结束当前物体标注，准备标下一个"""
        object_prob = self.current_object_prob
        if object_prob is None:
            return

        self.object_count += 1  # TODO: 当前是按照第几个目标给结果中的数，改成根据目标编号
        object_mask = object_prob > self.prob_thresh
        self._result_mask[object_mask] = self.object_count
        self.reset_last_object()

    def reset_last_object(self, update_image=True):
        """重置控制器状态

        Parameters
        ----------
        update_image : bool
            Description of parameter `update_image`.

        Returns
        -------
        type
            Description of returned object.

        """

        self.states = []
        self.probs_history = []
        self.clicker.reset_clicks()
        self.reset_predictor()
        if update_image:
            self.update_image_callback()

    def reset_predictor(self, predictor_params=None):
        # TODO: 这里添加换网络支持？
        """重置推理器，可以换权重

        Parameters
        ----------
        predictor_params : 网络权重
            新的网络权重
        """
        if predictor_params is not None:
            self.predictor_params = predictor_params
        self.predictor = get_predictor(self.net, **self.predictor_params)
        if self.image_nd is not None:
            self.predictor.set_input_image(self.image_nd)

    @property
    def current_object_prob(self):
        """获取当前推理标签"""
        if self.probs_history:
            current_prob_total, current_prob_additive = self.probs_history[-1]
            return np.maximum(current_prob_total, current_prob_additive)
        else:
            return None

    @property
    def is_incomplete_mask(self):
        """
        Returns
        -------
        bool
            当前的物体是不是还没标完
        """
        return len(self.probs_history) > 0

    @property
    def result_mask(self):
        return self._result_mask.copy()

    @property
    def img_size(self):
        print(self.image.shape)
        return self.image.shape[1::-1]

    def get_visualization(self, alpha_blend, click_radius):
        if self.image is None:
            return None

        # 1. 画当前没标完的mask
        results_mask_for_vis = self.result_mask
        if self.probs_history:
            results_mask_for_vis[self.current_object_prob > self.prob_thresh] = (
                self.object_count + 1
            )

        vis = draw_with_blend_and_clicks(
            self.image,
            mask=results_mask_for_vis,
            alpha=alpha_blend,
            clicks_list=self.clicker.clicks_list,
            radius=click_radius,
        )

        # 2. 在图片和当前mask的基础上画之前标完的mask
        if self.probs_history:
            total_mask = self.probs_history[-1][0] > self.prob_thresh
            results_mask_for_vis[np.logical_not(total_mask)] = 0
            vis = draw_with_blend_and_clicks(
                vis, mask=results_mask_for_vis, alpha=alpha_blend
            )

        return vis
