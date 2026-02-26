import os, requests, zipfile, shutil, subprocess, tarfile
try:
    import zstandard as zstd
except ImportError:
    zstd = None
from PyQt5.QtCore import pyqtSignal, QThread
from src.core.translator import translator

# Python 版本列表

PYTHON_VERSIONS = {
    "3.8.5": "https://github.com/astral-sh/python-build-standalone/releases/download/20200822/cpython-3.8.5-x86_64-pc-windows-msvc-shared-pgo-20200823T0130.tar.zst",
    "3.7.9": "https://github.com/astral-sh/python-build-standalone/releases/download/20200822/cpython-3.7.9-x86_64-pc-windows-msvc-shared-pgo-20200823T0118.tar.zst",
}

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str) # 发送 python.exe 的路径
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
                os.makedirs(self.target_dir)

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
                    msg = translator.get("downloader.zstd_missing", "Please install 'zstandard' library (pip install zstandard) to extract .tar.zst files")
                    raise Exception(msg)
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
            # 查找包含 python.exe 的目录，优先查找 install 目录
            python_root = None
            found = False
            
            # 1. 尝试直接查找 install 目录
            for root, dirs, files in os.walk(extract_temp):
                if "install" in dirs:
                    candidate = os.path.join(root, "install")
                    if os.path.exists(os.path.join(candidate, "python.exe")):
                        python_root = candidate
                        found = True
                        break
            
            # 2. 如果没找到 install 目录，尝试在整个解压目录中查找 python.exe
            if not found:
                for root, dirs, files in os.walk(extract_temp):
                    if "python.exe" in files:
                        python_root = root
                        found = True
                        break
            
            if not found or python_root is None:
                 raise Exception(translator.get("downloader.python_not_found", "Could not find Python executable in the downloaded package"))

            # 移动到最终目录
            if os.path.exists(version_dir):
                shutil.rmtree(version_dir)
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(version_dir), exist_ok=True)
            
            # 移动内容到最终目录 (确保扁平化，不包含嵌套的 install 文件夹)
            if not os.path.exists(version_dir):
                os.makedirs(version_dir)
            
            for item in os.listdir(python_root):
                s = os.path.join(python_root, item)
                d = os.path.join(version_dir, item)
                if os.path.exists(d):
                    if os.path.isdir(d):
                        shutil.rmtree(d)
                    else:
                        os.remove(d)
                shutil.move(s, d)
            
            # 清理临时解压目录
            if os.path.exists(extract_temp):
                shutil.rmtree(extract_temp)

            python_exe = os.path.join(version_dir, "python.exe")

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
