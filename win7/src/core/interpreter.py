import os, subprocess
from src.config import config, EMBEDDED_PYTHON

class InterpreterManager:
    @staticmethod
    def get_interpreter():
        return config.get('interpreter')

    @staticmethod
    def is_embedded():
        """检查当前使用的解释器是否为内置版本"""
        current = InterpreterManager.get_interpreter()
        return current == EMBEDDED_PYTHON and os.path.exists(current)

    @staticmethod
    def has_pip():
        """检查当前解释器是否安装了 pip"""
        path = InterpreterManager.get_interpreter()
        if not path or not os.path.exists(path):
            return False
        try:
            result = subprocess.run([path, '-m', 'pip', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    @staticmethod
    def run_script(script_path, output_callback=None, finished_callback=None):
        """
        使用配置的解释器运行 Python 脚本。
        返回类似 QProcess 的对象或管理执行。
        对于 GUI 集成，我们通常在 UI 线程中使用 QProcess，
        但这里我们可以提供要运行的命令。
        """
        python_exe = InterpreterManager.get_interpreter()
        return [python_exe, '-u', script_path] # -u 用于无缓冲输出

    @staticmethod
    def is_valid(path):
        if not path or not os.path.exists(path):
            return False
        try:
            # 通过获取版本来检查是否为有效的 Python
            result = subprocess.run([path, '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
