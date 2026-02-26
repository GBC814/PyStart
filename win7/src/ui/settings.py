from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtCore import Qt
from qfluentwidgets import PrimaryPushButton, LineEdit, SubtitleLabel, CaptionLabel, CardWidget, ComboBox, SwitchButton
from src.config import config
from src.core.translator import translator
from src.ui.downloader_dialog import DownloaderDialog

class SettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        self.title = SubtitleLabel(translator.get("settings.title"), self)
        self.layout.addWidget(self.title)
        
        # 语言部分
        self.language_card = CardWidget(self)
        self.language_layout = QVBoxLayout(self.language_card)
        
        self.language_label = CaptionLabel(translator.get("settings.language"), self)
        self.language_layout.addWidget(self.language_label)
        
        self.language_combo = ComboBox(self)
        self.init_languages()
        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        
        self.language_layout.addWidget(self.language_combo)
        
        self.layout.addWidget(self.language_card)
        
        # 解释器部分
        self.interpreter_card = CardWidget(self)
        self.interpreter_layout = QVBoxLayout(self.interpreter_card)
        
        self.interpreter_label = CaptionLabel(translator.get("interpreter.path"), self)
        self.interpreter_layout.addWidget(self.interpreter_label)
        
        self.interpreter_row = QHBoxLayout()
        self.path_edit = LineEdit(self)
        self.path_edit.setText(config.get('interpreter', ''))
        self.path_edit.setReadOnly(True)
        
        self.btn_select = PrimaryPushButton(translator.get("interpreter.select"), self)
        self.btn_select.clicked.connect(self.select_interpreter)
        
        self.btn_download = PrimaryPushButton(translator.get("interpreter.download"), self)
        self.btn_download.clicked.connect(self.download_python)
        
        self.interpreter_row.addWidget(self.path_edit)
        self.interpreter_row.addWidget(self.btn_select)
        self.interpreter_row.addWidget(self.btn_download)
        
        self.interpreter_layout.addLayout(self.interpreter_row)
        
        self.layout.addWidget(self.interpreter_card)
        
        # 编辑器部分
        self.editor_card = CardWidget(self)
        self.editor_layout = QVBoxLayout(self.editor_card)
        
        self.editor_label = CaptionLabel(translator.get("settings.editor"), self)
        self.editor_layout.addWidget(self.editor_label)
        
        self.indent_guide_row = QHBoxLayout()
        self.indent_guide_label = CaptionLabel(translator.get("settings.show_indent_guides"), self)
        self.indent_guide_switch = SwitchButton(self)
        self.indent_guide_switch.setChecked(config.get('show_indent_guides', True))
        self.indent_guide_switch.setOnText(translator.get("settings.on"))
        self.indent_guide_switch.setOffText(translator.get("settings.off"))
        self.indent_guide_switch.checkedChanged.connect(self.on_indent_guide_changed)
        
        self.indent_guide_row.addWidget(self.indent_guide_label)
        self.indent_guide_row.addStretch(1)
        self.indent_guide_row.addWidget(self.indent_guide_switch)
        
        self.editor_layout.addLayout(self.indent_guide_row)
        self.layout.addWidget(self.editor_card)
        
        self.layout.addStretch(1)

        # 连接语言更改信号
        translator.languageChanged.connect(self.update_texts)
        
        # 初始化时设置对齐方式
        self.update_alignment()

    def update_texts(self):
        self.title.setText(translator.get("settings.title"))
        self.language_label.setText(translator.get("settings.language"))
        self.interpreter_label.setText(translator.get("interpreter.path"))
        self.btn_select.setText(translator.get("interpreter.select"))
        self.btn_download.setText(translator.get("interpreter.download"))
        self.editor_label.setText(translator.get("settings.editor"))
        self.indent_guide_label.setText(translator.get("settings.show_indent_guides"))
        self.indent_guide_switch.setOnText(translator.get("settings.on"))
        self.indent_guide_switch.setOffText(translator.get("settings.off"))
        self.update_alignment()

    def update_alignment(self):
        """
        根据当前语言方向更新所有标签的对齐方式
        """
        # 获取当前语言方向
        is_rtl = translator.is_rtl()
        
        # 设置对齐方式
        alignment = Qt.AlignRight if is_rtl else Qt.AlignLeft
        
        # 对所有标签应用对齐设置
        labels_info = [
            ('title', self.title, self.layout),
            ('language_label', self.language_label, self.language_layout),
            ('interpreter_label', self.interpreter_label, self.interpreter_layout),
            ('editor_label', self.editor_label, self.editor_layout),
            ('indent_guide_label', self.indent_guide_label, self.indent_guide_row)
        ]
        
        for name, label, parent_layout in labels_info:
            label.setAlignment(alignment)
            # 也在layout中设置widget的对齐
            if hasattr(parent_layout, 'setAlignment'):
                parent_layout.setAlignment(label, alignment)
            # 调试输出
            # print(f"设置 {name} 对齐为 {alignment} (RTL={is_rtl})")

    def on_indent_guide_changed(self, checked):
        config.set('show_indent_guides', checked)
        if self.window():
            # 假设 SettingsInterface 是嵌入在 MainWindow 中的
            if hasattr(self.window(), 'update_editor_settings'):
                self.window().update_editor_settings()

    def init_languages(self):
        # 映射代码到显示名称（包含全部 55 种支持的语言）
        self.languages = {
            "ar_AR": "العربية (Arabic)",
            "be_BY": "Беларуская (Belarusian)",
            "bg_BG": "Български (Bulgarian)",
            "bn_BD": "বাংলা (Bengali)",
            "ca_ES": "Català (Catalan)",
            "cs_CZ": "Čeština (Czech)",
            "da_DK": "Dansk (Danish)",
            "de_DE": "Deutsch (German)",
            "el_GR": "Ελληνικά (Greek)",
            "en_GB": "English (UK)",
            "en_US": "English (US)",
            "es_ES": "Español (Spanish)",
            "et_EE": "Eesti (Estonian)",
            "eu_ES": "Euskara (Basque)",
            "fa_IR": "فارسی (Persian)",
            "fi_FI": "Suomi (Finnish)",
            "fil_PH": "Filipino",
            "fr_FR": "Français (French)",
            "he_IL": "עברית (Hebrew)",
            "hi_IN": "हिन्दी (Hindi)",
            "hr_HR": "Hrvatski (Croatian)",
            "hu_HU": "Magyar (Hungarian)",
            "hy_AM": "Հայերեն (Armenian)",
            "id_ID": "Bahasa Indonesia (Indonesian)",
            "is_IS": "Íslenska (Icelandic)",
            "it_IT": "Italiano (Italian)",
            "ja_JP": "日本語 (Japanese)",
            "ko_KR": "한국어 (Korean)",
            "lt_LT": "Lietuvių (Lithuanian)",
            "lv_LV": "Latviešu (Latvian)",
            "mn_MN": "Монгол (Mongolian)",
            "ms_MY": "Bahasa Melayu (Malay)",
            "nb_NO": "Norsk Bokmål (Norwegian)",
            "nl_NL": "Nederlands (Dutch)",
            "nn_NO": "Norsk Nynorsk (Norwegian)",
            "pl_PL": "Polski (Polish)",
            "pt_BR": "Português (Brasil)",
            "pt_PT": "Português (Portugal)",
            "ro_RO": "Română (Romanian)",
            "ru_RU": "Русский (Russian)",
            "sk_SK": "Slovenčina (Slovak)",
            "sl_SI": "Slovenščina (Slovenian)",
            "sq_AL": "Shqip (Albanian)",
            "sr_RS": "Српски (Serbian)",
            "sv_SE": "Svenska (Swedish)",
            "sw_KE": "Kiswahili (Swahili)",
            "ta_IN": "தமிழ் (Tamil)",
            "th_TH": "ภาษาไทย (Thai)",
            "tr_TR": "Türkçe (Turkish)",
            "uk_UA": "Українська (Ukrainian)",
            "vi_VN": "Tiếng Việt (Vietnamese)",
            "zh_CN": "简体中文 (Chinese Simplified)",
            "zh_HK": "繁體中文 (香港)",
            "zh_TW": "繁體中文 (台灣)",
            "zh_Hans": "简体中文 (zh-Hans)"
        }
        
        current_code = config.get('language', 'en_US')
        
        # 按显示名称排序
        sorted_langs = sorted(self.languages.items(), key=lambda x: x[1])
        
        for code, name in sorted_langs:
            self.language_combo.addItem(name, code)
            if code == current_code:
                self.language_combo.setCurrentText(name)

    def on_language_changed(self, index):
        # 使用 currentData() 而不是 itemData(index)，因为在 Fluent ComboBox 中它似乎更可靠
        code = self.language_combo.currentData()
        
        if code:
            config.set('language', code)
            translator.set_language(code)
        else:
            # 后备方案：如果数据缺失，尝试匹配文本
            text = self.language_combo.itemText(index)
            for c, n in self.languages.items():
                if n == text:
                    config.set('language', c)
                    translator.set_language(c)
                    break

    def select_interpreter(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Python Interpreter", "", "Executable (*.exe)")
        if file_path:
            config.set('interpreter', file_path)
            self.path_edit.setText(file_path)
            
            # 立即重启 Shell 以应用新的解释器
            main_window = self.window()
            if hasattr(main_window, 'terminal'):
                main_window.terminal.restart_shell()

    def download_python(self):
        dialog = DownloaderDialog(self.window())
        if dialog.exec_():
            # Refresh path if changed
            new_path = config.get('interpreter', '')
            self.path_edit.setText(new_path)
            
            # 立即重启 Shell
            main_window = self.window()
            if hasattr(main_window, 'terminal'):
                main_window.terminal.restart_shell()
