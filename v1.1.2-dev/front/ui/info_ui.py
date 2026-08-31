# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'info.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.setWindowModality(Qt.WindowModal)
        Form.setEnabled(True)
        Form.resize(393, 75)
        Form.setStyleSheet(u"background-color: rgba(0, 0, 0, 0);")
        self.info_label = QLabel(Form)
        self.info_label.setObjectName(u"info_label")
        self.info_label.setGeometry(QRect(9, 9, 381, 61))
        font = QFont()
        font.setFamilies([u"Sans"])
        self.info_label.setFont(font)
        self.info_label.setStyleSheet(u"background-color: rgb(53, 132, 228);\n"
"color: rgb(255, 255, 255);\n"
"border-radius:10px")
        self.info_label.setAlignment(Qt.AlignCenter)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"info", None))
        self.info_label.setText(QCoreApplication.translate("Form", u"INFO Anything", None))
    # retranslateUi

