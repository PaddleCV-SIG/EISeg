from qtpy import QtWidgets, QtGui


class LineItem(QtWidgets.QGraphicsLineItem):
    fixedWidth = 3

    def __init__(self, annotation_item, idx, color):
        super(LineItem, self).__init__()
        self.polygon_item = annotation_item
        self.idx = idx
        self.color = color
        self.setPen(QtGui.QPen(color, self.width))

        self.setZValue(11)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)

    @property
    def width(self):
        if not self.scene():
            width = 1
        else:
            width = LineItem.fixedWidth / self.scene().scale
        return width

    def updateWidth(self):
        if not self.scene():
            width = 1
        else:
            width = LineItem.fixedWidth / self.scene().scale
        self.setPen(QtGui.QPen(self.color, width))

    def hoverEnterEvent(self, ev):
        print("Hover line: ", self.idx)
        self.polygon_item.line_hovering = True
        self.setPen(QtGui.QPen(self.color, self.width * 2))
        super(LineItem, self).hoverEnterEvent(ev)

    def hoverLeaveEvent(self, ev):
        self.polygon_item.line_hovering = False
        self.setPen(QtGui.QPen(self.color, self.width))
        super(LineItem, self).hoverLeaveEvent(ev)

    def mouseDoubleClickEvent(self, ev):
        print("Double click line: ", self.idx, ev.pos())
        self.setPen(QtGui.QPen(self.color, self.width))
        self.polygon_item.addPointMiddle(self.idx, ev.pos())
        super(LineItem, self).mouseDoubleClickEvent(ev)
