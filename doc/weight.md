# 模型参数下载

交互式标注过程中需要进行深度学习推理，网络结构已经在软件中定义，但是Github项目或pip包中并不包含模型权重，目前需要单独下载。未来会加入软件内自动下载功能。注意模型的权重需要和网络结构对应，否则推理过程中会出错。

**下载链接**：[https://github.com/PaddleCV-SIG/EISeg/releases/download/v1.0.5/models.zip](https://github.com/PaddleCV-SIG/EISeg/releases/download/v1.0.5/models.zip)

其中包含模型如下：

| 参数名                                       | 对应网络      | 说明             |
| -------------------------------------------- | ------------- | ---------------- |
| hrnet18_ocr64_cocolvis_mask.pdparams         | HRNet18_OCR64 | 大型通用分割网络 |
| hrnet18_ocr64_mask_self_f_human_034.pdparams | HRNet18_OCR64 | 大型人像分割网络 |
| hrnet18s_ocr48_human_f_007.pdparams          | HRNet18_OCR48 | 小型人像分割网络 |
| hrnet18s_ocr48_self_f_005.pdparams           | HRNet18_OCR48 | 小型通用分割网络 |
