import os
import sys
import platform
from PyQt6.QtGui import QFontDatabase, QFont

def load_fonts():
    """
    加载系统字体和项目 assets/fonts 目录下的字体，
    并返回一个推荐的字体族列表，用于 font.setFamilies()。
    """
    loaded_families = []
    
    # 0. 尝试加载项目内置字体 (如果有)
    # 获取项目根目录
    base_dir = None
    try:
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
            else:
                # Nuitka standalone or other freezers
                # 尝试多个可能的路径
                exe_dir = os.path.dirname(sys.executable)
                candidates = [
                    exe_dir,
                    os.path.join(exe_dir, '..'),
                    os.path.join(exe_dir, 'src'),
                    os.path.join(exe_dir, '..', 'src'),
                    '/opt/PyStart'  # [CRITICAL] 显式添加 RPM 安装路径，防止路径探测失败
                ]
                for path in candidates:
                    if os.path.exists(os.path.join(path, 'assets')):
                        base_dir = path
                        print(f"DEBUG: Found assets dir at: {base_dir}")
                        break
                if not base_dir:
                     base_dir = exe_dir
                     print(f"DEBUG: Assets dir not found, defaulting to: {base_dir}")
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
        # [RPM FIX] 针对 AnolisOS RPM 安装的硬编码路径检查
        # 无论之前探测结果如何，如果有这个目录，必须加载
        rpm_font_path = "/opt/PyStart/assets/fonts"
        if os.path.exists(rpm_font_path):
            print(f"DEBUG: Found RPM font path: {rpm_font_path}")
            try:
                for filename in os.listdir(rpm_font_path):
                    if filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        full_path = os.path.join(rpm_font_path, filename)
                        font_id = QFontDatabase.addApplicationFont(full_path)
                        if font_id != -1:
                            families = QFontDatabase.applicationFontFamilies(font_id)
                            for f in families:
                                if f not in loaded_families:
                                    loaded_families.append(f)
                                    print(f"Loaded RPM font: {filename} -> {f}")
                        else:
                            print(f"ERROR: Failed to load font: {full_path}")
            except Exception as e:
                print(f"ERROR accessing RPM font path: {e}")
            
        if base_dir:
            font_dir = os.path.join(base_dir, 'assets', 'fonts')
            if os.path.exists(font_dir):
                for filename in os.listdir(font_dir):
                    if filename.lower().endswith(('.ttf', '.otf', '.woff', '.woff2')):
                        font_path = os.path.join(font_dir, filename)
                        font_id = QFontDatabase.addApplicationFont(font_path)
                        if font_id != -1:
                            families = QFontDatabase.applicationFontFamilies(font_id)
                            for f in families:
                                if f not in loaded_families:
                                    loaded_families.append(f)
                                    print(f"Loaded bundled font: {filename} -> {f}")
    except Exception as e:
        print(f"Error loading bundled fonts: {e}")

    # 1. 针对特定 Linux 发行版 (如 AnolisOS/RHEL/CentOS) 的已知字体路径
    # 如果系统字体配置有问题，Qt 可能无法自动发现这些字体，手动加载它们
    linux_font_paths = [
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansArmenian.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansDevanagari-Regular.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansTamil-Regular.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansThai.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSans.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansHebrew-Regular.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidSansHebrew-Bold.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidKufi-Regular.ttf",
        "/usr/share/fonts/google-droid-sans-fonts/DroidKufi-Bold.ttf",
        "/usr/share/fonts/lohit-bengali/Lohit-Bengali.ttf", 
        "/usr/share/fonts/smc/Meera.ttf"
    ]
    
    if platform.system() == "Linux":
        for path in linux_font_paths:
            if os.path.exists(path):
                # 显式添加应用字体
                font_id = QFontDatabase.addApplicationFont(path)
                if font_id != -1:
                    families = QFontDatabase.applicationFontFamilies(font_id)
                    # 将这些手动加载的系统字体也加入推荐列表
                    for f in families:
                        if f not in loaded_families:
                            loaded_families.append(f)
                            print(f"Loaded system font manually: {path} -> {f}")
    
    # 2. 构建最终的推荐字体列表
    # 优先级：加载的字体 > Noto Sans > Lohit > Droid > 系统默认
    
    # 基础列表
    recommended_families = []
    
    # 首先加入刚才加载的字体 (去重)
    seen = set()
    for f in loaded_families:
        if f not in seen:
            recommended_families.append(f)
            seen.add(f)
            
    # 添加标准回退列表
    fallback_list = [
        "Noto Sans", 
        "Noto Sans Arabic",
        "Noto Sans Armenian", 
        "Noto Sans Bengali", 
        "Noto Sans Devanagari", 
        "Noto Sans Hebrew",
        "Noto Sans Tamil",
        "Lohit Bengali", 
        "Lohit Devanagari", 
        "Lohit Tamil", 
        "Gargi", 
        "Mukti Narrow", 
        "Nakula", 
        "Sahadeva", 
        "Samyak Devanagari",
        "Droid Sans", 
        "Droid Sans Thai",
        "Droid Sans Fallback", 
        "Droid Sans Devanagari", 
        "Droid Sans Tamil", 
        "Droid Sans Armenian",
        "Droid Sans Hebrew",
        "Droid Arabic Kufi",
        "DejaVu Sans", 
        "Liberation Sans", 
        "FreeSans", 
        "Unifont",
        "Arial Unicode MS", 
        "Microsoft YaHei", 
        "Segoe UI", 
        "sans-serif"
    ]
    
    for f in fallback_list:
        if f not in seen:
            recommended_families.append(f)
            seen.add(f)
            
    return recommended_families

def apply_fonts(app_or_widget):
    """
    将推荐的字体列表应用到 QApplication 或 QWidget
    """
    families = load_fonts()
    font = app_or_widget.font()
    font.setFamilies(families)
    app_or_widget.setFont(font)
    # print(f"Applied font families: {families[:5]}...") # Debug log
