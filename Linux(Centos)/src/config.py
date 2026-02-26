import os, json, sys, platform

# [VERSION CONTROL]
APP_VERSION = "1.0.0"

# 获取程序运行目录
if hasattr(sys, 'frozen'):
    # sys.executable 指向可执行文件所在目录
    BASE_DIR = os.path.dirname(sys.executable)
    
    # 兼容 Nuitka 打包后的资源路径
    # Nuitka 可能将资源放在 src 目录下，或者直接在根目录
    try:
        if not os.path.exists(os.path.join(BASE_DIR, 'assets')):
            if os.path.exists(os.path.join(BASE_DIR, 'src', 'assets')):
                BASE_DIR = os.path.join(BASE_DIR, 'src')
            elif os.path.exists(os.path.join(os.path.dirname(BASE_DIR), 'assets')):
                BASE_DIR = os.path.dirname(BASE_DIR)
    except Exception:
        # 防止在某些极端路径下 dirname 报错
        pass
    
    # 对于 standalone 模式，数据文件就在可执行文件同级目录或其子目录
    BUNDLE_DIR = BASE_DIR
    
    # [CRITICAL FIX]
    # 如果通过上述逻辑仍然找不到正确的 BASE_DIR，我们需要一个后备方案
    # 特别是在 RPM 安装环境下，assets 可能在 /opt/PyStart/assets，但可执行文件在 /opt/PyStart/bin/PyStart
    # 或者其他非常规布局
    if not os.path.exists(os.path.join(BASE_DIR, 'assets')):
        # 尝试回退到 sys.executable 的父目录（如果之前被修改了）
        exec_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(exec_dir, 'assets')):
            BASE_DIR = exec_dir
            BUNDLE_DIR = BASE_DIR
        elif os.path.exists(os.path.join(os.path.dirname(exec_dir), 'assets')):
            BASE_DIR = os.path.dirname(exec_dir)
            BUNDLE_DIR = BASE_DIR
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = BASE_DIR

# 检测操作系统
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Python 可执行文件名
PYTHON_EXECUTABLE_NAME = 'python.exe' if IS_WINDOWS else 'python3'
# Python 可执行文件路径（相对于 runtime/python-3.14.2/）
if IS_WINDOWS:
    PYTHON_EXECUTABLE = PYTHON_EXECUTABLE_NAME
else:
    PYTHON_EXECUTABLE = os.path.join('bin', PYTHON_EXECUTABLE_NAME)

# 获取用户数据目录（用于存储下载的 Python 解释器）
def get_user_runtime_dir():
    """获取用户目录，用于存储可写的数据"""
    if IS_WINDOWS:
        app_data = os.getenv('APPDATA')
        if not app_data:
            app_data = os.path.expanduser('~')
    else:
        # Linux 使用 XDG_DATA_HOME 或 ~/.local/share
        app_data = os.getenv('XDG_DATA_HOME')
        if not app_data:
            app_data = os.path.join(os.path.expanduser('~'), '.local', 'share')
    
    user_dir = os.path.join(app_data, 'PyStart')
    user_runtime_dir = os.path.join(user_dir, 'runtime')
    
    # 确保目录存在
    if not os.path.exists(user_runtime_dir):
        try:
            os.makedirs(user_runtime_dir, exist_ok=True)
        except:
            pass
    
    return user_runtime_dir

# 获取 runtime 目录的位置
def get_runtime_dir():
    """获取 runtime 目录，优先检查程序目录是否可写"""
    # 先尝试程序目录
    program_runtime = os.path.join(BUNDLE_DIR, 'runtime')
    
    # 检查程序目录是否可写
    try:
        test_file = os.path.join(program_runtime, '.write_test')
        if not os.path.exists(program_runtime):
            os.makedirs(program_runtime, exist_ok=True)
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        return program_runtime
    except (PermissionError, OSError):
        # 不可写，使用用户目录
        return get_user_runtime_dir()

def get_config_path():
    """确定配置文件路径，支持跨平台。"""
    local_config = os.path.join(BASE_DIR, 'config.json')
    
    # 检查 BASE_DIR 是否可写 (用于判断是否是便携版)
    is_writable = False
    try:
        test_file = os.path.join(BASE_DIR, '.write_test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        is_writable = True
    except (PermissionError, OSError):
        is_writable = False

    # 如果本地配置文件存在且目录可写，直接使用 (便携版模式)
    if os.path.exists(local_config) and is_writable:
        return local_config
        
    # 如果本地配置文件不存在但目录可写，也使用本地配置 (新解压的便携版)
    if is_writable:
        return local_config
        
    # 如果目录不可写 (如安装在 Program Files 或 /opt)，则强制使用用户目录
    # 即使 local_config 存在，我们也忽略它，因为它是只读的模板
    # 
    # [IMPORTANT] 在 Linux 安装版中，config.json 应该始终位于用户配置目录
    # 即 ~/.config/PyStart/config.json
    # 如果用户删除了这个文件，check_first_run() 应该返回 True
        
    # 对于安装版本，根据操作系统选择用户目录
    if IS_WINDOWS:
        app_data = os.getenv('APPDATA')
        if not app_data:
            app_data = os.path.expanduser('~')
    else:
        # Linux 使用 XDG_CONFIG_HOME 或 ~/.config
        app_data = os.getenv('XDG_CONFIG_HOME')
        if not app_data:
            app_data = os.path.join(os.path.expanduser('~'), '.config')
    
    # 兼容旧版本：如果 ~/.config/PyStart 不存在，但 ~/.local/share/PyStart/config.json 存在，则迁移
    # 这是为了解决用户反馈的"已经删除 .config 但仍不弹窗"的问题（虽然理论上配置在 .config）
    # 但我们也要检查其他可能的位置
    
    user_dir = os.path.join(app_data, 'PyStart')
    
    # 强制检查：如果在 XDG_DATA_HOME 下有遗留配置，优先使用吗？
    # 不，我们应该标准化到 .config。但如果用户删除了 .config 下的，
    # 我们要确保没有其他地方残留配置干扰首次运行判断。
    
    # 【修复】对于像 AnolisOS 这样默认可能没有 .config 目录的系统
    # 我们必须确保能够成功创建目录结构
    if not os.path.exists(user_dir):
        try:
            # os.makedirs 会自动创建中间目录（包括 .config），如果它们不存在
            os.makedirs(user_dir, exist_ok=True)
        except Exception as e:
            # 如果无法创建用户目录，回退到本地并尽力而为
            # 但这对于 RPM 安装版来说通常意味着无法保存配置
            print(f"Error creating config dir {user_dir}: {e}")
            # [CRITICAL FIX] 即使创建目录失败，也不要轻易返回 local_config，因为 local_config 可能是只读的
            # 如果 local_config 不可写，返回它会导致 save() 时崩溃
            # 这种情况下，我们应该尝试返回一个临时目录
            if not is_writable:
                import tempfile
                temp_dir = os.path.join(tempfile.gettempdir(), 'PyStart')
                try:
                    os.makedirs(temp_dir, exist_ok=True)
                    return os.path.join(temp_dir, 'config.json')
                except:
                    pass
            return local_config
            
    # [CRITICAL FIX] 确保我们生成的路径是有效的
    return os.path.join(user_dir, 'config.json')

CONFIG_FILE = get_config_path()

# 获取 runtime 目录
RUNTIME_DIR = get_runtime_dir()

# 默认集成 Python 解释器最新版本
# 优先从程序目录中找内置 Python
EMBEDDED_PYTHON_DIR = os.path.join(BUNDLE_DIR, 'runtime', 'python-3.14.2')
EMBEDDED_PYTHON = os.path.join(EMBEDDED_PYTHON_DIR, PYTHON_EXECUTABLE)

# 下载的 Python 存储在用户可写的目录中
USER_RUNTIME_DIR = get_user_runtime_dir()
DEFAULT_RUNTIME = os.path.join(RUNTIME_DIR, PYTHON_EXECUTABLE)

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
            # 根据平台选择合适的默认字体
            if IS_WINDOWS:
                data['font_family'] = 'Consolas'
            else:
                data['font_family'] = 'Monospace'
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
        """探测默认解释器，支持跨平台"""
        # 优先检查内置的 Python 3.14.2
        if os.path.exists(EMBEDDED_PYTHON):
            return EMBEDDED_PYTHON
            
        # 检查用户目录中的 Python 解释器
        if os.path.exists(USER_RUNTIME_DIR):
            for item in os.listdir(USER_RUNTIME_DIR):
                if item.startswith('python-') and os.path.isdir(os.path.join(USER_RUNTIME_DIR, item)):
                    candidate = os.path.join(USER_RUNTIME_DIR, item, PYTHON_EXECUTABLE)
                    if os.path.exists(candidate):
                        return candidate
            
        # 检查相对于当前执行文件的 runtime 目录
        portable_runtime = os.path.join(BUNDLE_DIR, 'runtime', 'python-3.14.2', PYTHON_EXECUTABLE)
        if os.path.exists(portable_runtime):
            return portable_runtime

        # 检查通用 runtime/python（或 python.exe）
        if os.path.exists(DEFAULT_RUNTIME):
            return DEFAULT_RUNTIME
            
        # 最后退回到当前运行的解释器
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
