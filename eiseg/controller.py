import time
import json
import paddle
import numpy as np
import paddleseg.transforms as T
from skimage.measure import label

from inference import clicker
from inference.predictor import get_predictor
from util.vis import draw_with_blend_and_clicks
from util import MODELS, LabelList

# DEBUG:
import matplotlib.pyplot as plt


# TODO: 研究标签从0开始的时候怎么处理
class InteractiveController:
    def __init__(
        self,
        update_image_callback,
        predictor_params: dict = None,
        prob_thresh: float = 0.5,
    ):
        self.update_image_callback = update_image_callback  # TODO: 改成返回image，不调用函数
        self.predictor_params = predictor_params
        self.prob_thresh = prob_thresh
        self.model = None
        self.image = None
        self.predictor = None
        self.clicker = clicker.Clicker()
        self.states = []
        self.probs_history = []

        # 用于redo
        self.undo_states = []
        self.undo_probs_history = []

        self.curr_label_number = 0
        self._result_mask = None
        self.labelList = LabelList()
        self.filterLargestCC = False

        self.addLabel = self.labelList.add


    def setModel(self, modelName: str):
        if not isinstance(modelName, str):
            return False, "模型名应为str类型"
        try:
            self.model = MODELS[modelName]()
        except KeyError as e:
            return False, str(e)
        return True, "模型设置成功"


    def setParam(self, paramPath: str):
        if not self.modelSet:
            return False, "模型未设置，请先设置模型"
        try:
            self.model.load_param(paramPath)
        except Exception as e:
            return False, str(e)
        return True, "权重设置成功"


    def setImage(self, image: np.array):
        self.image = image
        self._result_mask = np.zeros(image.shape[:2], dtype=np.uint8)
        self.reset_last_object(update_image=False)
        self.update_image_callback(reset_canvas=True)


    def setLabelList(self, labelList: json):
        """
            {
                "idx" : int         (like 0, 1, 2···)
                "name" : str        (like "car", "airplan"···)
                "color" : list      (like [255, 0, 0]···)
            }
        """
        self.labelList.clear()
        labels = json.loads(labelList)
        for lab in labels:
            self.labelList.add(lab["id"], lab["name"], lab["color"])


    def addClick(self, x: int, y: int, is_positive: bool):
        """
            添加一个点跑推理，保存历史用于undo
            Parameters
                x(int): 点击点的x坐标.
                y(int): 点击点的y坐标.
            is_positive : bool
                是否是正点
            Returns
                bool: 点击是否成功添加
        """
        # 1. 确定可以点
        if not self.inImage(x, y):
            return False, "点击越界"
        if not self.modelSet:
            return False, "模型未设置"
        if not self.paramSet:
            return False, "参数未设置"
        if not self.imageSet:
            return False, "图像未设置"

        if len(self.states) == 0:  # 保存一个空状态
            self.states.append(
                {
                    "clicker": self.clicker.get_state(),
                    "predictor": self.predictor.get_state(),
                }
            )

        # 2. 添加点击，跑推理
        click = clicker.Click(is_positive=is_positive, coords=(y, x))
        self.clicker.add_click(click)
        start = time.time()
        pred = self.predictor.get_prediction(self.clicker)
        end = time.time()
        print("cost time", end - start)

        # 3. 保存状态
        self.states.append(
            {
                "clicker": self.clicker.get_state(),
                "predictor": self.predictor.get_state(),
            }
        )
        if self.probs_history:
            self.probs_history.append((self.probs_history[-1][1], pred))
        else:
            self.probs_history.append((np.zeros_like(pred), pred))

        # 点击之后就不能接着之前的历史redo了
        self.undo_states = []
        self.undo_probs_history = []
        self.update_image_callback()


    def undo_click(self):
        """
            undo一步点击
        """
        if len(self.states) <= 1:  # == 1就只剩下一个空状态了，不用再退
            return
        self.undo_states.append(self.states.pop())
        self.clicker.set_state(self.states[-1]["clicker"])
        self.predictor.set_state(self.states[-1]["predictor"])
        self.undo_probs_history.append(self.probs_history.pop())
        if not self.probs_history:
            self.reset_init_mask()
        self.update_image_callback()


    def redo_click(self):
        """
            redo一步点击
        """
        if len(self.undo_states) == 0:  # 如果还没撤销过
            return
        if len(self.undo_probs_history) >= 1:
            next_state = self.undo_states.pop()
            self.states.append(next_state)
            self.clicker.set_state(next_state["clicker"])
            self.predictor.set_state(next_state["predictor"])
            self.probs_history.append(self.undo_probs_history.pop())
            self.update_image_callback()


    def finishObject(self):
        """
            结束当前物体标注，准备标下一个
        """
        object_prob = self.current_object_prob
        if object_prob is None:
            return None
        object_mask = object_prob > self.prob_thresh
        if self.filterLargestCC:
            object_mask = self.getLargestCC(object_mask)
        print("curr_label_number:", self.curr_label_number)
        self._result_mask[object_mask] = self.curr_label_number
        self.reset_last_object()
        return object_mask


    def change_label_num(self, number):
        """
            修改当前标签的编号
                1. 如果当前有标注到一半的目标，改mask
                2. 如果没有，下一个目标是这个数
            Parameters
                number(int): 换成目标的编号
        """
        assert isinstance(number, int), "标签编号应为整数"
        self.curr_label_number = number
        if self.is_incomplete_mask:
            pass
            # TODO: 改当前mask的编号


    def reset_last_object(self, update_image=True):
        """
            重置控制器状态
            Parameters
                update_image(bool): 是否更新图像
        """
        self.states = []
        self.probs_history = []
        self.undo_states = []
        self.undo_probs_history = []
        # self.current_object_prob = None
        self.clicker.reset_clicks()
        self.reset_predictor()
        self.reset_init_mask()
        if update_image:
            self.update_image_callback()


    def reset_predictor(self, predictor_params=None):
        """
            重置推理器，可以换推理配置
            Parameters
                predictor_params(dict): 推理配置
        """
        if predictor_params is not None:
            self.predictor_params = predictor_params
        self.predictor = get_predictor(self.model.model, **self.predictor_params)
        if self.image is not None:
            self.predictor.set_input_image(self.image)


    def reset_init_mask(self):
        self.clicker.click_indx_offset = 0


    def getLargestCC(self, mask):
        # TODO: 从所有正点开始找，漫水到所有包括正点的联通块
        mask = label(mask)
        if mask.max() == 0:
            return mask
        mask = mask == np.argmax(np.bincount(mask.flat)[1:]) + 1
        return mask


    def get_visualization(self, alpha_blend: float, click_radius: int):
        if self.image is None:
            return None
        # 1. 正在标注的mask
        # results_mask_for_vis = self.result_mask  # 加入之前标完的mask
        results_mask_for_vis = np.zeros_like(self.result_mask)
        results_mask_for_vis *= self.curr_label_number
        if self.probs_history:
            results_mask_for_vis[
                self.current_object_prob > self.prob_thresh
            ] = self.curr_label_number
        if self.filterLargestCC:
            results_mask_for_vis = self.getLargestCC(results_mask_for_vis)
        vis = draw_with_blend_and_clicks(
            self.image,
            mask=results_mask_for_vis,
            alpha=alpha_blend,
            clicks_list=self.clicker.clicks_list,
            radius=click_radius,
            palette=self.palette,
        )
        return vis


    def inImage(self, x: int, y: int):
        s = self.image.shape
        if x < 0 or y < 0 or x >= s[1] or y >= s[0]:
            print("点击越界")
            return False
        return True


    @property
    def result_mask(self):
        result_mask = self._result_mask.copy()
        return result_mask


    @property
    def palette(self):
        if self.labelList:
            colors = [ml.color for ml in self.labelList]
            # colors.insert(0, self.backgroundColor)
            colors.insert(0, [0, 0, 0])
        else:
            colors = [[0, 0, 0]]
        # print(colors)
        return colors


    @property
    def current_object_prob(self):
        """
            获取当前推理标签
        """
        if self.probs_history:
            _, current_prob_additive = self.probs_history[-1]
            return current_prob_additive
        else:
            return None


    @property
    def is_incomplete_mask(self):
        """
            Returns
                bool: 当前的物体是不是还没标完
        """
        return len(self.probs_history) > 0


    @property
    def img_size(self):
        print(self.image.shape)
        return self.image.shape[1::-1]


    @property
    def paramSet(self):
        return self.model.paramSet


    @property
    def modelSet(self):
        return self.model is not None


    @property
    def modelName(self):
        return self.model.__name__


    @property
    def imageSet(self):
        return self.image is not None
