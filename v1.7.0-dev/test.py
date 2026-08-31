import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, 
    QTreeWidget, QTreeWidgetItem, QLineEdit,
    QAbstractItemView
)
from PySide6.QtGui import QDrag
from PySide6.QtCore import QMimeData, Qt

# --- 1. 보내는 위젯 (Source) ---
class MyTreeWidget(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderLabels(["항목"])
        
        # 1. 드래그 활성화
        self.setDragEnabled(True)
        # 2. 드롭 모드 설정 (외부로도 나갈 수 있게)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.CopyAction) # 이동 대신 복사

        # --- 🎨 스타일시트 적용 ---
        self.setStyleSheet("""
            QTreeWidget {
                background-color: black;  /* 전체 배경색 */
                color: #E0E0E0;             /* 기본 글자색 (완전 흰색보다 부드러움) */
                border: none;             /* 테두리 없음 */
                outline: 0;               /* 포커스 테두리 제거 */
                font-size: 10pt;          /* 폰트 크기 */
            }

            /* --- 항목(Item) 스타일 --- */
            QTreeWidget::item {
                padding-top: 5px;       /* 항목 위 여백 */
                padding-bottom: 5px;    /* 항목 아래 여백 */
            }

            /* 항목에 마우스를 올렸을 때 */
            QTreeWidget::item:hover {
                background-color: #2a2a2a;
                border-radius: 4px;
            }

            /* 항목을 선택했을 때 */
            QTreeWidget::item:selected {
                background-color: #4a4a4a;
                border-radius: 4px;
            }

            /* --- 헤드(Branch) 스타일 (화살표 아이콘) --- */
            
            /* 기본 점선 및 아이콘 숨기기 */
            QTreeWidget::branch {
                background: transparent;
                border-image: none;
                image: none;
            }

            /* * ---  중요  ---
             * 아래 'image: url(...)' 경로가 작동하려면
             * 'arrow-right.png' (접힌 화살표)와 
             * 'arrow-down.png' (펼친 화살표) 파일이
             * 이 스크립트와 동일한 폴더에 있어야 합니다.
             * (또는, Qt 리소스(.qrc)를 사용하세요.)
            */
            
            /* 자식이 있고(has-children) 접혔을 때(closed) 아이콘 */
            QTreeWidget::branch:closed:has-children {
                image: url(arrow-right.png);
            }

            /* 자식이 있고(has-children) 펼쳐졌을 때(open) 아이콘 */
            QTreeWidget::branch:open:has-children {
                image: url(arrow-down.png);
            }
        """)

        # --- 예제 데이터 (항목 3개 추가) ---
        parent_a = QTreeWidgetItem(self, ["그룹 A"])
        QTreeWidgetItem(parent_a, ["아이템 A"])
        QTreeWidgetItem(parent_a, ["아이템 B"])
        QTreeWidgetItem(parent_a, ["아이템 C"])

        parent_b = QTreeWidgetItem(self, ["그룹 B"])
        # 요청하신 3개 추가 항목
        QTreeWidgetItem(parent_b, ["아이템 D (추가)"])
        QTreeWidgetItem(parent_b, ["아이템 E (추가)"])
        QTreeWidgetItem(parent_b, ["아이템 F (추가)"])

        # 모든 항목 펼치기
        self.expandAll()
        
        # 헤더 숨기기 (이미지처럼 보이게)
        self.setHeaderHidden(True)


    def startDrag(self, supportedActions):
        """드래그가 시작될 때 호출되는 메서드 (재정의)"""
        
        selected_item = self.currentItem()
        if not selected_item:
            return
            
        # ⭐️ 부모 항목(그룹 A, B)은 드래그되지 않도록 방지
        if selected_item.childCount() > 0:
            print("부모 항목은 드래그할 수 없습니다.")
            return

        mime_data = QMimeData()
        mime_data.setText(selected_item.text(0))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # 드래그 중인 아이템의 반투명 이미지 표시
        pixmap = selected_item.icon(0).pixmap(32, 32) 
        if pixmap.isNull():
             pixmap = self.viewport().grab(selected_item.visualRect(self.viewport().rect()))
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())

        print(f"[{selected_item.text(0)}] 드래그 시작...")
        
        drag.exec(Qt.DropAction.CopyAction)


# --- 2. 받는 위젯 (Target) ---
class MyLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        
        self.setAcceptDrops(True)
        self.setPlaceholderText("여기에 아이템을 드롭하세요...")
        
        # 받는 쪽도 다크 테마 적용
        self.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                background-color: #222;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
            }
            QLineEdit::placeholder {
                color: #777;
            }
        """)

    def dragEnterEvent(self, event):
        """드래그가 위젯 영역으로 들어왔을 때 호출됨 (재정의)"""
        
        if event.mimeData().hasText():
            event.acceptProposedAction() 
            print("드래그 진입: (드롭 가능)")
        else:
            event.ignore()

    def dropEvent(self, event):
        """아이템을 실제로 드롭했을 때 호출됨 (재정의)"""
        
        if event.mimeData().hasText():
            text = event.mimeData().text()
            self.setText(text) 
            print(f"드롭 완료: [{text}]")
            event.acceptProposedAction()
        else:
            event.ignore()


# --- 3. 메인 윈도우 ---
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("스타일이 적용된 드래그 앤 드롭")
        
        self.tree = MyTreeWidget()
        self.line_edit = MyLineEdit()
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addWidget(self.line_edit)
        
        self.resize(400, 500)
        
        # 메인 윈도우 배경색 (일관성을 위해)
        self.setStyleSheet("background-color: black;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())