import os
import subprocess
from PyQt5.QtWidgets import QWidget
from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciLexerBatch
from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt5.QtCore import Qt, QProcess, QProcessEnvironment, QEvent
from src.config import config
from src.core.interpreter import InterpreterManager
from src.core.translator import translator

class BaseShell(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 基础设置
        self.font_family = config.get('font_family', 'Consolas')
        
        # 启用自动换行，避免水平滚动
        self.setWrapMode(QsciScintilla.WrapWord)
        
        # 去掉行号，更像终端
        self.setMarginWidth(0, 0)
        self.setMarginsBackgroundColor(QColor("#f0f0f0"))
        
        # 颜色
        self.setCaretForegroundColor(QColor("black"))
        self.setCaretLineVisible(False)
        
        # 交互逻辑
        self.internal_process = QProcess()
        self.internal_process.setProcessChannelMode(QProcess.MergedChannels)
        self.internal_process.readyRead.connect(self.read_output)
        self.process = self.internal_process # 当前活跃进程
        
        self.history = []
        self.history_index = 0
        self.last_pos = 0
        
        # 补全状态初始化
        self.completing = False
        self.completion_matches = []
        self.completion_index = 0
        self.completion_start_pos = 0
        self.completion_token = ""

        # 应用初始偏好设置
        self.update_preferences()

    def append_output(self, text):
        self.SendScintilla(QsciScintilla.SCI_GOTOPOS, self.length())
        self.append(text)
        self.last_pos = self.length()
        self.SendScintilla(QsciScintilla.SCI_GOTOPOS, self.length())

    def paintEvent(self, event):
        # 先让 Scintilla 绘制其内容（包括文字和默认背景色）
        super().paintEvent(event)
        
        # 获取背景图片路径
        bg_image_path = config.get('background_image', '')
        if bg_image_path and os.path.exists(bg_image_path):
            painter = QPainter(self.viewport())
            pixmap = QPixmap(bg_image_path)
            if not pixmap.isNull():
                # 使用透明度绘制，使文字依然可见
                opacity = config.get('background_opacity', 0.3)
                painter.setOpacity(opacity)
                
                # 缩放图片以适应窗口，保持比例
                scaled_pixmap = pixmap.scaled(self.viewport().size(), 
                                            Qt.KeepAspectRatioByExpanding, 
                                            Qt.SmoothTransformation)
                
                # 居中绘制
                x = (self.viewport().width() - scaled_pixmap.width()) // 2
                y = (self.viewport().height() - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()

    def _is_dark(self, color):
        """判断颜色是否为深色"""
        brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        return brightness < 128

    def update_preferences(self):
        """更新终端配置"""
        self.font_family = config.get('font_family', 'Consolas')
        # 优先使用 terminal_font_size，如果没有则使用通用的 font_size
        self.font_size = config.get('terminal_font_size', config.get('font_size', 12))
        
        # 获取当前主题色和基本样式信息
        theme_color_str = config.get('theme_color', '#ffffff')
        theme_color = QColor(theme_color_str)
        is_dark = self._is_dark(theme_color)
        default_fg = QColor("#D4D4D4") if is_dark else QColor("#000000")
        
        # 1. 启用 DirectWrite 以修复 Windows 上的字体缩放和渲染问题
        self.SendScintilla(QsciScintilla.SCI_SETTECHNOLOGY, 1)
        
        # 2. 强制设置默认样式 (style 32) 并清除所有样式以实现继承
        # 必须先设置背景色再调用 SCI_STYLECLEARALL，否则清除时会使用旧的背景色
        font_name_bytes = self.font_family.encode('utf-8')
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 32, font_name_bytes)
        self.SendScintilla(QsciScintilla.SCI_STYLESETSIZE, 32, self.font_size)
        self.SendScintilla(QsciScintilla.SCI_STYLESETBACK, 32, theme_color)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFORE, 32, default_fg)
        
        # 清除所有样式，使它们继承 style 32 的属性（包括新的背景色）
        self.SendScintilla(QsciScintilla.SCI_STYLECLEARALL)
        
        # 3. 设置基础属性
        font = QFont(self.font_family, self.font_size)
        self.setFont(font)
        self.setPaper(theme_color)
        self.setColor(default_fg)
        
        # 设置光标颜色
        if is_dark:
            self.setCaretForegroundColor(QColor("white"))
        else:
            self.setCaretForegroundColor(QColor("black"))
        # 随字体大小调整光标宽度，确保在大字体下依然可见
        self.setCaretWidth(max(2, self.font_size // 8))

        lexer = self.lexer()
        if lexer:
            lexer.setDefaultFont(font)
            lexer.setFont(font)
            # 再次确保所有可能的样式都应用了正确的字体
            for i in range(256): # 扩展到 256 以覆盖所有可能样式
                lexer.setFont(font, i)
            
            # 更新背景颜色
            lexer.setDefaultPaper(theme_color)
            for i in range(256):
                lexer.setPaper(theme_color, i)
            
            # 设置前景颜色
            lexer.setDefaultColor(default_fg)
            for i in range(256):
                lexer.setColor(default_fg, i)

            # 恢复行号栏背景色为默认浅灰色
            self.setMarginsBackgroundColor(QColor("#f0f0f0"))
        else:
            self.setMarginsBackgroundColor(QColor("#f0f0f0"))
            
        # 4. 强制重新着色所有文本并重绘
        self.SendScintilla(QsciScintilla.SCI_COLOURISE, 0, -1)
        self.viewport().update()
        self.update()

    def read_output(self):
        data = self.internal_process.readAll()
        try:
            # 优先使用 utf-8
            text = bytes(data).decode("utf-8")
        except UnicodeDecodeError:
            # 备选使用 cp936
            text = bytes(data).decode("cp936", errors="ignore")
            
        self.append_output(text)

    def event(self, event):
        if event.type() in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride) and \
           event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            if event.type() == QEvent.Type.KeyPress:
                self.keyPressEvent(event)
            return True
        return super().event(event)

    def focusNextPrevChild(self, next):
        # 禁止通过 Tab/Shift+Tab 切换焦点
        return False

    def keyPressEvent(self, event):
        # 重置补全状态（除非按的是 Tab）
        if event.key() not in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            self.completing = False
            
        if event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            # Shift+Tab 反向循环
            direction = -1 if (event.key() == Qt.Key.Key_Backtab or (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)) else 1
            self.handle_tab_completion(direction)
            return
            
        cursor_pos = self.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
        if cursor_pos < self.last_pos:
            if event.key() not in (Qt.Key.Key_Control, Qt.Key.Key_C):
                self.SendScintilla(QsciScintilla.SCI_GOTOPOS, self.length())
        
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.handle_enter()
            return
            
        if event.key() == Qt.Key.Key_Backspace:
            if self.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS) <= self.last_pos:
                return
                
        super().keyPressEvent(event)

    def handle_tab_completion(self, direction=1):
        """处理 Tab 键补全"""
        import re
        
        # 1. 获取当前输入行内容
        # 注意：self.text() 返回 unicode 字符串，但 self.last_pos 和 SCI_GETCURRENTPOS 是 UTF-8 字节偏移量
        # 如果终端有中文输出，直接切片会导致索引错位。必须先转换为 bytes 处理。
        full_text_unicode = self.text()
        full_text_bytes = full_text_unicode.encode('utf-8')
        
        cursor_pos = self.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
        
        # 相对位置 (字节)
        rel_pos_bytes = cursor_pos - self.last_pos
        if rel_pos_bytes < 0: 
            return  # 不在输入区
        
        # 2. 如果正在补全中，继续循环下一个
        if self.completing and self.completion_matches:
            self.completion_index = (self.completion_index + direction) % len(self.completion_matches)
            match = self.completion_matches[self.completion_index]
            self.replace_token(match)
            return

        # 3. 开始新的补全
        # 获取光标前的字节内容并解码
        try:
            current_input_bytes = full_text_bytes[self.last_pos:cursor_pos]
            text_before_cursor = current_input_bytes.decode('utf-8')
        except UnicodeDecodeError:
            # 如果解码失败（比如只输入了一半的字节），可能无法补全
            return
            
        # 查找最后一个空格
        last_space_index = text_before_cursor.rfind(' ')
        if last_space_index == -1:
            token_start_char = 0
        else:
            token_start_char = last_space_index + 1
            
        token = text_before_cursor[token_start_char:]
        
        # 如果 token 为空，不要列出所有文件
        if not token:
            return

        # 简单的去除引号处理 (只处理首尾)
        clean_token = token.strip('"\'')
        
        # 计算 token 开始的绝对字节位置
        # 需要计算 token 之前部分的字节长度
        prefix = text_before_cursor[:token_start_char]
        prefix_bytes = prefix.encode('utf-8')
        self.completion_start_pos = self.last_pos + len(prefix_bytes)
        self.completion_token = token
        
        # 4. 获取当前工作目录
        cwd = os.getcwd()  # 默认当前目录
        
        # 辅助函数：去除 ANSI 转义序列
        def strip_ansi(text):
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            return ansi_escape.sub('', text)
        
        # 尝试从最后一行中寻找 PowerShell Prompt
        # self.last_pos 是字节位置，所以要用 bytes 切片
        try:
            prompt_text = full_text_bytes[:self.last_pos].decode('utf-8', errors='ignore')
        except:
            prompt_text = ""
            
        lines = prompt_text.split('\n')
        for line in reversed(lines):
            line_clean = strip_ansi(line.strip())
            if not line_clean: 
                continue
            # PowerShell 格式: PS D:\path>
            # CMD 格式: D:\path>
            match = re.search(r'(?:PS\s+)?([a-zA-Z]:\\[^>]*)', line_clean)
            if match:
                cwd = match.group(1).strip()
                break
        
        # 5. 寻找匹配的文件
        dirname = os.path.dirname(clean_token)
        basename = os.path.basename(clean_token)
        
        # 特殊处理盘符: "D:" -> "D:\"
        if re.match(r'^[a-zA-Z]:$', clean_token):
            dirname = clean_token + "\\"
            basename = ""
        
        search_dir = cwd
        if dirname:
            if os.path.isabs(dirname):
                search_dir = dirname
            else:
                search_dir = os.path.join(cwd, dirname)
        
        matches = []
        try:
            if os.path.exists(search_dir) and os.path.isdir(search_dir):
                # 忽略大小写排序
                for name in sorted(os.listdir(search_dir), key=str.lower):
                    # 过滤系统文件/隐藏文件
                    if name.startswith('$') or name == "System Volume Information":
                        continue
                        
                    if name.lower().startswith(basename.lower()):
                        # 构造完整路径部分（相对于输入的 token）
                        if dirname:
                            full_match = os.path.join(dirname, name)
                        else:
                            full_match = name
                            
                        # 目录加反斜杠
                        full_path = os.path.join(search_dir, name)
                        if os.path.isdir(full_path):
                            full_match += "\\"
                            
                        matches.append(full_match)
        except Exception as e:
            pass
        
        if matches:
            self.completing = True
            self.completion_matches = matches
            # 如果方向是 -1 (Shift+Tab)，从最后一个开始
            self.completion_index = 0 if direction == 1 else len(matches) - 1
            # 应用匹配
            self.replace_token(matches[self.completion_index])
            
    def replace_token(self, new_text):
        """替换补全的 token"""
        # 选中从 completion_start_pos 到当前光标的内容
        current_pos = self.SendScintilla(QsciScintilla.SCI_GETCURRENTPOS)
        self.SendScintilla(QsciScintilla.SCI_SETSEL, self.completion_start_pos, current_pos)
        self.replaceSelectedText(new_text)
        # 更新光标位置
        self.SendScintilla(QsciScintilla.SCI_GOTOPOS, self.completion_start_pos + len(new_text))

    def handle_enter(self):
        full_text = self.text()
        # 处理编码问题：转换为 bytes 后再切片
        try:
            full_text_bytes = full_text.encode('utf-8')
            user_input_bytes = full_text_bytes[self.last_pos:]
            user_input = user_input_bytes.decode('utf-8').strip()
        except:
            user_input = full_text[self.last_pos:].strip() # Fallback

        self.append("\n")
        
        if user_input:
            self.process.write(user_input.encode("utf-8") + b"\n")
            self.history.append(user_input)
            self.history_index = len(self.history)
        else:
            self.process.write(b"\n")
        
        self.last_pos = self.length()
        self.SendScintilla(QsciScintilla.SCI_GOTOPOS, self.length())
        
    def clear_shell(self, start_repl=True):
        self.clear()
        if start_repl:
            self.start_process()

    def set_active_process(self, process=None):
        """设置当前接收输入的进程。如果为 None，则恢复为内部进程。"""
        if process:
            self.process = process
        else:
            self.process = self.internal_process

    def start_process(self):
        pass

class InteractiveShell(BaseShell):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 词法分析器
        lexer = QsciLexerPython()
        lexer.setDefaultFont(QFont(self.font_family, self.font_size))
        self.setLexer(lexer)
        
        self.interpreter = InterpreterManager.get_interpreter()
        self.prompt = translator.get("shell.prompt", ">>> ")
        self.start_process()
        
        # 确保在设置 lexer 后应用主题
        self.update_preferences()

    def restart_shell(self):
        self.interpreter = InterpreterManager.get_interpreter()
        self.clear_shell()

    def stop_interpreter(self):
        """停止当前的交互式 Python 解释器"""
        if self.internal_process.state() != QProcess.NotRunning:
            self.internal_process.kill()
            self.internal_process.waitForFinished()

    def start_process(self):
        if not self.interpreter or not os.path.exists(self.interpreter):
            error_msg = translator.get("shell.interpreter_not_found", "Error: Python interpreter not found")
            self.append(f"{error_msg}: {self.interpreter}\n")
            return
            
        if self.internal_process.state() != QProcess.NotRunning:
            self.internal_process.kill()
            self.internal_process.waitForFinished()
            
        # 设置 UTF-8 环境
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUTF8", "1")
        self.internal_process.setProcessEnvironment(env)
        
        self.internal_process.start(self.interpreter, ["-i", "-q"])
        self.internal_process.waitForStarted()
        
        try:
            res = subprocess.run([self.interpreter, "--version"], capture_output=True, text=True)
            version = res.stdout.strip() or res.stderr.strip()
        except:
            version = translator.get("shell.python_fallback", "Python")
            
        self.append_output(f"{version} ({self.interpreter})\n{self.prompt}")
        self.last_pos = self.length()

    def read_output(self):
        data = self.internal_process.readAll()
        try:
            # 优先使用 utf-8
            text = bytes(data).decode("utf-8")
        except UnicodeDecodeError:
            # 备选使用 cp936
            text = bytes(data).decode("cp936", errors="ignore")
            
        if "Ctrl click to launch VS Code Native REPL" in text:
            return
            
        text_stripped = text.strip()
        if text_stripped == ">>>" or text_stripped.endswith(">>>"):
            line_count = self.lines()
            if line_count > 0:
                last_line = self.text(line_count - 1).strip()
                if last_line == ">>>" or last_line.endswith(">>>"):
                    return

        self.append_output(text)

class SystemShell(BaseShell):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 词法分析器 - Batch/CMD
        lexer = QsciLexerBatch()
        lexer.setDefaultFont(QFont(self.font_family, self.font_size))
        self.setLexer(lexer)
        
        self.start_process()
        
        # 确保在设置 lexer 后应用主题
        self.update_preferences()

    def start_process(self):
        if self.internal_process.state() != QProcess.NotRunning:
            self.internal_process.kill()
            self.internal_process.waitForFinished()
        
        # 更新 PATH 以包含 python
        interpreter = InterpreterManager.get_interpreter()
        env = QProcessEnvironment.systemEnvironment()
        if interpreter:
            python_dir = os.path.dirname(interpreter)
            scripts_dir = os.path.join(python_dir, "Scripts")
            # 将其添加到 PATH 的开头
            path = env.value("PATH", "")
            new_path = f"{python_dir};{scripts_dir};{path}"
            env.insert("PATH", new_path)
            self.internal_process.setProcessEnvironment(env)
            
        self.internal_process.start("powershell.exe")
        self.internal_process.waitForStarted()
        
        self.clear() # 使用 clear 而不是 setText("")
        self.last_pos = self.length()
        
        # 补全状态
        self.completing = False
        self.completion_matches = []
        self.completion_index = 0
        self.completion_start_pos = 0

class ShellInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 此类在 MainWindow 中似乎未被使用，或仅作为包装类。
        # 如有需要，保留以保持兼容性。
        pass
