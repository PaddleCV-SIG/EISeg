# 脚本工具相关

以下内容为EISeg中的相关工具使用。位置位于EISeg/tool

## 语义标签转实例标签

语义分割标签转实例分割标签（原标签为0/255），结果为单通道图像采用调色板调色。通过`tool`中的`semantic2instance`，可以将EISeg标注好的语义分割数据转为实例分割数据。使用以下方法：

``` shell
python semantic2instance.py -o label_path -d save_path
```

其中:

- `label_path`: 语义标签存放路径，必填
- `save_path`: 实例标签保存路径，必填

![68747470733a2f2f73332e626d702e6f76682f696d67732f323032312f30392f303038633562373638623765343737612e706e67](https://user-images.githubusercontent.com/71769312/141392781-d99ec177-f445-4336-9ab2-0ba7ae75d664.png)

