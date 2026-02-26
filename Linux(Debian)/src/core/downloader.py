import os, requests, zipfile, shutil, subprocess, tarfile, platform
try:
    import zstandard as zstd
except ImportError:
    zstd = None
from PyQt6.QtCore import pyqtSignal, QThread
from src.core.translator import translator

# 检测操作系统
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Python 可执行文件名和路径
PYTHON_EXECUTABLE_NAME = 'python.exe' if IS_WINDOWS else 'python3'
if IS_WINDOWS:
    PYTHON_EXECUTABLE = PYTHON_EXECUTABLE_NAME
    PYTHON_EXECUTABLE_SEARCH = PYTHON_EXECUTABLE_NAME
else:
    import os
    PYTHON_EXECUTABLE = os.path.join('bin', PYTHON_EXECUTABLE_NAME)
    PYTHON_EXECUTABLE_SEARCH = PYTHON_EXECUTABLE_NAME

# Python 版本列表 - 根据系统选择不同的下载链接
PYTHON_VERSIONS_WINDOWS = {
    "3.14.2": "https://github.com/astral-sh/python-build-standalone/releases/download/20251205/cpython-3.14.2+20251205-x86_64-pc-windows-msvc-install_only.tar.gz",
    "3.13.1": "https://github.com/astral-sh/python-build-standalone/releases/download/20250106/cpython-3.13.1+20250106-x86_64-pc-windows-msvc-shared-install_only.tar.gz",
    "3.12.8": "https://github.com/astral-sh/python-build-standalone/releases/download/20250106/cpython-3.12.8+20250106-x86_64-pc-windows-msvc-shared-install_only.tar.gz",
    "3.11.9": "https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-pc-windows-msvc-shared-install_only.tar.gz",
    "3.10.11": "https://github.com/astral-sh/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-pc-windows-msvc-shared-install_only.tar.gz",
    "3.9.13": "https://github.com/astral-sh/python-build-standalone/releases/download/20220802/cpython-3.9.13+20220802-x86_64-pc-windows-msvc-shared-install_only.tar.gz",
    "3.8.10": "https://github.com/astral-sh/python-build-standalone/releases/download/20210506/cpython-3.8.10-x86_64-pc-windows-msvc-shared-pgo-20210506T0943.tar.zst",
}

PYTHON_VERSIONS_LINUX = {
    "3.14.2": "https://github.com/astral-sh/python-build-standalone/releases/download/20251205/cpython-3.14.2+20251205-x86_64-unknown-linux-gnu-install_only.tar.gz",
    "3.13.1": "https://github.com/astral-sh/python-build-standalone/releases/download/20250115/cpython-3.13.1+20250115-x86_64-unknown-linux-gnu-install_only.tar.gz",
    "3.12.8": "https://github.com/astral-sh/python-build-standalone/releases/download/20250106/cpython-3.12.8+20250106-x86_64-unknown-linux-gnu-install_only.tar.gz",
    "3.11.9": "https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.11.9+20240415-x86_64-unknown-linux-gnu-install_only.tar.gz",
    "3.10.11": "https://github.com/astral-sh/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-unknown-linux-gnu-install_only.tar.gz",
    "3.9.13": "https://github.com/astral-sh/python-build-standalone/releases/download/20220802/cpython-3.9.13+20220802-x86_64-unknown-linux-gnu-install_only.tar.gz", 
    "3.8.10": "https://github.com/astral-sh/python-build-standalone/releases/download/20210506/cpython-3.8.10-x86_64-unknown-linux-gnu-pgo-20210506T0943.tar.zst",
}

# 根据系统选择对应的版本列表
PYTHON_VERSIONS = PYTHON_VERSIONS_WINDOWS if IS_WINDOWS else PYTHON_VERSIONS_LINUX

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str) # 发送 Python 可执行文件的路径
    error = pyqtSignal(str)

    def __init__(self, version, url, target_dir):
        super().__init__()
        self.version = version
        self.url = url
        self.target_dir = target_dir
        self.is_cancelled = False

    def run(self):
        try:
            # 如果目标目录不存在则创建
            if not os.path.exists(self.target_dir):
                os.makedirs(self.target_dir, exist_ok=True)

            version_dir = os.path.join(self.target_dir, f"python-{self.version}")
            if os.path.exists(version_dir):
                pass 

            # 确定文件名和扩展名
            filename = self.url.split('/')[-1]
            archive_path = os.path.join(self.target_dir, filename)
            extract_temp = os.path.join(self.target_dir, f"temp_extract_{self.version}")

            # 下载
            response = requests.get(self.url, stream=True)
            total_length = response.headers.get('content-length')

            if total_length is None: # 没有内容长度头
                with open(archive_path, 'wb') as f:
                    f.write(response.content)
            else:
                dl = 0
                total_length = int(total_length)
                with open(archive_path, 'wb') as f:
                    for data in response.iter_content(chunk_size=4096):
                        if self.is_cancelled:
                            response.close()
                            if os.path.exists(archive_path):
                                os.remove(archive_path)
                            return
                        dl += len(data)
                        f.write(data)
                        percent = int(100 * dl / total_length)
                        self.progress.emit(percent)

            if self.is_cancelled:
                return

            # 解压
            self.progress.emit(100) # 下载完成，开始解压
            
            if os.path.exists(extract_temp):
                shutil.rmtree(extract_temp)
            
            if filename.endswith(".zip"):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_temp)
            elif filename.endswith(".tar.gz") or filename.endswith(".tgz"):
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(extract_temp)
            elif filename.endswith(".tar.zst"):
                if zstd is None:
                    raise Exception("Please install 'zstandard' library to extract .tar.zst files")
                with open(archive_path, 'rb') as f:
                    dctx = zstd.ZstdDecompressor()
                    with dctx.stream_reader(f) as reader:
                        with tarfile.open(fileobj=reader, mode='r|') as tar:
                            tar.extractall(path=extract_temp)
            else:
                 raise Exception(translator.get("downloader.unsupported_format", "Unsupported compression format"))

            # 清理压缩包
            os.remove(archive_path)

            # 处理目录结构
            python_root = None
            found = False
            
            # 打印调试信息（临时）
            print(f"解压目录内容: {os.listdir(extract_temp)}")
            
            # 1. 首先检查解压后的第一层目录
            for item in os.listdir(extract_temp):
                item_path = os.path.join(extract_temp, item)
                if os.path.isdir(item_path):
                    # 检查这个目录是否直接包含 Python
                    if IS_WINDOWS:
                        candidate_python = os.path.join(item_path, PYTHON_EXECUTABLE)
                    else:
                        candidate_python = os.path.join(item_path, PYTHON_EXECUTABLE)
                    
                    if os.path.exists(candidate_python):
                        python_root = item_path
                        found = True
                        break
                    
                    # 检查是否有 bin 子目录（Linux）
                    if IS_LINUX:
                        bin_python = os.path.join(item_path, "bin", PYTHON_EXECUTABLE_NAME)
                        if os.path.exists(bin_python):
                            python_root = item_path
                            found = True
                            break
            
            # 2. 如果第一层没找到，深度搜索
            if not found:
                for root, dirs, files in os.walk(extract_temp):
                    # 检查是否有 install 目录
                    if "install" in dirs:
                        install_dir = os.path.join(root, "install")
                        if IS_WINDOWS:
                            install_python = os.path.join(install_dir, PYTHON_EXECUTABLE)
                        else:
                            install_python = os.path.join(install_dir, PYTHON_EXECUTABLE)
                        
                        if os.path.exists(install_python):
                            python_root = install_dir
                            found = True
                            break
                    
                    # 检查当前目录是否有 Python 可执行文件
                    if PYTHON_EXECUTABLE_SEARCH in files:
                        if IS_LINUX and os.path.basename(root) == "bin":
                            # Linux: python3 在 bin/ 目录中，返回父目录
                            python_root = os.path.dirname(root)
                            found = True
                            break
                        elif IS_WINDOWS:
                            python_root = root
                            found = True
                            break
            
            if not found or python_root is None:
                # 打印目录结构帮助调试
                print("目录结构:")
                for root, dirs, files in os.walk(extract_temp):
                    level = root.replace(extract_temp, '').count(os.sep)
                    indent = ' ' * 2 * level
                    print(f"{indent}{os.path.basename(root)}/")
                    subindent = ' ' * 2 * (level + 1)
                    for file in files[:5]:
                        print(f"{subindent}{file}")
                    if len(files) > 5:
                        print(f"{subindent}... ({len(files)} 个文件)")
                
                raise Exception(translator.get("downloader.python_not_found", "Could not find Python executable in the downloaded package"))

            # 移动到最终目录
            if os.path.exists(version_dir):
                shutil.rmtree(version_dir)
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(version_dir), exist_ok=True)
            
            # 移动内容
            if os.path.basename(python_root) == "install":
                # 如果是 install 目录，我们需要移动其内容
                os.makedirs(version_dir, exist_ok=True)
                for item in os.listdir(python_root):
                    s = os.path.join(python_root, item)
                    d = os.path.join(version_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)
            else:
                shutil.move(python_root, version_dir)
            
            # 清理临时解压目录
            if os.path.exists(extract_temp):
                shutil.rmtree(extract_temp)

            python_exe = os.path.join(version_dir, PYTHON_EXECUTABLE)
            
            # 在 Linux 上设置可执行权限
            if IS_LINUX:
                os.chmod(python_exe, 0o755)

            # 确保 pip 和 setuptools 已安装
            # 独立构建通常包含 pip，但为了保险起见，运行 ensurepip
            try:
                # 运行 ensurepip
                subprocess.run([python_exe, "-m", "ensurepip", "--default-pip"], 
                               check=True, capture_output=True)
                
                # 升级 pip
                subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"],
                               check=False, capture_output=True)
                               
                v_major, v_minor = map(int, self.version.split('.')[:2])
                if v_major < 3 or (v_major == 3 and v_minor < 12):
                    subprocess.run([python_exe, "-m", "pip", "install", "setuptools"],
                                   check=False, capture_output=True)
                               
            except Exception as e:
                print(f"Pip setup warning: {e}")

            self.finished.emit(python_exe)

        except Exception as e:
            self.error.emit(str(e))
            # 清理可能残留的文件
            if 'archive_path' in locals() and os.path.exists(archive_path):
                os.remove(archive_path)
            if 'extract_temp' in locals() and os.path.exists(extract_temp):
                shutil.rmtree(extract_temp)

    def cancel(self):
        self.is_cancelled = True

class PythonDownloader:
    @staticmethod
    def get_available_versions():
        return PYTHON_VERSIONS
