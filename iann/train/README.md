# 训练iann可用的自定义模型

目前初步完成训练和简单的配置，但是其中有点设置和数据集格式都还比较死，还有很大的改进空间。

## 一、数据组织

在需要训练自己的数据集时，目前需要将数据集构造为如下格式，直接放在datasets文件夹中。

```
trainDataset
     ├── img
     |    └── filename.jpg
     └── gt
          └── filename.png
          
evalDataset
     ├── img
     |    └── filename.jpg
     └── gt
          └── filename.png
```

## 二、训练

直接运行ritm_train.py即可开始训练。目前一些简单的参数已经可以在yaml配置文件中进行自定义设置，不过现阶段不够灵活，也可能容易出现问题。

```
iters: 100000  # 训练轮数
batch_size: 16  # bs大小
save_interval: 1000  # 保存间隔
log_iters: 10  # 打印log的间隔
worker: 4  # 子进程数
save_dir: model_output  # 保存路径
use_vdl: False  # 是否使用vdl

train_dataset:  # 训练数据
  dataset_path: iann/train/datasets/egoHands  # 数据路径
  crop_size: [320, 480]  # 裁剪尺寸

val_dataset:  # 验证数据
  dataset_path: iann/train/datasets/testData  # 数据路径

optimizer:
  type: adam  # 优化器，目前仅可以选择‘adam’和‘sgd’

learning_rate:
  value_1: 5e-5  # 需要设置两个学习率
  value_2: 5e-6
  decay:
    type: poly  # 学习率衰减，目前仅支持‘poly’，可以修改下面的参数
    steps: 1000
    power: 0.9
    end_lr: 0.0

model:
  type: deeplab  # 模型名称，目前支持‘hrnet’、‘deeplab’以及‘shufflenet’
  backbone: resnet18  # 下面的参数是模型对应的参数，可在源码中查看
  is_ritm: True
  weights: None  # 加载权重的路径
```



### * 说明

1. 这里有个坑，数据不能有没有标签的纯背景，这样找不到正样点训练就会卡住，并且还不报错。

### * TODO

- [ ] 整理自定义的Dataset
- [ ] 整理ritm_train.py的代码使其清晰
- [ ] 将训练的配置和数据集配置抽成配置文件放在当前目录中，方便训练

