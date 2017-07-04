from PyQt4.QtGui import QWidget, QSizePolicy, QStyleOption, QStylePainter
from PyQt4.QtCore import Qt, QEvent, QSize

__author__ = 'brandon.corfman'


class TextLabel(QWidget):
    """A plain text label widget with support for elided text."""
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.setSizePolicy(QSizePolicy.Expanding,
                           QSizePolicy.Preferred)

        self.__text = ""
        self.__textElideMode = Qt.ElideMiddle
        self.__sizeHint = None
        self.__alignment = Qt.AlignLeft | Qt.AlignVCenter

    def setText(self, text):
        """Set the `text` string to display.
        """
        if self.__text != text:
            self.__text = text
            self.__update()

    def text(self):
        """Return the text"""
        return self.__text

    def setTextElideMode(self, mode):
        """Set elide mode (`Qt.TextElideMode`)"""
        if self.__textElideMode != mode:
            self.__textElideMode = mode
            self.__update()

    def elideMode(self):
        return self.__elideMode

    def setAlignment(self, align):
        """Set text alignment (`Qt.Alignment`)."""
        if self.__alignment != align:
            self.__alignment = align
            self.__update()

    def sizeHint(self):
        if self.__sizeHint is None:
            option = QStyleOption()
            option.initFrom(self)
            metrics = option.fontMetrics

            self.__sizeHint = QSize(200, metrics.height())

        return self.__sizeHint

    # noinspection PyUnusedLocal
    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = QStyleOption()
        option.initFrom(self)

        rect = option.rect
        metrics = option.fontMetrics
        text = metrics.elidedText(self.__text, self.__textElideMode,
                                  rect.width())
        painter.drawItemText(rect, self.__alignment,
                             option.palette, self.isEnabled(), text,
                             self.foregroundRole())
        painter.end()

    def changeEvent(self, event):
        if event.type() == QEvent.FontChange:
            self.__update()

        return QWidget.changeEvent(self, event)

    def __update(self):
        self.__sizeHint = None
        self.updateGeometry()
        self.update()
