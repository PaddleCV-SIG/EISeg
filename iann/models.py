import paddle

from model.model import get_hrnet_model, get_deeplab_model


class HumanSeg:
    name = "人像分割"

    def get_model(self):
        model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
        para_state_dict = paddle.load("./iann/weight/human_resnet/model.pdparams")
        model.set_dict(para_state_dict)
        return model


class HumanSegCopy:
    name = "人像分割-另一个"

    def get_model(self):
        model = get_deeplab_model(backbone="resnet18", is_ritm=True, cpu_dist_maps=True)
        para_state_dict = paddle.load("./iann/weight/human_resnet/model.pdparams")
        model.set_dict(para_state_dict)
        return model


models = [HumanSeg(), HumanSegCopy()]
# print(models[1].name)
