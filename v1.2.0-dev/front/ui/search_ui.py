# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'search.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDateEdit,
    QDoubleSpinBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QSizePolicy, QTableWidget, QTableWidgetItem,
    QWidget)
import ms_ai_img_rc
import ms_ai_img_rc

class Ui_Search_window(object):
    def setupUi(self, Search_window):
        if not Search_window.objectName():
            Search_window.setObjectName(u"Search_window")
        Search_window.resize(1163, 526)
        Search_window.setWindowTitle(u"Search")
        Search_window.setStyleSheet(u"background-color: rgb(20, 20, 20);\n"
"")
        self.search_viewer = QLabel(Search_window)
        self.search_viewer.setObjectName(u"search_viewer")
        self.search_viewer.setGeometry(QRect(20, 54, 640, 451))
        font = QFont()
        font.setFamilies([u"Sans"])
        self.search_viewer.setFont(font)
        self.search_viewer.setStyleSheet(u"border: 1px solid rgb(119, 118, 123);\n"
"border-radius: 10px ;")
        self.search_viewer.setPixmap(QPixmap(u":/newPrefix/images/logo.png"))
        self.search_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label = QLabel(Search_window)
        self.time_label.setObjectName(u"time_label")
        self.time_label.setGeometry(QRect(666, 15, 61, 41))
        font1 = QFont()
        font1.setFamilies([u"Sans"])
        font1.setPointSize(12)
        self.time_label.setFont(font1)
        self.time_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(191, 64, 64, 0);")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.event_table = QTableWidget(Search_window)
        if (self.event_table.columnCount() < 4):
            self.event_table.setColumnCount(4)
        font2 = QFont()
        font2.setPointSize(12)
        __qtablewidgetitem = QTableWidgetItem()
        __qtablewidgetitem.setFont(font2);
        self.event_table.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        __qtablewidgetitem1.setFont(font2);
        self.event_table.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        __qtablewidgetitem2.setFont(font2);
        self.event_table.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        __qtablewidgetitem3.setFont(font2);
        self.event_table.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.event_table.setObjectName(u"event_table")
        self.event_table.setGeometry(QRect(671, 132, 481, 371))
        font3 = QFont()
        font3.setFamilies([u"Sans"])
        font3.setPointSize(11)
        font3.setBold(False)
        self.event_table.setFont(font3)
        self.event_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.event_table.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"")
        self.event_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.event_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.event_table.setShowGrid(False)
        self.event_table.setGridStyle(Qt.PenStyle.DashDotLine)
        self.event_table.setSortingEnabled(False)
        self.event_table.setWordWrap(False)
        self.event_table.horizontalHeader().setHighlightSections(False)
        self.event_table.horizontalHeader().setStretchLastSection(True)
        self.event_table.verticalHeader().setVisible(False)
        self.event_table.verticalHeader().setHighlightSections(False)
        self.event_table.verticalHeader().setStretchLastSection(False)
        self.time_tilde = QLabel(Search_window)
        self.time_tilde.setObjectName(u"time_tilde")
        self.time_tilde.setGeometry(QRect(920, 25, 41, 21))
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.time_tilde.sizePolicy().hasHeightForWidth())
        self.time_tilde.setSizePolicy(sizePolicy)
        self.time_tilde.setFont(font1)
        self.time_tilde.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(191, 64, 64, 0);")
        self.time_tilde.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_day_start_input = QDateEdit(Search_window)
        self.time_day_start_input.setObjectName(u"time_day_start_input")
        self.time_day_start_input.setGeometry(QRect(720, 20, 121, 31))
        font4 = QFont()
        font4.setFamilies([u"Sans"])
        font4.setPointSize(10)
        self.time_day_start_input.setFont(font4)
        self.time_day_start_input.setStyleSheet(u"\n"
"\n"
"\n"
"            QDateEdit {\n"
"                padding: 5px;\n"
"					color: rgb(255, 255, 255);\n"
"					background-color: rgb(13, 16, 23);\n"
"					selection-background-color: rgb(53, 132, 228);\n"
"\n"
"            }\n"
"			QCalendarWidget {\n"
"                background-color: rgb(87, 227, 137);\n"
"                alternate-background-color: rgb(87, 227, 137);\n"
"            }\n"
"            QCalendarWidget QWidget { /* All child widgets of QCalendarWidget */\n"
"                color: black;\n"
"					background-color: #f0f0f0;  \n"
"					alternate-background-color: rgb(28, 113, 216);\n"
"            }\n"
"            QCalendarWidget QAbstractItemView {\n"
"                selection-background-color: rgb(87, 227, 137);;\n"
"                selection-color: white;\n"
"            }\n"
"\n"
"")
        self.time_day_start_input.setCalendarPopup(True)
        self.search_close_bnt = QPushButton(Search_window)
        self.search_close_bnt.setObjectName(u"search_close_bnt")
        self.search_close_bnt.setGeometry(QRect(1080, 95, 61, 31))
        self.search_close_bnt.setFont(font4)
        self.search_close_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.search_close_bnt.setStyleSheet(u"background-color: rgb(237, 51, 59);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 10px;\n"
"border: 1px solid rgba(255, 255, 255, 100);\n"
"")
        self.time_search_bnt = QPushButton(Search_window)
        self.time_search_bnt.setObjectName(u"time_search_bnt")
        self.time_search_bnt.setGeometry(QRect(1010, 94, 61, 31))
        self.time_search_bnt.setFont(font4)
        self.time_search_bnt.setCursor(QCursor(Qt.PointingHandCursor))
        self.time_search_bnt.setStyleSheet(u"background-color: qlineargradient(spread:pad, x1:0.244, y1:0.477, x2:1, y2:0.489, stop:0.0845771 rgba(0, 205, 0, 255), stop:1 rgba(56, 188, 56, 255));\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 10px;\n"
"border: 1px solid rgba(255, 255, 255, 100);")
        self.time_day_end_input = QDateEdit(Search_window)
        self.time_day_end_input.setObjectName(u"time_day_end_input")
        self.time_day_end_input.setGeometry(QRect(956, 20, 121, 31))
        self.time_day_end_input.setFont(font4)
        self.time_day_end_input.setStyleSheet(u"            QDateEdit {\n"
"                padding: 5px;\n"
"                color: white;\n"
"            }\n"
"			QCalendarWidget {\n"
"                background-color: rgb(87, 227, 137);\n"
"                alternate-background-color: rgb(87, 227, 137);\n"
"            }\n"
"            QCalendarWidget QWidget { /* All child widgets of QCalendarWidget */\n"
"                color: black;\n"
"					background-color: #f0f0f0;  \n"
"					alternate-background-color: rgb(28, 113, 216);\n"
"            }\n"
"            QCalendarWidget QAbstractItemView {\n"
"                selection-background-color: rgb(87, 227, 137);;\n"
"                selection-color: white;\n"
"            }\n"
"\n"
"")
        self.time_day_end_input.setCalendarPopup(True)
        self.layoutWidget = QWidget(Search_window)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(997, 60, 131, 28))
        self.layoutWidget.setFont(font)
        self.horizontalLayout_2 = QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.sort_label = QLabel(self.layoutWidget)
        self.sort_label.setObjectName(u"sort_label")
        self.sort_label.setFont(font1)
        self.sort_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(191, 64, 64, 0);")
        self.sort_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout_2.addWidget(self.sort_label)

        self.sort_box = QComboBox(self.layoutWidget)
        self.sort_box.addItem("")
        self.sort_box.addItem("")
        self.sort_box.setObjectName(u"sort_box")
        self.sort_box.setFont(font3)
        self.sort_box.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.sort_box.setMinimumContentsLength(0)

        self.horizontalLayout_2.addWidget(self.sort_box)

        self.layoutWidget1 = QWidget(Search_window)
        self.layoutWidget1.setObjectName(u"layoutWidget1")
        self.layoutWidget1.setGeometry(QRect(861, 61, 123, 28))
        self.layoutWidget1.setFont(font)
        self.horizontalLayout = QHBoxLayout(self.layoutWidget1)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.event_label = QLabel(self.layoutWidget1)
        self.event_label.setObjectName(u"event_label")
        self.event_label.setFont(font1)
        self.event_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(191, 64, 64, 0);")
        self.event_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.event_label)

        self.event_box = QComboBox(self.layoutWidget1)
        self.event_box.addItem("")
        self.event_box.addItem("")
        self.event_box.addItem("")
        self.event_box.addItem("")
        self.event_box.addItem("")
        self.event_box.addItem("")
        self.event_box.setObjectName(u"event_box")
        self.event_box.setFont(font3)
        self.event_box.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.event_box.setMinimumContentsLength(0)

        self.horizontalLayout.addWidget(self.event_box)

        self.time_hour_start_box = QComboBox(Search_window)
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.addItem("")
        self.time_hour_start_box.setObjectName(u"time_hour_start_box")
        self.time_hour_start_box.setGeometry(QRect(850, 20, 71, 31))
        font5 = QFont()
        font5.setFamilies([u"Sans"])
        font5.setPointSize(10)
        font5.setBold(False)
        self.time_hour_start_box.setFont(font5)
        self.time_hour_start_box.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.time_hour_start_box.setEditable(True)
        self.time_hour_start_box.setMinimumContentsLength(0)
        self.time_hour_end_box = QComboBox(Search_window)
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.addItem("")
        self.time_hour_end_box.setObjectName(u"time_hour_end_box")
        self.time_hour_end_box.setGeometry(QRect(1080, 20, 71, 31))
        self.time_hour_end_box.setFont(font5)
        self.time_hour_end_box.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.time_hour_end_box.setEditable(True)
        self.time_hour_end_box.setMinimumContentsLength(0)
        self.camera_num_label = QLabel(Search_window)
        self.camera_num_label.setObjectName(u"camera_num_label")
        self.camera_num_label.setGeometry(QRect(676, 60, 81, 25))
        self.camera_num_label.setFont(font1)
        self.camera_num_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(191, 64, 64, 0);")
        self.camera_num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_name_box = QComboBox(Search_window)
        self.camera_name_box.setObjectName(u"camera_name_box")
        self.camera_name_box.setGeometry(QRect(763, 60, 86, 25))
        self.camera_name_box.setFont(font3)
        self.camera_name_box.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"background-color: rgb(13, 16, 23);\n"
"selection-background-color: rgb(53, 132, 228);\n"
"")
        self.camera_name_box.setMinimumContentsLength(0)
        self.time_video_time_speed_label = QLabel(Search_window)
        self.time_video_time_speed_label.setObjectName(u"time_video_time_speed_label")
        self.time_video_time_speed_label.setGeometry(QRect(680, 90, 31, 31))
        font6 = QFont()
        font6.setFamilies([u"Sans"])
        font6.setPointSize(11)
        self.time_video_time_speed_label.setFont(font6)
        self.time_video_time_speed_label.setStyleSheet(u"color: rgb(179,179,179);\n"
"background-color: rgba(255, 255, 255, 0);")
        self.time_video_time_speed_label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        self.time_video_time_speed_input = QDoubleSpinBox(Search_window)
        self.time_video_time_speed_input.setObjectName(u"time_video_time_speed_input")
        self.time_video_time_speed_input.setGeometry(QRect(718, 87, 65, 36))
        self.time_video_time_speed_input.setStyleSheet(u"color: rgb(255, 255, 255);")
        self.time_video_time_speed_input.setMinimum(1.000000000000000)
        self.time_video_time_speed_input.setMaximum(10.000000000000000)
        self.time_video_time_speed_input.setSingleStep(0.200000000000000)
        self.top_logo = QLabel(Search_window)
        self.top_logo.setObjectName(u"top_logo")
        self.top_logo.setGeometry(QRect(20, 11, 189, 32))
        self.top_logo.setMinimumSize(QSize(1, 1))
        self.top_logo.setMaximumSize(QSize(251, 41))
        self.top_logo.setFont(font)
        self.top_logo.setPixmap(QPixmap(u":/newPrefix/images/logo.png"))
        self.top_logo.setScaledContents(True)

        self.retranslateUi(Search_window)

        QMetaObject.connectSlotsByName(Search_window)
    # setupUi

    def retranslateUi(self, Search_window):
        self.search_viewer.setText("")
        self.time_label.setText(QCoreApplication.translate("Search_window", u"\uae30\uac04", None))
        ___qtablewidgetitem = self.event_table.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Search_window", u"\ubc88\ud638", None));
        ___qtablewidgetitem1 = self.event_table.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Search_window", u"\uce74\uba54\ub77c", None));
        ___qtablewidgetitem2 = self.event_table.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("Search_window", u"\uc885\ub958", None));
        ___qtablewidgetitem3 = self.event_table.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("Search_window", u"\uc2dc\uac04", None));
        self.time_tilde.setText(QCoreApplication.translate("Search_window", u"~", None))
        self.time_day_start_input.setDisplayFormat(QCoreApplication.translate("Search_window", u"yyyy. M. d", None))
        self.search_close_bnt.setText(QCoreApplication.translate("Search_window", u"\ub2eb\uae30", None))
        self.time_search_bnt.setText(QCoreApplication.translate("Search_window", u"\uac80\uc0c9", None))
        self.time_day_end_input.setDisplayFormat(QCoreApplication.translate("Search_window", u"yyyy. M. d", None))
        self.sort_label.setText(QCoreApplication.translate("Search_window", u"\uc815\ub82c", None))
        self.sort_box.setItemText(0, QCoreApplication.translate("Search_window", u"\uc2dc\uac04\uc21c", None))
        self.sort_box.setItemText(1, QCoreApplication.translate("Search_window", u"\ucd5c\uc2e0\uc21c", None))

        self.event_label.setText(QCoreApplication.translate("Search_window", u"\uc774\ubca4\ud2b8", None))
        self.event_box.setItemText(0, QCoreApplication.translate("Search_window", u"\uc804\uccb4", None))
        self.event_box.setItemText(1, QCoreApplication.translate("Search_window", u"\uce68\uc785", None))
        self.event_box.setItemText(2, QCoreApplication.translate("Search_window", u"\ubc30\ud68c", None))
        self.event_box.setItemText(3, QCoreApplication.translate("Search_window", u"\uc4f0\ub7ec\uc9d0", None))
        self.event_box.setItemText(4, QCoreApplication.translate("Search_window", u"\uc2f8\uc6c0", None))
        self.event_box.setItemText(5, QCoreApplication.translate("Search_window", u"\ubc29\ud654", None))

        self.time_hour_start_box.setItemText(0, QCoreApplication.translate("Search_window", u"00:00", None))
        self.time_hour_start_box.setItemText(1, QCoreApplication.translate("Search_window", u"01:00", None))
        self.time_hour_start_box.setItemText(2, QCoreApplication.translate("Search_window", u"02:00", None))
        self.time_hour_start_box.setItemText(3, QCoreApplication.translate("Search_window", u"03:00", None))
        self.time_hour_start_box.setItemText(4, QCoreApplication.translate("Search_window", u"04:00", None))
        self.time_hour_start_box.setItemText(5, QCoreApplication.translate("Search_window", u"05:00", None))
        self.time_hour_start_box.setItemText(6, QCoreApplication.translate("Search_window", u"06:00", None))
        self.time_hour_start_box.setItemText(7, QCoreApplication.translate("Search_window", u"07:00", None))
        self.time_hour_start_box.setItemText(8, QCoreApplication.translate("Search_window", u"08:00", None))
        self.time_hour_start_box.setItemText(9, QCoreApplication.translate("Search_window", u"09:00", None))
        self.time_hour_start_box.setItemText(10, QCoreApplication.translate("Search_window", u"10:00", None))
        self.time_hour_start_box.setItemText(11, QCoreApplication.translate("Search_window", u"11:00", None))
        self.time_hour_start_box.setItemText(12, QCoreApplication.translate("Search_window", u"12:00", None))
        self.time_hour_start_box.setItemText(13, QCoreApplication.translate("Search_window", u"13:00", None))
        self.time_hour_start_box.setItemText(14, QCoreApplication.translate("Search_window", u"14:00", None))
        self.time_hour_start_box.setItemText(15, QCoreApplication.translate("Search_window", u"15:00", None))
        self.time_hour_start_box.setItemText(16, QCoreApplication.translate("Search_window", u"16:00", None))
        self.time_hour_start_box.setItemText(17, QCoreApplication.translate("Search_window", u"17:00", None))
        self.time_hour_start_box.setItemText(18, QCoreApplication.translate("Search_window", u"18:00", None))
        self.time_hour_start_box.setItemText(19, QCoreApplication.translate("Search_window", u"19:00", None))
        self.time_hour_start_box.setItemText(20, QCoreApplication.translate("Search_window", u"20:00", None))
        self.time_hour_start_box.setItemText(21, QCoreApplication.translate("Search_window", u"21:00", None))
        self.time_hour_start_box.setItemText(22, QCoreApplication.translate("Search_window", u"22:00", None))
        self.time_hour_start_box.setItemText(23, QCoreApplication.translate("Search_window", u"23:00", None))

        self.time_hour_end_box.setItemText(0, QCoreApplication.translate("Search_window", u"00:00", None))
        self.time_hour_end_box.setItemText(1, QCoreApplication.translate("Search_window", u"01:00", None))
        self.time_hour_end_box.setItemText(2, QCoreApplication.translate("Search_window", u"02:00", None))
        self.time_hour_end_box.setItemText(3, QCoreApplication.translate("Search_window", u"03:00", None))
        self.time_hour_end_box.setItemText(4, QCoreApplication.translate("Search_window", u"04:00", None))
        self.time_hour_end_box.setItemText(5, QCoreApplication.translate("Search_window", u"05:00", None))
        self.time_hour_end_box.setItemText(6, QCoreApplication.translate("Search_window", u"06:00", None))
        self.time_hour_end_box.setItemText(7, QCoreApplication.translate("Search_window", u"07:00", None))
        self.time_hour_end_box.setItemText(8, QCoreApplication.translate("Search_window", u"08:00", None))
        self.time_hour_end_box.setItemText(9, QCoreApplication.translate("Search_window", u"09:00", None))
        self.time_hour_end_box.setItemText(10, QCoreApplication.translate("Search_window", u"10:00", None))
        self.time_hour_end_box.setItemText(11, QCoreApplication.translate("Search_window", u"11:00", None))
        self.time_hour_end_box.setItemText(12, QCoreApplication.translate("Search_window", u"12:00", None))
        self.time_hour_end_box.setItemText(13, QCoreApplication.translate("Search_window", u"13:00", None))
        self.time_hour_end_box.setItemText(14, QCoreApplication.translate("Search_window", u"14:00", None))
        self.time_hour_end_box.setItemText(15, QCoreApplication.translate("Search_window", u"15:00", None))
        self.time_hour_end_box.setItemText(16, QCoreApplication.translate("Search_window", u"16:00", None))
        self.time_hour_end_box.setItemText(17, QCoreApplication.translate("Search_window", u"17:00", None))
        self.time_hour_end_box.setItemText(18, QCoreApplication.translate("Search_window", u"18:00", None))
        self.time_hour_end_box.setItemText(19, QCoreApplication.translate("Search_window", u"19:00", None))
        self.time_hour_end_box.setItemText(20, QCoreApplication.translate("Search_window", u"20:00", None))
        self.time_hour_end_box.setItemText(21, QCoreApplication.translate("Search_window", u"21:00", None))
        self.time_hour_end_box.setItemText(22, QCoreApplication.translate("Search_window", u"22:00", None))
        self.time_hour_end_box.setItemText(23, QCoreApplication.translate("Search_window", u"23:00", None))

        self.camera_num_label.setText(QCoreApplication.translate("Search_window", u"\uce74\uba54\ub77c \uc774\ub984", None))
        self.time_video_time_speed_label.setText(QCoreApplication.translate("Search_window", u"\ubc30\uc18d", None))
        self.top_logo.setText("")
        pass
    # retranslateUi

