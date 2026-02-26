import os, sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from PyQt5.QtGui import QPixmap, QDesktopServices
from qfluentwidgets import SubtitleLabel, CaptionLabel, FluentIcon, MessageBoxBase, TitleLabel
from src.core.translator import translator

class LicenseDialog(MessageBoxBase):
    """ 许可协议对话框 """
    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.titleLabel = TitleLabel(translator.get("about.license"), self)
        
        self.content_edit = QTextEdit(self)
        self.content_edit.setPlainText(content)
        self.content_edit.setReadOnly(True)
        self.content_edit.setFrameShape(QTextEdit.Shape.NoFrame)
        # 强制设置背景色和字体，防止样式冲突
        self.content_edit.setStyleSheet("""
            QTextEdit { 
                background-color: white; 
                font-size: 13px; 
                color: #333333; 
                border: 1px solid #e5e5e5;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        self.content_edit.setMinimumHeight(400)
        self.content_edit.setMinimumWidth(500)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.content_edit)

        self.yesButton.setText(translator.get("confirm"))
        self.cancelButton.hide()

        self.widget.setMinimumWidth(550)
        
        # 连接确定按钮
        self.yesButton.clicked.connect(self.accept)

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class AboutInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("aboutInterface")
        self.setStyleSheet("QWidget#aboutInterface { background-color: white; }")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(0)

        # 关于内容容器 (不使用 CardWidget 以匹配原图白底效果)
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)

        # Logo
        self.logo_label = QLabel(self)
        if os.path.exists("assets/PyStart.png"):
            pixmap = QPixmap("assets/PyStart.png").scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.logo_label)

        # Name
        self.name_label = SubtitleLabel("PyStart", self)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 10px;")
        self.content_layout.addWidget(self.name_label)

        # Version
        version = self.read_version()
        self.version_label = CaptionLabel(f"{translator.get('about.version')}: {version}", self)
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("color: #666666;")
        self.content_layout.addWidget(self.version_label)

        # Links
        self.links_layout = QVBoxLayout()
        self.links_layout.setSpacing(5)
        self.github_link = self.create_link_label(translator.get("about.open_source"), "https://github.com/PyStart/PyStart/", color="#0078d4")
        self.download_link = self.create_link_label(translator.get("about.download"), "https://github.com/PyStart/PyStart/releases", color="#0078d4")
        self.links_layout.addWidget(self.github_link)
        self.links_layout.addWidget(self.download_link)
        self.content_layout.addLayout(self.links_layout)

        # Description
        self.desc_label = CaptionLabel(translator.get("about.description"), self)
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("color: #666666; margin-top: 25px; line-height: 1.5;")
        self.content_layout.addWidget(self.desc_label)

        # License Note (HTML Label)
        self.license_note_label = QLabel(self)
        self.license_note_label.setAlignment(Qt.AlignCenter)
        self.license_note_label.setOpenExternalLinks(False)  # 设为 False 才能通过 linkActivated 手动处理
        self.license_note_label.linkActivated.connect(self.handle_link)
        self.license_note_label.setStyleSheet("margin-top: 20px;")
        self.update_license_note()
        self.content_layout.addWidget(self.license_note_label)

        self.layout.addWidget(self.content_widget, 0, Qt.AlignTop)
        
        # 弹簧将内容推向上方，将联系方式推向下方
        self.layout.addStretch(1)

        # Contact Info Section (Bottom Left)
        self.contact_container = QWidget(self)
        self.contact_layout = QVBoxLayout(self.contact_container)
        self.contact_layout.setContentsMargins(0, 0, 0, 0)
        self.contact_layout.setSpacing(8)

        self.contact_title = CaptionLabel(translator.get("about.contact"), self)
        self.contact_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #333333;")
        self.contact_layout.addWidget(self.contact_title)
        
        self.contacts_data = [
            ("about.wechat_qq", "1966477607"),
            ("about.qq_email", "1966477607@qq.com"),
            ("about.bilibili", "小白爱卖萌"),
            ("about.douyin_kuaishou", "正心电脑网络科技"),
            ("about.video_channel", "小小的郭子")
        ]
        
        self.contact_labels = []
        for key, value_text in self.contacts_data:
            l = CaptionLabel(f"{translator.get(key)}: {value_text}", self)
            l.setStyleSheet("color: #666666;")
            self.contact_layout.addWidget(l)
            self.contact_labels.append((l, key, value_text))

        self.hint_container = QWidget(self)
        self.hint_layout = QHBoxLayout(self.hint_container)
        self.hint_layout.setContentsMargins(0, 5, 0, 0)
        self.hint_layout.setSpacing(5)
        
        from qfluentwidgets import IconWidget
        self.hint_icon = IconWidget(FluentIcon.INFO, self)
        self.hint_icon.setFixedSize(14, 14)
        # 设置图标颜色为醒目的橘红色
        self.hint_icon.setStyleSheet("padding: 0px; border: none; background: transparent;")
        self.hint_icon.setProperty("qss_color", "#d83b01") 
        
        self.hint_label = CaptionLabel(translator.get("about.add_hint"), self)
        self.hint_label.setStyleSheet("""
            color: #d83b01; 
            font-weight: bold;
        """)
        
        self.hint_layout.addWidget(self.hint_icon)
        self.hint_layout.addWidget(self.hint_label)
        self.hint_layout.addStretch(1)
        
        self.contact_layout.addWidget(self.hint_container)
        
        self.layout.addWidget(self.contact_container, 0, Qt.AlignLeft | Qt.AlignBottom)

        translator.languageChanged.connect(self.update_texts)

    def update_license_note(self):
        license_text = translator.get("about.license")
        here_text = translator.get("about.here")
        online_url = "https://github.com/PyStart/PyStart/blob/main/LICENSE"
        
        note_html = translator.get("about.license_note").format(
            license_text, 
            online_url, 
            here_text
        )
        self.license_note_label.setText(note_html)

    def handle_link(self, link):
        if link == "#license":
            self.show_license()
        elif link.startswith("http"):
            QDesktopServices.openUrl(QUrl(link))

    def read_version(self):
        try:
            version_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "VERSION")
            if os.path.exists(version_path):
                with open(version_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            return "1.0.0"
        except:
            return "1.0.0"

    def create_link_label(self, text, url, color="#0078d4"):
        label = QLabel(f'<a href="{url}" style="color: {color}; text-decoration: none;">{text}</a>', self)
        label.setOpenExternalLinks(True)
        label.setAlignment(Qt.AlignCenter)
        return label

    def show_license(self):
        # 查找 LICENSE 文件的可能路径
        possible_paths = []
        
        # 1. 打包环境 (Nuitka)
        # 优先检查 exe 同级目录
        if getattr(sys, 'frozen', False) or 'nuitka' in sys.modules:
             possible_paths.append(os.path.join(os.path.dirname(sys.executable), "LICENSE"))
        
        # 2. 源码环境，相对于当前文件
        # src/ui/about.py -> src/LICENSE
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        possible_paths.append(os.path.join(src_dir, "LICENSE"))
        
        # 3. 源码环境，项目根目录
        root_dir = os.path.dirname(src_dir)
        possible_paths.append(os.path.join(root_dir, "LICENSE"))

        license_path = None
        for path in possible_paths:
            if os.path.exists(path):
                license_path = path
                break
        
        if license_path:
            try:
                with open(license_path, "r", encoding="utf-8") as f:
                    content = f.read()
                w = LicenseDialog(content, self.window())
                w.exec_()
            except Exception as e:
                print(f"Error reading license: {e}")
                QDesktopServices.openUrl(QUrl.fromLocalFile(license_path))
        else:
             print("License file not found")
             # 如果找不到文件，尝试打开在线链接作为后备
             QDesktopServices.openUrl(QUrl("https://github.com/PyStart/PyStart/blob/main/LICENSE"))

    def update_texts(self):
        self.version_label.setText(f"{translator.get('about.version')}: {self.read_version()}")
        self.desc_label.setText(translator.get("about.description"))
        self.update_license_note()
        self.contact_title.setText(translator.get("about.contact"))
        for label, key, value in self.contact_labels:
            label.setText(f"{translator.get(key)}: {value}")
        self.hint_label.setText(translator.get("about.add_hint"))
        self.github_link.setText(f'<a href="https://github.com/PyStart/PyStart/" style="color: #0078d4; text-decoration: none;">{translator.get("about.open_source")}</a>')
        self.download_link.setText(f'<a href="https://github.com/PyStart/PyStart/releases" style="color: #0078d4; text-decoration: none;">{translator.get("about.download")}</a>')
