[![Python 3.6](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/release/python-360/) [![License](https://img.shields.io/badge/license-Apache%202-blue.svg)](LICENSE)
<!-- [![GitHub release](https://img.shields.io/github/release/Naereen/StrapDown.js.svg)](https://github.com/PaddleCV-SIG/iseg/releases) -->

# EISeg

EISeg(Efficient Interactive Segmentation)是基于飞桨开发的一个高效智能的交互式分割标注软件。它使用了RITM(Reviving Iterative Training with Mask Guidance for Interactive Segmentation)算法，涵盖了高精度和轻量级等不同方向的高质量交互式分割模型，方便开发者快速实现语义及实例标签的标注，降低标注成本。 另外，将EISeg获取到的标注应用到PaddleSeg提供的其他分割模型进行训练，便可得到定制化场景的高精度模型，打通分割任务从数据标注到模型训练及预测的全流程。



## 模型准备

在使用EIseg前，请先下载模型参数。EISeg开放了在COCO+LVIS和大规模人像数据上训练的四个标注模型，满足通用场景和人像场景的标注需求。其中模型结构对应EISeg交互工具中的网络选择模块，用户需要根据自己的场景需求选择不同的网络结构和加载参数。

| 模型类型 | 适用场景 | 模型结构 | 下载地址|
| --- | --- | --- | ---|
| 高精度模型  | 适用于通用场景的图像标注。 |HRNet18_OCR64 | [hrnet18_ocr64_cocolvis](https://bj.bcebos.com/paddleseg/dygraph/interactive_segmentation/ritm/hrnet18_ocr64_cocolvis.pdparams) |
| 轻量化模型  | 适用于通用场景的图像标注。 |HRNet18s_OCR48 | [hrnet18s_ocr48_cocolvis](https://bj.bcebos.com/paddleseg/dygraph/interactive_segmentation/ritm/hrnet18s_ocr48_cocolvis.pdparams) |
| 高精度模型  | 适用于人像标注场景。 |HRNet18_OCR64 | [hrnet18_ocr64_human](https://bj.bcebos.com/paddleseg/dygraph/interactive_segmentation/ritm/hrnet18_ocr64_human.pdparams) |
| 轻量化模型  | 适用于人像标注场景。 |HRNet18s_OCR48 | [hrnet18s_ocr48_human](https://bj.bcebos.com/paddleseg/dygraph/interactive_segmentation/ritm/hrnet18s_ocr48_human.pdparams) |



## 安装使用

### 使用版

目前带有交互式标注的EISeg已在PaddleSeg中提供。具体安装使用等说明详见[PaddleSeg/contrib/EISeg](https://github.com/PaddlePaddle/PaddleSeg/tree/release/2.2/contrib/EISeg)。支持多种安装方式，可兼容Windows，Mac OS和Linux。欢迎大家体验、start和fork。

### 开发版

此repo下的EISeg为开发版本，目前正在开发中，暂未提供最新的pip包和exe，仅支持clone到本地运行，参考下面代码运行：

```shell
git clone https://github.com/PaddleCV-SIG/EISeg.git
cd EISeg
pip install -r requirements.txt
python -m eiseg
```
即可开始执行。



## 使用

打开软件后，在对项目进行标注前，需要进行如下设置：

1. 选择合适的网络，并加载对应的模型参数。在EISeg中，目前网络分为`HRNet18s_OCR48`和`HRNet18_OCR64`，并分别提供了人像和通用两种模型参数。在正确加载模型参数后，右下角状态栏会给予说明。若网络参数与模型参数不符，将会弹出警告，此时加载失败需重新加载。正确加载的模型参数会记录在`近期模型参数`中，可以方便切换，并且下次打开软件时自动加载退出时的模型参数。
2. 打开图像/图像文件夹。当看到主界面图像正确加载，`数据列表`正确出现图像路径即可。
3. 添加/加载标签。可以通过`添加标签`新建标签，标签分为4列，分别对应像素值、说明、颜色和删除。新建好的标签可以通过`保存标签列表`保存为txt文件，其他合作者可以通过`加载标签列表`将标签导入。通过加载方式导入的标签，重启软件后会自动加载。
4. 在使用中可以将`自动保存`设置上，设定好文件夹（目前只支持英文路径）即可，这样在使用时切换图像会自动将完成标注的图像进行保存。

当设置完成后即可开始进行标注，默认情况下常用的按键/快捷键有：

| 按键/快捷键           | 功能         |
| --------------------- | ------------ |
| 鼠标左键              | 增加正样本点 |
| 鼠标右键              | 增加负样本点 |
| 鼠标中键              | 平移图像     |
| Ctrl+鼠标中键（滚轮） | 缩放图像     |
| S                     | 切换上一张图 |
| F                     | 切换下一张图 |
| Space（空格）         | 完成标注     |
| Ctrl+Z                | 撤销         |
| Ctrl+Shift+Z          | 清除         |
| Ctrl+Y                | 重做         |
| Ctrl+A                | 打开图像     |
| Shift+A               | 打开文件夹   |
| E                     | 打开快捷键表 |



## 更新

1. 目前基本完成大功能角点编辑功能，`空格`完成后会生成基本边界，可以通过添加、删除和移动角点对边界进行微调。新增操作方法如下：

   | 按键/快捷键       | 功能           |
   | ----------------- | -------------- |
   | 鼠标左键/移动     | 角点选择/移动  |
   | Backspace（退格） | 删除点         |
   | Ctrl+Backspace    | 删除多边形     |
   | 双击【边】        | 在此边上新加点 |

   

2. 基本完成小功能快捷键的设置，伪彩色保存等。

3. 医疗&遥感专业领域标注正在开发中。

## 效果

![CornerPoint](https://user-images.githubusercontent.com/71769312/126030819-0ee2777c-47ec-46f2-a06a-b365d0dd07bf.gif)

## 常见问题

下面列举了一些常见问题及可能的解决方案

<details> <summary> 选择模型权重后崩溃</summary><pre><code>
提示：EISeg推理过程中使用CPU和GPU版本的Paddle体验差异不是很大，如果GPU版本安装遇到问题可以先使用CPU版本快速尝试。相关安装方法参见[官方安装教程](https://www.paddlepaddle.org.cn/)。
1. Paddle版本低：EISeg中需要Paddle版本为2.1.x，如果版本过低请升级Paddle版本。查看Paddle版本：
<code>python -c "import paddle; print(paddle.__version__)"</code>
升级Paddle：
<code># CPU版本
pip install --upgrade paddlepaddle
# GPU版本
pip install --upgrade paddlepaddle-gpu</code>
2. Paddle安装问题：GPU版本Paddle和Cuda之间版本需要对应，检查安装是否存在问题可以运行。
<code>python -c "import paddle; paddle.utils.run_check()"</code></pre></details>
# 开发者

[Yuying Hao](https://github.com/haoyuying), [Yizhou Chen](https://github.com/geoyee), [Lin Han](https://github.com/linhandev/), [GT](https://github.com/GT-ZhangAcer), [Zhiliang Yu](https://github.com/yzl19940819)

<!-- pip install 'git+https://github.com/openvinotoolkit/datumaro' -->
