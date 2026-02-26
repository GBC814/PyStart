import os, sys, json
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsDropShadowEffect, QApplication
from PyQt6.QtGui import QIcon, QColor
from qfluentwidgets import PrimaryPushButton, SubtitleLabel, BodyLabel, ComboBox


class LanguageSelectorDialog(QDialog):
    """语言选择对话框 - 下拉菜单样式"""
    languageSelected = pyqtSignal(str)

    # 语言代码到显示名称的映射 (英文名称, 本地名称)
    LANGUAGE_NAMES = {
        "ar_AR": ("Arabic","العربية"),
        "be_BY": ("Belarusian", "Беларуская"),
        "bg_BG": ("Bulgarian", "Български"),
        "bn_BD": ("Bengali", "বাংলা"),
        "ca_ES": ("Catalan", "Català"),
        "cs_CZ": ("Czech", "Čeština"),
        "da_DK": ("Danish", "Dansk"),
        "de_DE": ("German", "Deutsch"),
        "el_GR": ("Greek", "Ελληνικά"),
        "en_GB": ("English (UK)", "English"),
        "en_US": ("English (US)", "English"),
        "es_ES": ("Spanish", "Español"),
        "et_EE": ("Estonian", "Eesti"),
        "eu_ES": ("Basque", "Euskara"),
        "fa_IR": ("Persian", "فارسی"),
        "fil_PH": ("Filipino", "Filipino"),
        "fi_FI": ("Finnish", "Suomi"),
        "fr_FR": ("French", "Français"),
        "he_IL": ("Hebrew", "עברית"),
        "hi_IN": ("Hindi", "हिन्दी"),
        "hr_HR": ("Croatian", "Hrvatski"),
        "hu_HU": ("Hungarian", "Magyar"),
        "hy_AM": ("Armenian", "Հայերեն"),
        "id_ID": ("Indonesian", "Bahasa Indonesia"),
        "is_IS": ("Icelandic", "Íslenska"),
        "it_IT": ("Italian", "Italiano"),
        "ja_JP": ("Japanese", "日本語"),
        "ko_KR": ("Korean", "한국어"),
        "lt_LT": ("Lithuanian", "Lietuvių"),
        "lv_LV": ("Latvian", "Latviešu"),
        "mn_MN": ("Mongolian", "Монгол"),
        "ms_MY": ("Malay", "Bahasa Melayu"),
        "nb_NO": ("Norwegian Bokmål", "Norsk Bokmål"),
        "nl_NL": ("Dutch", "Nederlands"),
        "nn_NO": ("Norwegian Nynorsk", "Norsk Nynorsk"),
        "pl_PL": ("Polish", "Polski"),
        "pt_BR": ("Portuguese (Brazil)", "Português"),
        "pt_PT": ("Portuguese", "Português"),
        "ro_RO": ("Romanian", "Română"),
        "ru_RU": ("Russian", "Русский"),
        "sk_SK": ("Slovak", "Slovenčina"),
        "sl_SI": ("Slovenian", "Slovenščina"),
        "sq_AL": ("Albanian", "Shqip"),
        "sr_RS": ("Serbian", "Српски"),
        "sv_SE": ("Swedish", "Svenska"),
        "sw_KE": ("Swahili", "Kiswahili"),
        "ta_IN": ("Tamil", "தமிழ்"),
        "th_TH": ("Thai", "ไทย"),
        "tr_TR": ("Turkish", "Türkçe"),
        "uk_UA": ("Ukrainian", "Українська"),
        "vi_VN": ("Vietnamese", "Tiếng Việt"),
        "zh_CN": ("Chinese Simplified", "简体中文"),
        "zh_Hans": ("zh-Hans", "简体中文"),
        "zh_HK": ("Chinese Hong Kong", "繁體中文"),
        "zh_TW": ("Chinese Traditional", "繁體中文"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_code = "en_US"
        self.language_codes = []
        self.init_ui()
        self.load_languages()

    def init_ui(self):
        self.setFixedSize(520, 360)

        # 设置窗口图标
        from src.config import BASE_DIR
        icon_path = os.path.join(BASE_DIR, 'assets', 'PyStart.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 无边框窗口，用于实现圆角
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 窗口居中显示
        self.center_window()

        # 创建主容器（用于绘制圆角和背景）
        self.container = QWidget(self)
        self.container.setGeometry(10, 10, 500, 340)
        self.container.setObjectName("container")

        # 主布局
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # 标题区域（两行显示）
        title_container = QWidget(self.container)
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 第一行：PyStart
        self.title_line1 = SubtitleLabel("PyStart", self.container)
        self.title_line1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_line1.setFixedHeight(35)
        font = self.title_line1.font()
        font.setPointSize(16)
        font.setBold(True)
        self.title_line1.setFont(font)
        self.title_line1.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(self.title_line1)
        
        # 第二行：副标题
        self.title_line2 = SubtitleLabel("一款专为入门打造的Python代码编辑器", self.container)
        self.title_line2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_line2.setFixedHeight(30)
        font2 = self.title_line2.font()
        font2.setPointSize(12)
        font2.setBold(True)
        self.title_line2.setFont(font2)
        self.title_line2.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(self.title_line2)
        
        main_layout.addWidget(title_container)

        main_layout.addSpacing(30)

        # 语言选择行
        language_layout = QHBoxLayout()
        language_layout.setSpacing(15)

        self.language_label = BodyLabel("Language:", self.container)
        self.language_label.setFixedWidth(100)
        font = self.language_label.font()
        font.setPointSize(12)
        self.language_label.setFont(font)
        self.language_label.setStyleSheet("color: #34495e;")
        language_layout.addWidget(self.language_label)

        self.language_combo = ComboBox(self.container)
        self.language_combo.setFixedHeight(35)
        self.language_combo.setMinimumWidth(280)
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        language_layout.addWidget(self.language_combo)

        main_layout.addLayout(language_layout)

        # 初始设置行（可选，预留）
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(15)

        self.settings_label = BodyLabel("Initial settings:", self.container)
        self.settings_label.setFixedWidth(100)
        font = self.settings_label.font()
        font.setPointSize(12)
        self.settings_label.setFont(font)
        self.settings_label.setStyleSheet("color: #34495e;")
        settings_layout.addWidget(self.settings_label)

        self.settings_combo = ComboBox(self.container)
        self.settings_combo.setFixedHeight(35)
        self.settings_combo.setMinimumWidth(280)
        self.settings_combo.addItem("Standard")
        settings_layout.addWidget(self.settings_combo)

        main_layout.addLayout(settings_layout)

        main_layout.addStretch(1)

        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        self.confirm_btn = PrimaryPushButton("OK/确定", self.container)
        self.confirm_btn.setFixedSize(120, 40)
        self.confirm_btn.clicked.connect(self.on_confirm)
        button_layout.addWidget(self.confirm_btn)

        main_layout.addLayout(button_layout)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        # 设置容器样式（圆角 + 彩色渐变背景）
        self.container.setStyleSheet("""
            QWidget#container {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #667eea,
                    stop: 0.3 #764ba2,
                    stop: 0.6 #f093fb,
                    stop: 1 #f5576c
                );
                border-radius: 16px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)

        # 更新文字颜色为白色以适应彩色背景
        self.title_line1.setStyleSheet("color: #ffffff;")
        self.title_line2.setStyleSheet("color: #ffffff;")
        self.language_label.setStyleSheet("color: #ffffff;")
        self.settings_label.setStyleSheet("color: #ffffff;")

    def load_languages(self):
        """加载所有可用语言到下拉菜单"""
        from src.config import BASE_DIR
        # 在打包环境下，locale 目录被映射到了根目录
        locale_dir = os.path.join(BASE_DIR, 'locale')

        if not os.path.exists(locale_dir):
            # 开发环境下可能在 src/locale
            locale_dir = os.path.join(BASE_DIR, 'src', 'locale')

        if not os.path.exists(locale_dir):
            print(f"Locale directory not found: {locale_dir}")
            # 至少添加默认语言
            self.add_language_item("zh_CN")
            return

        # 获取所有语言文件
        available_codes = []
        for filename in sorted(os.listdir(locale_dir)):
            if filename.endswith('.json'):
                code = filename[:-5]  # 移除.json后缀
                available_codes.append(code)

        # 按英文名称排序
        sorted_codes = sorted(available_codes, key=lambda c: self.LANGUAGE_NAMES.get(c, (c, c))[0])

        # 确保 en_US 在第一位
        if "en_US" in sorted_codes:
            sorted_codes.remove("en_US")
            sorted_codes.insert(0, "en_US")

        # 添加到下拉菜单
        for code in sorted_codes:
            self.add_language_item(code)
            self.language_codes.append(code)

        # 默认选择 zh_CN
        if "zh_CN" in self.language_codes:
            index = self.language_codes.index("zh_CN")
            self.language_combo.setCurrentIndex(index)
        
        # 初始化UI文本
        self.update_ui_texts()

    def add_language_item(self, code):
        """添加语言项到下拉菜单"""
        name, native_name = self.LANGUAGE_NAMES.get(code, (code, code))
        display_text = f"{native_name} ({name})"
        self.language_combo.addItem(display_text)

    def get_base_dir(self):
        """获取程序基础目录"""
        from src.config import BUNDLE_DIR
        return BUNDLE_DIR

    def on_language_changed(self, index):
        """语言选择改变"""
        if 0 <= index < len(self.language_codes):
            self.selected_code = self.language_codes[index]
            self.update_ui_texts()

    def load_translation(self, lang_code):
        """从JSON文件加载翻译"""
        from src.config import BASE_DIR
        locale_dir = os.path.join(BASE_DIR, 'locale')
        
        # 尝试开发环境路径
        if not os.path.exists(locale_dir):
            locale_dir = os.path.join(BASE_DIR, 'src', 'locale')
        
        file_path = os.path.join(locale_dir, f"{lang_code}.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # 如果加载失败，返回空字典
        return {}

    def update_ui_texts(self):
        """根据当前选择的语言更新UI文本"""
        trans = self.load_translation(self.selected_code)
        
        # 如果没有找到翻译，使用默认英文
        if not trans:
            trans = self.load_translation("en_US")
        
        # 更新标题（分成两行显示）
        full_title = trans.get("selector.title", "PyStart - A Python Code Editor for Beginners")
        # 尝试分割标题，如果包含 " - " 或 "-" 则分割
        if " - " in full_title:
            parts = full_title.split(" - ", 1)
            self.title_line1.setText(parts[0])
            self.title_line2.setText(parts[1])
        elif "-" in full_title and not full_title.startswith("PyStart-"):
            parts = full_title.split("-", 1)
            self.title_line1.setText(parts[0])
            self.title_line2.setText(parts[1])
        else:
            # 如果没有分隔符，第一行显示PyStart，第二行显示完整标题（去掉PyStart前缀）
            if full_title.startswith("PyStart"):
                self.title_line1.setText("PyStart")
                subtitle = full_title.replace("PyStart", "").replace("-", "").strip()
                self.title_line2.setText(subtitle)
            else:
                self.title_line1.setText("PyStart")
                self.title_line2.setText(full_title)
        
        # 更新标签文本
        self.language_label.setText(trans.get("selector.language", "Language:"))
        self.settings_label.setText(trans.get("selector.settings", "Initial settings:"))
        
        # 更新按钮文本
        self.confirm_btn.setText(trans.get("selector.ok", "OK"))
        
        # 更新下拉选项
        current_settings = self.settings_combo.currentText()
        self.settings_combo.clear()
        self.settings_combo.addItem(trans.get("selector.standard", "Standard"))

    def on_confirm(self):
        """确认选择"""
        self.languageSelected.emit(self.selected_code)
        self.accept()

    def get_selected_language(self):
        """获取选中的语言代码"""
        return self.selected_code

    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖动窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 用于拖动窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, '_drag_pos'):
            self.move(self.pos() + event.globalPosition().toPoint() - self._drag_pos)
            self._drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if hasattr(self, '_drag_pos'):
            delattr(self, '_drag_pos')
        event.accept()

    def keyPressEvent(self, event):
        """键盘按下事件 - ESC关闭窗口"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def center_window(self):
        """将窗口居中显示在屏幕中央"""
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                screen_geometry = screen.availableGeometry()
                x = (screen_geometry.width() - self.width()) // 2
                y = (screen_geometry.height() - self.height()) // 2
                self.move(x, y)


def show_language_selector():
    """显示语言选择对话框，返回选中的语言代码或None"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    dialog = LanguageSelectorDialog()

    if dialog.exec() == LanguageSelectorDialog.DialogCode.Accepted:
        return dialog.get_selected_language()
    return None


if __name__ == '__main__':
    selected = show_language_selector()
    if selected:
        print(selected, flush=True)
        sys.exit(0)
    else:
        sys.exit(1)
