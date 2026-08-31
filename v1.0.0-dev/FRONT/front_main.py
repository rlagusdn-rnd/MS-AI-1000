import base64
import json
import os
import platform
import socket
import subprocess
import sys
import time

import psutil
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QUrl, pyqtSlot, QVariant
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QFileDialog

import fn

import sys
import os
from pathlib import Path

File_Path = Path(__file__).resolve()



class WebEnginePage(QWebEnginePage):
    """
    자바스크립트 채널을 통해 웹페이지와 통신
    """
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # print('-' * 20)
        # print(message)
        # print("in jsconsole at ", lineNumber, ' lines')
        # print('-' * 20)
        pass
        """
        print('-' * 20)
        print(message)
        print("in jsconsole at ", lineNumber, ' lines')
        print('-' * 20)
        """

class Viewer(QtWidgets.QMainWindow):
    def __init__(self):
        super(Viewer, self).__init__()
        self.socket_setting = ("127.0.0.1", 18393, '!@')
        self.working_directory = os.path.dirname(os.path.realpath(__file__)).replace("\\","/")
        #print('direc ', self.working_directory)

        self.is_window = (platform.system().lower().find('windows') >= 0)
        self.browser = None
        self.is_browser_load_finished = False
        # 백엔드와의 통신을 위한 쓰레드
        self.socket_worker = None
        # 브라우져와의 통신을 위한 채널
        self.channel = QWebChannel()
        self.channel.registerObject('backend', self)
        QtCore.qInstallMessageHandler(lambda x, y, z: None)

    def __del__(self):
        pass


    def start(self):
        try:
            self.backend_start()
            screen = app.primaryScreen()
            size = screen.size()
            self.browser = QWebEngineView()

            self.browser.setPage(WebEnginePage(self.browser))
            self.browser.page().setWebChannel(self.channel)
            self.browser.loadFinished.connect(self.onLoadFinished)
            self.browser.urlChanged.connect(self.onUrlChanged)

            self.browser.setWindowTitle('MS AI')
            self.browser.setWindowIcon(QtGui.QIcon(self.working_directory + '/HTML/images/icon2.png'))
            self.browser.load(QUrl.fromLocalFile(self.working_directory +'/HTML/login.html'))
            #self.browser.load(QUrl(self.working_directory +'/HTML/manage.html'))
            self.browser.daemon = True
            self.browser.show()

            #for dual monitor left
            #self.browser.setGeometry(-1920 + 50, 70, 1600, 900)
            #single monitor
            self.browser.setGeometry(50, 70, 1600, 900)
            #self.browser.showFullScreen()
            self.browser.activateWindow()

        except Exception as ex:
            fn.error(ex)
    """
    자바스크립트를 통해 들어온 명령어를 처리
    """
    # region === CHANNEL COMMUNICATION MAIN ===
    @pyqtSlot(QVariant, result=QVariant)
    def be_send_cmd(self, param_json):
        # json = {cmd:cmd, data:data}
        try:
            cmd = param_json["cmd"]
            data = param_json["data"]
            print("Front",cmd)
            result = {"cmd": "", "data": {}, "error": "", "action": ""}

            #region === without socket treatment ===
            if cmd == 'mg-setting-record-folder':
                folder = self.show_folder_dialog("녹화폴더를 선택하세요.", data)
                if folder=="":
                    result["error"]="취소하였습니다."
                else:
                    result["data"]=folder
                pass
            elif cmd == 'mg-setting-snapshot-folder':
                folder = self.show_folder_dialog("정지영상 폴더를 선택하세요.", data)
                if folder == "":
                    result["error"] = "취소하였습니다."
                else:
                    result["data"] = folder
                pass
            elif cmd == 'mg-admin-logo':
                file = self.show_file_dialog("로그 이미지를 선택하세요.", os.path.dirname(data), "Images (*.png *.jpg *.gif, *.bmp)")
                if file == "":
                    result["error"] = "취소하였습니다."
                else:
                    result["data"] = file
                pass
            elif cmd == 'mg-admin-manual':
                file = self.show_file_dialog("매뉴얼을 선택하세요.", os.path.dirname(data), "PDF(*.pdf)")
                if file == "":
                    result["error"] = "취소하였습니다."
                else:
                    result["data"] = file
                pass
            elif cmd == 'mg-admin-firmware':
                file = self.show_file_dialog("매뉴얼을 선택하세요.", os.path.dirname(data), "ZIP(*.zip)")
                if file == "":
                    result["error"] = "취소하였습니다."
                else:
                    result["data"] = file
            elif cmd == 'mg-admin-firmware-apply': #TODO 펌웨어 업데이트 로직 필요
                pass
            elif cmd == 'mg-load-image':
                image_url = self.load_url_image(data)
                if image_url == "":
                    result["error"] = "파일이 없습니다.\n"+data
                else:
                    result["data"] = image_url
                pass
            elif cmd == 'mg-setting-manual':
                pdf_path = os.path.join(File_Path.parents[1], "MS-AI_1000_v1.0_제품_메뉴얼.pdf")
                cmd_ = f"xdg-open {pdf_path}"
                os.system(cmd_)

            elif cmd == 'mg-exit':
                self.ask_exit()
            # endregion

            # region === with socket treatment ===
            else :
                HOST, PORT, DELIMITER = self.socket_setting
                BUFFER = 2048
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((HOST, PORT))
                    try:
                        # print('###', json.dumps(param_json) + DELIMITER)
                        sock.sendall((json.dumps(param_json) + DELIMITER).encode('utf-8'))
                        buffer = b''
                        while True:
                            buffer += sock.recv(BUFFER)
                            # print('received ', len(buffer))
                            received_str = buffer.decode('utf-8')
                            if received_str.find(DELIMITER)>-1:
                                received_str = received_str[:received_str.find(DELIMITER)]
                                result = json.loads(received_str)
                                break
                        # sleep(0.5)
                    except Exception as ex:
                        result["error"] = str(ex)
                        fn.error(ex)
            # endregion
        except Exception as ex:
            result["error"] = str(ex)
            fn.error(ex)
        finally:
            return result

    # endregion


    # region === ETC ===
    @pyqtSlot()
    def ask_exit(self):
        QtWidgets.QApplication.exit(0)

    def backend_start(self):
        try:
            #return
            # print("PREPARE BACKEND SERVER.")
            self.backend_end()

            direc = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/").replace("/FRONT", "/BACK")

            os.system('echo admin123 | xhost + local:docker')
            os.system('docker start ms-ai')
            subprocess.Popen([f'docker exec -it ms-ai sh -c "python3 /root/workspace/{str(File_Path.parents[1]).split("/")[-1]}/BACK/backend_main.py" '], cwd=direc, shell=True )

            itry = 0
            print("***Wait server***")
            for i in range(10):
                itry += 1
                HOST, PORT, DELIMITER = self.socket_setting
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    try:
                        sock.connect((HOST, PORT))
                        sock.sendall(('{"cmd": "check", "data": {}}' + DELIMITER).encode())
                        sock.recv(2048)
                        break
                    except Exception as ex:
                        # print("check backend server is alive ! ", itry)
                        time.sleep(0.5)
                    finally:
                        sock.close()
            #10번(5초) 백엔드에 연결에 실패하면 프로그램 종료
            if itry>=100:
                print("cannot backend server 관리자에게 문의하여 주세요")
                exit()
            else:
                print("complete.")
        except Exception as ex:
            fn.error(ex)

    def backend_end(self):
        #return
        try:
            os.system("docker stop ms-ai")
            # os.system("docker stop test")

            for proc in psutil.process_iter():
                if proc.name().find("python") > -1:
                    cmdline = proc.cmdline()
                    if "backend_main.py" in cmdline:
                        print("kill ", proc.name(), proc.cmdline())
                        proc.kill()
        except Exception as ex:
            fn.error(ex)

    #url 변경시 호출
    def onUrlChanged(self, url):
        try:
            pass
            #fn.debug(url.toString())
        except Exception as ex:
            fn.error(ex)
    def onLoadFinished(self, ok):
        try:
            if ok:
                self.run_script("if(location.href.indexOf('manage.html')>-1) mg.init()")
                self.is_browser_load_finished = True
                pass
        except Exception as ex:
            fn.error(ex)


    #브라우져에 자바스크립트를 실행
    def run_script(self, script):
        try:
            if self.is_browser_load_finished:
                self.browser.page().runJavaScript(script)
            else:
                pass
                # print("Browser doesn't load finished!!")
            # print(script)
        except Exception as ex:
            fn.error(ex)

    #로컬이미지를 URL 이미지로 변경
    def load_url_image(self, filename):
        try:
            if not os.path.exists(filename) :
                filename = str(File_Path.parents[0]) + "/HTML/images/logo.png"
            binary_fc = open(filename, 'rb').read()  # fc aka file_content
            base64_utf8_str = base64.b64encode(binary_fc).decode('utf-8')

            ext = filename.split('.')[-1]
            return f'data:image/{ext};base64,{base64_utf8_str}'

        except Exception as ex:
            fn.error(ex)
            return ""

    # 파일 다이얼로그
    def show_file_dialog(self, msg, folder, sfilter):
        fname = QFileDialog.getOpenFileName(self, msg, folder, sfilter)
        if len(fname)>0:
            return fname[0]
        else:
            return ""

    # 폴더 다이얼로그
    def show_folder_dialog(self, msg, folder):
        fname = QFileDialog.getExistingDirectory(self, msg, folder)
        if fname != "":
            return fname
        else:
            return ""
    # endregion

if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        window = Viewer()
        window.start()

        sys.exit(app.exec())
    except Exception as ex:
        fn.error(ex)
    finally:
        window.backend_end()



