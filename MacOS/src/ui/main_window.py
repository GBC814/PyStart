import os
from PyQt6.QtCore import Qt, QProcess, QProcessEnvironment, QTimer
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QFileDialog, QFrame
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence, QColor, QFontMetrics
from qfluentwidgets import FluentWindow, NavigationItemPosition, FluentIcon, ToolButton, TabWidget
from src.core.translator import translator
from src.ui.editor import CodeEditor

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        
        # 获取基础目录
        from src.config import BASE_DIR
        
        # 窗口设置
        self.setWindowTitle(translator.get("app.title"))
        icon_path = os.path.join(BASE_DIR, "assets", "PyStart.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 700)
        
        # 中央布局
        self.central_widget = QWidget()
        self.central_widget.setObjectName("homeInterface")
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 32, 0, 0) # 标题栏的顶部边距
        
        # 工具栏
        self.setup_toolbar()
        
        # 右侧分割器
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 编辑器标签页
        self.editor_tabs = TabWidget()
        self.editor_tabs.tabBar.setTabShadowEnabled(False)
        self.editor_tabs.tabAddRequested.connect(self.new_file)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        self.right_splitter.addWidget(self.editor_tabs)

        # 终端/输出容器
        self.terminal_container = TabWidget()
        self.terminal_container.tabBar.setTabShadowEnabled(False)
        self.terminal_container.tabAddRequested.connect(self.new_terminal)
        self.terminal_container.currentChanged.connect(self.on_terminal_tab_changed)
        self.terminal_container.setTabsClosable(True)
        self.terminal_container.tabCloseRequested.connect(self.handle_terminal_close)
        
        self.right_splitter.addWidget(self.terminal_container)
        self.right_splitter.setSizes([700, 300])
        self.central_layout.addWidget(self.right_splitter)
        
        # 优先添加主界面
        self.addSubInterface(self.central_widget, FluentIcon.HOME.colored(QColor(0, 103, 192), QColor(0, 153, 255)), translator.get("home"))
        
        # 初始化运行脚本的进程
        self.process = None
        
        # 连接语言更改信号
        translator.languageChanged.connect(self.update_texts)

        # 侧边栏优化
        self.navigationInterface.setExpandWidth(160)
        self.navigationInterface.setMinimumWidth(1)
        self.navigationInterface.setStyleSheet("""
            NavigationInterface {
                background-color: transparent;
            }
            NavigationItem {
                height: 48px;
                border-radius: 8px;
                margin: 6px 8px;
                background-color: transparent;
                border: none;
            }
            NavigationItem:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
            NavigationItem[isSelected=true] {
                background-color: rgba(0, 0, 0, 0.06);
            }
            /* 增加图标大小感官 */
            NavigationItem > QLabel {
                padding: 2px;
            }
        """)

        # 性能优化：在第一帧显示后延迟加载所有其他内容
        QTimer.singleShot(0, self.init_delayed_components)

    def init_delayed_components(self):
        """延迟加载组件，确保主窗口先显示出来"""
        # 1. 将所有可能阻塞的初始化都推迟到下一帧
        QTimer.singleShot(50, self._init_core_and_ui)

    def _init_core_and_ui(self):
        # 2. 检查 Python 环境 (config.check_interpreter 内部有多次 os.path.exists)
        from src.config import config
        config.check_interpreter()
        
        # 主窗口创建前已经设置过主题，这里不再重复设置，避免潜在的 QConfig 冲突
        pass

        # 4. 加载核心交互组件 ( InteractiveShell 导入和实例化)
        self.ensure_terminal_created()
        self.new_file()
        self.init_shortcuts()
        
        # 5. 将非核心次要界面的初始化进一步推迟
        QTimer.singleShot(200, self.init_sub_interfaces)

    def ensure_terminal_created(self):
        """确保终端已创建"""
        if not hasattr(self, 'terminal'):
            self.new_terminal()

    def new_terminal(self):
        """创建一个新的终端标签页"""
        from src.ui.shell import InteractiveShell
        terminal = InteractiveShell(self)
        terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        terminal.customContextMenuRequested.connect(lambda pos: self.show_terminal_menu(pos, terminal))

        # 如果是第一个终端，赋值给 self.terminal 以保持兼容性
        if not hasattr(self, 'terminal'):
            self.terminal = terminal

        index = self.terminal_container.addTab(terminal, translator.get("shell"))
        self.terminal_container.setTabToolTip(index, translator.get("terminal.close", "Close Terminal"))
        self.terminal_container.setCurrentIndex(index)
        self.terminal_container.show()
        terminal.setFocus()
        # 更新标签页宽度
        self.update_tab_widths()

    def init_sub_interfaces(self):
        """异步初始化其他次要界面，减少启动时的卡顿"""
        from src.ui.library_interface import LibraryManagerInterface
        from src.ui.font_settings import FontSettingsInterface
        from src.ui.theme_settings import ThemeSettingsInterface
        from src.ui.settings import SettingsInterface
        from src.ui.about import AboutInterface

        self.library_interface = LibraryManagerInterface(self)
        self.library_interface.setObjectName("libraryInterface")
        self.addSubInterface(self.library_interface, FluentIcon.TILES.colored(QColor(0, 153, 0), QColor(0, 204, 0)), translator.get("library.manager", "Library Manager"))
        
        self.font_settings_interface = FontSettingsInterface(self)
        self.font_settings_interface.setObjectName("fontSettingsInterface")
        self.addSubInterface(self.font_settings_interface, FluentIcon.EDIT.colored(QColor(136, 23, 152), QColor(191, 107, 203)), translator.get("font_settings.title", "Font Settings"))
        
        self.theme_settings_interface = ThemeSettingsInterface(self)
        self.theme_settings_interface.setObjectName("themeSettingsInterface")
        self.addSubInterface(self.theme_settings_interface, FluentIcon.PALETTE.colored(QColor(232, 17, 35), QColor(255, 67, 67)), translator.get("theme.title", "Theme Color"), NavigationItemPosition.BOTTOM)
        
        self.settings_interface = SettingsInterface(self)
        self.settings_interface.setObjectName("settingsInterface")
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING.colored(QColor(60, 60, 60), QColor(200, 200, 200)), translator.get("settings"), NavigationItemPosition.BOTTOM)
        
        self.about_interface = AboutInterface(self)
        self.about_interface.setObjectName("aboutInterface")
        self.addSubInterface(self.about_interface, FluentIcon.INFO.colored(QColor(0, 153, 188), QColor(0, 183, 195)), translator.get("about.title"), NavigationItemPosition.BOTTOM)

    def init_shortcuts(self):
        # 新建文件 (Ctrl+N)
        self.shortcut_new = QShortcut(QKeySequence("Ctrl+N"), self)
        self.shortcut_new.activated.connect(self.new_file)
        
        # 打开文件 (Ctrl+O)
        self.shortcut_open = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_open.activated.connect(self.open_file_dialog)
        
        # 保存文件 (Ctrl+S)
        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_current_file)
        
        # 运行脚本 (F5)
        self.shortcut_run = QShortcut(QKeySequence("F5"), self)
        self.shortcut_run.activated.connect(self.run_current_script)
        
        # 切换终端 (Ctrl+J) - VS Code 风格
        self.shortcut_toggle_terminal = QShortcut(QKeySequence("Ctrl+J"), self)
        self.shortcut_toggle_terminal.activated.connect(self.toggle_terminal)

    def on_terminal_tab_changed(self, index):
        """当终端标签页切换时，更新当前活跃的终端引用"""
        if index != -1:
            self.terminal = self.terminal_container.widget(index)

    def handle_terminal_close(self, index):
        # 标签上的关闭按钮 -> 如果有多个标签则关闭当前标签，否则隐藏整个面板
        if self.terminal_container.count() > 1:
            self.terminal_container.removeTab(index)
        else:
            self.terminal_container.hide()

    def clear_terminal(self, index):
        # 保留旧方法名兼容性，或者直接删除
        self.handle_terminal_close(index)

    def show_terminal_menu(self, pos, terminal_widget=None):
        if terminal_widget is None:
            terminal_widget = self.terminal
            
        menu = terminal_widget.createStandardContextMenu()
        menu.clear() # 清除默认菜单
        
        from PyQt6.QtGui import QAction
        
        action_copy = QAction(translator.get("menu.copy"), self)
        action_copy.setShortcut("Ctrl+C")
        action_copy.triggered.connect(terminal_widget.copy)
        # 判断是否有选中内容
        action_copy.setEnabled(terminal_widget.hasSelectedText())
        menu.addAction(action_copy)
        
        action_paste = QAction(translator.get("menu.paste"), self)
        action_paste.setShortcut("Ctrl+V")
        action_paste.triggered.connect(terminal_widget.paste)
        menu.addAction(action_paste)
        
        action_select_all = QAction(translator.get("menu.select_all"), self)
        action_select_all.setShortcut("Ctrl+A")
        action_select_all.triggered.connect(terminal_widget.selectAll)
        menu.addAction(action_select_all)
        
        menu.addSeparator()
        
        action_clear = QAction(translator.get("terminal.clear", "Clear"), self)
        action_clear.triggered.connect(terminal_widget.clear_shell)
        menu.addAction(action_clear)
        
        menu.exec(terminal_widget.mapToGlobal(pos))

    def calculate_tab_width(self, text):
        """根据文本内容计算标签页宽度，确保文字完整显示"""
        # 获取标签栏的字体
        font = self.editor_tabs.tabBar.font()
        metrics = QFontMetrics(font)
        # 计算文本宽度，加上一些边距（关闭按钮、图标等）
        text_width = metrics.horizontalAdvance(text)
        # 添加边距：关闭按钮(约20px) + 左右边距(各10px) + 图标(约20px)
        total_width = text_width + 60
        # 设置最小和最大宽度限制
        return max(80, min(total_width, 300))

    def update_tab_widths(self):
        """更新所有标签页的宽度以适应内容"""
        # 更新编辑器标签页宽度
        if self.editor_tabs.count() > 0:
            max_editor_width = 0
            for i in range(self.editor_tabs.count()):
                text = self.editor_tabs.tabText(i)
                width = self.calculate_tab_width(text)
                max_editor_width = max(max_editor_width, width)
            self.editor_tabs.setTabMaximumWidth(max_editor_width)

        # 更新终端标签页宽度
        if self.terminal_container.count() > 0:
            max_terminal_width = 0
            for i in range(self.terminal_container.count()):
                text = self.terminal_container.tabText(i)
                width = self.calculate_tab_width(text)
                max_terminal_width = max(max_terminal_width, width)
            self.terminal_container.setTabMaximumWidth(max_terminal_width)

    def update_texts(self):
        self.setWindowTitle(translator.get("app.title"))
        self.terminal_container.setTabText(0, translator.get("shell"))

        # 更新导航界面
        try:
            # 辅助函数：更新项目的文本和提示
            def update_item(route_key, text, tooltip=None):
                item = self.navigationInterface.widget(route_key)
                if item:
                    item.setText(text)
                    if tooltip:
                        item.setToolTip(tooltip)

            update_item("homeInterface", translator.get("home"), translator.get("home"))
            update_item("libraryInterface", translator.get("library.manager"), translator.get("library.manager"))
            update_item("themeSettingsInterface", translator.get("theme.title"), translator.get("theme.title"))
            update_item("settingsInterface", translator.get("settings"), translator.get("settings"))
            update_item("fontSettingsInterface", translator.get("font_settings.title"), translator.get("font_settings.title"))
            update_item("aboutInterface", translator.get("about.title"), translator.get("about.title"))

        except Exception as e:
            print(f"Error updating navigation text: {e}")

        self.btn_run.setToolTip(f"{translator.get('run.tooltip')} (F5)")
        self.btn_new.setToolTip(f"{translator.get('new.tooltip')} (Ctrl+N)")
        self.btn_open.setToolTip(f"{translator.get('open.tooltip')} (Ctrl+O)")
        self.btn_save.setToolTip(f"{translator.get('save.tooltip')} (Ctrl+S)")
        self.btn_toggle_terminal.setToolTip(f"{translator.get('view.terminal', 'Toggle Terminal')} (Ctrl+J)")

        # 更新未命名的编辑器标签
        import re
        new_base_name = translator.get("editor.untitled", "Untitled")
        for i in range(self.editor_tabs.count()):
            # 只有未保存的文件才没有 tooltip (或者 tooltip 为空)
            if not self.editor_tabs.tabToolTip(i):
                current_text = self.editor_tabs.tabText(i)
                # 匹配模式: 任意字符-数字.py
                match = re.search(r'-(\d+)\.py$', current_text)
                if match:
                    number = match.group(1)
                    new_name = f"{new_base_name}-{number}.py"
                    self.editor_tabs.setTabText(i, new_name)

        # 更新标签页宽度以适应新的语言
        self.update_tab_widths()

    def setup_toolbar(self):
        self.toolbar_layout = QHBoxLayout()
        # 设置边距以使工具栏按钮与下方的标签页对齐
        self.toolbar_layout.setContentsMargins(10, 5, 10, 5)
        self.toolbar_layout.setSpacing(8)
        
        self.btn_run = ToolButton(FluentIcon.PLAY, self)
        self.btn_run.setToolTip(f"{translator.get('run.tooltip')} (F5)")
        self.btn_run.clicked.connect(self.run_current_script)
        
        # 终端切换按钮
        self.btn_toggle_terminal = ToolButton(FluentIcon.COMMAND_PROMPT, self)
        self.btn_toggle_terminal.setToolTip(f"{translator.get('view.terminal', 'Toggle Terminal')} (Ctrl+J)")
        self.btn_toggle_terminal.clicked.connect(self.toggle_terminal)
        
        self.btn_new = ToolButton(FluentIcon.ADD, self)
        self.btn_new.setToolTip(f"{translator.get('new.tooltip')} (Ctrl+N)")
        self.btn_new.clicked.connect(self.new_file)

        self.btn_open = ToolButton(FluentIcon.FOLDER, self)
        self.btn_open.setToolTip(f"{translator.get('open.tooltip')} (Ctrl+O)")
        self.btn_open.clicked.connect(self.open_file_dialog)

        self.btn_save = ToolButton(FluentIcon.SAVE, self)
        self.btn_save.setToolTip(f"{translator.get('save.tooltip')} (Ctrl+S)")
        self.btn_save.clicked.connect(self.save_current_file)
        
        self.toolbar_layout.addWidget(self.btn_new)
        self.toolbar_layout.addWidget(self.btn_open)
        self.toolbar_layout.addWidget(self.btn_save)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.toolbar_layout.addWidget(separator)
        
        self.toolbar_layout.addWidget(self.btn_run)
        self.toolbar_layout.addWidget(self.btn_toggle_terminal)
        self.toolbar_layout.addStretch(1)
        
        self.central_layout.addLayout(self.toolbar_layout)

    def toggle_terminal(self):
        self.ensure_terminal_created()
        if self.terminal_container.isVisible():
            self.terminal_container.hide()
        else:
            self.terminal_container.show()
            # 如果没有焦点，给予焦点
            self.terminal.setFocus()

    def update_editor_settings(self):
        """更新所有打开的编辑器和终端的设置"""
        # 更新所有编辑器标签页
        for i in range(self.editor_tabs.count()):
            editor = self.editor_tabs.widget(i)
            if isinstance(editor, CodeEditor):
                editor.update_preferences()
        
        # 更新所有终端标签页
        for i in range(self.terminal_container.count()):
            shell = self.terminal_container.widget(i)
            if hasattr(shell, 'update_preferences'):
                shell.update_preferences()

    def new_file(self):
        editor = CodeEditor()
        # 默认内容
        editor.set_text("")

        # 生成唯一标题
        count = 1
        base_name = translator.get("editor.untitled", "Untitled")
        while True:
            name = f"{base_name}-{count}.py"
            exists = False
            for i in range(self.editor_tabs.count()):
                if self.editor_tabs.tabText(i) == name:
                    exists = True
                    break
            if not exists:
                break
            count += 1

        index = self.editor_tabs.addTab(editor, name)
        self.editor_tabs.setCurrentIndex(index)
        # 此时没有 toolTip (没有文件路径)，save_current_file 会处理这种情况
        # 更新标签页宽度
        self.update_tab_widths()

    def open_file_dialog(self):
        file_filter = f"{translator.get('file.python_files', 'Python Files (*.py)')};;{translator.get('file.all_files', 'All Files (*)')}"
        file_path, _ = QFileDialog.getOpenFileName(self, translator.get("open"), "", file_filter)
        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path):
        self.ensure_terminal_created()
        if not os.path.isfile(file_path):
            return

        # 检查是否已打开
        for i in range(self.editor_tabs.count()):
            if self.editor_tabs.tabToolTip(i) == file_path:
                self.editor_tabs.setCurrentIndex(i)
                return

        # 先读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.terminal.append(f"Error opening file: {e}")
            return

        # 检查是否应该复用当前标签页（如果是未命名且为空）
        reuse = False
        # 获取当前标签页索引
        current_index = self.editor_tabs.currentIndex()
        if current_index != -1:
            # 未命名文件没有 tooltip 路径
            if not self.editor_tabs.tabToolTip(current_index):
                editor = self.editor_tabs.widget(current_index)
                # 检查内容是否为空
                if not editor.get_text().strip():
                    reuse = True

        # 如果复用为真，使用当前标签页，否则添加新标签页
        if reuse:
            editor = self.editor_tabs.widget(current_index)
            editor.set_text(content)
            self.editor_tabs.setTabText(current_index, os.path.basename(file_path))
            self.editor_tabs.setTabToolTip(current_index, file_path)
            # 确保复用的标签页是当前标签页（应该已经是了）
            self.editor_tabs.setCurrentIndex(current_index)
        else:
            # 创建新编辑器
            editor = CodeEditor()
            editor.set_text(content)
            index = self.editor_tabs.addTab(editor, os.path.basename(file_path))
            self.editor_tabs.setTabToolTip(index, file_path)
            self.editor_tabs.setCurrentIndex(index)
        # 更新标签页宽度
        self.update_tab_widths()

    def save_current_file(self):
        self.ensure_terminal_created()
        index = self.editor_tabs.currentIndex()
        if index == -1:
            return

        editor = self.editor_tabs.widget(index)
        file_path = self.editor_tabs.tabToolTip(index)

        if not file_path:
            # 另存为
            file_filter = translator.get('file.python_files', 'Python Files (*.py)')
            file_path, _ = QFileDialog.getSaveFileName(self, translator.get("save.tooltip", "Save File"), "", file_filter)
            if not file_path:
                return
            self.editor_tabs.setTabText(index, os.path.basename(file_path))
            self.editor_tabs.setTabToolTip(index, file_path)
            # 更新标签页宽度
            self.update_tab_widths()

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(editor.get_text())
            self.terminal.append(f"{translator.get('file.saved', 'Saved')}: {file_path}")
        except Exception as e:
            self.terminal.append(f"{translator.get('file.save_error', 'Error saving file')}: {e}")

    def close_tab(self, index):
        self.editor_tabs.removeTab(index)

    def run_current_script(self):
        try:
            self.ensure_terminal_created()
            index = self.editor_tabs.currentIndex()
            if index == -1:
                self.terminal.append(translator.get("run.no_file", "No file open to run."))
                return
                
            # 获取编辑器内容
            editor = self.editor_tabs.widget(index)
            code_content = editor.get_text()
            
            original_file_path = self.editor_tabs.tabToolTip(index)
            script_path_to_run = ""
            is_temp = False
            working_directory = ""
            
            import tempfile
            
            # 确定工作目录 and 脚本路径
            if original_file_path:
                working_directory = os.path.dirname(original_file_path)
                
                # 尝试在同一目录下创建临时文件，以便更好地处理相对导入
                # 并确保 __file__ 指向原始文件附近
                try:
                    original_name = os.path.basename(original_file_path)
                    temp_name = f"tmp_{original_name}"
                    temp_path = os.path.join(working_directory, temp_name)
                    
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(code_content)
                    
                    script_path_to_run = temp_path
                    is_temp = True
                except Exception as e:
                    # 如果无法写入原始目录，则回退到系统临时目录
                    try:
                        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w', encoding='utf-8')
                        temp.write(code_content)
                        temp.close()
                        script_path_to_run = temp.name
                        is_temp = True
                    except Exception as e2:
                        self.terminal.append(f"Error creating temp file: {e2}")
                        return
            else:
                # 未保存的文件
                try:
                    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w', encoding='utf-8')
                    temp.write(code_content)
                    temp.close()
                    script_path_to_run = temp.name
                    is_temp = True
                except Exception as e:
                    self.terminal.append(f"Error creating temp file: {e}")
                    return

            self.terminal.stop_interpreter() # 停止当前的 REPL 进程
            self.terminal.clear_shell(start_repl=False) # 清空终端，且不启动新的 REPL
            
            # 确保终端可见
            if self.terminal_container.isHidden():
                self.terminal_container.show()
                
            self.terminal.append_output(f"> Running script...\n")
            
            from src.core.interpreter import InterpreterManager
            interpreter = InterpreterManager.get_interpreter()
            if not interpreter:
                 self.terminal.append("Error: No Python interpreter configured.")
                 return
                 
            # 如果已经有进程在运行，先停止它
            if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
                try:
                    self.process.terminate()
                    if not self.process.waitForFinished(1000):
                        self.process.kill()
                        self.process.waitForFinished(500)
                except RuntimeError:
                    pass
                 
            self.process = QProcess()
            self.terminal.set_active_process(self.process) # 将终端输入绑定到当前脚本进程
            
            # 关键：将工作目录设置为原始文件所在的目录
            if working_directory:
                self.process.setWorkingDirectory(working_directory)
                
                env = QProcessEnvironment.systemEnvironment()
                env.insert("PYTHONUTF8", "1")
                current_path = env.value("PYTHONPATH", "")
                if current_path:
                    new_path = working_directory + os.pathsep + current_path
                else:
                    new_path = working_directory
                env.insert("PYTHONPATH", new_path)
                self.process.setProcessEnvironment(env)
            else:
                env = QProcessEnvironment.systemEnvironment()
                env.insert("PYTHONUTF8", "1")
                self.process.setProcessEnvironment(env)
                
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            
            current_p = self.process
            self.process.finished.connect(lambda: self.process_finished(current_p, script_path_to_run if is_temp else None))
            
            self.process.start(interpreter, ['-u', script_path_to_run])
        except Exception as crash_err:
            import traceback
            print(f"CRASH IN RUN: {crash_err}")
            traceback.print_exc()
            if hasattr(self, 'terminal'):
                self.terminal.append(f"Critical error: {crash_err}")

    def process_finished(self, process, temp_path=None):
        try:
            # 检查 C++ 对象是否还存在
            if process:
                exit_code = process.exitCode()
                self.terminal.append_output(f"\n> Process finished with exit code {exit_code}\n")
        except RuntimeError:
            # 捕获 "wrapped C/C++ object of type QProcess has been deleted"
            pass
            
        self.terminal.set_active_process(None) # 解绑脚本进程
        
        # 优化：延迟恢复 REPL，避免与进程退出抢占资源导致卡顿
        # self.terminal.start_process() 
        QTimer.singleShot(100, lambda: self.terminal.start_process())
        
        # 如果是临时文件，运行结束后删除
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

    def closeEvent(self, event):
        """窗口关闭时停止正在运行的进程"""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            try:
                self.process.terminate()
                if not self.process.waitForFinished(1000):
                    self.process.kill()
                    self.process.waitForFinished(500)
            except RuntimeError:
                pass
        super().closeEvent(event)

    def handle_stdout(self):
        # 优化：批量读取，减少 GUI 刷新频率，缓解卡顿
        data = self.process.readAllStandardOutput()
        if data.isEmpty():
            return
            
        try:
            # 优先使用 utf-8 
            stdout = bytes(data).decode("utf-8")
        except UnicodeDecodeError:
            # 备选使用 cp936 (GBK)
            stdout = bytes(data).decode("cp936", errors="ignore")
        
        self.terminal.append_output(stdout)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        if data.isEmpty():
            return
            
        try:
            # 优先使用 utf-8
            stderr = bytes(data).decode("utf-8")
        except UnicodeDecodeError:
            # 备选使用 cp936 (GBK)
            stderr = bytes(data).decode("cp936", errors="ignore")
        
        self.terminal.append_output(stderr)