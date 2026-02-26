import os, json, sys

# 获取程序运行目录
if hasattr(sys, 'frozen'):
    # sys.executable 指向 .dist 目录下的 exe
    BASE_DIR = os.path.dirname(sys.executable)
    # 对于 standalone 模式，数据文件就在 exe 同级目录或其子目录
    BUNDLE_DIR = BASE_DIR
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = BASE_DIR

def get_config_path():
    """确定配置文件路径。"""
    local_config = os.path.join(BASE_DIR, 'config.json')
    
    # 如果本地配置文件存在，直接使用
    if os.path.exists(local_config):
        return local_config
        
    # 尝试写入 BASE_DIR 以检查是否可写
    # 如果可写，我们使用本地配置以在解压版本中保持默认的便携性。
    try:
        test_file = os.path.join(BASE_DIR, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return local_config
    except (PermissionError, OSError):
        pass
        
    # 对于安装版本，回退到 APPDATA
    app_data = os.getenv('APPDATA')
    if not app_data:
        app_data = os.path.expanduser('~')
    
    user_dir = os.path.join(app_data, 'PyStart')
    if not os.path.exists(user_dir):
        try:
            os.makedirs(user_dir)
        except:
            # 如果无法创建用户目录，回退到本地并尽力而为
            return local_config
            
    return os.path.join(user_dir, 'config.json')

CONFIG_FILE = get_config_path()
# 默认集成 Python 解释器版本
# 优先从运行目录找，如果找不到，则尝试使用系统默认的 python
EMBEDDED_PYTHON_DIR = os.path.join(BUNDLE_DIR, 'runtime', 'python-3.8.5')
EMBEDDED_PYTHON = os.path.join(EMBEDDED_PYTHON_DIR, 'python.exe')
DEFAULT_RUNTIME = 'python.exe'

class ConfigManager:
    def __init__(self):
        self.config = self._load_config()

    def reload(self):
        """从磁盘重新加载配置"""
        self.config = self._load_config()

    def _load_config(self):
        data = None
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        if data is None:
            data = {}

        # 确保有默认值
        if 'font_size' not in data:
            data['font_size'] = 12
        if 'font_family' not in data:
            data['font_family'] = 'Consolas'
        if 'show_indent_guides' not in data:
            data['show_indent_guides'] = True
        if 'theme_color' not in data:
            data['theme_color'] = '#ffffff'
        if 'theme_mode' not in data:
            data['theme_mode'] = 'Light'
        if 'background_image' not in data:
            data['background_image'] = ''
        if 'background_opacity' not in data:
            data['background_opacity'] = 0.3
            
        # 解释器路径检查将在程序启动后通过 check_interpreter() 延迟执行
        return data

    def check_interpreter(self):
        """检测并更新解释器配置，使用缓存避免频繁 IO"""
        if hasattr(self, '_interpreter_checked'):
            return
            
        current_interpreter = self.config.get('interpreter')
        changed = False
        
        # 1. 如果检测到内置的 Python 3.14.2
        if os.path.exists(EMBEDDED_PYTHON):
            if not current_interpreter or 'runtime' in current_interpreter:
                if current_interpreter != EMBEDDED_PYTHON:
                    self.config['interpreter'] = EMBEDDED_PYTHON
                    changed = True
        
        # 2. 如果配置中没有解释器
        if not self.config.get('interpreter') or not os.path.exists(str(self.config.get('interpreter'))):
            self.config['interpreter'] = self._detect_default_interpreter()
            changed = True
            
        if changed:
            self.save()
            
        self._interpreter_checked = True

    def _detect_default_interpreter(self):
        """探测默认解释器"""
        # 优先检查内置的 Python 3.14.2
        if os.path.exists(EMBEDDED_PYTHON):
            return EMBEDDED_PYTHON
            
        # 检查相对于当前执行文件的 runtime 目录
        portable_runtime = os.path.join(BUNDLE_DIR, 'runtime', 'python-3.14.2', 'python.exe')
        if os.path.exists(portable_runtime):
            return portable_runtime

        # 检查通用 runtime/python.exe
        if os.path.exists(DEFAULT_RUNTIME):
            return DEFAULT_RUNTIME
            
        # 最后退回到当前运行的解释器，避免使用 shutil.which 遍历 PATH
        return sys.executable

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

config = ConfigManager()
