import sys, os, time, json

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from qfluentwidgets import qconfig, setTheme, Theme

from src.config import BASE_DIR, CONFIG_FILE, config as global_config

def get_base_dir():
    """获取程序基础目录"""
    return BASE_DIR

def check_first_run():
    """检查是否是首次运行（没有配置文件或配置文件中没有语言设置）"""
    config_file = CONFIG_FILE
    
    # [IMPORTANT] 在 Linux 安装版模式下，如果 config.json 指向只读目录下的文件（这不应该发生，但防御性编程）
    # 我们认为它是“默认配置”，也应该视为首次运行
    if not os.access(os.path.dirname(config_file), os.W_OK):
        print(f"DEBUG: Config dir not writable ({config_file}), assuming first run.")
        return True

    # 强制调试：如果命令行参数包含 --force-selector，则返回 True
    if "--force-selector" in sys.argv:
        return True
        
    print(f"DEBUG: Checking config file at: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"DEBUG: Config file not found at {config_file}, showing selector.")
        return True
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 打印当前配置内容摘要
        lang = config.get('language', '')
        print(f"DEBUG: Current config language: '{lang}'")

        # 如果读取的 config.json 来自只读的 /opt/PyStart，且内容为空，必须视为首次运行
        if config_file.startswith('/opt/PyStart') and not lang:
             print("DEBUG: Reading empty config from /opt/PyStart, treating as first run.")
             return True
            
        # 如果没有语言设置或语言设置为空，认为是首次运行
        # [CRITICAL FIX] 强制检查空字符串
        if not lang or str(lang).strip() == "":
            print(f"DEBUG: 'language' is empty or invalid, showing selector.")
            return True

        # [VERSION CONTROL]
        # 强制修正：如果版本号不匹配，认为是首次运行（或者需要重置）
        from src.config import APP_VERSION
        saved_version = config.get('app_version', '0.0.0')
        if saved_version != APP_VERSION:
            print(f"DEBUG: Version mismatch ({saved_version} != {APP_VERSION}), forcing setup.")
            return True
            
        is_first = 'language' not in config
        if is_first:
            print(f"DEBUG: 'language' key missing, showing selector.")
        return is_first
    except Exception as e:
        print(f"DEBUG: Error reading config: {e}, showing selector.")
        return True

def save_language(language_code):
    """保存语言设置到配置文件"""
    config_file = CONFIG_FILE
    config_data = {}
    
    # 读取现有配置
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except:
            pass
    
    # 设置语言
    config_data['language'] = language_code
    
    # [VERSION CONTROL]
    from src.config import APP_VERSION
    config_data['app_version'] = APP_VERSION
    
    # 保存配置
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        # 更新全局配置对象
        global_config.reload()
    except Exception as e:
        print(f"Error saving language config: {e}")

def show_language_selector(app):
    """直接显示语言选择对话框"""
    from src.ui.language_selector import LanguageSelectorDialog
    
    # 将 dialog 绑定到 app 实例上，防止在 show_language_selector 结束时
    # 局部变量销毁导致 qfluentwidgets 的全局状态 (qconfig) 出现异常
    app._language_dialog = LanguageSelectorDialog()
    dialog = app._language_dialog
    selected_language = [None]
    
    def on_selected(lang):
        selected_language[0] = lang
        dialog.accept()
        
    dialog.languageSelected.connect(on_selected)
    
    # 如果用户关闭窗口或按取消
    result = dialog.exec()
    
    # 获取结果后清理引用，但允许它存活到 dialog.exec 结束
    if result == LanguageSelectorDialog.DialogCode.Accepted:
        return selected_language[0]
    return None

def main():
    # 0. 启动计时
    start_time = time.time()
    
    # [CRITICAL DIAGNOSTICS]
    try:
        from src.config import BASE_DIR, CONFIG_FILE
        print(f"DEBUG: sys.executable: {sys.executable}")
        print(f"DEBUG: sys.frozen: {getattr(sys, 'frozen', False)}")
        print(f"DEBUG: BASE_DIR: {BASE_DIR}")
        print(f"DEBUG: CONFIG_FILE: {CONFIG_FILE}")
        
        assets_dir = os.path.join(BASE_DIR, 'assets')
        print(f"DEBUG: assets path: {assets_dir}")
        print(f"DEBUG: assets exists? {os.path.exists(assets_dir)}")
        if os.path.exists(assets_dir):
            print(f"DEBUG: assets content: {os.listdir(assets_dir)}")
            
        fonts_dir = os.path.join(assets_dir, 'fonts')
        print(f"DEBUG: fonts path: {fonts_dir}")
        print(f"DEBUG: fonts exists? {os.path.exists(fonts_dir)}")
        if os.path.exists(fonts_dir):
            print(f"DEBUG: fonts content: {os.listdir(fonts_dir)}")
            
        # New diagnostics
        import pwd
        print(f"DEBUG: Current User: {pwd.getpwuid(os.getuid()).pw_name} (uid={os.getuid()})")
        print(f"DEBUG: Home Dir: {os.path.expanduser('~')}")
        print(f"DEBUG: Config File being checked: {os.path.join(os.path.expanduser('~'), '.config/PyStart/config.json')}")
    except Exception as e:
        print(f"ERROR during diagnostics: {e}")

    # 1. 性能优化环境变量设置
    os.environ["QT_QUICK_BACKEND"] = "software"
    os.environ["QSG_RHI_BACKEND"] = "software"
    os.environ["QT_RHI_BACKEND"] = "software"
    os.environ["QT_OPENGL"] = "software"
    os.environ["QT_NO_OPENGL_CHECK"] = "1"
    
    if not hasattr(sys, 'frozen'):
        os.environ["QT_PLUGIN_PATH"] = ""
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""
    os.environ["QT_DEBUG_PLUGINS"] = "0"
    
    os.environ["QT_USE_DIRECTWRITE"] = "0"
    os.environ["QT_FONTCONFIG_PATH"] = ""
    
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    os.environ["QT_SCALE_FACTOR"] = "1"
    
    os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.window=false;qt.widgets.styling=false"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # 2. 初始化 QApplication
    # 必须在创建前设置
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    
    # 设置全局字体回退，解决部分语言显示乱码问题
    from src.utils.font_manager import apply_fonts
    apply_fonts(app)
    
    # 3. 检查是否是首次运行
    if check_first_run():
        selected_language = show_language_selector(app)
        if selected_language:
            print(f"DEBUG: Language selected: {selected_language}, saving to config.")
            save_language(selected_language)
            os.environ['PYSTART_LANGUAGE'] = selected_language
        else:
            # 如果用户在语言选择界面点击关闭或取消，应该退出程序，而不是进入主界面
            print("DEBUG: Language selector cancelled, exiting.")
            sys.exit(0)
    
    print(f"App initialized: {time.time() - start_time:.4f}s")
    
    # 4. 加载主界面
    from src.core.translator import translator
    
    # 再次确认语言设置（如果是刚刚从语言选择器设置的，确保 translator 同步更新）
    current_lang = os.environ.get('PYSTART_LANGUAGE')
    if current_lang and current_lang != translator.current_locale:
        print(f"DEBUG: Updating translator locale from {translator.current_locale} to {current_lang}")
        translator.set_language(current_lang)
        
    translator.install(app)
    
    # 在创建主窗口前应用主题，确保 qconfig 状态正确
    from src.config import config
    theme_mode = config.get('theme_mode', 'Light')
    setTheme(Theme.DARK if theme_mode == 'Dark' else Theme.LIGHT)
    
    from src.ui.main_window import MainWindow
    window = MainWindow()
    
    # [CRITICAL FIX] Ensure fonts are applied to the main window
    # This fixes the issue where Hebrew/Hindi characters are displayed as squares
    try:
        from src.utils.font_manager import apply_fonts
        apply_fonts(window)
    except Exception as e:
        print(f"Error applying fonts to window: {e}")
    
    print(f"Startup total: {time.time() - start_time:.4f}s")
    
    window.showMaximized()
    sys.exit(app.exec())

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
