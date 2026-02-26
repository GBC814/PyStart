import sys, os, time, json

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from qfluentwidgets import qconfig, setTheme, Theme

from src.config import BASE_DIR, CONFIG_FILE, config as global_config

def get_base_dir():
    """获取程序基础目录"""
    return BASE_DIR

def check_first_run():
    """检查是否是首次运行（没有配置文件或配置文件中没有语言设置）"""
    config_file = CONFIG_FILE
    
    # 强制调试：如果命令行参数包含 --force-selector，则返回 True
    if "--force-selector" in sys.argv:
        return True
        
    if not os.path.exists(config_file):
        print(f"DEBUG: Config file not found at {config_file}, showing selector.")
        return True
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # 如果没有语言设置或语言设置为空，认为是首次运行
        is_first = 'language' not in config or not config.get('language')
        if is_first:
            print(f"DEBUG: 'language' not in config or empty, showing selector.")
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
    from PyQt5.QtWidgets import QDialog
    
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
    result = dialog.exec_()
    
    # 获取结果后清理引用，但允许它存活到 dialog.exec 结束
    if result == QDialog.Accepted:
        return selected_language[0]
    return None

def main():
    start_time = time.time()
    
    # [彻底解决任务栏图标] 设置 Windows 7/10 任务栏 AppUserModelID
    # 必须在创建任何窗口之前调用，最好在启动最前端
    if sys.platform == 'win32':
        try:
            import ctypes
            # 使用更规范的 AppID，确保与打包后的 exe 内部 ID 一致
            myappid = u'PyStart.Editor.Win7.Portable'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            
            # 强制刷新当前窗口的 AppID (针对部分 Win7 环境)
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.shell32.SHGetPropertyStoreForWindow(hwnd, None)
        except Exception as e:
            print(f"DEBUG: Failed to set AppUserModelID: {e}")

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
    # 在 PyQt5 中设置高 DPI 缩放
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    app = QApplication(sys.argv)
    
    # [彻底解决任务栏图标] 设置应用程序全局图标
    from PyQt5.QtGui import QIcon
    icon_path = os.path.join(BASE_DIR, 'assets', 'PyStart.ico')
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    elif hasattr(sys, 'frozen'):
        # 如果是打包环境但找不到外部图标，尝试从 exe 资源加载
        app.setWindowIcon(QIcon(sys.executable))
    
    # 3. 检查是否是首次运行
    if check_first_run():
        selected_language = show_language_selector(app)
        if selected_language:
            print(f"DEBUG: Language selected: {selected_language}, saving to config.")
            save_language(selected_language)
            os.environ['PYSTART_LANGUAGE'] = selected_language
        else:
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
    
    # [关键修复] 在窗口显示之前，再次强制设置一次全局图标和窗口图标
    # 有时 FluentWindow 的初始化会重置窗口图标
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))
    
    print(f"Startup total: {time.time() - start_time:.4f}s")
    
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
