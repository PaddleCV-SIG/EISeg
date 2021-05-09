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

- [ ] 整理创建网络/推理部分代码，简化main分支下代码
- [x] 网络结构抽象成一个类，规定必须实现一些方法，集中注册，允许用户自己添加新的网络结构
- [x] 实现切换模型
- [ ] 实现多标签
- [ ] 不同标签允许不同模型
- [ ] 实现outputDir
- [ ] APPNAME全局变量
- [x] 清理ui，顶部功能按钮改成下拉菜单，切换图片改成小按钮+快捷键
- [x] 参考cvat/labelimg设计快捷键布局，尽量左手不要离开键盘
- [x] 解决图片放大后缩小，顶部定格显示不能居中的问题
- [x] 解决放大图像后平移速度变快
- [x] 解决图像切换后窗口缩放没有清除（顺便缩放到显示框最佳）
- [ ] 训练代码整理和训练配置的抽出（初步实现）
- [ ] 重新审查修改按键图标，确保图标完整清晰
- [ ] 界面配色以paddle蓝色为主，同时做一个ico窗口图标
- [ ] 标签可修改？