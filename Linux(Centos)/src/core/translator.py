import os, json
from PyQt6.QtCore import QObject, pyqtSignal, QTranslator, QLibraryInfo, QLocale
from src.config import config

class JSONTranslator(QTranslator):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translations = {}

    def load_data(self, data):
        self.translations = data

    def translate(self, context, source_text, disambiguation=None, n=-1):
        # 移除加速键符号 (&)
        clean_text = source_text.replace('&', '')
        
        # 处理快捷键修饰符
        if context == "QShortcut":
            if clean_text in ["Ctrl", "Alt", "Shift", "Meta", "+"]:
                # 如果我们没有特定翻译，返回原值，确保不为空
                # 这样 Qt 就会显示 "Ctrl" 而不是忽略它
                return clean_text
        
        # 映射标准 Qt 文本到我们的 JSON 键
        if clean_text == "Select All":
            val = self.translations.get("Select all")
            if val: return val
            
        # 尝试直接匹配
        if clean_text in self.translations:
            return self.translations[clean_text]
            
        return ""

class Translator(QObject):
    languageChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        from src.config import BASE_DIR
        self.locale_dir = os.path.join(BASE_DIR, 'locale')
        if not os.path.exists(self.locale_dir):
            self.locale_dir = os.path.join(BASE_DIR, 'src', 'locale')
            
        # 优先从环境变量读取语言设置（首次运行时由语言选择界面设置）
        import os as os_module
        self.current_locale = os_module.environ.get('PYSTART_LANGUAGE') or config.get('language', 'en_US')
        print(f"DEBUG: Translator initialized. current_locale={self.current_locale}, env={os_module.environ.get('PYSTART_LANGUAGE')}")
        self.translations = {}
        # RTL 语言列表
        self.rtl_languages = ['ar_AR', 'fa_IR', 'he_IL', 'ur_PK']
        
        self.q_translator = JSONTranslator(self)
        self.qt_base_translator = QTranslator(self) # 用于加载 Qt 原生翻译 (如 Ctrl -> Ctrl)
        self._loaded = False

    def _ensure_loaded(self):
        if not self._loaded:
            self.load_translations()
            self._loaded = True

    def load_translations(self):
        # 加载 Qt 原生翻译
        qt_locale = QLocale(self.current_locale)
        path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        
        print(f"DEBUG: Loading translations for {self.current_locale}")
        print(f"DEBUG: Locale dir: {self.locale_dir}")
        
        if self.qt_base_translator.load(qt_locale, "qtbase", "_", path):
            pass
        elif self.qt_base_translator.load(qt_locale, "qt", "_", path):
            pass
            
        # 优化：只有在非英语环境下才加载英语作为后备，或者直接加载目标语言
        self.translations = {}
        
        # 如果是英语，直接加载即可
        if self.current_locale == 'en_US':
            fallback_path = os.path.join(self.locale_dir, 'en_US.json')
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
        else:
            # 如果是非英语，先尝试加载目标语言
            locale_path = os.path.join(self.locale_dir, f'{self.current_locale}.json')
            print(f"DEBUG: Attempting to load locale file: {locale_path}")
            if os.path.exists(locale_path):
                try:
                    with open(locale_path, 'r', encoding='utf-8') as f:
                        self.translations = json.load(f)
                    print(f"DEBUG: Successfully loaded {len(self.translations)} translations from {locale_path}")
                except Exception as e:
                    print(f"DEBUG: Error loading locale {self.current_locale}: {e}")
            else:
                print(f"DEBUG: Locale file NOT FOUND: {locale_path}")
            
            # 如果目标语言加载失败或为空，才加载英语作为后备
            if not self.translations:
                fallback_path = os.path.join(self.locale_dir, 'en_US.json')
                if os.path.exists(fallback_path):
                    with open(fallback_path, 'r', encoding='utf-8') as f:
                        self.translations = json.load(f)
        
        # 更新 QTranslator 数据
        self.q_translator.load_data(self.translations)

    def install(self, app):
        """安装 QTranslator 到应用程序"""
        self._ensure_loaded()
        app.installTranslator(self.qt_base_translator) # 先安装 Qt 原生翻译
        app.installTranslator(self.q_translator)       # 再安装我们的自定义翻译 (覆盖)

    def set_language(self, language_code):
        if self.current_locale != language_code:
            self.current_locale = language_code
            self.load_translations()
            self.languageChanged.emit()
        else:
            # 即使语言代码相同也强制重新加载/更新
            self.load_translations()
            self.languageChanged.emit()

    def get(self, key, default=None):
        self._ensure_loaded()
        return self.translations.get(key, default if default is not None else key)

    def is_rtl(self) -> bool:
        return self.current_locale in self.rtl_languages

# 全局实例
translator = Translator()
