from PySide6.QtWidgets import QDialog
from ui.ai_setting_ui import Ui_Ai_Setting_Window
from datetime import datetime
from PySide6.QtCore import QTimer
import requests

from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QPolygon, QBrush, QFont, QStandardItem, QStandardItemModel, QIcon
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QObject, QEvent, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QComboBox,
    QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QPushButton, QSizePolicy,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

from utils import save_info, load_info
from ui import ms_ai_img_rc

import cv2
import numpy as np 

class Ai_setting_page_view(QLabel):
    Checked = Signal(QLabel)
    def __init__(self, base_viewer, camera_num, camera_name, ai_check_box, name_label, instance):
        super().__init__(base_viewer)
        self.setGeometry(QRect(1, 1, 253, 145))

        self.checked = False
        self.camera_num = camera_num
        self.camera_name = camera_name
        self.ai_check_box = ai_check_box
        self.name_label = name_label

        # self.ai_off_img = QPixmap(u":/newPrefix/images/ai_off.png")
        # self.ai_on_img = QPixmap(u":/newPrefix/images/ai_on.png")

        self.instance = instance

        self.frame_flag = False


    def setChecked(self, checked):
        self.checked = checked
        self.updateStyle()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self.checked)

    def enterEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.setChecked(True)
            
    def updateStyle(self):
            if self.checked:
                if self.frame_flag:
                    self.setStyleSheet("""
                        QLabel {
                            border: 2px solid rgb(56, 188, 56);
                        }
                    """)

                    self.set_img(self.frame, 1)
                    # self.ai_check_box.setPixmap(self.ai_on_img)
                    self.ai_check_box.show()
                    self.name_label.setStyleSheet("""
                            QLabel {
                                        color: rgb(56, 188, 56);
                                    }
                                """)
                    self.instance.camera_info_dict[self.camera_name]["AI"] = True
            else:
                if self.frame_flag:
                    self.setStyleSheet("""
                        QLabel {
                            border: 1px solid white;
                        }
                    """)
                    self.set_img(self.frame, 0.5)
                    # self.ai_check_box.setPixmap(self.ai_off_img)
                    self.name_label.setStyleSheet("""
                            QLabel {
                                        color: rgb(255, 255, 255);
                                    }
                                """)
                    self.ai_check_box.hide()
                    self.instance.camera_info_dict[self.camera_name]["AI"] = False



    def set_img(self, img, brightness = 1):
        self.frame_flag = True
        self.frame = img.copy()
        cv_image = self.frame.astype('float32')
        cv_image = cv_image * brightness
        cv_image = np.clip(cv_image, 0, 255)
        cv_image = cv_image.astype('uint8')

        height, width, channels = cv_image.shape
        # Calculate the number of bytes per line.
        bytes_per_line = width * channels
        # Convert image from BGR (cv2 default color format) to RGB (Qt default color format).
        cv_rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        # print(cv_rgb_image.shape)
        # Convert the image to Qt format.
        qt_rgb_image = QImage(cv_rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)


        self.setPixmap(QPixmap.fromImage(qt_rgb_image))

def open_ai_setting_window(click, self):
    self.dark_layer.show()
    self.popup_window = QDialog()  # QDialog 인스턴스 생성
    self.popup_window.setWindowFlag(Qt.FramelessWindowHint)

    self.popup_ui = Ui_Ai_Setting_Window()
    self.popup_ui.setupUi(self.popup_window)


    self.ai_setting_camera_view_list = {}

    for camera_name, camera_info in self.camera_info_dict.items():
        num = str(camera_info["Num"])
        self.ai_setting_camera_view_list[camera_name] = Ai_setting_page_view(getattr(self.popup_ui, f"camera_view_{num}"), 
                                                                             camera_name = camera_name, 
                                                                             camera_num = str(num), 
                                                                             ai_check_box = getattr(self.popup_ui, f"camera_view_ai_check_{num}"),
                                                                             name_label = getattr(self.popup_ui, f"camera_view_name_{num}"),
                                                                             instance = self)
        
        getattr(self.popup_ui, f"camera_view_name_{num}").setText(camera_name)
    
    for camera_name, camera_viewer in self.ai_setting_camera_view_list.items():
        find_worker_flag = False
        if camera_name in self.camera_view_list.keys():
            for worker in self.camera_worker_list:
                if camera_name == worker.camera_name:
                    # img_buffer = worker.img_buffer

                    img = worker.frame.copy()

                    frame = cv2.resize(img, (camera_viewer.width(), camera_viewer.height()))
                    camera_viewer.set_img(frame, 0.5)
                    find_worker_flag = True

                    break

        if find_worker_flag == False:
            camera_viewer.setPixmap(QPixmap(u":/newPrefix/images/ico_video_off.svg"))
            camera_viewer.setAlignment(Qt.AlignCenter)
            # getattr(self.popup_ui, f"camera_view_dark_{camera_viewer.camera_num}").hide()
            getattr(self.popup_ui, f"camera_view_ai_check_{camera_viewer.camera_num}").hide()

    check_camera_viewer(self)

    self.popup_ui.camera_save_bnt.clicked.connect(lambda click, instance = self : send_camera_info_and_close(click, instance))
    self.popup_ui.close_bnt.clicked.connect(lambda click, instance = self : cancel_ai_setting(click, instance))
    self.popup_ui.all_select_bnt.clicked.connect(lambda click, instance = self : select_camera(click, instance))

    self.popup_window.finished.connect(self.dark_layer.hide)

    # 메인 윈도우의 중앙에 팝업 윈도우 위치 계산
    mainWindowGeometry = self.frameGeometry()
    centerPoint = mainWindowGeometry.center()

    popupWindowGeometry = self.popup_window.frameGeometry()
    popupCenterPoint = popupWindowGeometry.center()

    # 중앙점에서 팝업 윈도우의 절반 크기를 빼서 팝업 윈도우의 좌상단 좌표를 계산
    topLeftPoint = centerPoint - (popupCenterPoint - popupWindowGeometry.topLeft())
    self.popup_window.move(topLeftPoint)

    # 팝업 윈도우 표시
    self.popup_window.show()

def select_camera(click, self):
    all_check_flag = False
    for camera_name, camera_info in self.camera_info_dict.items():
        if self.ai_setting_camera_view_list[camera_name].checked == False:
            self.ai_setting_camera_view_list[camera_name].setChecked(True)
            all_check_flag = True

    if all_check_flag == False:
        for camera_name, camera_info in self.camera_info_dict.items():
            self.ai_setting_camera_view_list[camera_name].setChecked(False)

def cancel_ai_setting(click, self):

    self.camera_info_dict = load_info(host=self.HOST,
                                    port=self.PORT,
                                    file_name="camera_info")

    self.popup_window.close()

def send_camera_info_and_close(click, self):
    save_info(host=self.HOST, port=self.PORT, file_name="camera_info", info=self.camera_info_dict)

    run_ms_ai(self)
    self.popup_window.close()

    camera_num = self.ui_main.camera_page_name_box.currentText()

    if self.camera_info_dict[camera_num]["AI"] == True:
        self.ui_main.camera_page_viewer.reset()
        self.ui_main.camera_page_ai_active_label.show()
        self.ui_main.camera_page_ai_active_icon.show()


    # 현재 시간을 계산하고 다음 정각까지 남은 시간을 초 단위로 계산합니다.
    now = datetime.now()
    seconds_till_next_hour = (60 - now.minute) * 60 - now.second

    # 타이머 설정
    self.ai_timer = QTimer(self)
    # 첫 번째 실행을 위해 남은 시간 설정
    self.ai_timer.setSingleShot(True)
    self.ai_timer.timeout.connect(lambda : setup_hourly_timer(self))
    self.ai_timer.start(seconds_till_next_hour * 1000)  # 밀리초 단위로 변환
    del self.ai_setting_camera_view_list

def setup_hourly_timer(self):
    run_ms_ai(self)
    # 이제 매시간 함수를 실행하기 위한 타이머 설정
    self.hourly_timer = QTimer(self)
    self.hourly_timer.timeout.connect(run_ms_ai(self))
    self.hourly_timer.start(3600 * 1000)  # 매시간 반복

def run_ms_ai(self):
    save_info(host=self.HOST, port=self.PORT, file_name="camera_info", info=self.camera_info_dict)

    data = {"msg" : "ms_ai"}
    url = f'http://{self.HOST}:{self.PORT}/run_ms_ai'
    receive_data = requests.post(url, json=data).json()

    if self.camera_info_dict[self.ui_main.camera_page_name_box.currentText()]["AI"] == True:
        self.ui_main.camera_page_ai_active_label.show()
        self.ui_main.camera_page_ai_active_icon.show()


def check_camera_viewer(self):
    for camera_name, camera_info in self.camera_info_dict.items():
        if len(camera_info["IP"]):
            if camera_info["AI"] == False:
                self.ai_setting_camera_view_list[camera_name].setChecked(False)

            elif camera_info["AI"] == True:
                self.ai_setting_camera_view_list[camera_name].setChecked(True)