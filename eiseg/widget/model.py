        widget = QtWidgets.QWidget()
        horizontalLayout = QtWidgets.QHBoxLayout(widget)
        ModelRegion = QtWidgets.QVBoxLayout()
        ModelRegion.setObjectName("ModelRegion")
        combo = QtWidgets.QComboBox(self)
        combo.addItems([self.tr(m.name) for m in MODELS])
        self.comboModelSelect = combo
        ModelRegion.addWidget(self.comboModelSelect)
        # 网络参数
        self.btnParamsSelect = p_create_button(
            "btnParamsLoad",
            self.tr("加载网络参数"),
            osp.join(pjpath, "resource/Model.png"),
            "",
        )
        ModelRegion.addWidget(self.btnParamsSelect)  # 模型选择
        horizontalLayout.addLayout(ModelRegion)
        self.ModelDock = p_create_dock("ModelDock", self.tr("模型选择"), widget)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.ModelDock)
