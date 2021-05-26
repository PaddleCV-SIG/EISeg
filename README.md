# iann
交互式标注软件，暂定名iann。

# 安装
按照[官网介绍](https://www.paddlepaddle.org.cn/install/quick)安装paddle。
安装其他依赖
```shell
pip install -r requirements.txt
```

# 运行
```shell
git clone https://github.com/PaddleCV-SIG/iann/
cd iann
python iann/__main__.py
```

# TODO

- 整理创建网络/推理部分代码，简化main分支下代码
- 不同标签允许不同模型
- APPNAME全局变量
- 训练代码整理和训练配置的抽出（初步实现）
- 重新审查修改按键图标，确保图标完整清晰
- 界面配色以paddle蓝色为主，同时做一个ico窗口图标
- 标签可修改？

include iann/weight/sky_resnet/*
include iann/weight/aorta/*
include iann/weight/human_resnet/*
