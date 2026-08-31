# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'schedule.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QListView, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)
import ms_ai_img_rc
import ms_ai_img_rc

class Ui_schedule_window(object):
    def setupUi(self, schedule_window):
        if not schedule_window.objectName():
            schedule_window.setObjectName(u"schedule_window")
        schedule_window.resize(1243, 672)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(schedule_window.sizePolicy().hasHeightForWidth())
        schedule_window.setSizePolicy(sizePolicy)
        schedule_window.setMinimumSize(QSize(1163, 562))
        schedule_window.setMaximumSize(QSize(16777215, 16777215))
        schedule_window.setStyleSheet(u"background-color: rgb(20, 20, 20);\n"
"\n"
"")
        self.layoutWidget = QWidget(schedule_window)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(7, 51, 181, 611))
        self.verticalLayout_3 = QVBoxLayout(self.layoutWidget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.schedule_camera_list_label = QLabel(self.layoutWidget)
        self.schedule_camera_list_label.setObjectName(u"schedule_camera_list_label")
        self.schedule_camera_list_label.setMinimumSize(QSize(0, 0))
        font = QFont()
        font.setFamilies([u"Ubuntu Light"])
        font.setPointSize(11)
        font.setBold(True)
        self.schedule_camera_list_label.setFont(font)
        self.schedule_camera_list_label.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.schedule_camera_list_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.schedule_camera_list_label)

        self.widget_3 = QWidget(self.layoutWidget)
        self.widget_3.setObjectName(u"widget_3")
        self.widget_3.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.verticalLayout_7 = QVBoxLayout(self.widget_3)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.schedule_camera_list = QListWidget(self.widget_3)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        QListWidgetItem(self.schedule_camera_list)
        self.schedule_camera_list.setObjectName(u"schedule_camera_list")
        font1 = QFont()
        font1.setPointSize(11)
        font1.setBold(False)
        font1.setItalic(False)
        font1.setUnderline(False)
        font1.setStrikeOut(False)
        font1.setKerning(True)
        self.schedule_camera_list.setFont(font1)
        self.schedule_camera_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.schedule_camera_list.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.schedule_camera_list.setAcceptDrops(True)
        self.schedule_camera_list.setStyleSheet(u"QListWidget::item {\n"
"    padding: 3px;\n"
"}\n"
"QListWidget::item:selected {\n"
"    border: 2px solid rgb(26, 95, 180);\n"
"    border-radius: 5px; /* \ub465\uadfc \ud14c\ub450\ub9ac \ucd94\uac00 */\n"
"}\n"
"")
        self.schedule_camera_list.setFrameShape(QFrame.Shape.NoFrame)
        self.schedule_camera_list.setLineWidth(1)
        self.schedule_camera_list.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.schedule_camera_list.setTabKeyNavigation(False)
        self.schedule_camera_list.setProperty("showDropIndicator", False)
        self.schedule_camera_list.setDragEnabled(False)
        self.schedule_camera_list.setDragDropOverwriteMode(False)
        self.schedule_camera_list.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.schedule_camera_list.setDefaultDropAction(Qt.DropAction.IgnoreAction)
        self.schedule_camera_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.schedule_camera_list.setTextElideMode(Qt.TextElideMode.ElideLeft)
        self.schedule_camera_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerItem)
        self.schedule_camera_list.setMovement(QListView.Movement.Static)
        self.schedule_camera_list.setFlow(QListView.Flow.TopToBottom)
        self.schedule_camera_list.setProperty("isWrapping", False)
        self.schedule_camera_list.setResizeMode(QListView.ResizeMode.Fixed)
        self.schedule_camera_list.setLayoutMode(QListView.LayoutMode.SinglePass)
        self.schedule_camera_list.setSpacing(2)
        self.schedule_camera_list.setViewMode(QListView.ViewMode.ListMode)
        self.schedule_camera_list.setModelColumn(0)
        self.schedule_camera_list.setUniformItemSizes(True)
        self.schedule_camera_list.setWordWrap(False)
        self.schedule_camera_list.setSelectionRectVisible(True)

        self.verticalLayout_7.addWidget(self.schedule_camera_list)


        self.verticalLayout_3.addWidget(self.widget_3)

        self.detect_type_tab_widget = QWidget(schedule_window)
        self.detect_type_tab_widget.setObjectName(u"detect_type_tab_widget")
        self.detect_type_tab_widget.setGeometry(QRect(200, 2, 291, 41))
        self.detect_type_tab_widget.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border-radius: 15px;\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.horizontalLayout = QHBoxLayout(self.detect_type_tab_widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.intr_bnt = QPushButton(self.detect_type_tab_widget)
        self.intr_bnt.setObjectName(u"intr_bnt")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.intr_bnt.sizePolicy().hasHeightForWidth())
        self.intr_bnt.setSizePolicy(sizePolicy1)
        self.intr_bnt.setMinimumSize(QSize(50, 29))
        font2 = QFont()
        font2.setPointSize(10)
        self.intr_bnt.setFont(font2)
        self.intr_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.intr_bnt.setStyleSheet(u"QPushButton {\n"
"				background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0.233831 rgba(237, 87, 4, 255), stop:1 rgba(253, 207, 137, 255));\n"
"				border-radius: 14px;\n"
"\n"
"            }\n"
"QPushButton:checked {\n"
"                color: white;\n"
"				border-radius: 14px;\n"
"				border: 3px solid rgb(255, 255, 255);\n"
"\n"
"            }")
        self.intr_bnt.setCheckable(True)
        self.intr_bnt.setChecked(False)

        self.horizontalLayout.addWidget(self.intr_bnt)

        self.fire_bnt = QPushButton(self.detect_type_tab_widget)
        self.fire_bnt.setObjectName(u"fire_bnt")
        sizePolicy1.setHeightForWidth(self.fire_bnt.sizePolicy().hasHeightForWidth())
        self.fire_bnt.setSizePolicy(sizePolicy1)
        self.fire_bnt.setMinimumSize(QSize(50, 29))
        self.fire_bnt.setFont(font2)
        self.fire_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.fire_bnt.setStyleSheet(u"\n"
"QPushButton {\n"
"				background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0.298507 rgba(30, 92, 184, 255), stop:0.905473 rgba(3, 254, 254, 255));\n"
"				border-radius: 14px;\n"
"            }\n"
"QPushButton:checked {\n"
"                color: white;\n"
"				border-radius: 14px;\n"
"				border: 3px solid rgb(255, 255, 255);\n"
"\n"
"            }")
        self.fire_bnt.setCheckable(True)
        self.fire_bnt.setChecked(False)

        self.horizontalLayout.addWidget(self.fire_bnt)

        self.loit_bnt = QPushButton(self.detect_type_tab_widget)
        self.loit_bnt.setObjectName(u"loit_bnt")
        sizePolicy1.setHeightForWidth(self.loit_bnt.sizePolicy().hasHeightForWidth())
        self.loit_bnt.setSizePolicy(sizePolicy1)
        self.loit_bnt.setMinimumSize(QSize(50, 29))
        self.loit_bnt.setFont(font2)
        self.loit_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.loit_bnt.setStyleSheet(u"\n"
"\n"
"QPushButton {\n"
"				background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0.134328 rgba(66, 110, 23, 255), stop:0.905473 rgba(202, 224, 59, 255));\n"
"				border-radius: 14px;\n"
"\n"
"            }\n"
"QPushButton:checked {\n"
"                color: white;\n"
"				border-radius: 14px;\n"
"				border: 3px solid rgb(255, 255, 255);\n"
"\n"
"            }")
        self.loit_bnt.setCheckable(True)
        self.loit_bnt.setChecked(False)

        self.horizontalLayout.addWidget(self.loit_bnt)

        self.fall_bnt = QPushButton(self.detect_type_tab_widget)
        self.fall_bnt.setObjectName(u"fall_bnt")
        sizePolicy1.setHeightForWidth(self.fall_bnt.sizePolicy().hasHeightForWidth())
        self.fall_bnt.setSizePolicy(sizePolicy1)
        self.fall_bnt.setMinimumSize(QSize(50, 29))
        self.fall_bnt.setFont(font2)
        self.fall_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.fall_bnt.setStyleSheet(u"\n"
"\n"
"QPushButton {\n"
"				background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0.134328 rgba(52, 65, 88, 255), stop:0.905473 rgba(91, 106, 128, 255));\n"
"\n"
"				border-radius: 14px;\n"
"\n"
"\n"
"            }\n"
"QPushButton:checked {\n"
"                color: white;\n"
"				border-radius: 14px;\n"
"				border: 3px solid rgb(255, 255, 255);\n"
"\n"
"            }")
        self.fall_bnt.setCheckable(True)
        self.fall_bnt.setChecked(False)

        self.horizontalLayout.addWidget(self.fall_bnt)

        self.fight_bnt = QPushButton(self.detect_type_tab_widget)
        self.fight_bnt.setObjectName(u"fight_bnt")
        sizePolicy1.setHeightForWidth(self.fight_bnt.sizePolicy().hasHeightForWidth())
        self.fight_bnt.setSizePolicy(sizePolicy1)
        self.fight_bnt.setMinimumSize(QSize(50, 29))
        self.fight_bnt.setMaximumSize(QSize(50, 29))
        self.fight_bnt.setFont(font2)
        self.fight_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.fight_bnt.setStyleSheet(u"\n"
"\n"
"QPushButton {\n"
"	color: rgb(0, 0, 0);\n"
"\n"
"	\n"
"	background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(230, 230, 231, 255), stop:1 rgba(101, 102, 103, 255));\n"
"\n"
"				border-radius: 14px;\n"
"\n"
"\n"
"            }\n"
"QPushButton:checked {\n"
"                color: white;\n"
"				border-radius: 14px;\n"
"				border: 3px solid rgb(255, 255, 255);\n"
"\n"
"            }")
        self.fight_bnt.setCheckable(True)
        self.fight_bnt.setChecked(False)

        self.horizontalLayout.addWidget(self.fight_bnt)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.detect_time_table_widget = QWidget(schedule_window)
        self.detect_time_table_widget.setObjectName(u"detect_time_table_widget")
        self.detect_time_table_widget.setGeometry(QRect(197, 50, 1031, 611))
        self.detect_time_table_widget.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(32,39,49);\n"
"\n"
"")
        self.schedule_time_table = QTableWidget(self.detect_time_table_widget)
        if (self.schedule_time_table.columnCount() < 24):
            self.schedule_time_table.setColumnCount(24)
        __qtablewidgetitem = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        __qtablewidgetitem7 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(7, __qtablewidgetitem7)
        __qtablewidgetitem8 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(8, __qtablewidgetitem8)
        __qtablewidgetitem9 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(9, __qtablewidgetitem9)
        __qtablewidgetitem10 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(10, __qtablewidgetitem10)
        __qtablewidgetitem11 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(11, __qtablewidgetitem11)
        __qtablewidgetitem12 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(12, __qtablewidgetitem12)
        __qtablewidgetitem13 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(13, __qtablewidgetitem13)
        __qtablewidgetitem14 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(14, __qtablewidgetitem14)
        __qtablewidgetitem15 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(15, __qtablewidgetitem15)
        __qtablewidgetitem16 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(16, __qtablewidgetitem16)
        __qtablewidgetitem17 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(17, __qtablewidgetitem17)
        __qtablewidgetitem18 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(18, __qtablewidgetitem18)
        __qtablewidgetitem19 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(19, __qtablewidgetitem19)
        __qtablewidgetitem20 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(20, __qtablewidgetitem20)
        __qtablewidgetitem21 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(21, __qtablewidgetitem21)
        __qtablewidgetitem22 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(22, __qtablewidgetitem22)
        __qtablewidgetitem23 = QTableWidgetItem()
        self.schedule_time_table.setHorizontalHeaderItem(23, __qtablewidgetitem23)
        if (self.schedule_time_table.rowCount() < 7):
            self.schedule_time_table.setRowCount(7)
        __qtablewidgetitem24 = QTableWidgetItem()
        self.schedule_time_table.setVerticalHeaderItem(0, __qtablewidgetitem24)
        __qtablewidgetitem25 = QTableWidgetItem()
        self.schedule_time_table.setVerticalHeaderItem(1, __qtablewidgetitem25)
        __qtablewidgetitem26 = QTableWidgetItem()
        self.schedule_time_table.setVerticalHeaderItem(2, __qtablewidgetitem26)
        __qtablewidgetitem27 = QTableWidgetItem()
        self.schedule_time_table.setVerticalHeaderItem(3, __qtablewidgetitem27)
        __qtablewidgetitem28 = QTableWidgetItem()
        self.schedule_time_table.setVerticalHeaderItem(4, __qtablewidgetitem28)
        __qtablewidgetitem29 = QTableWidgetItem()
        self.schedule_time_table.setVerticalHeaderItem(5, __qtablewidgetitem29)
        __qtablewidgetitem30 = QTableWidgetItem()
        self.schedule_time_table.setVerticalHeaderItem(6, __qtablewidgetitem30)
        self.schedule_time_table.setObjectName(u"schedule_time_table")
        self.schedule_time_table.setGeometry(QRect(31, 0, 991, 601))
        self.schedule_time_table.setMinimumSize(QSize(0, 575))
        self.schedule_time_table.setMaximumSize(QSize(9999, 9999))
        font3 = QFont()
        font3.setFamilies([u"Sans"])
        self.schedule_time_table.setFont(font3)
        self.schedule_time_table.setStyleSheet(u"QTableView {gridline-color: rgb(119, 118, 123);}")
        self.schedule_time_table.setProperty("showDropIndicator", True)
        self.schedule_time_table.setDragEnabled(False)
        self.schedule_time_table.setDragDropOverwriteMode(True)
        self.schedule_time_table.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.schedule_time_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.schedule_time_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.schedule_time_table.setGridStyle(Qt.PenStyle.SolidLine)
        self.schedule_time_table.setSortingEnabled(False)
        self.schedule_time_table.horizontalHeader().setMinimumSectionSize(3)
        self.schedule_time_table.horizontalHeader().setDefaultSectionSize(40)
        self.schedule_time_table.horizontalHeader().setProperty("showSortIndicator", False)
        self.schedule_time_table.horizontalHeader().setStretchLastSection(False)
        self.schedule_time_table.verticalHeader().setVisible(True)
        self.schedule_time_table.verticalHeader().setCascadingSectionResizes(False)
        self.schedule_time_table.verticalHeader().setMinimumSectionSize(18)
        self.schedule_time_table.verticalHeader().setDefaultSectionSize(82)
        self.schedule_time_table.verticalHeader().setProperty("showSortIndicator", False)
        self.schedule_time_table.verticalHeader().setStretchLastSection(False)
        self.check_box_mon = QPushButton(self.detect_time_table_widget)
        self.check_box_mon.setObjectName(u"check_box_mon")
        self.check_box_mon.setGeometry(QRect(3, 135, 23, 23))
        self.check_box_mon.setStyleSheet(u"\n"
"background-color: rgb(32,39,49);")
        icon = QIcon()
        icon.addFile(u":/newPrefix/images/checkm.jpg", QSize(), QIcon.Normal, QIcon.Off)
        icon.addFile(u":/newPrefix/images/check.png", QSize(), QIcon.Normal, QIcon.On)
        icon.addFile(u":/newPrefix/images/checkm.jpg", QSize(), QIcon.Disabled, QIcon.Off)
        icon.addFile(u":/newPrefix/images/check.png", QSize(), QIcon.Disabled, QIcon.On)
        self.check_box_mon.setIcon(icon)
        self.check_box_mon.setIconSize(QSize(20, 20))
        self.check_box_mon.setCheckable(True)
        self.check_box_mon.setChecked(False)
        self.check_box_tue = QPushButton(self.detect_time_table_widget)
        self.check_box_tue.setObjectName(u"check_box_tue")
        self.check_box_tue.setGeometry(QRect(3, 216, 23, 23))
        self.check_box_tue.setStyleSheet(u"\n"
"background-color: rgb(32,39,49);")
        self.check_box_tue.setIcon(icon)
        self.check_box_tue.setIconSize(QSize(20, 20))
        self.check_box_tue.setCheckable(True)
        self.check_box_tue.setChecked(False)
        self.check_box_wed = QPushButton(self.detect_time_table_widget)
        self.check_box_wed.setObjectName(u"check_box_wed")
        self.check_box_wed.setGeometry(QRect(3, 298, 23, 23))
        self.check_box_wed.setStyleSheet(u"\n"
"background-color: rgb(32,39,49);")
        self.check_box_wed.setIcon(icon)
        self.check_box_wed.setIconSize(QSize(20, 20))
        self.check_box_wed.setCheckable(True)
        self.check_box_wed.setChecked(False)
        self.check_box_thu = QPushButton(self.detect_time_table_widget)
        self.check_box_thu.setObjectName(u"check_box_thu")
        self.check_box_thu.setGeometry(QRect(3, 380, 23, 23))
        self.check_box_thu.setStyleSheet(u"\n"
"background-color: rgb(32,39,49);")
        self.check_box_thu.setIcon(icon)
        self.check_box_thu.setIconSize(QSize(20, 20))
        self.check_box_thu.setCheckable(True)
        self.check_box_thu.setChecked(False)
        self.check_box_fri = QPushButton(self.detect_time_table_widget)
        self.check_box_fri.setObjectName(u"check_box_fri")
        self.check_box_fri.setGeometry(QRect(3, 465, 23, 23))
        self.check_box_fri.setStyleSheet(u"\n"
"background-color: rgb(32,39,49);")
        self.check_box_fri.setIcon(icon)
        self.check_box_fri.setIconSize(QSize(20, 20))
        self.check_box_fri.setCheckable(True)
        self.check_box_fri.setChecked(False)
        self.check_box_sat = QPushButton(self.detect_time_table_widget)
        self.check_box_sat.setObjectName(u"check_box_sat")
        self.check_box_sat.setGeometry(QRect(3, 547, 23, 23))
        self.check_box_sat.setStyleSheet(u"\n"
"background-color: rgb(32,39,49);")
        self.check_box_sat.setIcon(icon)
        self.check_box_sat.setIconSize(QSize(20, 20))
        self.check_box_sat.setCheckable(True)
        self.check_box_sat.setChecked(False)
        self.check_box_sun = QPushButton(self.detect_time_table_widget)
        self.check_box_sun.setObjectName(u"check_box_sun")
        self.check_box_sun.setGeometry(QRect(3, 51, 23, 23))
        self.check_box_sun.setStyleSheet(u"\n"
"background-color: rgb(32,39,49);")
        self.check_box_sun.setIcon(icon)
        self.check_box_sun.setIconSize(QSize(20, 20))
        self.check_box_sun.setCheckable(True)
        self.check_box_sun.setChecked(False)
        self.schedule_close_bnt = QPushButton(schedule_window)
        self.schedule_close_bnt.setObjectName(u"schedule_close_bnt")
        self.schedule_close_bnt.setGeometry(QRect(1160, 10, 61, 31))
        font4 = QFont()
        font4.setFamilies([u"Sans"])
        font4.setPointSize(10)
        self.schedule_close_bnt.setFont(font4)
        self.schedule_close_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.schedule_close_bnt.setStyleSheet(u"background-color: rgb(237, 51, 59);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 10px;\n"
"\n"
"")
        self.schedule_remove_bnt = QPushButton(schedule_window)
        self.schedule_remove_bnt.setObjectName(u"schedule_remove_bnt")
        self.schedule_remove_bnt.setGeometry(QRect(500, 10, 61, 31))
        self.schedule_remove_bnt.setFont(font4)
        self.schedule_remove_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.schedule_remove_bnt.setStyleSheet(u"background-color: rgb(36, 39, 44);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 10px;\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"")
        self.top_logo_2 = QLabel(schedule_window)
        self.top_logo_2.setObjectName(u"top_logo_2")
        self.top_logo_2.setGeometry(QRect(10, 10, 184, 31))
        self.top_logo_2.setMinimumSize(QSize(1, 1))
        self.top_logo_2.setMaximumSize(QSize(251, 41))
        self.top_logo_2.setFont(font3)
        self.top_logo_2.setPixmap(QPixmap(u":/newPrefix/images/logo.png"))
        self.top_logo_2.setScaledContents(True)

        self.retranslateUi(schedule_window)

        QMetaObject.connectSlotsByName(schedule_window)
    # setupUi

    def retranslateUi(self, schedule_window):
        schedule_window.setWindowTitle(QCoreApplication.translate("schedule_window", u"camera schedule", None))
        self.schedule_camera_list_label.setText(QCoreApplication.translate("schedule_window", u"\uce74\uba54\ub77c \ub9ac\uc2a4\ud2b8", None))

        __sortingEnabled = self.schedule_camera_list.isSortingEnabled()
        self.schedule_camera_list.setSortingEnabled(False)
        ___qlistwidgetitem = self.schedule_camera_list.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem1 = self.schedule_camera_list.item(1)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem2 = self.schedule_camera_list.item(2)
        ___qlistwidgetitem2.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem3 = self.schedule_camera_list.item(3)
        ___qlistwidgetitem3.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem4 = self.schedule_camera_list.item(4)
        ___qlistwidgetitem4.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem5 = self.schedule_camera_list.item(5)
        ___qlistwidgetitem5.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem6 = self.schedule_camera_list.item(6)
        ___qlistwidgetitem6.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem7 = self.schedule_camera_list.item(7)
        ___qlistwidgetitem7.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem8 = self.schedule_camera_list.item(8)
        ___qlistwidgetitem8.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        ___qlistwidgetitem9 = self.schedule_camera_list.item(9)
        ___qlistwidgetitem9.setText(QCoreApplication.translate("schedule_window", u"New Item", None));
        self.schedule_camera_list.setSortingEnabled(__sortingEnabled)

        self.intr_bnt.setText(QCoreApplication.translate("schedule_window", u"\uce68\uc785", None))
        self.fire_bnt.setText(QCoreApplication.translate("schedule_window", u"\ubc29\ud654", None))
        self.loit_bnt.setText(QCoreApplication.translate("schedule_window", u"\ubc30\ud68c", None))
        self.fall_bnt.setText(QCoreApplication.translate("schedule_window", u"\uc4f0\ub7ec\uc9d0", None))
        self.fight_bnt.setText(QCoreApplication.translate("schedule_window", u"\uc2f8\uc6c0", None))
        ___qtablewidgetitem = self.schedule_time_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("schedule_window", u"0", None));
        ___qtablewidgetitem1 = self.schedule_time_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("schedule_window", u"1", None));
        ___qtablewidgetitem2 = self.schedule_time_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("schedule_window", u"2", None));
        ___qtablewidgetitem3 = self.schedule_time_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("schedule_window", u"3", None));
        ___qtablewidgetitem4 = self.schedule_time_table.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("schedule_window", u"4", None));
        ___qtablewidgetitem5 = self.schedule_time_table.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("schedule_window", u"5", None));
        ___qtablewidgetitem6 = self.schedule_time_table.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("schedule_window", u"6", None));
        ___qtablewidgetitem7 = self.schedule_time_table.horizontalHeaderItem(7)
        ___qtablewidgetitem7.setText(QCoreApplication.translate("schedule_window", u"7", None));
        ___qtablewidgetitem8 = self.schedule_time_table.horizontalHeaderItem(8)
        ___qtablewidgetitem8.setText(QCoreApplication.translate("schedule_window", u"8", None));
        ___qtablewidgetitem9 = self.schedule_time_table.horizontalHeaderItem(9)
        ___qtablewidgetitem9.setText(QCoreApplication.translate("schedule_window", u"9", None));
        ___qtablewidgetitem10 = self.schedule_time_table.horizontalHeaderItem(10)
        ___qtablewidgetitem10.setText(QCoreApplication.translate("schedule_window", u"10", None));
        ___qtablewidgetitem11 = self.schedule_time_table.horizontalHeaderItem(11)
        ___qtablewidgetitem11.setText(QCoreApplication.translate("schedule_window", u"11", None));
        ___qtablewidgetitem12 = self.schedule_time_table.horizontalHeaderItem(12)
        ___qtablewidgetitem12.setText(QCoreApplication.translate("schedule_window", u"12", None));
        ___qtablewidgetitem13 = self.schedule_time_table.horizontalHeaderItem(13)
        ___qtablewidgetitem13.setText(QCoreApplication.translate("schedule_window", u"13", None));
        ___qtablewidgetitem14 = self.schedule_time_table.horizontalHeaderItem(14)
        ___qtablewidgetitem14.setText(QCoreApplication.translate("schedule_window", u"14", None));
        ___qtablewidgetitem15 = self.schedule_time_table.horizontalHeaderItem(15)
        ___qtablewidgetitem15.setText(QCoreApplication.translate("schedule_window", u"15", None));
        ___qtablewidgetitem16 = self.schedule_time_table.horizontalHeaderItem(16)
        ___qtablewidgetitem16.setText(QCoreApplication.translate("schedule_window", u"16", None));
        ___qtablewidgetitem17 = self.schedule_time_table.horizontalHeaderItem(17)
        ___qtablewidgetitem17.setText(QCoreApplication.translate("schedule_window", u"17", None));
        ___qtablewidgetitem18 = self.schedule_time_table.horizontalHeaderItem(18)
        ___qtablewidgetitem18.setText(QCoreApplication.translate("schedule_window", u"18", None));
        ___qtablewidgetitem19 = self.schedule_time_table.horizontalHeaderItem(19)
        ___qtablewidgetitem19.setText(QCoreApplication.translate("schedule_window", u"19", None));
        ___qtablewidgetitem20 = self.schedule_time_table.horizontalHeaderItem(20)
        ___qtablewidgetitem20.setText(QCoreApplication.translate("schedule_window", u"20", None));
        ___qtablewidgetitem21 = self.schedule_time_table.horizontalHeaderItem(21)
        ___qtablewidgetitem21.setText(QCoreApplication.translate("schedule_window", u"21", None));
        ___qtablewidgetitem22 = self.schedule_time_table.horizontalHeaderItem(22)
        ___qtablewidgetitem22.setText(QCoreApplication.translate("schedule_window", u"22", None));
        ___qtablewidgetitem23 = self.schedule_time_table.horizontalHeaderItem(23)
        ___qtablewidgetitem23.setText(QCoreApplication.translate("schedule_window", u"23", None));
        ___qtablewidgetitem24 = self.schedule_time_table.verticalHeaderItem(0)
        ___qtablewidgetitem24.setText(QCoreApplication.translate("schedule_window", u"\uc77c", None));
        ___qtablewidgetitem25 = self.schedule_time_table.verticalHeaderItem(1)
        ___qtablewidgetitem25.setText(QCoreApplication.translate("schedule_window", u"\uc6d4", None));
        ___qtablewidgetitem26 = self.schedule_time_table.verticalHeaderItem(2)
        ___qtablewidgetitem26.setText(QCoreApplication.translate("schedule_window", u"\ud654", None));
        ___qtablewidgetitem27 = self.schedule_time_table.verticalHeaderItem(3)
        ___qtablewidgetitem27.setText(QCoreApplication.translate("schedule_window", u"\uc218", None));
        ___qtablewidgetitem28 = self.schedule_time_table.verticalHeaderItem(4)
        ___qtablewidgetitem28.setText(QCoreApplication.translate("schedule_window", u"\ubaa9", None));
        ___qtablewidgetitem29 = self.schedule_time_table.verticalHeaderItem(5)
        ___qtablewidgetitem29.setText(QCoreApplication.translate("schedule_window", u"\uae08", None));
        ___qtablewidgetitem30 = self.schedule_time_table.verticalHeaderItem(6)
        ___qtablewidgetitem30.setText(QCoreApplication.translate("schedule_window", u"\ud1a0", None));
        self.check_box_mon.setText("")
        self.check_box_tue.setText("")
        self.check_box_wed.setText("")
        self.check_box_thu.setText("")
        self.check_box_fri.setText("")
        self.check_box_sat.setText("")
        self.check_box_sun.setText("")
        self.schedule_close_bnt.setText(QCoreApplication.translate("schedule_window", u"\ub2eb\uae30", None))
        self.schedule_remove_bnt.setText(QCoreApplication.translate("schedule_window", u"\uc804\uccb4 \uc0ad\uc81c", None))
        self.top_logo_2.setText("")
    # retranslateUi

