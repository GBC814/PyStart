import sys, subprocess, urllib.request, json, platform
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QHeaderView, QTableWidgetItem
from qfluentwidgets import PrimaryPushButton, PushButton, LineEdit, TableWidget, FluentIcon, InfoBar, InfoBarPosition, SubtitleLabel, IndeterminateProgressRing, ComboBox
from src.core.interpreter import InterpreterManager
from src.core.translator import translator
from src.config import config
from src.ui.shell import SystemShell
from qfluentwidgets import MessageBoxBase, SubtitleLabel

# 检测操作系统
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

class TerminalDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(translator.get("terminal", "System Terminal"), self)
        self.viewLayout.addWidget(self.titleLabel)
        
        self.terminal = SystemShell(self)
        self.terminal.setMinimumHeight(400)
        self.terminal.setMinimumWidth(1400)
        self.viewLayout.addWidget(self.terminal)
        
        # 隐藏默认的按钮，我们只需要关闭按钮（右上角自带）或者添加一个关闭按钮
        self.yesButton.hide()
        self.cancelButton.setText(translator.get("terminal.close", "Close"))
        
        self.widget.setMinimumWidth(650)

class PyPIWorker(QThread):
    finished = pyqtSignal(bool, str, str) # success, package_name, version

    def __init__(self, package_name):
        super().__init__()
        self.package_name = package_name

    def run(self):
        try:
            url = f"https://pypi.org/pypi/{self.package_name}/json"
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    version = data.get("info", {}).get("version", "")
                    if version:
                        self.finished.emit(True, self.package_name, version)
                        return
            self.finished.emit(False, self.package_name, "")
        except Exception as e:
            self.finished.emit(False, self.package_name, str(e))

class PipWorker(QThread):
    finished = pyqtSignal(bool, str, str) # 成功, 输出, 错误

    def __init__(self, command, args):
        super().__init__()
        self.command = command
        self.args = args

    def run(self):
        interpreter = InterpreterManager.get_interpreter()
        if not interpreter:
            self.finished.emit(False, "", translator.get("interpreter.not_found", "Interpreter not found"))
            return

        cmd = [interpreter, "-m", "pip", self.command] + self.args
        try:
            # 强制 UTF-8 编码以避免解码问题
            env = subprocess.os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.finished.emit(True, stdout, stderr)
            else:
                self.finished.emit(False, stdout, stderr)
        except Exception as e:
            self.finished.emit(False, "", str(e))

class OutdatedCheckWorker(QThread):
    finished = pyqtSignal(list) # list of (name, latest_version)

    def __init__(self, packages, mirror_url=None):
        super().__init__()
        self.packages = packages
        self.mirror_url = mirror_url

    def run(self):
        interpreter = InterpreterManager.get_interpreter()
        if not interpreter:
            self.finished.emit([])
            return

        cmd = [interpreter, "-m", "pip", "list", "--outdated", "--format=json"]
        if self.mirror_url and self.mirror_url != "https://pypi.org/simple":
             cmd.extend(["-i", self.mirror_url])

        try:
            env = subprocess.os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                import json
                import re
                try:
                    match = re.search(r'\[.*\]', stdout, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        outdated = json.loads(json_str)
                        results = []
                        for pkg in outdated:
                            results.append((pkg.get('name'), pkg.get('latest_version')))
                        self.finished.emit(results)
                    else:
                        self.finished.emit([])
                except:
                    self.finished.emit([])
            else:
                self.finished.emit([])
        except:
            self.finished.emit([])

class LibraryManagerInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("libraryInterface")
        
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(30, 30, 30, 30)
        self.vBoxLayout.setSpacing(15)

        # 顶部标题栏
        self.headerLayout = QHBoxLayout()
        self.titleLabel = SubtitleLabel(translator.get("library.manager", "Library Manager"), self)
        self.headerLayout.addWidget(self.titleLabel)
        self.headerLayout.addStretch(1)
        
        # 镜像源选择
        self.mirrorCombo = ComboBox(self)
        self.mirrors = [
            (translator.get("mirror.aliyun", "Aliyun (阿里云)"), "https://mirrors.aliyun.com/pypi/simple/"),
            (translator.get("mirror.tsinghua", "Tsinghua (清华)"), "https://pypi.tuna.tsinghua.edu.cn/simple"),
            (translator.get("mirror.douban", "Douban (豆瓣)"), "https://pypi.doubanio.com/simple/"),
            (translator.get("mirror.tencent", "Tencent (腾讯)"), "https://mirrors.cloud.tencent.com/pypi/simple"),
            (translator.get("mirror.pypi", "PyPI (Official)"), "https://pypi.org/simple"),
        ]
        for name, url in self.mirrors:
            self.mirrorCombo.addItem(name, url)
        
        # 加载保存的镜像源设置
        saved_mirror = config.get('pypi_mirror', "https://pypi.org/simple")
        for i, (_, url) in enumerate(self.mirrors):
            if url == saved_mirror:
                self.mirrorCombo.setCurrentIndex(i)
                break
                
        self.mirrorCombo.currentIndexChanged.connect(self.on_mirror_changed)
        self.headerLayout.addWidget(self.mirrorCombo)

        self.refreshBtn = PushButton(FluentIcon.SYNC, translator.get("library.refresh", "Refresh"), self)
        self.refreshBtn.clicked.connect(self.load_packages)
        self.headerLayout.addWidget(self.refreshBtn)
        
        self.vBoxLayout.addLayout(self.headerLayout)
        
        # 工具栏
        self.toolLayout = QHBoxLayout()
        self.searchEdit = LineEdit(self)
        self.searchEdit.setPlaceholderText(translator.get("library.search_placeholder", "Search installed packages or input package name to install..."))
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.textChanged.connect(self.filter_packages)
        self.searchEdit.returnPressed.connect(self.install_package)
        self.toolLayout.addWidget(self.searchEdit)
        
        # 版本输入框
        self.versionEdit = LineEdit(self)
        self.versionEdit.setPlaceholderText(translator.get("library.version_placeholder", "Version (optional)"))
        self.versionEdit.setFixedWidth(120)
        self.versionEdit.returnPressed.connect(self.install_package)
        self.toolLayout.addWidget(self.versionEdit)
        
        self.installBtn = PrimaryPushButton(FluentIcon.DOWNLOAD, translator.get("library.install", "Install"), self)
        self.installBtn.clicked.connect(self.install_package)
        self.toolLayout.addWidget(self.installBtn)
        
        self.terminalBtn = PushButton(FluentIcon.COMMAND_PROMPT, translator.get("terminal", "Terminal"), self)
        self.terminalBtn.clicked.connect(self.show_terminal_dialog)
        self.toolLayout.addWidget(self.terminalBtn)
        
        self.vBoxLayout.addLayout(self.toolLayout)
        
        # 表格
        self.table = TableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            translator.get("library.name", "Name"),
            translator.get("library.version", "Version"),
            translator.get("library.latest", "Latest"), # 可选，没有网络很难获取所有包的最新版本
            translator.get("library.action", "Action")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 220)
        self.table.verticalHeader().hide()
        
        self.vBoxLayout.addWidget(self.table)
        
        # 加载指示器
        self.loadingRing = IndeterminateProgressRing(self)
        self.loadingRing.setFixedSize(50, 50)
        self.loadingRing.hide()
        
        # PyPI 查询防抖定时器
        self.pypi_timer = QTimer()
        self.pypi_timer.setSingleShot(True)
        self.pypi_timer.setInterval(500) # 500ms 防抖
        self.pypi_timer.timeout.connect(self.start_pypi_query)
        self.pypi_worker = None
        self.outdated_worker = None
        
        # 初始加载
        self.load_packages()
        
        translator.languageChanged.connect(self.update_texts)

    def on_mirror_changed(self, index):
        url = self.mirrorCombo.itemData(index)
        if url:
            config.set('pypi_mirror', url)

    def update_texts(self):
        self.titleLabel.setText(translator.get("library.manager", "Library Manager"))
        self.refreshBtn.setText(translator.get("library.refresh", "Refresh"))
        self.searchEdit.setPlaceholderText(translator.get("library.search_placeholder", "Search installed packages or input package name to install..."))
        self.versionEdit.setPlaceholderText(translator.get("library.version_placeholder", "Version (optional)"))
        self.installBtn.setText(translator.get("library.install", "Install"))
        self.terminalBtn.setText(translator.get("terminal", "Terminal"))
        
        # 更新表头
        self.table.setHorizontalHeaderLabels([
            translator.get("library.name", "Name"),
            translator.get("library.version", "Version"),
            translator.get("library.latest", "Latest"),
            translator.get("library.action", "Action")
        ])
        
        # 重新填充表格以更新按钮文本
        if hasattr(self, 'packages'):
            self.populate_table(self.packages)
            # 如果需要，重新应用过滤
            if self.searchEdit.text():
                self.filter_packages(self.searchEdit.text())

    def show_loading(self, show):
        if show:
            self.loadingRing.show()
            self.loadingRing.start()
            self.table.setEnabled(False)
            self.installBtn.setEnabled(False)
            self.refreshBtn.setEnabled(False)
            # 居中显示加载圈
            self.loadingRing.move(
                self.width() // 2 - self.loadingRing.width() // 2,
                self.height() // 2 - self.loadingRing.height() // 2
            )
        else:
            self.loadingRing.stop()
            self.loadingRing.hide()
            self.table.setEnabled(True)
            self.installBtn.setEnabled(True)
            self.refreshBtn.setEnabled(True)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.loadingRing.move(
            self.width() // 2 - self.loadingRing.width() // 2,
            self.height() // 2 - self.loadingRing.height() // 2
        )

    def load_packages(self):
        self.show_loading(True)
        # 使用 list --format=json 可能更好
        self.worker = PipWorker("list", ["--format=json"])
        self.worker.finished.connect(self.on_list_finished)
        self.worker.start()

    def on_list_finished(self, success, stdout, stderr):
        if not success:
            self.show_loading(False) # 只有失败才这里停止 loading，成功的话在 check outdated 后停止
            InfoBar.error(
                title=translator.get("error"),
                content=f"{translator.get('library.list_failed', 'Failed to list packages')}: {stderr}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self
            )
            return
            
        import json
        import re
        try:
            # 尝试提取 JSON 部分（从 [ 开始，到 ] 结束）
            json_str = stdout
            match = re.search(r'\[.*\]', stdout, re.DOTALL)
            if match:
                json_str = match.group(0)
                
            packages = json.loads(json_str)
            self.populate_table(packages)
            
            # 重新应用过滤（如果搜索框有内容）
            if self.searchEdit.text():
                self.filter_packages(self.searchEdit.text())
            
            # 启动过期检查
            self.check_outdated_packages(packages)
                
        except json.JSONDecodeError:
            self.show_loading(False)
            InfoBar.error(
                title=translator.get("error"),
                content=f"{translator.get('library.parse_failed', 'Failed to parse pip output')}. Raw output: {stdout[:100]}...",
                parent=self
            )

    def check_outdated_packages(self, packages):
        # 保持 loading 状态
        mirror_url = self.mirrorCombo.currentData()
        self.outdated_worker = OutdatedCheckWorker(packages, mirror_url)
        self.outdated_worker.finished.connect(self.on_outdated_checked)
        self.outdated_worker.start()

    def on_outdated_checked(self, outdated_list):
        self.show_loading(False)
        
        # 创建一个快速查找字典
        outdated_dict = {name.lower(): version for name, version in outdated_list}
        
        # 更新表格
        for i in range(self.table.rowCount()):
            name_item = self.table.item(i, 0)
            if not name_item: continue
            
            # 忽略引导行
            if name_item.data(Qt.ItemDataRole.UserRole) == "guide_row":
                continue
                
            name = name_item.text().lower()
            if name in outdated_dict:
                latest_version = outdated_dict[name]
                # 设置最新版本
                self.table.setItem(i, 2, QTableWidgetItem(latest_version))
                
                # 可选：高亮显示需要更新的包
                # self.table.item(i, 1).setForeground(Qt.GlobalColor.red)
            else:
                # 如果不在 outdated 列表中，说明已是最新（或者是检查失败/无法检查的包）
                # 为了用户体验，我们可以把当前版本填进去，表示"已是最新"
                current_version = self.table.item(i, 1).text()
                self.table.setItem(i, 2, QTableWidgetItem(current_version))

    def populate_table(self, packages):
        self.packages = packages # 保存以便过滤
        self.table.setRowCount(len(packages))
        for i, pkg in enumerate(packages):
            name = pkg.get('name', '')
            version = pkg.get('version', '')
            
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(version))
            self.table.setItem(i, 2, QTableWidgetItem("-")) # 获取最新版本较慢
            
            # 操作按钮
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 2, 5, 2)
            layout.setSpacing(5)
            
            updateBtn = PushButton(translator.get("library.update", "Update"), widget)
            updateBtn.setFixedSize(90, 26)
            updateBtn.clicked.connect(lambda checked, n=name: self.update_package(n))
            
            uninstallBtn = PushButton(translator.get("library.uninstall", "Uninstall"), widget)
            uninstallBtn.setFixedSize(80, 26)
            uninstallBtn.clicked.connect(lambda checked, n=name: self.uninstall_package(n))
            
            layout.addWidget(updateBtn)
            layout.addWidget(uninstallBtn)
            layout.addStretch(1)
            self.table.setCellWidget(i, 3, widget)

    def filter_packages(self, text):
        text = text.lower().strip()
        all_hidden = True
        
        # 重置并启动防抖定时器
        self.pypi_timer.start()
        
        # 移除旧的引导行（如果存在）
        if self.table.rowCount() > 0:
            last_item = self.table.item(self.table.rowCount() - 1, 0)
            if last_item and last_item.data(Qt.ItemDataRole.UserRole) == "guide_row":
                self.table.removeRow(self.table.rowCount() - 1)
        
        for i in range(self.table.rowCount()):
            name_item = self.table.item(i, 0)
            if not name_item: continue
            
            name = name_item.text().lower()
            # 简单包含匹配
            hidden = name.find(text) == -1
            self.table.setRowHidden(i, hidden)
            if not hidden:
                all_hidden = False
        
        # 如果全部隐藏且有搜索内容，显示引导安装行
        if all_hidden and text:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 第一列显示包名（使用用户输入的名称）
            name_item = QTableWidgetItem(text)
            name_item.setData(Qt.ItemDataRole.UserRole, "guide_row")
            name_item.setFlags(Qt.ItemFlag.NoItemFlags) # 不可选中
            self.table.setItem(row, 0, name_item)
            
            # 版本列留空或显示提示
            self.table.setItem(row, 1, QTableWidgetItem("-"))
            self.table.setItem(row, 2, QTableWidgetItem("-"))
            
            # 操作列显示安装按钮
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(5, 2, 5, 2)
            
            installBtn = PrimaryPushButton(translator.get("library.install", "Install"), widget)
            installBtn.setFixedSize(90, 26)
            installBtn.clicked.connect(self.install_package) # 直接调用安装逻辑，它会读取输入框
            
            layout.addWidget(installBtn)
            layout.addStretch(1)
            self.table.setCellWidget(row, 3, widget)
            
            # 确保这行不被隐藏
            self.table.setRowHidden(row, False)

    def start_pypi_query(self):
        text = self.searchEdit.text().strip()
        if not text:
            return
            
        # 如果当前搜索结果不是"未安装"状态，则不需要查询PyPI来显示引导
        # 但我们仍然需要查询来更新"最新版本"列（如果是已安装包）
        # 这里主要为了优化：如果用户输入了一个无效包名，且本地也没安装，我们才去查询看是否存在
        
        if self.pypi_worker and self.pypi_worker.isRunning():
            self.pypi_worker.terminate()
            self.pypi_worker.wait()
            
        self.pypi_worker = PyPIWorker(text)
        self.pypi_worker.finished.connect(self.on_pypi_info_received)
        self.pypi_worker.start()

    def on_pypi_info_received(self, success, package_name, version):
        # 1. 更新已安装包的最新版本信息
        for i in range(self.table.rowCount()):
            name_item = self.table.item(i, 0)
            if not name_item: continue
            
            # 忽略引导行
            if name_item.data(Qt.ItemDataRole.UserRole) == "guide_row":
                continue
                
            if name_item.text().lower() == package_name.lower():
                if success and version:
                    self.table.setItem(i, 2, QTableWidgetItem(version))
                return # 找到了已安装包，就不需要处理引导行了

        # 2. 如果没找到已安装包，处理引导行
        # 检查是否存在引导行（通常是最后一行）
        if self.table.rowCount() > 0:
            last_row = self.table.rowCount() - 1
            name_item = self.table.item(last_row, 0)
            
            if name_item and name_item.data(Qt.ItemDataRole.UserRole) == "guide_row":
                # 确认引导行的包名匹配
                if name_item.text().lower() == package_name.lower():
                    if success and version:
                        # PyPI 上存在该包：更新最新版本显示
                        self.table.setItem(last_row, 2, QTableWidgetItem(version))
                    else:
                        # PyPI 上不存在该包：移除引导行
                        self.table.removeRow(last_row)

    def install_package(self):
        # 如果搜索框内容在列表中找不到，就尝试安装
        name = self.searchEdit.text().strip()
        if not name:
            return
            
        version = self.versionEdit.text().strip()
        install_target = name
        if version:
            install_target = f"{name}=={version}"
            
        self.show_loading(True)
        
        args = [install_target]
        mirror_url = self.mirrorCombo.currentData()
        if mirror_url and mirror_url != "https://pypi.org/simple":
             args.extend(["-i", mirror_url])
             
        self.worker = PipWorker("install", args)
        self.worker.finished.connect(self.on_install_finished)
        self.worker.start()

    def on_install_finished(self, success, stdout, stderr):
        self.searchEdit.clear()
        self.versionEdit.clear()
        if success:
            InfoBar.success(
                title=translator.get("success"),
                content=translator.get("library.install_success", "Package installed successfully"),
                parent=self
            )
            self.load_packages()
        else:
            self.show_loading(False)
            InfoBar.error(
                title=translator.get("error"),
                content=f"{translator.get('library.install_failed', 'Installation failed')}: {stderr}\n{stdout}",
                parent=self
            )

    def show_terminal_dialog(self):
        import os
        try:
            # 获取当前配置的解释器路径
            interpreter = InterpreterManager.get_interpreter()
            if interpreter:
                python_dir = os.path.dirname(interpreter)
                if IS_WINDOWS:
                    scripts_dir = os.path.join(python_dir, "Scripts")
                    # 构造设置环境变量的 PowerShell 命令
                    # 使用 -NoExit 参数保持窗口打开
                    # 优先将解释器路径添加到 PATH 前面
                    cmd = f'start powershell -NoExit -Command "$env:PATH = \'{python_dir};{scripts_dir};\' + $env:PATH"'
                    os.system(cmd)
                else:
                    bin_dir = os.path.join(python_dir, "bin")
                    # Linux 使用 bash，设置 PATH 并打开终端
                    # 使用 x-terminal-emulator 或 gnome-terminal 等
                    path_env = f"{python_dir}:{bin_dir}:$PATH"
                    # 尝试多种终端
                    terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal', 'xterm']
                    terminal_found = False
                    for term in terminals:
                        if subprocess.run(['which', term], capture_output=True).returncode == 0:
                            if term in ['gnome-terminal', 'konsole', 'xfce4-terminal']:
                                # 这些终端需要特殊处理
                                os.system(f'{term} -- bash -c "export PATH={path_env}; exec bash"')
                            else:
                                os.system(f'{term} -e "bash -c \'export PATH={path_env}; exec bash\'"')
                            terminal_found = True
                            break
                    if not terminal_found:
                        # 回退到简单的 bash
                        os.system(f'bash -c "export PATH={path_env}; exec bash"')
            else:
                # 如果没有配置解释器，直接打开
                if IS_WINDOWS:
                    os.system("start powershell")
                else:
                    # 尝试多种终端
                    terminals = ['x-terminal-emulator', 'gnome-terminal', 'konsole', 'xfce4-terminal', 'xterm']
                    terminal_found = False
                    for term in terminals:
                        if subprocess.run(['which', term], capture_output=True).returncode == 0:
                            os.system(term)
                            terminal_found = True
                            break
                    if not terminal_found:
                        os.system('bash')
        except Exception as e:
            InfoBar.error(
                title=translator.get("error"),
                content=f"{translator.get('terminal.open_failed', 'Failed to open terminal')}: {str(e)}",
                parent=self
            )

    def update_package(self, name):
        self.show_loading(True)
        args = ["--upgrade", name]
        mirror_url = self.mirrorCombo.currentData()
        if mirror_url and mirror_url != "https://pypi.org/simple":
             args.extend(["-i", mirror_url])
             
        self.worker = PipWorker("install", args)
        self.worker.finished.connect(self.on_update_finished)
        self.worker.start()

    def on_update_finished(self, success, stdout, stderr):
        if success:
            InfoBar.success(
                title=translator.get("success"),
                content=translator.get("library.update_success", "Package updated successfully"),
                parent=self
            )
            self.load_packages()
        else:
            self.show_loading(False)
            InfoBar.error(
                title=translator.get("error"),
                content=f"{translator.get('library.update_failed', 'Update failed')}: {stderr}",
                parent=self
            )

    def uninstall_package(self, name):
        self.show_loading(True)
        # -y 自动确认
        self.worker = PipWorker("uninstall", ["-y", name])
        self.worker.finished.connect(self.on_uninstall_finished)
        self.worker.start()

    def on_uninstall_finished(self, success, stdout, stderr):
        if success:
            InfoBar.success(
                title=translator.get("success"),
                content=translator.get("library.uninstall_success", "Package uninstalled successfully"),
                parent=self
            )
            self.load_packages()
        else:
            self.show_loading(False)
            InfoBar.error(
                title=translator.get("error"),
                content=f"{translator.get('library.uninstall_failed', 'Uninstallation failed')}: {stderr}",
                parent=self
            )
