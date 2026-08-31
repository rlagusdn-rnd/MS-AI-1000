# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_new.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QComboBox,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLayout, QLineEdit, QListView,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton,
    QSizePolicy, QSlider, QSpacerItem, QSpinBox,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)
import ms_ai_img_rc
import ms_ai_img_rc
import ms_ai_img_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1270, 655)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(1270, 655))
        MainWindow.setMaximumSize(QSize(3840, 2160))
        icon = QIcon()
        icon.addFile(u":/newPrefix/images/icon2.png", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setStyleSheet(u"background-color: rgb(3, 3, 13);")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_52 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_52.setObjectName(u"verticalLayout_52")
        self.verticalLayout_11 = QVBoxLayout()
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.top_logo = QLabel(self.centralwidget)
        self.top_logo.setObjectName(u"top_logo")
        self.top_logo.setMinimumSize(QSize(251, 41))
        self.top_logo.setMaximumSize(QSize(251, 41))
        font = QFont()
        font.setFamilies([u"Sans"])
        self.top_logo.setFont(font)
        self.top_logo.setPixmap(QPixmap(u":/newPrefix/images/logo.png"))
        self.top_logo.setScaledContents(True)

        self.horizontalLayout.addWidget(self.top_logo)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalSpacer_2 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.verson_label = QLabel(self.centralwidget)
        self.verson_label.setObjectName(u"verson_label")
        self.verson_label.setMaximumSize(QSize(16777215, 21))
        self.verson_label.setFont(font)
        self.verson_label.setStyleSheet(u"color: rgb(255, 255, 255)")

        self.verticalLayout.addWidget(self.verson_label)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.server_icon = QLabel(self.centralwidget)
        self.server_icon.setObjectName(u"server_icon")
        self.server_icon.setMaximumSize(QSize(23, 23))
        self.server_icon.setFont(font)
        self.server_icon.setPixmap(QPixmap(u":/newPrefix/images/ico_server.svg"))
        self.server_icon.setScaledContents(True)

        self.horizontalLayout.addWidget(self.server_icon)

        self.server_info_label = QLabel(self.centralwidget)
        self.server_info_label.setObjectName(u"server_info_label")
        self.server_info_label.setMaximumSize(QSize(91, 41))
        font1 = QFont()
        font1.setFamilies([u"Sans"])
        font1.setPointSize(10)
        font1.setBold(True)
        self.server_info_label.setFont(font1)
        self.server_info_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.server_info_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.server_info_label)

        self.horizontalSpacer = QSpacerItem(20, 18, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.server_ip_label = QLabel(self.centralwidget)
        self.server_ip_label.setObjectName(u"server_ip_label")
        self.server_ip_label.setMaximumSize(QSize(38, 41))
        self.server_ip_label.setFont(font1)
        self.server_ip_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.server_ip_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.server_ip_label)

        self.server_ip_input = QLineEdit(self.centralwidget)
        self.server_ip_input.setObjectName(u"server_ip_input")
        self.server_ip_input.setMinimumSize(QSize(0, 31))
        self.server_ip_input.setMaximumSize(QSize(121, 31))
        font2 = QFont()
        font2.setFamilies([u"Sans"])
        font2.setPointSize(10)
        self.server_ip_input.setFont(font2)
        self.server_ip_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.server_ip_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);\n"
"lineedit-password-character: 9679; /* Unicode for '\u2022' */")
        self.server_ip_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)

        self.horizontalLayout.addWidget(self.server_ip_input)

        self.server_id_label = QLabel(self.centralwidget)
        self.server_id_label.setObjectName(u"server_id_label")
        self.server_id_label.setMaximumSize(QSize(61, 41))
        self.server_id_label.setFont(font1)
        self.server_id_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.server_id_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.server_id_label)

        self.server_id_input = QLineEdit(self.centralwidget)
        self.server_id_input.setObjectName(u"server_id_input")
        self.server_id_input.setMaximumSize(QSize(121, 41))
        self.server_id_input.setFont(font2)
        self.server_id_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.server_id_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")

        self.horizontalLayout.addWidget(self.server_id_input)

        self.server_pw_label = QLabel(self.centralwidget)
        self.server_pw_label.setObjectName(u"server_pw_label")
        self.server_pw_label.setMaximumSize(QSize(61, 41))
        self.server_pw_label.setFont(font1)
        self.server_pw_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.server_pw_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.server_pw_label)

        self.server_pw_input = QLineEdit(self.centralwidget)
        self.server_pw_input.setObjectName(u"server_pw_input")
        self.server_pw_input.setMaximumSize(QSize(121, 41))
        self.server_pw_input.setFont(font2)
        self.server_pw_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.server_pw_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.server_pw_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.horizontalLayout.addWidget(self.server_pw_input)

        self.sever_login_bnt = QPushButton(self.centralwidget)
        self.sever_login_bnt.setObjectName(u"sever_login_bnt")
        self.sever_login_bnt.setMinimumSize(QSize(51, 21))
        self.sever_login_bnt.setMaximumSize(QSize(51, 21))
        font3 = QFont()
        font3.setFamilies([u"NanumSquareRound"])
        font3.setPointSize(10)
        font3.setBold(False)
        self.sever_login_bnt.setFont(font3)
        self.sever_login_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.sever_login_bnt.setStyleSheet(u"background-color: qlineargradient(spread:pad, x1:0.244, y1:0.477, x2:1, y2:0.489, stop:0.0845771 rgba(0, 205, 0, 255), stop:1 rgba(56, 188, 56, 255));\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 10px;\n"
"")

        self.horizontalLayout.addWidget(self.sever_login_bnt)

        self.horizontalSpacer_2 = QSpacerItem(37, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.shutdown_bnt = QPushButton(self.centralwidget)
        self.shutdown_bnt.setObjectName(u"shutdown_bnt")
        self.shutdown_bnt.setMinimumSize(QSize(61, 31))
        self.shutdown_bnt.setMaximumSize(QSize(61, 31))
        self.shutdown_bnt.setFont(font3)
        self.shutdown_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.shutdown_bnt.setStyleSheet(u"background-color: rgb(237, 51, 59);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"")

        self.horizontalLayout.addWidget(self.shutdown_bnt)


        self.verticalLayout_11.addLayout(self.horizontalLayout)

        self.horizontalLayout_32 = QHBoxLayout()
        self.horizontalLayout_32.setObjectName(u"horizontalLayout_32")
        self.camera_info_side_widget = QWidget(self.centralwidget)
        self.camera_info_side_widget.setObjectName(u"camera_info_side_widget")
        self.camera_info_side_widget.setMaximumSize(QSize(401, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.camera_info_side_widget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.camera_list_table = QTableWidget(self.camera_info_side_widget)
        if (self.camera_list_table.columnCount() < 4):
            self.camera_list_table.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.camera_list_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        font4 = QFont()
        font4.setFamilies([u"Ubuntu Light"])
        font4.setPointSize(10)
        font4.setBold(False)
        __qtablewidgetitem1 = QTableWidgetItem()
        __qtablewidgetitem1.setFont(font4);
        self.camera_list_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        font5 = QFont()
        font5.setFamilies([u"Ubuntu Light"])
        font5.setPointSize(10)
        __qtablewidgetitem2 = QTableWidgetItem()
        __qtablewidgetitem2.setFont(font5);
        self.camera_list_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        __qtablewidgetitem3.setFont(font4);
        self.camera_list_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.camera_list_table.setObjectName(u"camera_list_table")
        self.camera_list_table.setMinimumSize(QSize(368, 100))
        self.camera_list_table.setMaximumSize(QSize(401, 16777215))
        font6 = QFont()
        font6.setFamilies([u"Sans"])
        font6.setPointSize(10)
        font6.setBold(False)
        self.camera_list_table.setFont(font6)
        self.camera_list_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.camera_list_table.setStyleSheet(u"color: rgb(209,209,209);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgba(19, 193, 13, 100);")
        self.camera_list_table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.camera_list_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.camera_list_table.setTabKeyNavigation(False)
        self.camera_list_table.setDragDropOverwriteMode(False)
        self.camera_list_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.camera_list_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.camera_list_table.setShowGrid(False)
        self.camera_list_table.setGridStyle(Qt.PenStyle.NoPen)
        self.camera_list_table.setWordWrap(False)
        self.camera_list_table.setCornerButtonEnabled(False)
        self.camera_list_table.horizontalHeader().setCascadingSectionResizes(False)
        self.camera_list_table.horizontalHeader().setMinimumSectionSize(5)
        self.camera_list_table.horizontalHeader().setDefaultSectionSize(80)
        self.camera_list_table.horizontalHeader().setHighlightSections(False)
        self.camera_list_table.horizontalHeader().setProperty("showSortIndicator", False)
        self.camera_list_table.horizontalHeader().setStretchLastSection(True)
        self.camera_list_table.verticalHeader().setVisible(False)
        self.camera_list_table.verticalHeader().setCascadingSectionResizes(False)
        self.camera_list_table.verticalHeader().setHighlightSections(False)
        self.camera_list_table.verticalHeader().setProperty("showSortIndicator", False)
        self.camera_list_table.verticalHeader().setStretchLastSection(False)

        self.verticalLayout_4.addWidget(self.camera_list_table)

        self.camera_info_widget = QWidget(self.camera_info_side_widget)
        self.camera_info_widget.setObjectName(u"camera_info_widget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.camera_info_widget.sizePolicy().hasHeightForWidth())
        self.camera_info_widget.setSizePolicy(sizePolicy1)
        self.camera_info_widget.setMinimumSize(QSize(373, 312))
        self.camera_info_widget.setMaximumSize(QSize(401, 312))
        self.camera_info_widget.setStyleSheet(u"background-color: rgb(13, 16, 23);\n"
"border-radius: 20px;\n"
"color: rgb(255, 255, 255);")
        self.verticalLayout_24 = QVBoxLayout(self.camera_info_widget)
        self.verticalLayout_24.setObjectName(u"verticalLayout_24")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.camera_info_title = QLabel(self.camera_info_widget)
        self.camera_info_title.setObjectName(u"camera_info_title")
        self.camera_info_title.setMinimumSize(QSize(95, 20))
        self.camera_info_title.setMaximumSize(QSize(95, 20))
        font7 = QFont()
        font7.setFamilies([u"Sans"])
        font7.setPointSize(13)
        self.camera_info_title.setFont(font7)
        self.camera_info_title.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(191, 64, 64, 0);")

        self.horizontalLayout_3.addWidget(self.camera_info_title)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_3)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.camera_info_title_line = QFrame(self.camera_info_widget)
        self.camera_info_title_line.setObjectName(u"camera_info_title_line")
        self.camera_info_title_line.setMinimumSize(QSize(370, 3))
        self.camera_info_title_line.setMaximumSize(QSize(327, 3))
        font8 = QFont()
        font8.setFamilies([u"Sans"])
        font8.setPointSize(5)
        font8.setStrikeOut(False)
        self.camera_info_title_line.setFont(font8)
        self.camera_info_title_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.camera_info_title_line.setAutoFillBackground(False)
        self.camera_info_title_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.camera_info_title_line.setFrameShape(QFrame.Shape.HLine)
        self.camera_info_title_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_5.addWidget(self.camera_info_title_line)


        self.verticalLayout_6.addLayout(self.verticalLayout_5)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_6.addItem(self.verticalSpacer_3)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.camera_name = QLabel(self.camera_info_widget)
        self.camera_name.setObjectName(u"camera_name")
        self.camera_name.setMinimumSize(QSize(29, 22))
        self.camera_name.setMaximumSize(QSize(29, 22))
        self.camera_name.setFont(font1)
        self.camera_name.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.camera_name.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.camera_name)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_4)

        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.camera_info_name_input = QLineEdit(self.camera_info_widget)
        self.camera_info_name_input.setObjectName(u"camera_info_name_input")
        self.camera_info_name_input.setMinimumSize(QSize(275, 17))
        self.camera_info_name_input.setMaximumSize(QSize(275, 17))
        self.camera_info_name_input.setFont(font6)
        self.camera_info_name_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.camera_info_name_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")

        self.verticalLayout_7.addWidget(self.camera_info_name_input)

        self.camera_info_name_line = QFrame(self.camera_info_widget)
        self.camera_info_name_line.setObjectName(u"camera_info_name_line")
        self.camera_info_name_line.setMinimumSize(QSize(275, 3))
        self.camera_info_name_line.setMaximumSize(QSize(275, 3))
        self.camera_info_name_line.setFont(font8)
        self.camera_info_name_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.camera_info_name_line.setAutoFillBackground(False)
        self.camera_info_name_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.camera_info_name_line.setFrameShape(QFrame.Shape.HLine)
        self.camera_info_name_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_7.addWidget(self.camera_info_name_line)


        self.horizontalLayout_4.addLayout(self.verticalLayout_7)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)

        self.verticalSpacer_11 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_11)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.camera_ip = QLabel(self.camera_info_widget)
        self.camera_ip.setObjectName(u"camera_ip")
        self.camera_ip.setMinimumSize(QSize(47, 22))
        self.camera_ip.setMaximumSize(QSize(47, 22))
        self.camera_ip.setFont(font1)
        self.camera_ip.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(0, 0, 0, 0);")

        self.horizontalLayout_5.addWidget(self.camera_ip)

        self.horizontalSpacer_9 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_9)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.camera_info_ip_input = QLineEdit(self.camera_info_widget)
        self.camera_info_ip_input.setObjectName(u"camera_info_ip_input")
        self.camera_info_ip_input.setMinimumSize(QSize(275, 17))
        self.camera_info_ip_input.setMaximumSize(QSize(275, 17))
        self.camera_info_ip_input.setFont(font6)
        self.camera_info_ip_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")

        self.verticalLayout_8.addWidget(self.camera_info_ip_input)

        self.camera_info_ip_line = QFrame(self.camera_info_widget)
        self.camera_info_ip_line.setObjectName(u"camera_info_ip_line")
        self.camera_info_ip_line.setMinimumSize(QSize(275, 3))
        self.camera_info_ip_line.setMaximumSize(QSize(275, 3))
        self.camera_info_ip_line.setFont(font8)
        self.camera_info_ip_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.camera_info_ip_line.setAutoFillBackground(False)
        self.camera_info_ip_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.camera_info_ip_line.setFrameShape(QFrame.Shape.HLine)
        self.camera_info_ip_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_8.addWidget(self.camera_info_ip_line)


        self.horizontalLayout_5.addLayout(self.verticalLayout_8)


        self.verticalLayout_6.addLayout(self.horizontalLayout_5)

        self.verticalSpacer_10 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_10)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.camera_id = QLabel(self.camera_info_widget)
        self.camera_id.setObjectName(u"camera_id")
        self.camera_id.setMinimumSize(QSize(63, 22))
        self.camera_id.setMaximumSize(QSize(63, 22))
        self.camera_id.setFont(font1)
        self.camera_id.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(0, 0, 0, 0);")

        self.horizontalLayout_6.addWidget(self.camera_id)

        self.horizontalSpacer_10 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer_10)

        self.verticalLayout_23 = QVBoxLayout()
        self.verticalLayout_23.setObjectName(u"verticalLayout_23")
        self.camera_info_id_input = QLineEdit(self.camera_info_widget)
        self.camera_info_id_input.setObjectName(u"camera_info_id_input")
        self.camera_info_id_input.setMinimumSize(QSize(275, 17))
        self.camera_info_id_input.setMaximumSize(QSize(275, 17))
        self.camera_info_id_input.setFont(font6)
        self.camera_info_id_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")

        self.verticalLayout_23.addWidget(self.camera_info_id_input)

        self.camera_info_id_line = QFrame(self.camera_info_widget)
        self.camera_info_id_line.setObjectName(u"camera_info_id_line")
        self.camera_info_id_line.setMinimumSize(QSize(275, 3))
        self.camera_info_id_line.setMaximumSize(QSize(275, 3))
        self.camera_info_id_line.setFont(font8)
        self.camera_info_id_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.camera_info_id_line.setAutoFillBackground(False)
        self.camera_info_id_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.camera_info_id_line.setFrameShape(QFrame.Shape.HLine)
        self.camera_info_id_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_23.addWidget(self.camera_info_id_line)


        self.horizontalLayout_6.addLayout(self.verticalLayout_23)


        self.verticalLayout_6.addLayout(self.horizontalLayout_6)

        self.verticalSpacer_9 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_9)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.camera_pw = QLabel(self.camera_info_widget)
        self.camera_pw.setObjectName(u"camera_pw")
        self.camera_pw.setMinimumSize(QSize(57, 22))
        self.camera_pw.setMaximumSize(QSize(57, 22))
        self.camera_pw.setFont(font1)
        self.camera_pw.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(0, 0, 0, 0);")

        self.horizontalLayout_7.addWidget(self.camera_pw)

        self.horizontalSpacer_11 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_11)

        self.verticalLayout_34 = QVBoxLayout()
        self.verticalLayout_34.setObjectName(u"verticalLayout_34")
        self.camera_info_pw_input = QLineEdit(self.camera_info_widget)
        self.camera_info_pw_input.setObjectName(u"camera_info_pw_input")
        sizePolicy1.setHeightForWidth(self.camera_info_pw_input.sizePolicy().hasHeightForWidth())
        self.camera_info_pw_input.setSizePolicy(sizePolicy1)
        self.camera_info_pw_input.setMinimumSize(QSize(275, 17))
        self.camera_info_pw_input.setMaximumSize(QSize(275, 17))
        self.camera_info_pw_input.setFont(font6)
        self.camera_info_pw_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")

        self.verticalLayout_34.addWidget(self.camera_info_pw_input)

        self.camera_info_pw_line = QFrame(self.camera_info_widget)
        self.camera_info_pw_line.setObjectName(u"camera_info_pw_line")
        self.camera_info_pw_line.setMinimumSize(QSize(275, 3))
        self.camera_info_pw_line.setMaximumSize(QSize(275, 3))
        self.camera_info_pw_line.setFont(font8)
        self.camera_info_pw_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.camera_info_pw_line.setAutoFillBackground(False)
        self.camera_info_pw_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.camera_info_pw_line.setFrameShape(QFrame.Shape.HLine)
        self.camera_info_pw_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_34.addWidget(self.camera_info_pw_line)


        self.horizontalLayout_7.addLayout(self.verticalLayout_34)


        self.verticalLayout_6.addLayout(self.horizontalLayout_7)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer_4)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.camera_remove_bn = QPushButton(self.camera_info_widget)
        self.camera_remove_bn.setObjectName(u"camera_remove_bn")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.camera_remove_bn.sizePolicy().hasHeightForWidth())
        self.camera_remove_bn.setSizePolicy(sizePolicy2)
        self.camera_remove_bn.setMinimumSize(QSize(76, 39))
        self.camera_remove_bn.setMaximumSize(QSize(76, 39))
        self.camera_remove_bn.setFont(font2)
        self.camera_remove_bn.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_remove_bn.setStyleSheet(u"background-color: rgb(36, 39, 44);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 19px;\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"")

        self.horizontalLayout_8.addWidget(self.camera_remove_bn)

        self.camera_add_bn = QPushButton(self.camera_info_widget)
        self.camera_add_bn.setObjectName(u"camera_add_bn")
        sizePolicy2.setHeightForWidth(self.camera_add_bn.sizePolicy().hasHeightForWidth())
        self.camera_add_bn.setSizePolicy(sizePolicy2)
        self.camera_add_bn.setMinimumSize(QSize(76, 39))
        self.camera_add_bn.setMaximumSize(QSize(76, 39))
        self.camera_add_bn.setFont(font2)
        self.camera_add_bn.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_add_bn.setStyleSheet(u"background-color: rgb(36, 39, 44);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 19px;\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"")

        self.horizontalLayout_8.addWidget(self.camera_add_bn)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_8.addItem(self.horizontalSpacer_5)

        self.camera_save_bn = QPushButton(self.camera_info_widget)
        self.camera_save_bn.setObjectName(u"camera_save_bn")
        sizePolicy.setHeightForWidth(self.camera_save_bn.sizePolicy().hasHeightForWidth())
        self.camera_save_bn.setSizePolicy(sizePolicy)
        self.camera_save_bn.setMinimumSize(QSize(76, 39))
        self.camera_save_bn.setMaximumSize(QSize(76, 39))
        self.camera_save_bn.setFont(font2)
        self.camera_save_bn.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_save_bn.setStyleSheet(u"\n"
"background-color: qlineargradient(spread:pad, x1:0.244, y1:0.477, x2:1, y2:0.489, stop:0.0845771 rgba(0, 205, 0, 255), stop:1 rgba(56, 188, 56, 255));\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 19px;\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"")

        self.horizontalLayout_8.addWidget(self.camera_save_bn)


        self.verticalLayout_6.addLayout(self.horizontalLayout_8)


        self.verticalLayout_24.addLayout(self.verticalLayout_6)


        self.verticalLayout_4.addWidget(self.camera_info_widget)


        self.verticalLayout_3.addLayout(self.verticalLayout_4)


        self.horizontalLayout_32.addWidget(self.camera_info_side_widget)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tab_layout = QHBoxLayout()
        self.tab_layout.setObjectName(u"tab_layout")
        self.tab_backgournd = QWidget(self.centralwidget)
        self.tab_backgournd.setObjectName(u"tab_backgournd")
        sizePolicy1.setHeightForWidth(self.tab_backgournd.sizePolicy().hasHeightForWidth())
        self.tab_backgournd.setSizePolicy(sizePolicy1)
        self.tab_backgournd.setMinimumSize(QSize(522, 50))
        self.tab_backgournd.setMaximumSize(QSize(682, 50))
        self.tab_backgournd.setStyleSheet(u"background-color: rgb(16, 20, 25);\n"
"\n"
"border-right: 1px solid rgb(119, 118, 123);\n"
"border-bottom-right-radius:20px solid rgb(119, 118, 123);\n"
"\n"
"border-bottom:1px solid rgb(119, 118, 123);\n"
"")
        self.horizontalLayout_35 = QHBoxLayout(self.tab_backgournd)
        self.horizontalLayout_35.setObjectName(u"horizontalLayout_35")
        self.horizontalLayout_34 = QHBoxLayout()
        self.horizontalLayout_34.setSpacing(0)
        self.horizontalLayout_34.setObjectName(u"horizontalLayout_34")
        self.horizontalLayout_34.setContentsMargins(-1, -1, -1, 0)
        self.live_bnt = QPushButton(self.tab_backgournd)
        self.live_bnt.setObjectName(u"live_bnt")
        self.live_bnt.setMinimumSize(QSize(163, 28))
        self.live_bnt.setMaximumSize(QSize(163, 28))
        self.live_bnt.setFont(font7)
        self.live_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.live_bnt.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border: 1px solid rgba(0, 0, 0, 0);\n"
"background-color: rgba(191, 64, 64, 0);")
        self.live_bnt.setCheckable(True)
        self.live_bnt.setChecked(False)
        self.live_bnt.setAutoExclusive(True)

        self.horizontalLayout_34.addWidget(self.live_bnt)

        self.tab_partion_10 = QLabel(self.tab_backgournd)
        self.tab_partion_10.setObjectName(u"tab_partion_10")
        sizePolicy1.setHeightForWidth(self.tab_partion_10.sizePolicy().hasHeightForWidth())
        self.tab_partion_10.setSizePolicy(sizePolicy1)
        self.tab_partion_10.setMinimumSize(QSize(3, 0))
        font9 = QFont()
        font9.setFamilies([u"Sans"])
        font9.setPointSize(14)
        self.tab_partion_10.setFont(font9)
        self.tab_partion_10.setStyleSheet(u"color: rgb(119, 118, 123);\n"
"background-color: rgba(191, 64, 64, 0);\n"
"border: 1px solid rgba(0, 0, 0, 0);\n"
"background-color: rgba(0, 0 0, 0);")
        self.tab_partion_10.setTextFormat(Qt.TextFormat.PlainText)
        self.tab_partion_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_34.addWidget(self.tab_partion_10)

        self.camera_bnt = QPushButton(self.tab_backgournd)
        self.camera_bnt.setObjectName(u"camera_bnt")
        self.camera_bnt.setMinimumSize(QSize(163, 28))
        self.camera_bnt.setMaximumSize(QSize(163, 28))
        self.camera_bnt.setFont(font7)
        self.camera_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_bnt.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border: 1px solid rgba(0, 0, 0, 0);\n"
"background-color: rgba(191, 64, 64, 0);")

        self.horizontalLayout_34.addWidget(self.camera_bnt)

        self.tab_partion_11 = QLabel(self.tab_backgournd)
        self.tab_partion_11.setObjectName(u"tab_partion_11")
        sizePolicy1.setHeightForWidth(self.tab_partion_11.sizePolicy().hasHeightForWidth())
        self.tab_partion_11.setSizePolicy(sizePolicy1)
        self.tab_partion_11.setMinimumSize(QSize(3, 0))
        self.tab_partion_11.setFont(font9)
        self.tab_partion_11.setStyleSheet(u"color: rgb(119, 118, 123);\n"
"background-color: rgba(191, 64, 64, 0);\n"
"border: 1px solid rgba(0, 0, 0, 0);\n"
"background-color: rgba(0, 0 0, 0);")
        self.tab_partion_11.setTextFormat(Qt.TextFormat.PlainText)
        self.tab_partion_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_34.addWidget(self.tab_partion_11)

        self.setting_bnt = QPushButton(self.tab_backgournd)
        self.setting_bnt.setObjectName(u"setting_bnt")
        self.setting_bnt.setMinimumSize(QSize(163, 28))
        self.setting_bnt.setMaximumSize(QSize(163, 28))
        self.setting_bnt.setFont(font7)
        self.setting_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.setting_bnt.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgba(191, 64, 64, 0);\n"
"border: 1px solid rgba(0, 0, 0, 0);")

        self.horizontalLayout_34.addWidget(self.setting_bnt)

        self.tab_partion_3 = QLabel(self.tab_backgournd)
        self.tab_partion_3.setObjectName(u"tab_partion_3")
        sizePolicy1.setHeightForWidth(self.tab_partion_3.sizePolicy().hasHeightForWidth())
        self.tab_partion_3.setSizePolicy(sizePolicy1)
        self.tab_partion_3.setMinimumSize(QSize(3, 0))
        self.tab_partion_3.setFont(font9)
        self.tab_partion_3.setStyleSheet(u"color: rgb(119, 118, 123);\n"
"background-color: rgba(191, 64, 64, 0);\n"
"border: 1px solid rgba(0, 0, 0, 0);\n"
"background-color: rgba(0, 0 0, 0);")
        self.tab_partion_3.setTextFormat(Qt.TextFormat.PlainText)
        self.tab_partion_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_34.addWidget(self.tab_partion_3)

        self.admin_bnt = QPushButton(self.tab_backgournd)
        self.admin_bnt.setObjectName(u"admin_bnt")
        self.admin_bnt.setMinimumSize(QSize(163, 28))
        self.admin_bnt.setMaximumSize(QSize(163, 28))
        self.admin_bnt.setFont(font7)
        self.admin_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.admin_bnt.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border: 1px solid rgba(0, 0, 0, 0);\n"
"background-color: rgba(191, 64, 64, 0);")

        self.horizontalLayout_34.addWidget(self.admin_bnt)


        self.horizontalLayout_35.addLayout(self.horizontalLayout_34)


        self.tab_layout.addWidget(self.tab_backgournd)

        self.horizontalSpacer_18 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.tab_layout.addItem(self.horizontalSpacer_18)

        self.verticalLayout_55 = QVBoxLayout()
        self.verticalLayout_55.setObjectName(u"verticalLayout_55")
        self.verticalSpacer_17 = QSpacerItem(20, 11, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_55.addItem(self.verticalSpacer_17)

        self.horizontalLayout_36 = QHBoxLayout()
        self.horizontalLayout_36.setObjectName(u"horizontalLayout_36")
        self.camera_refresh_bnt = QPushButton(self.centralwidget)
        self.camera_refresh_bnt.setObjectName(u"camera_refresh_bnt")
        self.camera_refresh_bnt.setMinimumSize(QSize(37, 52))
        self.camera_refresh_bnt.setMaximumSize(QSize(37, 52))
        self.camera_refresh_bnt.setFont(font2)
        self.camera_refresh_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_refresh_bnt.setStyleSheet(u"background-color: rgb(3, 3, 13);\n"
"border: 1px solid rgb(3, 3, 13);\n"
"color: rgb(255, 255, 255);\n"
"\n"
"")
        icon1 = QIcon()
        icon1.addFile(u":/newPrefix/images/ico_refresh.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.camera_refresh_bnt.setIcon(icon1)
        self.camera_refresh_bnt.setIconSize(QSize(31, 50))

        self.horizontalLayout_36.addWidget(self.camera_refresh_bnt)

        self.camera_schedule_bnt = QPushButton(self.centralwidget)
        self.camera_schedule_bnt.setObjectName(u"camera_schedule_bnt")
        self.camera_schedule_bnt.setMinimumSize(QSize(37, 52))
        self.camera_schedule_bnt.setFont(font2)
        self.camera_schedule_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_schedule_bnt.setStyleSheet(u"background-color: rgb(3, 3, 13);\n"
"border: 1px solid rgb(3, 3, 13);\n"
"color: rgb(255, 255, 255);\n"
"\n"
"")
        icon2 = QIcon()
        icon2.addFile(u":/newPrefix/images/ico_timer.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.camera_schedule_bnt.setIcon(icon2)
        self.camera_schedule_bnt.setIconSize(QSize(31, 50))

        self.horizontalLayout_36.addWidget(self.camera_schedule_bnt)

        self.alarm_search_bnt = QPushButton(self.centralwidget)
        self.alarm_search_bnt.setObjectName(u"alarm_search_bnt")
        self.alarm_search_bnt.setMinimumSize(QSize(37, 52))
        self.alarm_search_bnt.setFont(font2)
        self.alarm_search_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.alarm_search_bnt.setStyleSheet(u"background-color: rgb(3, 3, 13);\n"
"border: 1px solid rgb(3, 3, 13);\n"
"color: rgb(255, 255, 255);\n"
"\n"
"")
        icon3 = QIcon()
        icon3.addFile(u":/newPrefix/images/search_ico.png", QSize(), QIcon.Normal, QIcon.Off)
        self.alarm_search_bnt.setIcon(icon3)
        self.alarm_search_bnt.setIconSize(QSize(31, 50))

        self.horizontalLayout_36.addWidget(self.alarm_search_bnt)


        self.verticalLayout_55.addLayout(self.horizontalLayout_36)


        self.tab_layout.addLayout(self.verticalLayout_55)


        self.verticalLayout_2.addLayout(self.tab_layout)

        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.stackedWidget.sizePolicy().hasHeightForWidth())
        self.stackedWidget.setSizePolicy(sizePolicy3)
        self.stackedWidget.setMinimumSize(QSize(790, 499))
        self.live_page = QWidget()
        self.live_page.setObjectName(u"live_page")
        self.horizontalLayout_9 = QHBoxLayout(self.live_page)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.camera_view_9 = QLabel(self.live_page)
        self.camera_view_9.setObjectName(u"camera_view_9")
        sizePolicy3.setHeightForWidth(self.camera_view_9.sizePolicy().hasHeightForWidth())
        self.camera_view_9.setSizePolicy(sizePolicy3)
        self.camera_view_9.setMinimumSize(QSize(200, 121))
        font10 = QFont()
        font10.setFamilies([u"Sans"])
        font10.setPointSize(16)
        self.camera_view_9.setFont(font10)
        self.camera_view_9.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_9.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_9.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_9.setScaledContents(False)
        self.camera_view_9.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_9, 2, 0, 1, 1)

        self.camera_view_1 = QLabel(self.live_page)
        self.camera_view_1.setObjectName(u"camera_view_1")
        sizePolicy3.setHeightForWidth(self.camera_view_1.sizePolicy().hasHeightForWidth())
        self.camera_view_1.setSizePolicy(sizePolicy3)
        self.camera_view_1.setMinimumSize(QSize(200, 121))
        self.camera_view_1.setFont(font10)
        self.camera_view_1.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_1.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_1.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_1.setScaledContents(False)
        self.camera_view_1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_1, 0, 0, 1, 1)

        self.camera_view_11 = QLabel(self.live_page)
        self.camera_view_11.setObjectName(u"camera_view_11")
        sizePolicy3.setHeightForWidth(self.camera_view_11.sizePolicy().hasHeightForWidth())
        self.camera_view_11.setSizePolicy(sizePolicy3)
        self.camera_view_11.setMinimumSize(QSize(200, 121))
        self.camera_view_11.setFont(font10)
        self.camera_view_11.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_11.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_11.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_11.setScaledContents(False)
        self.camera_view_11.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_11, 2, 2, 1, 1)

        self.camera_view_12 = QLabel(self.live_page)
        self.camera_view_12.setObjectName(u"camera_view_12")
        sizePolicy3.setHeightForWidth(self.camera_view_12.sizePolicy().hasHeightForWidth())
        self.camera_view_12.setSizePolicy(sizePolicy3)
        self.camera_view_12.setMinimumSize(QSize(200, 121))
        self.camera_view_12.setFont(font10)
        self.camera_view_12.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_12.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_12.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_12.setScaledContents(False)
        self.camera_view_12.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_12, 2, 3, 1, 1)

        self.camera_view_5 = QLabel(self.live_page)
        self.camera_view_5.setObjectName(u"camera_view_5")
        sizePolicy3.setHeightForWidth(self.camera_view_5.sizePolicy().hasHeightForWidth())
        self.camera_view_5.setSizePolicy(sizePolicy3)
        self.camera_view_5.setMinimumSize(QSize(200, 121))
        self.camera_view_5.setFont(font10)
        self.camera_view_5.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_5.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_5.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_5.setScaledContents(False)
        self.camera_view_5.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_5, 1, 0, 1, 1)

        self.camera_view_14 = QLabel(self.live_page)
        self.camera_view_14.setObjectName(u"camera_view_14")
        sizePolicy3.setHeightForWidth(self.camera_view_14.sizePolicy().hasHeightForWidth())
        self.camera_view_14.setSizePolicy(sizePolicy3)
        self.camera_view_14.setMinimumSize(QSize(200, 121))
        self.camera_view_14.setFont(font10)
        self.camera_view_14.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_14.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border: 1px solid rgb(119, 118, 123);")
        self.camera_view_14.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_14.setScaledContents(False)
        self.camera_view_14.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_14, 3, 1, 1, 1)

        self.camera_view_16 = QLabel(self.live_page)
        self.camera_view_16.setObjectName(u"camera_view_16")
        sizePolicy3.setHeightForWidth(self.camera_view_16.sizePolicy().hasHeightForWidth())
        self.camera_view_16.setSizePolicy(sizePolicy3)
        self.camera_view_16.setMinimumSize(QSize(200, 121))
        self.camera_view_16.setFont(font10)
        self.camera_view_16.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_16.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_16.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_16.setScaledContents(False)
        self.camera_view_16.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_16, 3, 3, 1, 1)

        self.camera_view_4 = QLabel(self.live_page)
        self.camera_view_4.setObjectName(u"camera_view_4")
        sizePolicy3.setHeightForWidth(self.camera_view_4.sizePolicy().hasHeightForWidth())
        self.camera_view_4.setSizePolicy(sizePolicy3)
        self.camera_view_4.setMinimumSize(QSize(200, 121))
        self.camera_view_4.setFont(font10)
        self.camera_view_4.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_4.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_4.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_4.setScaledContents(False)
        self.camera_view_4.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_4, 0, 3, 1, 1)

        self.camera_view_7 = QLabel(self.live_page)
        self.camera_view_7.setObjectName(u"camera_view_7")
        sizePolicy3.setHeightForWidth(self.camera_view_7.sizePolicy().hasHeightForWidth())
        self.camera_view_7.setSizePolicy(sizePolicy3)
        self.camera_view_7.setMinimumSize(QSize(200, 121))
        self.camera_view_7.setFont(font10)
        self.camera_view_7.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_7.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_7.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_7.setScaledContents(False)
        self.camera_view_7.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_7, 1, 2, 1, 1)

        self.camera_view_6 = QLabel(self.live_page)
        self.camera_view_6.setObjectName(u"camera_view_6")
        sizePolicy3.setHeightForWidth(self.camera_view_6.sizePolicy().hasHeightForWidth())
        self.camera_view_6.setSizePolicy(sizePolicy3)
        self.camera_view_6.setMinimumSize(QSize(200, 121))
        self.camera_view_6.setFont(font10)
        self.camera_view_6.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_6.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_6.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_6.setScaledContents(False)
        self.camera_view_6.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_6, 1, 1, 1, 1)

        self.camera_view_2 = QLabel(self.live_page)
        self.camera_view_2.setObjectName(u"camera_view_2")
        sizePolicy3.setHeightForWidth(self.camera_view_2.sizePolicy().hasHeightForWidth())
        self.camera_view_2.setSizePolicy(sizePolicy3)
        self.camera_view_2.setMinimumSize(QSize(200, 121))
        self.camera_view_2.setFont(font10)
        self.camera_view_2.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_2.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_2.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_2.setScaledContents(False)
        self.camera_view_2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_2, 0, 1, 1, 1)

        self.camera_view_15 = QLabel(self.live_page)
        self.camera_view_15.setObjectName(u"camera_view_15")
        sizePolicy3.setHeightForWidth(self.camera_view_15.sizePolicy().hasHeightForWidth())
        self.camera_view_15.setSizePolicy(sizePolicy3)
        self.camera_view_15.setMinimumSize(QSize(200, 121))
        self.camera_view_15.setFont(font10)
        self.camera_view_15.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_15.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_15.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_15.setScaledContents(False)
        self.camera_view_15.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_15, 3, 2, 1, 1)

        self.camera_view_13 = QLabel(self.live_page)
        self.camera_view_13.setObjectName(u"camera_view_13")
        sizePolicy3.setHeightForWidth(self.camera_view_13.sizePolicy().hasHeightForWidth())
        self.camera_view_13.setSizePolicy(sizePolicy3)
        self.camera_view_13.setMinimumSize(QSize(200, 121))
        self.camera_view_13.setFont(font10)
        self.camera_view_13.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_13.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_13.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_13.setScaledContents(False)
        self.camera_view_13.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_13, 3, 0, 1, 1)

        self.camera_view_10 = QLabel(self.live_page)
        self.camera_view_10.setObjectName(u"camera_view_10")
        sizePolicy3.setHeightForWidth(self.camera_view_10.sizePolicy().hasHeightForWidth())
        self.camera_view_10.setSizePolicy(sizePolicy3)
        self.camera_view_10.setMinimumSize(QSize(200, 121))
        self.camera_view_10.setFont(font10)
        self.camera_view_10.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_10.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_10.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_10.setScaledContents(False)
        self.camera_view_10.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_10, 2, 1, 1, 1)

        self.camera_view_3 = QLabel(self.live_page)
        self.camera_view_3.setObjectName(u"camera_view_3")
        sizePolicy3.setHeightForWidth(self.camera_view_3.sizePolicy().hasHeightForWidth())
        self.camera_view_3.setSizePolicy(sizePolicy3)
        self.camera_view_3.setMinimumSize(QSize(200, 121))
        self.camera_view_3.setFont(font10)
        self.camera_view_3.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_3.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_3.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_3.setScaledContents(False)
        self.camera_view_3.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_3, 0, 2, 1, 1)

        self.camera_view_8 = QLabel(self.live_page)
        self.camera_view_8.setObjectName(u"camera_view_8")
        sizePolicy3.setHeightForWidth(self.camera_view_8.sizePolicy().hasHeightForWidth())
        self.camera_view_8.setSizePolicy(sizePolicy3)
        self.camera_view_8.setMinimumSize(QSize(200, 121))
        self.camera_view_8.setFont(font10)
        self.camera_view_8.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.camera_view_8.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"color: rgb(255, 255, 255);")
        self.camera_view_8.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
        self.camera_view_8.setScaledContents(False)
        self.camera_view_8.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_2.addWidget(self.camera_view_8, 1, 3, 1, 1)


        self.horizontalLayout_9.addLayout(self.gridLayout_2)

        self.stackedWidget.addWidget(self.live_page)
        self.camera_page = QWidget()
        self.camera_page.setObjectName(u"camera_page")
        self.verticalLayout_47 = QVBoxLayout(self.camera_page)
        self.verticalLayout_47.setObjectName(u"verticalLayout_47")
        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.widget = QWidget(self.camera_page)
        self.widget.setObjectName(u"widget")
        self.widget.setMinimumSize(QSize(301, 351))
        self.widget.setMaximumSize(QSize(350, 9999))
        self.horizontalLayout_17 = QHBoxLayout(self.widget)
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.camera_page_camera_name_label = QLabel(self.widget)
        self.camera_page_camera_name_label.setObjectName(u"camera_page_camera_name_label")
        sizePolicy1.setHeightForWidth(self.camera_page_camera_name_label.sizePolicy().hasHeightForWidth())
        self.camera_page_camera_name_label.setSizePolicy(sizePolicy1)
        self.camera_page_camera_name_label.setMinimumSize(QSize(93, 31))
        font11 = QFont()
        font11.setFamilies([u"Sans"])
        font11.setPointSize(12)
        font11.setBold(True)
        self.camera_page_camera_name_label.setFont(font11)
        self.camera_page_camera_name_label.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.camera_page_camera_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_10.addWidget(self.camera_page_camera_name_label)

        self.camera_page_name_box = QComboBox(self.widget)
        self.camera_page_name_box.setObjectName(u"camera_page_name_box")
        self.camera_page_name_box.setMinimumSize(QSize(141, 39))
        self.camera_page_name_box.setMaximumSize(QSize(145, 39))
        font12 = QFont()
        font12.setFamilies([u"Sans"])
        font12.setPointSize(11)
        self.camera_page_name_box.setFont(font12)
        self.camera_page_name_box.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.camera_page_name_box.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.camera_page_name_box.setCurrentText(u"")

        self.horizontalLayout_10.addWidget(self.camera_page_name_box)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer_6)


        self.verticalLayout_9.addLayout(self.horizontalLayout_10)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.camera_page_camera_event_label = QLabel(self.widget)
        self.camera_page_camera_event_label.setObjectName(u"camera_page_camera_event_label")
        sizePolicy1.setHeightForWidth(self.camera_page_camera_event_label.sizePolicy().hasHeightForWidth())
        self.camera_page_camera_event_label.setSizePolicy(sizePolicy1)
        self.camera_page_camera_event_label.setMinimumSize(QSize(81, 31))
        self.camera_page_camera_event_label.setFont(font11)
        self.camera_page_camera_event_label.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.camera_page_camera_event_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_11.addWidget(self.camera_page_camera_event_label)

        self.camera_page_camera_event_box = QComboBox(self.widget)
        self.camera_page_camera_event_box.addItem("")
        self.camera_page_camera_event_box.addItem("")
        self.camera_page_camera_event_box.addItem("")
        self.camera_page_camera_event_box.addItem("")
        self.camera_page_camera_event_box.setObjectName(u"camera_page_camera_event_box")
        self.camera_page_camera_event_box.setMinimumSize(QSize(141, 39))
        self.camera_page_camera_event_box.setMaximumSize(QSize(141, 39))
        font13 = QFont()
        font13.setFamilies([u"Sans"])
        font13.setPointSize(11)
        font13.setBold(False)
        self.camera_page_camera_event_box.setFont(font13)
        self.camera_page_camera_event_box.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.camera_page_camera_event_box.setMinimumContentsLength(0)

        self.horizontalLayout_11.addWidget(self.camera_page_camera_event_box)

        self.camera_page_detect_add_bnt = QPushButton(self.widget)
        self.camera_page_detect_add_bnt.setObjectName(u"camera_page_detect_add_bnt")
        sizePolicy1.setHeightForWidth(self.camera_page_detect_add_bnt.sizePolicy().hasHeightForWidth())
        self.camera_page_detect_add_bnt.setSizePolicy(sizePolicy1)
        self.camera_page_detect_add_bnt.setMinimumSize(QSize(31, 31))
        self.camera_page_detect_add_bnt.setFont(font2)
        self.camera_page_detect_add_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_page_detect_add_bnt.setStyleSheet(u"background-color: rgb(3, 3, 13);\n"
"border: 1px solid rgb(3, 3, 13);\n"
"color: rgb(255, 255, 255);\n"
"\n"
"")
        icon4 = QIcon()
        icon4.addFile(u":/newPrefix/images/ico_add_circle.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.camera_page_detect_add_bnt.setIcon(icon4)
        self.camera_page_detect_add_bnt.setIconSize(QSize(31, 50))

        self.horizontalLayout_11.addWidget(self.camera_page_detect_add_bnt)

        self.horizontalSpacer_15 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_11.addItem(self.horizontalSpacer_15)


        self.verticalLayout_9.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.camera_page_detect_area_table = QTableWidget(self.widget)
        if (self.camera_page_detect_area_table.columnCount() < 1):
            self.camera_page_detect_area_table.setColumnCount(1)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.camera_page_detect_area_table.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        self.camera_page_detect_area_table.setObjectName(u"camera_page_detect_area_table")
        self.camera_page_detect_area_table.setMinimumSize(QSize(120, 400))
        self.camera_page_detect_area_table.setMaximumSize(QSize(231, 9999))
        self.camera_page_detect_area_table.setFont(font)
        self.camera_page_detect_area_table.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);")
        self.camera_page_detect_area_table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        self.camera_page_detect_area_table.setDragDropOverwriteMode(False)
        self.camera_page_detect_area_table.setAlternatingRowColors(False)
        self.camera_page_detect_area_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.camera_page_detect_area_table.setShowGrid(False)
        self.camera_page_detect_area_table.setGridStyle(Qt.PenStyle.NoPen)
        self.camera_page_detect_area_table.setWordWrap(False)
        self.camera_page_detect_area_table.setCornerButtonEnabled(False)
        self.camera_page_detect_area_table.horizontalHeader().setHighlightSections(False)
        self.camera_page_detect_area_table.horizontalHeader().setStretchLastSection(True)
        self.camera_page_detect_area_table.verticalHeader().setVisible(False)
        self.camera_page_detect_area_table.verticalHeader().setHighlightSections(False)

        self.horizontalLayout_12.addWidget(self.camera_page_detect_area_table)

        self.horizontalSpacer_7 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_12.addItem(self.horizontalSpacer_7)


        self.verticalLayout_9.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalSpacer_8 = QSpacerItem(166, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_8)

        self.camera_page_detect_area_del_bnt = QPushButton(self.widget)
        self.camera_page_detect_area_del_bnt.setObjectName(u"camera_page_detect_area_del_bnt")
        sizePolicy1.setHeightForWidth(self.camera_page_detect_area_del_bnt.sizePolicy().hasHeightForWidth())
        self.camera_page_detect_area_del_bnt.setSizePolicy(sizePolicy1)
        self.camera_page_detect_area_del_bnt.setMinimumSize(QSize(61, 31))
        self.camera_page_detect_area_del_bnt.setMaximumSize(QSize(61, 31))
        self.camera_page_detect_area_del_bnt.setFont(font2)
        self.camera_page_detect_area_del_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_page_detect_area_del_bnt.setStyleSheet(u"\n"
"background-color: rgb(237, 51, 59);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 10px;\n"
"border: 1px solid rgb(255, 255, 255);\n"
"")

        self.horizontalLayout_13.addWidget(self.camera_page_detect_area_del_bnt)

        self.horizontalSpacer_12 = QSpacerItem(25, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_12)


        self.verticalLayout_9.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.camera_page_camera_event_label_2 = QLabel(self.widget)
        self.camera_page_camera_event_label_2.setObjectName(u"camera_page_camera_event_label_2")
        sizePolicy1.setHeightForWidth(self.camera_page_camera_event_label_2.sizePolicy().hasHeightForWidth())
        self.camera_page_camera_event_label_2.setSizePolicy(sizePolicy1)
        self.camera_page_camera_event_label_2.setMinimumSize(QSize(111, 31))
        font14 = QFont()
        font14.setFamilies([u"Sans Serif"])
        font14.setPointSize(10)
        font14.setBold(False)
        self.camera_page_camera_event_label_2.setFont(font14)
        self.camera_page_camera_event_label_2.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.camera_page_camera_event_label_2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_14.addWidget(self.camera_page_camera_event_label_2)

        self.camera_page_person_conf_slider = QSlider(self.widget)
        self.camera_page_person_conf_slider.setObjectName(u"camera_page_person_conf_slider")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.camera_page_person_conf_slider.sizePolicy().hasHeightForWidth())
        self.camera_page_person_conf_slider.setSizePolicy(sizePolicy4)
        self.camera_page_person_conf_slider.setMinimumSize(QSize(121, 31))
        self.camera_page_person_conf_slider.setMaximumSize(QSize(16777215, 31))
        font15 = QFont()
        font15.setPointSize(11)
        self.camera_page_person_conf_slider.setFont(font15)
        self.camera_page_person_conf_slider.setStyleSheet(u"QSlider::handle:horizontal {\n"
"    	background-color: rgb(192, 191, 188);\n"
"        border: 1px solid #5c5c5c; /* \ud578\ub4e4\uc758 \ud14c\ub450\ub9ac */\n"
"        width: 20px; /* \ud578\ub4e4\uc758 \ub108\ube44 */\n"
"        margin: -2px 0; /* \ud578\ub4e4\uc758 \uc704, \uc544\ub798 \uc5ec\ubc31 */\n"
"        border-radius: 4px; /* \ud578\ub4e4\uc758 \ubaa8\uc11c\ub9ac \ub465\uae00\uac8c */\n"
"    }")
        self.camera_page_person_conf_slider.setMinimum(0)
        self.camera_page_person_conf_slider.setSingleStep(2)
        self.camera_page_person_conf_slider.setValue(33)
        self.camera_page_person_conf_slider.setOrientation(Qt.Orientation.Horizontal)

        self.horizontalLayout_14.addWidget(self.camera_page_person_conf_slider)

        self.camera_page_person_conf_value = QSpinBox(self.widget)
        self.camera_page_person_conf_value.setObjectName(u"camera_page_person_conf_value")
        sizePolicy1.setHeightForWidth(self.camera_page_person_conf_value.sizePolicy().hasHeightForWidth())
        self.camera_page_person_conf_value.setSizePolicy(sizePolicy1)
        self.camera_page_person_conf_value.setMinimumSize(QSize(51, 31))
        self.camera_page_person_conf_value.setMaximumSize(QSize(16777215, 31))
        self.camera_page_person_conf_value.setFont(font15)
        self.camera_page_person_conf_value.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.camera_page_person_conf_value.setMinimum(1)
        self.camera_page_person_conf_value.setValue(33)

        self.horizontalLayout_14.addWidget(self.camera_page_person_conf_value)

        self.horizontalSpacer_16 = QSpacerItem(20, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_14.addItem(self.horizontalSpacer_16)


        self.verticalLayout_9.addLayout(self.horizontalLayout_14)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.horizontalSpacer_13 = QSpacerItem(166, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_13)

        self.camera_page_ai_bnt = QPushButton(self.widget)
        self.camera_page_ai_bnt.setObjectName(u"camera_page_ai_bnt")
        sizePolicy1.setHeightForWidth(self.camera_page_ai_bnt.sizePolicy().hasHeightForWidth())
        self.camera_page_ai_bnt.setSizePolicy(sizePolicy1)
        self.camera_page_ai_bnt.setMinimumSize(QSize(141, 41))
        self.camera_page_ai_bnt.setFont(font2)
        self.camera_page_ai_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.camera_page_ai_bnt.setStyleSheet(u"background-color: rgb(36, 39, 44);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 20px;\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"\n"
"")

        self.horizontalLayout_15.addWidget(self.camera_page_ai_bnt)

        self.horizontalSpacer_17 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_17)


        self.verticalLayout_9.addLayout(self.horizontalLayout_15)

        self.verticalSpacer = QSpacerItem(20, 270, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        self.verticalLayout_9.addItem(self.verticalSpacer)


        self.horizontalLayout_17.addLayout(self.verticalLayout_9)


        self.horizontalLayout_16.addWidget(self.widget)

        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.widget_5 = QWidget(self.camera_page)
        self.widget_5.setObjectName(u"widget_5")
        self.widget_5.setMinimumSize(QSize(0, 0))
        self.widget_5.setMaximumSize(QSize(16777215, 50))
        self.verticalLayout_30 = QVBoxLayout(self.widget_5)
        self.verticalLayout_30.setObjectName(u"verticalLayout_30")
        self.horizontalLayout_54 = QHBoxLayout()
        self.horizontalLayout_54.setObjectName(u"horizontalLayout_54")
        self.horizontalSpacer_14 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_54.addItem(self.horizontalSpacer_14)

        self.camera_page_ai_active_icon = QLabel(self.widget_5)
        self.camera_page_ai_active_icon.setObjectName(u"camera_page_ai_active_icon")
        sizePolicy1.setHeightForWidth(self.camera_page_ai_active_icon.sizePolicy().hasHeightForWidth())
        self.camera_page_ai_active_icon.setSizePolicy(sizePolicy1)
        self.camera_page_ai_active_icon.setMinimumSize(QSize(21, 21))
        self.camera_page_ai_active_icon.setMaximumSize(QSize(21, 21))
        self.camera_page_ai_active_icon.setFont(font)
        self.camera_page_ai_active_icon.setStyleSheet(u"color: rgb(242, 18, 94);")
        self.camera_page_ai_active_icon.setPixmap(QPixmap(u":/newPrefix/images/ico_analysis_on.svg"))
        self.camera_page_ai_active_icon.setScaledContents(True)

        self.horizontalLayout_54.addWidget(self.camera_page_ai_active_icon)

        self.camera_page_ai_active_label = QLabel(self.widget_5)
        self.camera_page_ai_active_label.setObjectName(u"camera_page_ai_active_label")
        sizePolicy1.setHeightForWidth(self.camera_page_ai_active_label.sizePolicy().hasHeightForWidth())
        self.camera_page_ai_active_label.setSizePolicy(sizePolicy1)
        self.camera_page_ai_active_label.setMinimumSize(QSize(130, 21))
        self.camera_page_ai_active_label.setMaximumSize(QSize(130, 21))
        font16 = QFont()
        font16.setFamilies([u"Sans"])
        font16.setPointSize(12)
        self.camera_page_ai_active_label.setFont(font16)
        self.camera_page_ai_active_label.setStyleSheet(u"color: rgb(242, 18, 94);")

        self.horizontalLayout_54.addWidget(self.camera_page_ai_active_label)


        self.verticalLayout_30.addLayout(self.horizontalLayout_54)


        self.verticalLayout_15.addWidget(self.widget_5)

        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalSpacer_26 = QSpacerItem(20, 3, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_10.addItem(self.verticalSpacer_26)

        self.camera_page_viewer = QLabel(self.camera_page)
        self.camera_page_viewer.setObjectName(u"camera_page_viewer")
        sizePolicy3.setHeightForWidth(self.camera_page_viewer.sizePolicy().hasHeightForWidth())
        self.camera_page_viewer.setSizePolicy(sizePolicy3)
        self.camera_page_viewer.setMinimumSize(QSize(472, 360))
        self.camera_page_viewer.setMaximumSize(QSize(9999, 9999))
        self.camera_page_viewer.setFont(font)
        self.camera_page_viewer.setStyleSheet(u"border: 1px solid rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.camera_page_viewer.setScaledContents(False)

        self.verticalLayout_10.addWidget(self.camera_page_viewer)

        self.verticalSpacer_27 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.verticalLayout_10.addItem(self.verticalSpacer_27)


        self.verticalLayout_15.addLayout(self.verticalLayout_10)


        self.horizontalLayout_16.addLayout(self.verticalLayout_15)


        self.verticalLayout_47.addLayout(self.horizontalLayout_16)

        self.stackedWidget.addWidget(self.camera_page)
        self.setting_page = QWidget()
        self.setting_page.setObjectName(u"setting_page")
        self.verticalLayout_53 = QVBoxLayout(self.setting_page)
        self.verticalLayout_53.setObjectName(u"verticalLayout_53")
        self.horizontalLayout_49 = QHBoxLayout()
        self.horizontalLayout_49.setObjectName(u"horizontalLayout_49")
        self.setting_page_tab = QWidget(self.setting_page)
        self.setting_page_tab.setObjectName(u"setting_page_tab")
        self.setting_page_tab.setMinimumSize(QSize(190, 0))
        self.setting_page_tab.setMaximumSize(QSize(190, 16777215))
        self.verticalLayout_31 = QVBoxLayout(self.setting_page_tab)
        self.verticalLayout_31.setObjectName(u"verticalLayout_31")
        self.verticalLayout_32 = QVBoxLayout()
        self.verticalLayout_32.setObjectName(u"verticalLayout_32")
        self.setting_alarm_bnt = QPushButton(self.setting_page_tab)
        self.setting_alarm_bnt.setObjectName(u"setting_alarm_bnt")
        self.setting_alarm_bnt.setMinimumSize(QSize(171, 41))
        self.setting_alarm_bnt.setMaximumSize(QSize(171, 41))
        self.setting_alarm_bnt.setFont(font12)
        self.setting_alarm_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.setting_alarm_bnt.setStyleSheet(u"border-radius: 20px;\n"
"border: 1px solid rgb(179,179,179);\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(0, 0, 0, 0);\n"
"")
        self.setting_alarm_bnt.setCheckable(True)
        self.setting_alarm_bnt.setChecked(False)
        self.setting_alarm_bnt.setAutoExclusive(True)

        self.verticalLayout_32.addWidget(self.setting_alarm_bnt)

        self.setting_user_setting_bnt = QPushButton(self.setting_page_tab)
        self.setting_user_setting_bnt.setObjectName(u"setting_user_setting_bnt")
        self.setting_user_setting_bnt.setMinimumSize(QSize(171, 41))
        self.setting_user_setting_bnt.setMaximumSize(QSize(171, 41))
        self.setting_user_setting_bnt.setFont(font12)
        self.setting_user_setting_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.setting_user_setting_bnt.setStyleSheet(u"border-radius: 20px;\n"
"border: 1px solid rgb(179,179,179);\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(0, 0, 0, 0);\n"
"")
        self.setting_user_setting_bnt.setCheckable(True)
        self.setting_user_setting_bnt.setChecked(False)
        self.setting_user_setting_bnt.setAutoExclusive(True)

        self.verticalLayout_32.addWidget(self.setting_user_setting_bnt)

        self.verticalSpacer_8 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_32.addItem(self.verticalSpacer_8)


        self.verticalLayout_31.addLayout(self.verticalLayout_32)


        self.horizontalLayout_49.addWidget(self.setting_page_tab)

        self.setting_stack_widget = QStackedWidget(self.setting_page)
        self.setting_stack_widget.setObjectName(u"setting_stack_widget")
        self.setting_stack_widget.setStyleSheet(u"border-radius: 20px;\n"
"background-color: rgb(13, 16, 23);")
        self.setting_stack_widget.setFrameShape(QFrame.Shape.Box)
        self.setting_stack_widget.setFrameShadow(QFrame.Shadow.Plain)
        self.setting_notice_tab = QWidget()
        self.setting_notice_tab.setObjectName(u"setting_notice_tab")
        self.verticalLayout_14 = QVBoxLayout(self.setting_notice_tab)
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.horizontalLayout_52 = QHBoxLayout()
        self.horizontalLayout_52.setObjectName(u"horizontalLayout_52")
        self.horizontalSpacer_46 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_52.addItem(self.horizontalSpacer_46)

        self.verticalLayout_13 = QVBoxLayout()
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.verticalSpacer_25 = QSpacerItem(20, 14, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_13.addItem(self.verticalSpacer_25)

        self.verticalLayout_26 = QVBoxLayout()
        self.verticalLayout_26.setSpacing(1)
        self.verticalLayout_26.setObjectName(u"verticalLayout_26")
        self.horizontalLayout_29 = QHBoxLayout()
        self.horizontalLayout_29.setObjectName(u"horizontalLayout_29")
        self.horizontalSpacer_34 = QSpacerItem(0, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_29.addItem(self.horizontalSpacer_34)

        self.setting_detect_info_label = QLabel(self.setting_notice_tab)
        self.setting_detect_info_label.setObjectName(u"setting_detect_info_label")
        self.setting_detect_info_label.setMinimumSize(QSize(176, 28))
        self.setting_detect_info_label.setMaximumSize(QSize(176, 28))
        self.setting_detect_info_label.setFont(font12)
        self.setting_detect_info_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_detect_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_29.addWidget(self.setting_detect_info_label)

        self.horizontalSpacer_28 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_29.addItem(self.horizontalSpacer_28)


        self.verticalLayout_26.addLayout(self.horizontalLayout_29)

        self.horizontalLayout_30 = QHBoxLayout()
        self.horizontalLayout_30.setObjectName(u"horizontalLayout_30")
        self.horizontalSpacer_32 = QSpacerItem(85, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_30.addItem(self.horizontalSpacer_32)

        self.verticalLayout_22 = QVBoxLayout()
        self.verticalLayout_22.setSpacing(11)
        self.verticalLayout_22.setObjectName(u"verticalLayout_22")
        self.horizontalLayout_28 = QHBoxLayout()
        self.horizontalLayout_28.setObjectName(u"horizontalLayout_28")
        self.setting_detect_bbox_active_label = QLabel(self.setting_notice_tab)
        self.setting_detect_bbox_active_label.setObjectName(u"setting_detect_bbox_active_label")
        self.setting_detect_bbox_active_label.setMinimumSize(QSize(91, 28))
        self.setting_detect_bbox_active_label.setMaximumSize(QSize(91, 28))
        self.setting_detect_bbox_active_label.setFont(font12)
        self.setting_detect_bbox_active_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_detect_bbox_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_28.addWidget(self.setting_detect_bbox_active_label)

        self.setting_detect_bbox_active_bnt = QPushButton(self.setting_notice_tab)
        self.setting_detect_bbox_active_bnt.setObjectName(u"setting_detect_bbox_active_bnt")
        self.setting_detect_bbox_active_bnt.setMinimumSize(QSize(61, 25))
        self.setting_detect_bbox_active_bnt.setMaximumSize(QSize(61, 25))
        icon5 = QIcon()
        icon5.addFile(u":/newPrefix/images/icon-switch-off.png", QSize(), QIcon.Normal, QIcon.Off)
        icon5.addFile(u":/newPrefix/images/icon-switch-on.png", QSize(), QIcon.Normal, QIcon.On)
        icon5.addFile(u":/newPrefix/images/icon-switch-on.png", QSize(), QIcon.Disabled, QIcon.On)
        self.setting_detect_bbox_active_bnt.setIcon(icon5)
        self.setting_detect_bbox_active_bnt.setIconSize(QSize(55, 103))
        self.setting_detect_bbox_active_bnt.setCheckable(True)

        self.horizontalLayout_28.addWidget(self.setting_detect_bbox_active_bnt)

        self.horizontalSpacer_27 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_28.addItem(self.horizontalSpacer_27)


        self.verticalLayout_22.addLayout(self.horizontalLayout_28)

        self.horizontalLayout_27 = QHBoxLayout()
        self.horizontalLayout_27.setObjectName(u"horizontalLayout_27")
        self.setting_detect_label_active_label = QLabel(self.setting_notice_tab)
        self.setting_detect_label_active_label.setObjectName(u"setting_detect_label_active_label")
        self.setting_detect_label_active_label.setMinimumSize(QSize(91, 28))
        self.setting_detect_label_active_label.setMaximumSize(QSize(91, 28))
        self.setting_detect_label_active_label.setFont(font12)
        self.setting_detect_label_active_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_detect_label_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_27.addWidget(self.setting_detect_label_active_label)

        self.setting_detect_label_active_bnt = QPushButton(self.setting_notice_tab)
        self.setting_detect_label_active_bnt.setObjectName(u"setting_detect_label_active_bnt")
        self.setting_detect_label_active_bnt.setMinimumSize(QSize(61, 25))
        self.setting_detect_label_active_bnt.setMaximumSize(QSize(61, 25))
        self.setting_detect_label_active_bnt.setIcon(icon5)
        self.setting_detect_label_active_bnt.setIconSize(QSize(55, 103))
        self.setting_detect_label_active_bnt.setCheckable(True)

        self.horizontalLayout_27.addWidget(self.setting_detect_label_active_bnt)

        self.horizontalSpacer_26 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_27.addItem(self.horizontalSpacer_26)


        self.verticalLayout_22.addLayout(self.horizontalLayout_27)


        self.horizontalLayout_30.addLayout(self.verticalLayout_22)


        self.verticalLayout_26.addLayout(self.horizontalLayout_30)


        self.verticalLayout_13.addLayout(self.verticalLayout_26)

        self.verticalSpacer_5 = QSpacerItem(20, 13, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_13.addItem(self.verticalSpacer_5)

        self.verticalLayout_25 = QVBoxLayout()
        self.verticalLayout_25.setSpacing(1)
        self.verticalLayout_25.setObjectName(u"verticalLayout_25")
        self.horizontalLayout_26 = QHBoxLayout()
        self.horizontalLayout_26.setObjectName(u"horizontalLayout_26")
        self.setting_video_save_alarm_active_label = QLabel(self.setting_notice_tab)
        self.setting_video_save_alarm_active_label.setObjectName(u"setting_video_save_alarm_active_label")
        self.setting_video_save_alarm_active_label.setMinimumSize(QSize(161, 28))
        self.setting_video_save_alarm_active_label.setMaximumSize(QSize(161, 28))
        self.setting_video_save_alarm_active_label.setFont(font12)
        self.setting_video_save_alarm_active_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_video_save_alarm_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_26.addWidget(self.setting_video_save_alarm_active_label)

        self.setting_video_save_alarm_active_bnt = QPushButton(self.setting_notice_tab)
        self.setting_video_save_alarm_active_bnt.setObjectName(u"setting_video_save_alarm_active_bnt")
        self.setting_video_save_alarm_active_bnt.setMinimumSize(QSize(61, 25))
        self.setting_video_save_alarm_active_bnt.setMaximumSize(QSize(61, 25))
        self.setting_video_save_alarm_active_bnt.setIcon(icon5)
        self.setting_video_save_alarm_active_bnt.setIconSize(QSize(55, 103))
        self.setting_video_save_alarm_active_bnt.setCheckable(True)

        self.horizontalLayout_26.addWidget(self.setting_video_save_alarm_active_bnt)

        self.horizontalSpacer_25 = QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_26.addItem(self.horizontalSpacer_25)


        self.verticalLayout_25.addLayout(self.horizontalLayout_26)

        self.horizontalLayout_25 = QHBoxLayout()
        self.horizontalLayout_25.setObjectName(u"horizontalLayout_25")
        self.horizontalSpacer_31 = QSpacerItem(85, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_25.addItem(self.horizontalSpacer_31)

        self.setting_event_video_storage_period_label = QLabel(self.setting_notice_tab)
        self.setting_event_video_storage_period_label.setObjectName(u"setting_event_video_storage_period_label")
        self.setting_event_video_storage_period_label.setMinimumSize(QSize(141, 28))
        self.setting_event_video_storage_period_label.setMaximumSize(QSize(141, 28))
        self.setting_event_video_storage_period_label.setFont(font12)
        self.setting_event_video_storage_period_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_event_video_storage_period_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_25.addWidget(self.setting_event_video_storage_period_label)

        self.setting_event_video_storage_period = QComboBox(self.setting_notice_tab)
        self.setting_event_video_storage_period.addItem("")
        self.setting_event_video_storage_period.addItem("")
        self.setting_event_video_storage_period.addItem("")
        self.setting_event_video_storage_period.setObjectName(u"setting_event_video_storage_period")
        self.setting_event_video_storage_period.setMinimumSize(QSize(61, 31))
        self.setting_event_video_storage_period.setMaximumSize(QSize(61, 31))
        self.setting_event_video_storage_period.setFont(font12)
        self.setting_event_video_storage_period.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.setting_event_video_storage_period.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.setting_event_video_storage_period.setCurrentText(u"30\uc77c")

        self.horizontalLayout_25.addWidget(self.setting_event_video_storage_period)

        self.horizontalSpacer_24 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_25.addItem(self.horizontalSpacer_24)


        self.verticalLayout_25.addLayout(self.horizontalLayout_25)


        self.verticalLayout_13.addLayout(self.verticalLayout_25)

        self.verticalSpacer_6 = QSpacerItem(20, 13, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_13.addItem(self.verticalSpacer_6)

        self.horizontalLayout_24 = QHBoxLayout()
        self.horizontalLayout_24.setObjectName(u"horizontalLayout_24")
        self.horizontalSpacer_30 = QSpacerItem(3, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_24.addItem(self.horizontalSpacer_30)

        self.setting_popup_alarm_active_label = QLabel(self.setting_notice_tab)
        self.setting_popup_alarm_active_label.setObjectName(u"setting_popup_alarm_active_label")
        self.setting_popup_alarm_active_label.setMinimumSize(QSize(141, 28))
        self.setting_popup_alarm_active_label.setMaximumSize(QSize(141, 28))
        self.setting_popup_alarm_active_label.setFont(font12)
        self.setting_popup_alarm_active_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_popup_alarm_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_24.addWidget(self.setting_popup_alarm_active_label)

        self.setting_popup_alarm_active_bnt = QPushButton(self.setting_notice_tab)
        self.setting_popup_alarm_active_bnt.setObjectName(u"setting_popup_alarm_active_bnt")
        self.setting_popup_alarm_active_bnt.setMinimumSize(QSize(61, 25))
        self.setting_popup_alarm_active_bnt.setMaximumSize(QSize(61, 25))
        self.setting_popup_alarm_active_bnt.setIcon(icon5)
        self.setting_popup_alarm_active_bnt.setIconSize(QSize(55, 103))
        self.setting_popup_alarm_active_bnt.setCheckable(True)

        self.horizontalLayout_24.addWidget(self.setting_popup_alarm_active_bnt)

        self.horizontalSpacer_23 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_24.addItem(self.horizontalSpacer_23)


        self.verticalLayout_13.addLayout(self.horizontalLayout_24)

        self.horizontalLayout_23 = QHBoxLayout()
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.horizontalSpacer_29 = QSpacerItem(85, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_23.addItem(self.horizontalSpacer_29)

        self.setting_popup_alarm_cnt_label = QLabel(self.setting_notice_tab)
        self.setting_popup_alarm_cnt_label.setObjectName(u"setting_popup_alarm_cnt_label")
        self.setting_popup_alarm_cnt_label.setMinimumSize(QSize(121, 28))
        self.setting_popup_alarm_cnt_label.setMaximumSize(QSize(121, 28))
        self.setting_popup_alarm_cnt_label.setFont(font12)
        self.setting_popup_alarm_cnt_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_popup_alarm_cnt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_23.addWidget(self.setting_popup_alarm_cnt_label)

        self.setting_popup_alarm_cnt = QComboBox(self.setting_notice_tab)
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.addItem("")
        self.setting_popup_alarm_cnt.setObjectName(u"setting_popup_alarm_cnt")
        self.setting_popup_alarm_cnt.setMinimumSize(QSize(61, 31))
        self.setting_popup_alarm_cnt.setMaximumSize(QSize(61, 31))
        self.setting_popup_alarm_cnt.setFont(font12)
        self.setting_popup_alarm_cnt.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.setting_popup_alarm_cnt.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.setting_popup_alarm_cnt.setCurrentText(u"3")

        self.horizontalLayout_23.addWidget(self.setting_popup_alarm_cnt)

        self.horizontalSpacer_22 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_23.addItem(self.horizontalSpacer_22)


        self.verticalLayout_13.addLayout(self.horizontalLayout_23)

        self.verticalSpacer_7 = QSpacerItem(20, 13, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_13.addItem(self.verticalSpacer_7)

        self.horizontalLayout_22 = QHBoxLayout()
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.setting_email_active_label = QLabel(self.setting_notice_tab)
        self.setting_email_active_label.setObjectName(u"setting_email_active_label")
        self.setting_email_active_label.setMinimumSize(QSize(181, 28))
        self.setting_email_active_label.setMaximumSize(QSize(181, 28))
        self.setting_email_active_label.setFont(font12)
        self.setting_email_active_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_email_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_22.addWidget(self.setting_email_active_label)

        self.setting_email_active_bnt = QPushButton(self.setting_notice_tab)
        self.setting_email_active_bnt.setObjectName(u"setting_email_active_bnt")
        self.setting_email_active_bnt.setMinimumSize(QSize(61, 25))
        self.setting_email_active_bnt.setMaximumSize(QSize(61, 25))
        self.setting_email_active_bnt.setIcon(icon5)
        self.setting_email_active_bnt.setIconSize(QSize(55, 103))
        self.setting_email_active_bnt.setCheckable(True)

        self.horizontalLayout_22.addWidget(self.setting_email_active_bnt)

        self.horizontalSpacer_21 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_22.addItem(self.horizontalSpacer_21)


        self.verticalLayout_13.addLayout(self.horizontalLayout_22)

        self.horizontalLayout_51 = QHBoxLayout()
        self.horizontalLayout_51.setObjectName(u"horizontalLayout_51")
        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.horizontalSpacer_33 = QSpacerItem(13, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_19.addItem(self.horizontalSpacer_33)

        self.setting_email_active_id_label = QLabel(self.setting_notice_tab)
        self.setting_email_active_id_label.setObjectName(u"setting_email_active_id_label")
        self.setting_email_active_id_label.setMinimumSize(QSize(73, 28))
        self.setting_email_active_id_label.setMaximumSize(QSize(73, 28))
        self.setting_email_active_id_label.setFont(font12)
        self.setting_email_active_id_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_email_active_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_19.addWidget(self.setting_email_active_id_label)

        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.setting_email_id_input = QLineEdit(self.setting_notice_tab)
        self.setting_email_id_input.setObjectName(u"setting_email_id_input")
        self.setting_email_id_input.setMinimumSize(QSize(321, 0))
        self.setting_email_id_input.setMaximumSize(QSize(321, 17))
        self.setting_email_id_input.setFont(font2)
        self.setting_email_id_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setting_email_id_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")

        self.verticalLayout_16.addWidget(self.setting_email_id_input)

        self.setting_email_id_input_line = QFrame(self.setting_notice_tab)
        self.setting_email_id_input_line.setObjectName(u"setting_email_id_input_line")
        self.setting_email_id_input_line.setFont(font8)
        self.setting_email_id_input_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setting_email_id_input_line.setAutoFillBackground(False)
        self.setting_email_id_input_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.setting_email_id_input_line.setFrameShape(QFrame.Shape.HLine)
        self.setting_email_id_input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_16.addWidget(self.setting_email_id_input_line)


        self.horizontalLayout_19.addLayout(self.verticalLayout_16)


        self.verticalLayout_12.addLayout(self.horizontalLayout_19)

        self.horizontalLayout_48 = QHBoxLayout()
        self.horizontalLayout_48.setObjectName(u"horizontalLayout_48")
        self.horizontalSpacer_48 = QSpacerItem(13, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_48.addItem(self.horizontalSpacer_48)

        self.setting_email_active_pw_label = QLabel(self.setting_notice_tab)
        self.setting_email_active_pw_label.setObjectName(u"setting_email_active_pw_label")
        self.setting_email_active_pw_label.setMinimumSize(QSize(73, 28))
        self.setting_email_active_pw_label.setMaximumSize(QSize(73, 28))
        self.setting_email_active_pw_label.setFont(font12)
        self.setting_email_active_pw_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_email_active_pw_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_48.addWidget(self.setting_email_active_pw_label)

        self.verticalLayout_21 = QVBoxLayout()
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.setting_email_pw_input = QLineEdit(self.setting_notice_tab)
        self.setting_email_pw_input.setObjectName(u"setting_email_pw_input")
        self.setting_email_pw_input.setMinimumSize(QSize(321, 0))
        self.setting_email_pw_input.setMaximumSize(QSize(321, 17))
        self.setting_email_pw_input.setFont(font2)
        self.setting_email_pw_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setting_email_pw_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_email_pw_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.verticalLayout_21.addWidget(self.setting_email_pw_input)

        self.setting_email_pw_input_line = QFrame(self.setting_notice_tab)
        self.setting_email_pw_input_line.setObjectName(u"setting_email_pw_input_line")
        self.setting_email_pw_input_line.setFont(font8)
        self.setting_email_pw_input_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setting_email_pw_input_line.setAutoFillBackground(False)
        self.setting_email_pw_input_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.setting_email_pw_input_line.setFrameShape(QFrame.Shape.HLine)
        self.setting_email_pw_input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_21.addWidget(self.setting_email_pw_input_line)


        self.horizontalLayout_48.addLayout(self.verticalLayout_21)


        self.verticalLayout_12.addLayout(self.horizontalLayout_48)

        self.horizontalLayout_50 = QHBoxLayout()
        self.horizontalLayout_50.setObjectName(u"horizontalLayout_50")
        self.horizontalSpacer_49 = QSpacerItem(13, 13, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_50.addItem(self.horizontalSpacer_49)

        self.setting_email_active_to_id_label = QLabel(self.setting_notice_tab)
        self.setting_email_active_to_id_label.setObjectName(u"setting_email_active_to_id_label")
        self.setting_email_active_to_id_label.setMinimumSize(QSize(73, 28))
        self.setting_email_active_to_id_label.setMaximumSize(QSize(73, 28))
        self.setting_email_active_to_id_label.setFont(font12)
        self.setting_email_active_to_id_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_email_active_to_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_50.addWidget(self.setting_email_active_to_id_label)

        self.verticalLayout_27 = QVBoxLayout()
        self.verticalLayout_27.setObjectName(u"verticalLayout_27")
        self.setting_receive_email_id_input = QLineEdit(self.setting_notice_tab)
        self.setting_receive_email_id_input.setObjectName(u"setting_receive_email_id_input")
        self.setting_receive_email_id_input.setMinimumSize(QSize(321, 0))
        self.setting_receive_email_id_input.setMaximumSize(QSize(321, 17))
        self.setting_receive_email_id_input.setFont(font2)
        self.setting_receive_email_id_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setting_receive_email_id_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")

        self.verticalLayout_27.addWidget(self.setting_receive_email_id_input)

        self.setting_receive_email_id_input_line = QFrame(self.setting_notice_tab)
        self.setting_receive_email_id_input_line.setObjectName(u"setting_receive_email_id_input_line")
        self.setting_receive_email_id_input_line.setFont(font8)
        self.setting_receive_email_id_input_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setting_receive_email_id_input_line.setAutoFillBackground(False)
        self.setting_receive_email_id_input_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.setting_receive_email_id_input_line.setFrameShape(QFrame.Shape.HLine)
        self.setting_receive_email_id_input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_27.addWidget(self.setting_receive_email_id_input_line)


        self.horizontalLayout_50.addLayout(self.verticalLayout_27)


        self.verticalLayout_12.addLayout(self.horizontalLayout_50)


        self.horizontalLayout_51.addLayout(self.verticalLayout_12)

        self.horizontalSpacer_50 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_51.addItem(self.horizontalSpacer_50)


        self.verticalLayout_13.addLayout(self.horizontalLayout_51)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.verticalLayout_28 = QVBoxLayout()
        self.verticalLayout_28.setObjectName(u"verticalLayout_28")
        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.setting_page_email_info_label = QLabel(self.setting_notice_tab)
        self.setting_page_email_info_label.setObjectName(u"setting_page_email_info_label")
        sizePolicy1.setHeightForWidth(self.setting_page_email_info_label.sizePolicy().hasHeightForWidth())
        self.setting_page_email_info_label.setSizePolicy(sizePolicy1)
        self.setting_page_email_info_label.setMinimumSize(QSize(191, 21))
        self.setting_page_email_info_label.setMaximumSize(QSize(191, 21))
        self.setting_page_email_info_label.setFont(font2)
        self.setting_page_email_info_label.setStyleSheet(u"color: rgb(242, 18, 94);")

        self.horizontalLayout_21.addWidget(self.setting_page_email_info_label)

        self.horizontalSpacer_19 = QSpacerItem(128, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_21.addItem(self.horizontalSpacer_19)


        self.verticalLayout_28.addLayout(self.horizontalLayout_21)

        self.horizontalLayout_31 = QHBoxLayout()
        self.horizontalLayout_31.setObjectName(u"horizontalLayout_31")
        self.setting_page_email_info_label_2 = QLabel(self.setting_notice_tab)
        self.setting_page_email_info_label_2.setObjectName(u"setting_page_email_info_label_2")
        sizePolicy1.setHeightForWidth(self.setting_page_email_info_label_2.sizePolicy().hasHeightForWidth())
        self.setting_page_email_info_label_2.setSizePolicy(sizePolicy1)
        self.setting_page_email_info_label_2.setMinimumSize(QSize(281, 21))
        self.setting_page_email_info_label_2.setMaximumSize(QSize(281, 21))
        self.setting_page_email_info_label_2.setFont(font2)
        self.setting_page_email_info_label_2.setStyleSheet(u"color: rgb(242, 18, 94);")

        self.horizontalLayout_31.addWidget(self.setting_page_email_info_label_2)

        self.horizontalSpacer_20 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_31.addItem(self.horizontalSpacer_20)


        self.verticalLayout_28.addLayout(self.horizontalLayout_31)


        self.horizontalLayout_20.addLayout(self.verticalLayout_28)

        self.setting_email_save_bnt = QPushButton(self.setting_notice_tab)
        self.setting_email_save_bnt.setObjectName(u"setting_email_save_bnt")
        self.setting_email_save_bnt.setMinimumSize(QSize(91, 41))
        self.setting_email_save_bnt.setMaximumSize(QSize(91, 41))
        self.setting_email_save_bnt.setFont(font2)
        self.setting_email_save_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.setting_email_save_bnt.setStyleSheet(u"\n"
"background-color: qlineargradient(spread:pad, x1:0.244, y1:0.477, x2:1, y2:0.489, stop:0.0845771 rgba(0, 205, 0, 255), stop:1 rgba(56, 188, 56, 255));\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 20px;\n"
"")

        self.horizontalLayout_20.addWidget(self.setting_email_save_bnt)

        self.horizontalSpacer_51 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_51)


        self.verticalLayout_13.addLayout(self.horizontalLayout_20)

        self.verticalSpacer_12 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_13.addItem(self.verticalSpacer_12)


        self.horizontalLayout_52.addLayout(self.verticalLayout_13)

        self.horizontalSpacer_47 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_52.addItem(self.horizontalSpacer_47)


        self.verticalLayout_14.addLayout(self.horizontalLayout_52)

        self.setting_stack_widget.addWidget(self.setting_notice_tab)
        self.setting_user_setting_tab = QWidget()
        self.setting_user_setting_tab.setObjectName(u"setting_user_setting_tab")
        self.verticalLayout_51 = QVBoxLayout(self.setting_user_setting_tab)
        self.verticalLayout_51.setObjectName(u"verticalLayout_51")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_45 = QSpacerItem(15, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_45)

        self.verticalLayout_33 = QVBoxLayout()
        self.verticalLayout_33.setObjectName(u"verticalLayout_33")
        self.verticalSpacer_24 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_33.addItem(self.verticalSpacer_24)

        self.verticalLayout_29 = QVBoxLayout()
        self.verticalLayout_29.setObjectName(u"verticalLayout_29")
        self.horizontalLayout_40 = QHBoxLayout()
        self.horizontalLayout_40.setObjectName(u"horizontalLayout_40")
        self.horizontalSpacer_35 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_40.addItem(self.horizontalSpacer_35)

        self.setting_user_id_label = QLabel(self.setting_user_setting_tab)
        self.setting_user_id_label.setObjectName(u"setting_user_id_label")
        self.setting_user_id_label.setMinimumSize(QSize(43, 22))
        self.setting_user_id_label.setMaximumSize(QSize(43, 22))
        self.setting_user_id_label.setFont(font12)
        self.setting_user_id_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_user_id_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_40.addWidget(self.setting_user_id_label)

        self.verticalLayout_20 = QVBoxLayout()
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.setting_user_id_input = QLineEdit(self.setting_user_setting_tab)
        self.setting_user_id_input.setObjectName(u"setting_user_id_input")
        self.setting_user_id_input.setMinimumSize(QSize(439, 19))
        self.setting_user_id_input.setMaximumSize(QSize(439, 19))
        self.setting_user_id_input.setStyleSheet(u"color: rgb(255, 255, 255);")

        self.verticalLayout_20.addWidget(self.setting_user_id_input)

        self.setting_user_id_input_line = QFrame(self.setting_user_setting_tab)
        self.setting_user_id_input_line.setObjectName(u"setting_user_id_input_line")
        self.setting_user_id_input_line.setMinimumSize(QSize(439, 3))
        self.setting_user_id_input_line.setMaximumSize(QSize(439, 3))
        self.setting_user_id_input_line.setFont(font8)
        self.setting_user_id_input_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setting_user_id_input_line.setAutoFillBackground(False)
        self.setting_user_id_input_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.setting_user_id_input_line.setFrameShape(QFrame.Shape.HLine)
        self.setting_user_id_input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_20.addWidget(self.setting_user_id_input_line)


        self.horizontalLayout_40.addLayout(self.verticalLayout_20)


        self.verticalLayout_29.addLayout(self.horizontalLayout_40)

        self.horizontalLayout_39 = QHBoxLayout()
        self.horizontalLayout_39.setObjectName(u"horizontalLayout_39")
        self.setting_user_pw_label = QLabel(self.setting_user_setting_tab)
        self.setting_user_pw_label.setObjectName(u"setting_user_pw_label")
        self.setting_user_pw_label.setMinimumSize(QSize(87, 22))
        self.setting_user_pw_label.setMaximumSize(QSize(87, 22))
        self.setting_user_pw_label.setFont(font12)
        self.setting_user_pw_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_user_pw_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_39.addWidget(self.setting_user_pw_label)

        self.verticalLayout_19 = QVBoxLayout()
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.setting_user_pw_input = QLineEdit(self.setting_user_setting_tab)
        self.setting_user_pw_input.setObjectName(u"setting_user_pw_input")
        self.setting_user_pw_input.setMinimumSize(QSize(439, 19))
        self.setting_user_pw_input.setMaximumSize(QSize(439, 19))
        self.setting_user_pw_input.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.setting_user_pw_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.verticalLayout_19.addWidget(self.setting_user_pw_input)

        self.setting_user_pw_input_line = QFrame(self.setting_user_setting_tab)
        self.setting_user_pw_input_line.setObjectName(u"setting_user_pw_input_line")
        self.setting_user_pw_input_line.setMinimumSize(QSize(439, 3))
        self.setting_user_pw_input_line.setMaximumSize(QSize(439, 3))
        self.setting_user_pw_input_line.setFont(font8)
        self.setting_user_pw_input_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setting_user_pw_input_line.setAutoFillBackground(False)
        self.setting_user_pw_input_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.setting_user_pw_input_line.setFrameShape(QFrame.Shape.HLine)
        self.setting_user_pw_input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_19.addWidget(self.setting_user_pw_input_line)


        self.horizontalLayout_39.addLayout(self.verticalLayout_19)


        self.verticalLayout_29.addLayout(self.horizontalLayout_39)

        self.horizontalLayout_37 = QHBoxLayout()
        self.horizontalLayout_37.setObjectName(u"horizontalLayout_37")
        self.setting_user_new_pw_label = QLabel(self.setting_user_setting_tab)
        self.setting_user_new_pw_label.setObjectName(u"setting_user_new_pw_label")
        self.setting_user_new_pw_label.setMinimumSize(QSize(87, 22))
        self.setting_user_new_pw_label.setMaximumSize(QSize(87, 22))
        self.setting_user_new_pw_label.setFont(font12)
        self.setting_user_new_pw_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_user_new_pw_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_37.addWidget(self.setting_user_new_pw_label)

        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.setting_user_new_pw_input = QLineEdit(self.setting_user_setting_tab)
        self.setting_user_new_pw_input.setObjectName(u"setting_user_new_pw_input")
        self.setting_user_new_pw_input.setMinimumSize(QSize(439, 19))
        self.setting_user_new_pw_input.setMaximumSize(QSize(439, 19))
        self.setting_user_new_pw_input.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.setting_user_new_pw_input.setFrame(True)
        self.setting_user_new_pw_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.verticalLayout_17.addWidget(self.setting_user_new_pw_input)

        self.setting_user_new_pw_input_line = QFrame(self.setting_user_setting_tab)
        self.setting_user_new_pw_input_line.setObjectName(u"setting_user_new_pw_input_line")
        self.setting_user_new_pw_input_line.setMinimumSize(QSize(439, 3))
        self.setting_user_new_pw_input_line.setMaximumSize(QSize(439, 3))
        self.setting_user_new_pw_input_line.setFont(font8)
        self.setting_user_new_pw_input_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setting_user_new_pw_input_line.setAutoFillBackground(False)
        self.setting_user_new_pw_input_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.setting_user_new_pw_input_line.setFrameShape(QFrame.Shape.HLine)
        self.setting_user_new_pw_input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_17.addWidget(self.setting_user_new_pw_input_line)


        self.horizontalLayout_37.addLayout(self.verticalLayout_17)


        self.verticalLayout_29.addLayout(self.horizontalLayout_37)

        self.horizontalLayout_33 = QHBoxLayout()
        self.horizontalLayout_33.setObjectName(u"horizontalLayout_33")
        self.setting_user_new_pw_label2 = QLabel(self.setting_user_setting_tab)
        self.setting_user_new_pw_label2.setObjectName(u"setting_user_new_pw_label2")
        self.setting_user_new_pw_label2.setMinimumSize(QSize(87, 27))
        self.setting_user_new_pw_label2.setMaximumSize(QSize(87, 27))
        self.setting_user_new_pw_label2.setFont(font12)
        self.setting_user_new_pw_label2.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.setting_user_new_pw_label2.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_33.addWidget(self.setting_user_new_pw_label2)

        self.verticalLayout_18 = QVBoxLayout()
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.setting_user_new_pw_input2 = QLineEdit(self.setting_user_setting_tab)
        self.setting_user_new_pw_input2.setObjectName(u"setting_user_new_pw_input2")
        self.setting_user_new_pw_input2.setMinimumSize(QSize(439, 19))
        self.setting_user_new_pw_input2.setMaximumSize(QSize(439, 19))
        self.setting_user_new_pw_input2.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.setting_user_new_pw_input2.setEchoMode(QLineEdit.EchoMode.Password)

        self.verticalLayout_18.addWidget(self.setting_user_new_pw_input2)

        self.setting_user_new_pw_input2_line = QFrame(self.setting_user_setting_tab)
        self.setting_user_new_pw_input2_line.setObjectName(u"setting_user_new_pw_input2_line")
        self.setting_user_new_pw_input2_line.setMinimumSize(QSize(439, 3))
        self.setting_user_new_pw_input2_line.setMaximumSize(QSize(439, 3))
        self.setting_user_new_pw_input2_line.setFont(font8)
        self.setting_user_new_pw_input2_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setting_user_new_pw_input2_line.setAutoFillBackground(False)
        self.setting_user_new_pw_input2_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.setting_user_new_pw_input2_line.setFrameShape(QFrame.Shape.HLine)
        self.setting_user_new_pw_input2_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_18.addWidget(self.setting_user_new_pw_input2_line)


        self.horizontalLayout_33.addLayout(self.verticalLayout_18)


        self.verticalLayout_29.addLayout(self.horizontalLayout_33)

        self.horizontalLayout_41 = QHBoxLayout()
        self.horizontalLayout_41.setObjectName(u"horizontalLayout_41")
        self.horizontalSpacer_36 = QSpacerItem(442, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_41.addItem(self.horizontalSpacer_36)

        self.setting_user_save_bnt = QPushButton(self.setting_user_setting_tab)
        self.setting_user_save_bnt.setObjectName(u"setting_user_save_bnt")
        self.setting_user_save_bnt.setMinimumSize(QSize(71, 41))
        self.setting_user_save_bnt.setMaximumSize(QSize(71, 41))
        self.setting_user_save_bnt.setFont(font2)
        self.setting_user_save_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.setting_user_save_bnt.setStyleSheet(u"\n"
"background-color: qlineargradient(spread:pad, x1:0.244, y1:0.477, x2:1, y2:0.489, stop:0.0845771 rgba(0, 205, 0, 255), stop:1 rgba(56, 188, 56, 255));\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 20px;\n"
"\n"
"")

        self.horizontalLayout_41.addWidget(self.setting_user_save_bnt)


        self.verticalLayout_29.addLayout(self.horizontalLayout_41)


        self.verticalLayout_33.addLayout(self.verticalLayout_29)

        self.verticalSpacer_13 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_33.addItem(self.verticalSpacer_13)


        self.horizontalLayout_2.addLayout(self.verticalLayout_33)

        self.horizontalSpacer_44 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_44)


        self.verticalLayout_51.addLayout(self.horizontalLayout_2)

        self.setting_stack_widget.addWidget(self.setting_user_setting_tab)

        self.horizontalLayout_49.addWidget(self.setting_stack_widget)


        self.verticalLayout_53.addLayout(self.horizontalLayout_49)

        self.stackedWidget.addWidget(self.setting_page)
        self.admin_page = QWidget()
        self.admin_page.setObjectName(u"admin_page")
        self.verticalLayout_37 = QVBoxLayout(self.admin_page)
        self.verticalLayout_37.setObjectName(u"verticalLayout_37")
        self.verticalLayout_36 = QVBoxLayout()
        self.verticalLayout_36.setObjectName(u"verticalLayout_36")
        self.verticalSpacer_14 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_36.addItem(self.verticalSpacer_14)

        self.horizontalLayout_38 = QHBoxLayout()
        self.horizontalLayout_38.setObjectName(u"horizontalLayout_38")
        self.horizontalSpacer_37 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_38.addItem(self.horizontalSpacer_37)

        self.admin_pw_label = QLabel(self.admin_page)
        self.admin_pw_label.setObjectName(u"admin_pw_label")
        self.admin_pw_label.setMinimumSize(QSize(115, 46))
        self.admin_pw_label.setMaximumSize(QSize(115, 46))
        self.admin_pw_label.setFont(font16)
        self.admin_pw_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.admin_pw_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_38.addWidget(self.admin_pw_label)

        self.verticalLayout_35 = QVBoxLayout()
        self.verticalLayout_35.setSpacing(0)
        self.verticalLayout_35.setObjectName(u"verticalLayout_35")
        self.admin_pw_input = QLineEdit(self.admin_page)
        self.admin_pw_input.setObjectName(u"admin_pw_input")
        self.admin_pw_input.setMinimumSize(QSize(221, 21))
        self.admin_pw_input.setMaximumSize(QSize(221, 21))
        self.admin_pw_input.setFont(font2)
        self.admin_pw_input.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.admin_pw_input.setStyleSheet(u"qproperty-frame: false;\n"
"font-size:10pt;\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.admin_pw_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.verticalLayout_35.addWidget(self.admin_pw_input)

        self.admin_pw_input_line = QFrame(self.admin_page)
        self.admin_pw_input_line.setObjectName(u"admin_pw_input_line")
        self.admin_pw_input_line.setMinimumSize(QSize(221, 3))
        self.admin_pw_input_line.setMaximumSize(QSize(221, 3))
        self.admin_pw_input_line.setFont(font8)
        self.admin_pw_input_line.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.admin_pw_input_line.setAutoFillBackground(False)
        self.admin_pw_input_line.setStyleSheet(u"background-color: rgb(36, 39, 44)")
        self.admin_pw_input_line.setFrameShape(QFrame.Shape.HLine)
        self.admin_pw_input_line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_35.addWidget(self.admin_pw_input_line)


        self.horizontalLayout_38.addLayout(self.verticalLayout_35)

        self.admin_page_bnt = QPushButton(self.admin_page)
        self.admin_page_bnt.setObjectName(u"admin_page_bnt")
        self.admin_page_bnt.setMinimumSize(QSize(71, 41))
        self.admin_page_bnt.setMaximumSize(QSize(71, 41))
        self.admin_page_bnt.setFont(font2)
        self.admin_page_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.admin_page_bnt.setStyleSheet(u"\n"
"background-color: qlineargradient(spread:pad, x1:0.244, y1:0.477, x2:1, y2:0.489, stop:0.0845771 rgba(0, 205, 0, 255), stop:1 rgba(56, 188, 56, 255));\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 20px;\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"")

        self.horizontalLayout_38.addWidget(self.admin_page_bnt)

        self.horizontalSpacer_38 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_38.addItem(self.horizontalSpacer_38)


        self.verticalLayout_36.addLayout(self.horizontalLayout_38)

        self.verticalSpacer_15 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_36.addItem(self.verticalSpacer_15)


        self.verticalLayout_37.addLayout(self.verticalLayout_36)

        self.stackedWidget.addWidget(self.admin_page)
        self.admin_page_2 = QWidget()
        self.admin_page_2.setObjectName(u"admin_page_2")
        self.horizontalLayout_47 = QHBoxLayout(self.admin_page_2)
        self.horizontalLayout_47.setObjectName(u"horizontalLayout_47")
        self.widget_2 = QWidget(self.admin_page_2)
        self.widget_2.setObjectName(u"widget_2")
        self.verticalLayout_50 = QVBoxLayout(self.widget_2)
        self.verticalLayout_50.setObjectName(u"verticalLayout_50")
        self.verticalLayout_49 = QVBoxLayout()
        self.verticalLayout_49.setObjectName(u"verticalLayout_49")
        self.verticalLayout_48 = QVBoxLayout()
        self.verticalLayout_48.setObjectName(u"verticalLayout_48")
        self.admin_license_bnt = QPushButton(self.widget_2)
        self.admin_license_bnt.setObjectName(u"admin_license_bnt")
        sizePolicy3.setHeightForWidth(self.admin_license_bnt.sizePolicy().hasHeightForWidth())
        self.admin_license_bnt.setSizePolicy(sizePolicy3)
        self.admin_license_bnt.setMinimumSize(QSize(171, 41))
        self.admin_license_bnt.setMaximumSize(QSize(171, 41))
        self.admin_license_bnt.setFont(font12)
        self.admin_license_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.admin_license_bnt.setStyleSheet(u"border-radius: 20px;\n"
"border: 1px solid rgb(179,179,179);\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(3, 3, 13);\n"
"")
        self.admin_license_bnt.setCheckable(True)
        self.admin_license_bnt.setChecked(False)
        self.admin_license_bnt.setAutoExclusive(True)

        self.verticalLayout_48.addWidget(self.admin_license_bnt)

        self.admin_fn_permission_bnt = QPushButton(self.widget_2)
        self.admin_fn_permission_bnt.setObjectName(u"admin_fn_permission_bnt")
        sizePolicy3.setHeightForWidth(self.admin_fn_permission_bnt.sizePolicy().hasHeightForWidth())
        self.admin_fn_permission_bnt.setSizePolicy(sizePolicy3)
        self.admin_fn_permission_bnt.setMinimumSize(QSize(171, 41))
        self.admin_fn_permission_bnt.setMaximumSize(QSize(171, 41))
        self.admin_fn_permission_bnt.setFont(font12)
        self.admin_fn_permission_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.admin_fn_permission_bnt.setStyleSheet(u"border-radius: 20px;\n"
"border: 1px solid rgb(179,179,179);\n"
"color: rgb(255, 255, 255);\n"
"background-color: rgb(3, 3, 13);\n"
"")
        self.admin_fn_permission_bnt.setCheckable(True)
        self.admin_fn_permission_bnt.setChecked(False)
        self.admin_fn_permission_bnt.setAutoExclusive(True)

        self.verticalLayout_48.addWidget(self.admin_fn_permission_bnt)


        self.verticalLayout_49.addLayout(self.verticalLayout_48)

        self.verticalSpacer_23 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_49.addItem(self.verticalSpacer_23)


        self.verticalLayout_50.addLayout(self.verticalLayout_49)


        self.horizontalLayout_47.addWidget(self.widget_2)

        self.stackedWidget_2 = QStackedWidget(self.admin_page_2)
        self.stackedWidget_2.setObjectName(u"stackedWidget_2")
        self.stackedWidget_2.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(13, 16, 23);\n"
"")
        self.license_page = QWidget()
        self.license_page.setObjectName(u"license_page")
        self.horizontalLayout_18 = QHBoxLayout(self.license_page)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.verticalLayout_46 = QVBoxLayout()
        self.verticalLayout_46.setObjectName(u"verticalLayout_46")
        self.verticalSpacer_21 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_46.addItem(self.verticalSpacer_21)

        self.horizontalLayout_46 = QHBoxLayout()
        self.horizontalLayout_46.setObjectName(u"horizontalLayout_46")
        self.horizontalSpacer_42 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_46.addItem(self.horizontalSpacer_42)

        self.verticalLayout_38 = QVBoxLayout()
        self.verticalLayout_38.setObjectName(u"verticalLayout_38")
        self.horizontalLayout_42 = QHBoxLayout()
        self.horizontalLayout_42.setObjectName(u"horizontalLayout_42")
        self.verticalLayout_39 = QVBoxLayout()
        self.verticalLayout_39.setObjectName(u"verticalLayout_39")
        self.non_active_license_label = QLabel(self.license_page)
        self.non_active_license_label.setObjectName(u"non_active_license_label")
        self.non_active_license_label.setMinimumSize(QSize(171, 31))
        self.non_active_license_label.setMaximumSize(QSize(171, 31))
        font17 = QFont()
        font17.setFamilies([u"Ubuntu Light"])
        font17.setPointSize(11)
        font17.setBold(True)
        self.non_active_license_label.setFont(font17)
        self.non_active_license_label.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.non_active_license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_39.addWidget(self.non_active_license_label)

        self.widget_3 = QWidget(self.license_page)
        self.widget_3.setObjectName(u"widget_3")
        self.widget_3.setMinimumSize(QSize(171, 0))
        self.widget_3.setMaximumSize(QSize(171, 16777215))
        self.widget_3.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.verticalLayout_40 = QVBoxLayout(self.widget_3)
        self.verticalLayout_40.setObjectName(u"verticalLayout_40")
        self.non_active_license_list = QListWidget(self.widget_3)
        QListWidgetItem(self.non_active_license_list)
        QListWidgetItem(self.non_active_license_list)
        QListWidgetItem(self.non_active_license_list)
        QListWidgetItem(self.non_active_license_list)
        QListWidgetItem(self.non_active_license_list)
        self.non_active_license_list.setObjectName(u"non_active_license_list")
        self.non_active_license_list.setMinimumSize(QSize(156, 397))
        self.non_active_license_list.setMaximumSize(QSize(156, 16777215))
        font18 = QFont()
        font18.setPointSize(11)
        font18.setBold(False)
        font18.setItalic(False)
        font18.setUnderline(False)
        font18.setStrikeOut(False)
        font18.setKerning(True)
        self.non_active_license_list.setFont(font18)
        self.non_active_license_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.non_active_license_list.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.non_active_license_list.setAcceptDrops(True)
        self.non_active_license_list.setStyleSheet(u"QListWidget::item {\n"
"    padding: 3px;\n"
"}\n"
"QListWidget::item:selected {\n"
"    background-color: rgba(19, 193, 13, 200);\n"
"    border: 2px solid green;\n"
"    border-radius: 5px; /* \ub465\uadfc \ud14c\ub450\ub9ac \ucd94\uac00 */\n"
"}\n"
"")
        self.non_active_license_list.setFrameShape(QFrame.Shape.NoFrame)
        self.non_active_license_list.setLineWidth(1)
        self.non_active_license_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.non_active_license_list.setTabKeyNavigation(False)
        self.non_active_license_list.setProperty("showDropIndicator", True)
        self.non_active_license_list.setDragEnabled(True)
        self.non_active_license_list.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.non_active_license_list.setDefaultDropAction(Qt.DropAction.IgnoreAction)
        self.non_active_license_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.non_active_license_list.setTextElideMode(Qt.TextElideMode.ElideLeft)
        self.non_active_license_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.non_active_license_list.setMovement(QListView.Movement.Static)
        self.non_active_license_list.setFlow(QListView.Flow.TopToBottom)
        self.non_active_license_list.setProperty("isWrapping", False)
        self.non_active_license_list.setResizeMode(QListView.ResizeMode.Fixed)
        self.non_active_license_list.setLayoutMode(QListView.LayoutMode.SinglePass)
        self.non_active_license_list.setSpacing(1)
        self.non_active_license_list.setModelColumn(0)
        self.non_active_license_list.setUniformItemSizes(True)
        self.non_active_license_list.setWordWrap(False)
        self.non_active_license_list.setSelectionRectVisible(True)

        self.verticalLayout_40.addWidget(self.non_active_license_list)


        self.verticalLayout_39.addWidget(self.widget_3)


        self.horizontalLayout_42.addLayout(self.verticalLayout_39)

        self.verticalLayout_41 = QVBoxLayout()
        self.verticalLayout_41.setObjectName(u"verticalLayout_41")
        self.verticalSpacer_16 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_41.addItem(self.verticalSpacer_16)

        self.license_add_bnt = QPushButton(self.license_page)
        self.license_add_bnt.setObjectName(u"license_add_bnt")
        self.license_add_bnt.setMinimumSize(QSize(41, 41))
        self.license_add_bnt.setMaximumSize(QSize(41, 41))
        font19 = QFont()
        font19.setPointSize(10)
        self.license_add_bnt.setFont(font19)
        self.license_add_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.license_add_bnt.setStyleSheet(u"background-color: rgb(3, 3, 13);\n"
"border: 1px solid rgb(3, 3, 13);\n"
"color: rgb(255, 255, 255);\n"
"\n"
"")
        icon6 = QIcon()
        icon6.addFile(u":/newPrefix/images/ico_arrow_right.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.license_add_bnt.setIcon(icon6)
        self.license_add_bnt.setIconSize(QSize(31, 50))

        self.verticalLayout_41.addWidget(self.license_add_bnt)

        self.license_remove_bnt = QPushButton(self.license_page)
        self.license_remove_bnt.setObjectName(u"license_remove_bnt")
        self.license_remove_bnt.setMinimumSize(QSize(41, 41))
        self.license_remove_bnt.setMaximumSize(QSize(41, 41))
        self.license_remove_bnt.setFont(font19)
        self.license_remove_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.license_remove_bnt.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.license_remove_bnt.setStyleSheet(u"background-color: rgb(3, 3, 13);\n"
"border: 1px solid rgb(3, 3, 13);\n"
"color: rgb(255, 255, 255);\n"
"\n"
"Rotation: ( origin.x: 25; origin.y: 25; angle: 45);")
        icon7 = QIcon()
        icon7.addFile(u":/newPrefix/images/ico_arrow_left.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.license_remove_bnt.setIcon(icon7)
        self.license_remove_bnt.setIconSize(QSize(31, 50))

        self.verticalLayout_41.addWidget(self.license_remove_bnt)

        self.verticalSpacer_18 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_41.addItem(self.verticalSpacer_18)


        self.horizontalLayout_42.addLayout(self.verticalLayout_41)

        self.verticalLayout_42 = QVBoxLayout()
        self.verticalLayout_42.setObjectName(u"verticalLayout_42")
        self.active_license_label = QLabel(self.license_page)
        self.active_license_label.setObjectName(u"active_license_label")
        self.active_license_label.setMinimumSize(QSize(171, 31))
        self.active_license_label.setMaximumSize(QSize(171, 31))
        self.active_license_label.setFont(font17)
        self.active_license_label.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.active_license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_42.addWidget(self.active_license_label)

        self.widget_4 = QWidget(self.license_page)
        self.widget_4.setObjectName(u"widget_4")
        self.widget_4.setMinimumSize(QSize(171, 0))
        self.widget_4.setMaximumSize(QSize(171, 16777215))
        self.widget_4.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.verticalLayout_43 = QVBoxLayout(self.widget_4)
        self.verticalLayout_43.setObjectName(u"verticalLayout_43")
        self.active_license_list = QListWidget(self.widget_4)
        QListWidgetItem(self.active_license_list)
        QListWidgetItem(self.active_license_list)
        QListWidgetItem(self.active_license_list)
        QListWidgetItem(self.active_license_list)
        self.active_license_list.setObjectName(u"active_license_list")
        self.active_license_list.setMinimumSize(QSize(156, 397))
        self.active_license_list.setMaximumSize(QSize(156, 16777215))
        self.active_license_list.setFont(font18)
        self.active_license_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.active_license_list.setAcceptDrops(True)
        self.active_license_list.setStyleSheet(u"QListWidget::item {\n"
"    padding: 3px;\n"
"}\n"
"QListWidget::item:selected {\n"
"    background-color: rgba(19, 193, 13, 200);\n"
"    border: 2px solid green;\n"
"    border-radius: 5px; /* \ub465\uadfc \ud14c\ub450\ub9ac \ucd94\uac00 */\n"
"}\n"
"")
        self.active_license_list.setFrameShape(QFrame.Shape.NoFrame)
        self.active_license_list.setLineWidth(1)
        self.active_license_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.active_license_list.setTabKeyNavigation(False)
        self.active_license_list.setProperty("showDropIndicator", False)
        self.active_license_list.setDragEnabled(True)
        self.active_license_list.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.active_license_list.setDefaultDropAction(Qt.DropAction.IgnoreAction)
        self.active_license_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.active_license_list.setTextElideMode(Qt.TextElideMode.ElideLeft)
        self.active_license_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.active_license_list.setMovement(QListView.Movement.Static)
        self.active_license_list.setFlow(QListView.Flow.TopToBottom)
        self.active_license_list.setProperty("isWrapping", False)
        self.active_license_list.setResizeMode(QListView.ResizeMode.Fixed)
        self.active_license_list.setLayoutMode(QListView.LayoutMode.SinglePass)
        self.active_license_list.setSpacing(1)
        self.active_license_list.setModelColumn(0)
        self.active_license_list.setUniformItemSizes(True)
        self.active_license_list.setWordWrap(False)
        self.active_license_list.setSelectionRectVisible(True)

        self.verticalLayout_43.addWidget(self.active_license_list)


        self.verticalLayout_42.addWidget(self.widget_4)


        self.horizontalLayout_42.addLayout(self.verticalLayout_42)


        self.verticalLayout_38.addLayout(self.horizontalLayout_42)

        self.horizontalLayout_43 = QHBoxLayout()
        self.horizontalLayout_43.setObjectName(u"horizontalLayout_43")
        self.horizontalSpacer_39 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_43.addItem(self.horizontalSpacer_39)

        self.license_save_bnt = QPushButton(self.license_page)
        self.license_save_bnt.setObjectName(u"license_save_bnt")
        sizePolicy3.setHeightForWidth(self.license_save_bnt.sizePolicy().hasHeightForWidth())
        self.license_save_bnt.setSizePolicy(sizePolicy3)
        self.license_save_bnt.setMinimumSize(QSize(71, 41))
        self.license_save_bnt.setMaximumSize(QSize(71, 41))
        self.license_save_bnt.setFont(font19)
        self.license_save_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.license_save_bnt.setStyleSheet(u"\n"
"background-color: qlineargradient(spread:pad, x1:0.244, y1:0.477, x2:1, y2:0.489, stop:0.0845771 rgba(0, 205, 0, 255), stop:1 rgba(56, 188, 56, 255));\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 20px;\n"
"\n"
"")

        self.horizontalLayout_43.addWidget(self.license_save_bnt)


        self.verticalLayout_38.addLayout(self.horizontalLayout_43)


        self.horizontalLayout_46.addLayout(self.verticalLayout_38)

        self.horizontalSpacer_43 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_46.addItem(self.horizontalSpacer_43)


        self.verticalLayout_46.addLayout(self.horizontalLayout_46)

        self.verticalSpacer_22 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_46.addItem(self.verticalSpacer_22)


        self.horizontalLayout_18.addLayout(self.verticalLayout_46)

        self.stackedWidget_2.addWidget(self.license_page)
        self.fn_permission_page = QWidget()
        self.fn_permission_page.setObjectName(u"fn_permission_page")
        self.verticalLayout_45 = QVBoxLayout(self.fn_permission_page)
        self.verticalLayout_45.setObjectName(u"verticalLayout_45")
        self.verticalLayout_44 = QVBoxLayout()
        self.verticalLayout_44.setObjectName(u"verticalLayout_44")
        self.verticalSpacer_20 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.verticalLayout_44.addItem(self.verticalSpacer_20)

        self.horizontalLayout_45 = QHBoxLayout()
        self.horizontalLayout_45.setObjectName(u"horizontalLayout_45")
        self.horizontalSpacer_40 = QSpacerItem(40, 20, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_45.addItem(self.horizontalSpacer_40)

        self.horizontalLayout_44 = QHBoxLayout()
        self.horizontalLayout_44.setObjectName(u"horizontalLayout_44")
        self.admin_email_alarm_fn_active_label = QLabel(self.fn_permission_page)
        self.admin_email_alarm_fn_active_label.setObjectName(u"admin_email_alarm_fn_active_label")
        self.admin_email_alarm_fn_active_label.setMinimumSize(QSize(160, 25))
        self.admin_email_alarm_fn_active_label.setMaximumSize(QSize(160, 25))
        self.admin_email_alarm_fn_active_label.setFont(font12)
        self.admin_email_alarm_fn_active_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.admin_email_alarm_fn_active_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_44.addWidget(self.admin_email_alarm_fn_active_label)

        self.admin_email_alarm_fn_active_bnt = QPushButton(self.fn_permission_page)
        self.admin_email_alarm_fn_active_bnt.setObjectName(u"admin_email_alarm_fn_active_bnt")
        self.admin_email_alarm_fn_active_bnt.setMinimumSize(QSize(61, 25))
        self.admin_email_alarm_fn_active_bnt.setMaximumSize(QSize(61, 25))
        icon8 = QIcon()
        icon8.addFile(u":/newPrefix/images/icon-switch-off.png", QSize(), QIcon.Normal, QIcon.Off)
        icon8.addFile(u":/newPrefix/images/icon-switch-on.png", QSize(), QIcon.Normal, QIcon.On)
        icon8.addFile(u":/newPrefix/images/icon-switch-on.png", QSize(), QIcon.Disabled, QIcon.On)
        icon8.addFile(u":/newPrefix/images/icon-switch-on.png", QSize(), QIcon.Active, QIcon.On)
        icon8.addFile(u":/newPrefix/images/icon-switch-on.png", QSize(), QIcon.Selected, QIcon.On)
        self.admin_email_alarm_fn_active_bnt.setIcon(icon8)
        self.admin_email_alarm_fn_active_bnt.setIconSize(QSize(55, 103))
        self.admin_email_alarm_fn_active_bnt.setCheckable(True)

        self.horizontalLayout_44.addWidget(self.admin_email_alarm_fn_active_bnt)


        self.horizontalLayout_45.addLayout(self.horizontalLayout_44)

        self.horizontalSpacer_41 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_45.addItem(self.horizontalSpacer_41)


        self.verticalLayout_44.addLayout(self.horizontalLayout_45)

        self.verticalSpacer_19 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_44.addItem(self.verticalSpacer_19)


        self.verticalLayout_45.addLayout(self.verticalLayout_44)

        self.stackedWidget_2.addWidget(self.fn_permission_page)

        self.horizontalLayout_47.addWidget(self.stackedWidget_2)

        self.stackedWidget.addWidget(self.admin_page_2)

        self.verticalLayout_2.addWidget(self.stackedWidget)


        self.horizontalLayout_32.addLayout(self.verticalLayout_2)


        self.verticalLayout_11.addLayout(self.horizontalLayout_32)


        self.verticalLayout_52.addLayout(self.verticalLayout_11)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.stackedWidget.setCurrentIndex(0)
        self.setting_stack_widget.setCurrentIndex(0)
        self.setting_popup_alarm_cnt.setCurrentIndex(2)
        self.stackedWidget_2.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MS-AI 1000", None))
        self.top_logo.setText("")
        self.verson_label.setText(QCoreApplication.translate("MainWindow", u"MS-AI1000 1.1.0", None))
        self.server_icon.setText("")
        self.server_info_label.setText(QCoreApplication.translate("MainWindow", u"NVR\uc11c\ubc84\uc815\ubcf4", None))
        self.server_ip_label.setText(QCoreApplication.translate("MainWindow", u"\uc8fc\uc18c", None))
        self.server_ip_input.setText("")
        self.server_id_label.setText(QCoreApplication.translate("MainWindow", u"\uc544\uc774\ub514", None))
        self.server_id_input.setText("")
        self.server_pw_label.setText(QCoreApplication.translate("MainWindow", u"\ube44\ubc00\ubc88\ud638", None))
        self.server_pw_input.setText("")
        self.sever_login_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc5f0\uacb0", None))
        self.shutdown_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc885\ub8cc", None))
        ___qtablewidgetitem = self.camera_list_table.horizontalHeaderItem(1)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Num", None));
        ___qtablewidgetitem1 = self.camera_list_table.horizontalHeaderItem(2)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Name", None));
        ___qtablewidgetitem2 = self.camera_list_table.horizontalHeaderItem(3)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Address", None));
        self.camera_info_title.setText(QCoreApplication.translate("MainWindow", u"\uce74\uba54\ub77c \uc18d\uc131", None))
        self.camera_name.setText(QCoreApplication.translate("MainWindow", u"\uc774\ub984", None))
        self.camera_info_name_input.setText("")
        self.camera_ip.setText(QCoreApplication.translate("MainWindow", u"IP \uc8fc\uc18c", None))
        self.camera_info_ip_input.setText("")
        self.camera_id.setText(QCoreApplication.translate("MainWindow", u"\uc0ac\uc6a9\uc790 ID", None))
        self.camera_info_id_input.setText("")
        self.camera_pw.setText(QCoreApplication.translate("MainWindow", u"\ube44\ubc00\ubc88\ud638", None))
        self.camera_info_pw_input.setText("")
        self.camera_remove_bn.setText(QCoreApplication.translate("MainWindow", u"\uc0ad\uc81c", None))
        self.camera_add_bn.setText(QCoreApplication.translate("MainWindow", u"\ucd94\uac00", None))
        self.camera_save_bn.setText(QCoreApplication.translate("MainWindow", u"\uc800\uc7a5", None))
        self.live_bnt.setText(QCoreApplication.translate("MainWindow", u"Live", None))
        self.tab_partion_10.setText(QCoreApplication.translate("MainWindow", u"|", None))
        self.camera_bnt.setText(QCoreApplication.translate("MainWindow", u"Camera", None))
        self.tab_partion_11.setText(QCoreApplication.translate("MainWindow", u"|", None))
        self.setting_bnt.setText(QCoreApplication.translate("MainWindow", u"Setting", None))
        self.tab_partion_3.setText(QCoreApplication.translate("MainWindow", u"|", None))
        self.admin_bnt.setText(QCoreApplication.translate("MainWindow", u"Admin", None))
        self.camera_refresh_bnt.setText("")
        self.camera_schedule_bnt.setText("")
        self.alarm_search_bnt.setText("")
        self.camera_view_9.setText("")
        self.camera_view_1.setText("")
        self.camera_view_11.setText("")
        self.camera_view_12.setText("")
        self.camera_view_5.setText("")
        self.camera_view_14.setText("")
        self.camera_view_16.setText("")
        self.camera_view_4.setText("")
        self.camera_view_7.setText("")
        self.camera_view_6.setText("")
        self.camera_view_2.setText("")
        self.camera_view_15.setText("")
        self.camera_view_13.setText("")
        self.camera_view_10.setText("")
        self.camera_view_3.setText("")
        self.camera_view_8.setText("")
        self.camera_page_camera_name_label.setText(QCoreApplication.translate("MainWindow", u"\uce74\uba54\ub77c \ubc88\ud638", None))
        self.camera_page_camera_event_label.setText(QCoreApplication.translate("MainWindow", u"\uc774\ubca4\ud2b8 \uc885\ub958", None))
        self.camera_page_camera_event_box.setItemText(0, QCoreApplication.translate("MainWindow", u"\uce68\uc785", None))
        self.camera_page_camera_event_box.setItemText(1, QCoreApplication.translate("MainWindow", u"\ubc30\ud68c", None))
        self.camera_page_camera_event_box.setItemText(2, QCoreApplication.translate("MainWindow", u"\uc4f0\ub7ec\uc9d0", None))
        self.camera_page_camera_event_box.setItemText(3, QCoreApplication.translate("MainWindow", u"\ubc29\ud654", None))

        self.camera_page_detect_add_bnt.setText("")
        ___qtablewidgetitem3 = self.camera_page_detect_area_table.horizontalHeaderItem(0)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"\uac10\uc9c0 \uc601\uc5ed \ub9ac\uc2a4\ud2b8", None));
        self.camera_page_detect_area_del_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc0ad\uc81c", None))
        self.camera_page_camera_event_label_2.setText(QCoreApplication.translate("MainWindow", u"\uc0ac\ub78c \uac80\ucd9c \uc784\uacc4\uac12", None))
        self.camera_page_ai_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc9c0\ub2a5\ud615 \ubd84\uc11d \uc124\uc815", None))
        self.camera_page_ai_active_icon.setText("")
        self.camera_page_ai_active_label.setText(QCoreApplication.translate("MainWindow", u"\uc9c0\ub2a5\ud615 \ubd84\uc11d \uc9c4\ud589\uc911", None))
        self.camera_page_viewer.setText("")
        self.setting_alarm_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc54c\ub9bc \uc124\uc815", None))
        self.setting_user_setting_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc0ac\uc6a9\uc790 \uc815\ubcf4", None))
        self.setting_detect_info_label.setText(QCoreApplication.translate("MainWindow", u"\uc9c0\ub2a5\ud615 \uac80\ucd9c \uc815\ubcf4 \ud45c\uc2dc \uc124\uc815", None))
        self.setting_detect_bbox_active_label.setText(QCoreApplication.translate("MainWindow", u"BBox \ud65c\uc131\ud654", None))
        self.setting_detect_bbox_active_bnt.setText("")
        self.setting_detect_label_active_label.setText(QCoreApplication.translate("MainWindow", u"Label \ud65c\uc131\ud654", None))
        self.setting_detect_label_active_bnt.setText("")
        self.setting_video_save_alarm_active_label.setText(QCoreApplication.translate("MainWindow", u"\uc774\ubca4\ud2b8 \uc601\uc0c1 \uc800\uc7a5 \ud65c\uc131\ud654", None))
        self.setting_video_save_alarm_active_bnt.setText("")
        self.setting_event_video_storage_period_label.setText(QCoreApplication.translate("MainWindow", u"\uc774\ubca4\ud2b8 \uc601\uc0c1 \uc720\uc9c0 \uae30\uac04", None))
        self.setting_event_video_storage_period.setItemText(0, QCoreApplication.translate("MainWindow", u"30\uc77c", None))
        self.setting_event_video_storage_period.setItemText(1, QCoreApplication.translate("MainWindow", u"60\uc77c", None))
        self.setting_event_video_storage_period.setItemText(2, QCoreApplication.translate("MainWindow", u"90\uc77c", None))

        self.setting_popup_alarm_active_label.setText(QCoreApplication.translate("MainWindow", u"\uc774\ubca4\ud2b8 \uba54\uc138\uc9c0 \ud65c\uc131\ud654", None))
        self.setting_popup_alarm_active_bnt.setText("")
        self.setting_popup_alarm_cnt_label.setText(QCoreApplication.translate("MainWindow", u"\uc774\ubca4\ud2b8 \uba54\uc138\uc9c0 \uac1c\uc218", None))
        self.setting_popup_alarm_cnt.setItemText(0, QCoreApplication.translate("MainWindow", u"1", None))
        self.setting_popup_alarm_cnt.setItemText(1, QCoreApplication.translate("MainWindow", u"2", None))
        self.setting_popup_alarm_cnt.setItemText(2, QCoreApplication.translate("MainWindow", u"3", None))
        self.setting_popup_alarm_cnt.setItemText(3, QCoreApplication.translate("MainWindow", u"4", None))
        self.setting_popup_alarm_cnt.setItemText(4, QCoreApplication.translate("MainWindow", u"5", None))
        self.setting_popup_alarm_cnt.setItemText(5, QCoreApplication.translate("MainWindow", u"6", None))
        self.setting_popup_alarm_cnt.setItemText(6, QCoreApplication.translate("MainWindow", u"7", None))
        self.setting_popup_alarm_cnt.setItemText(7, QCoreApplication.translate("MainWindow", u"8", None))
        self.setting_popup_alarm_cnt.setItemText(8, QCoreApplication.translate("MainWindow", u"9", None))
        self.setting_popup_alarm_cnt.setItemText(9, QCoreApplication.translate("MainWindow", u"10", None))

        self.setting_email_active_label.setText(QCoreApplication.translate("MainWindow", u"\uc774\uba54\uc77c \uc54c\ub9bc \uc804\uc1a1 \uae30\ub2a5 \ud65c\uc131\ud654", None))
        self.setting_email_active_bnt.setText("")
        self.setting_email_active_id_label.setText(QCoreApplication.translate("MainWindow", u"\uc1a1\uc2e0 \uc774\uba54\uc77c", None))
        self.setting_email_id_input.setText("")
        self.setting_email_active_pw_label.setText(QCoreApplication.translate("MainWindow", u"    \ube44\ubc00\ubc88\ud638", None))
        self.setting_email_pw_input.setText("")
        self.setting_email_active_to_id_label.setText(QCoreApplication.translate("MainWindow", u"\uc218\uc2e0 \uc774\uba54\uc77c", None))
        self.setting_receive_email_id_input.setText("")
        self.setting_page_email_info_label.setText(QCoreApplication.translate("MainWindow", u"\u203bSTMP \uc11c\ubc84\ub97c \uc774\uc6a9\ud55c \uae30\ub2a5\uc785\ub2c8\ub2e4.", None))
        self.setting_page_email_info_label_2.setText(QCoreApplication.translate("MainWindow", u"\uad00\ub828 \uc11c\ube44\uc2a4\ub97c \uc774\uc6a9\ud558\uae30 \uc704\ud574 \ub9e4\ub274\uc5bc\uc744 \ucc38\uace0\ud558\uc138\uc694.", None))
        self.setting_email_save_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc774\uba54\uc77c \uc800\uc7a5", None))
        self.setting_user_id_label.setText(QCoreApplication.translate("MainWindow", u"\uc544\uc774\ub514", None))
        self.setting_user_id_input.setText("")
        self.setting_user_pw_label.setText(QCoreApplication.translate("MainWindow", u"\ud604\uc7ac \ube44\ubc00\ubc88\ud638", None))
        self.setting_user_pw_input.setText("")
        self.setting_user_new_pw_label.setText(QCoreApplication.translate("MainWindow", u"\uc2e0\uaddc \ube44\ubc00\ubc88\ud638", None))
        self.setting_user_new_pw_input.setText("")
        self.setting_user_new_pw_label2.setText(QCoreApplication.translate("MainWindow", u"\ube44\ubc00\ubc88\ud638 \ud655\uc778", None))
        self.setting_user_new_pw_input2.setText("")
        self.setting_user_save_bnt.setText(QCoreApplication.translate("MainWindow", u"\ubcc0\uacbd", None))
        self.admin_pw_label.setText(QCoreApplication.translate("MainWindow", u"\uad00\ub9ac\uc790 \ube44\ubc00\ubc88\ud638", None))
        self.admin_pw_input.setText(QCoreApplication.translate("MainWindow", u"asdsad", None))
        self.admin_page_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc785\ub825", None))
        self.admin_license_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc9c0\ub2a5\ud615 \ub77c\uc774\uc13c\uc2a4 \uc124\uc815", None))
        self.admin_fn_permission_bnt.setText(QCoreApplication.translate("MainWindow", u"\uae30\ub2a5 \uad8c\ud55c \uc124\uc815", None))
        self.non_active_license_label.setText(QCoreApplication.translate("MainWindow", u"\ube44\ud65c\uc131 \ub77c\uc774\uc13c\uc2a4", None))

        __sortingEnabled = self.non_active_license_list.isSortingEnabled()
        self.non_active_license_list.setSortingEnabled(False)
        ___qlistwidgetitem = self.non_active_license_list.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("MainWindow", u"\uce68\uc785", None));
        ___qlistwidgetitem1 = self.non_active_license_list.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("MainWindow", u"\ubc30\ud68c", None));
        ___qlistwidgetitem2 = self.non_active_license_list.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("MainWindow", u"\ubc29\ud654", None));
        ___qlistwidgetitem3 = self.non_active_license_list.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("MainWindow", u"\uc4f0\ub7ec\uc9d0", None));
        ___qlistwidgetitem4 = self.non_active_license_list.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("MainWindow", u"\uc2f8\uc6c0", None));
        self.non_active_license_list.setSortingEnabled(__sortingEnabled)

        self.license_add_bnt.setText("")
        self.license_remove_bnt.setText("")
        self.active_license_label.setText(QCoreApplication.translate("MainWindow", u"\ud65c\uc131 \ub77c\uc774\uc13c\uc2a4", None))

        __sortingEnabled1 = self.active_license_list.isSortingEnabled()
        self.active_license_list.setSortingEnabled(False)
        ___qlistwidgetitem5 = self.active_license_list.item(0)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("MainWindow", u"New Item", None));
        ___qlistwidgetitem6 = self.active_license_list.item(1)
        ___qlistwidgetitem6.setText(QCoreApplication.translate("MainWindow", u"New Item", None));
        ___qlistwidgetitem7 = self.active_license_list.item(2)
        ___qlistwidgetitem7.setText(QCoreApplication.translate("MainWindow", u"New Item", None));
        ___qlistwidgetitem8 = self.active_license_list.item(3)
        ___qlistwidgetitem8.setText(QCoreApplication.translate("MainWindow", u"New Item", None));
        self.active_license_list.setSortingEnabled(__sortingEnabled1)

        self.license_save_bnt.setText(QCoreApplication.translate("MainWindow", u"\uc800\uc7a5", None))
        self.admin_email_alarm_fn_active_label.setText(QCoreApplication.translate("MainWindow", u"\uc774\uba54\uc77c \uc54c\ub78c \uae30\ub2a5 \ud65c\uc131\ud654", None))
        self.admin_email_alarm_fn_active_bnt.setText("")
    # retranslateUi

