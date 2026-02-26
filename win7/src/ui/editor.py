import os
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import Qt, QPoint
from src.config import config
from src.core.translator import translator

class CodeEditor(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置配置
        self.font_family = config.get('font_family', 'Consolas')
        self.font_size = config.get('font_size', 12)
        
        # 词法分析器
        self.lexer = QsciLexerPython()
        self.setLexer(self.lexer)
        
        # 基本设置
        self.setUtf8(True)
        self.setIndentationsUseTabs(False)
        self.setTabWidth(4)
        self.setAutoIndent(True)
        
        # 行号
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsBackgroundColor(QColor("#f0f0f0"))
        
        # 设置行号栏与代码之间的间距
        self.SendScintilla(2155, 0, 8) # 设置左边距
        
        # 光标
        self.setCaretForegroundColor(QColor("black"))
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QColor("#e8e8ff"))
        
        # 括号匹配
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        self.setup_styles()
        self.update_preferences()
        
        # 右键菜单策略
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 缓存参考线颜色
        self.guide_color = None

    def _is_dark(self, color):
        """判断颜色是否为深色"""
        # 使用亮度公式
        brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        return brightness < 128

    def setup_styles(self):
        """设置语法高亮颜色和加粗"""
        if not self.lexer:
            return

        theme_color = QColor(config.get('theme_color', '#ffffff'))
        is_dark = self._is_dark(theme_color)

        font_normal = QFont(self.font_family, self.font_size)
        font_bold = QFont(self.font_family, self.font_size, QFont.Weight.Bold)
        font_italic_bold = QFont(self.font_family, self.font_size, QFont.Weight.Bold)
        font_italic_bold.setItalic(True)

        # 默认字体强制加粗
        self.lexer.setDefaultFont(font_bold)
        
        # 根据背景亮度调整颜色
        if is_dark:
            # 深色背景下的颜色 
            keyword_color = QColor("#C586C0")   # 浅紫色
            class_color = QColor("#4EC9B0")     # 青色
            func_color = QColor("#DCDCAA")      # 浅黄色
            string_color = QColor("#CE9178")    # 橙红色
            comment_color = QColor("#6A9955")   # 浅绿色
            number_color = QColor("#B5CEA8")    # 浅绿
            operator_color = QColor("#D4D4D4")  # 浅灰
            identifier_color = QColor("#9CDCFE") # 天蓝色
            default_fg = QColor("#D4D4D4")
        else:
            # 浅色背景下的颜色
            keyword_color = QColor("#AF00DB")
            class_color = QColor("#267F99")
            func_color = QColor("#795E26")
            string_color = QColor("#A31515")
            comment_color = QColor("#008000")
            number_color = QColor("#098658")
            operator_color = QColor("#0000FF")
            identifier_color = QColor("#001080")
            default_fg = QColor("#000000")

        self.lexer.setDefaultColor(default_fg)
        self.lexer.setColor(keyword_color, QsciLexerPython.Keyword)
        self.lexer.setFont(font_bold, QsciLexerPython.Keyword)
        
        self.lexer.setColor(class_color, QsciLexerPython.ClassName)
        self.lexer.setFont(font_bold, QsciLexerPython.ClassName)
        
        self.lexer.setColor(func_color, QsciLexerPython.FunctionMethodName)
        self.lexer.setFont(font_bold, QsciLexerPython.FunctionMethodName)
        
        self.lexer.setColor(string_color, QsciLexerPython.SingleQuotedString)
        self.lexer.setColor(string_color, QsciLexerPython.DoubleQuotedString)
        self.lexer.setColor(string_color, QsciLexerPython.TripleSingleQuotedString)
        self.lexer.setColor(string_color, QsciLexerPython.TripleDoubleQuotedString)
        self.lexer.setColor(string_color, QsciLexerPython.UnclosedString)
        self.lexer.setFont(font_bold, QsciLexerPython.SingleQuotedString)
        
        self.lexer.setColor(comment_color, QsciLexerPython.Comment)
        self.lexer.setColor(comment_color, QsciLexerPython.CommentBlock)
        self.lexer.setFont(font_italic_bold, QsciLexerPython.Comment)
        self.lexer.setFont(font_italic_bold, QsciLexerPython.CommentBlock)
        
        self.lexer.setColor(number_color, QsciLexerPython.Number)
        self.lexer.setFont(font_bold, QsciLexerPython.Number)
        
        self.lexer.setColor(operator_color, QsciLexerPython.Operator)
        self.lexer.setFont(font_bold, QsciLexerPython.Operator)
        
        self.lexer.setColor(identifier_color, QsciLexerPython.Identifier)
        self.lexer.setFont(font_bold, QsciLexerPython.Identifier)

        self.lexer.setColor(keyword_color, QsciLexerPython.Decorator)
        self.lexer.setFont(font_bold, QsciLexerPython.Decorator)
        
        # 更新光标和行高亮
        if is_dark:
            self.setCaretForegroundColor(QColor("white"))
            self.setCaretLineBackgroundColor(QColor(60, 60, 60, 100))
        else:
            self.setCaretForegroundColor(QColor("black"))
            self.setCaretLineBackgroundColor(QColor("#e8e8ff"))
        
        # 重置参考线颜色，触发重新计算
        self.guide_color = None

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
        
        # 自定义绘制参考线
        if config.get('show_indent_guides', True):
            self.paint_indent_guides()

    def paint_indent_guides(self):
        painter = QPainter(self.viewport())
        
        # 颜色计算
        if not self.guide_color:
            bg = QColor(config.get('theme_color', '#ffffff'))
            is_dark = self._is_dark(bg)
            
            if is_dark:
                # 深色背景下，参考线比背景稍亮
                ratio = 0.2
                r = min(255, int(bg.red() + (255 - bg.red()) * ratio))
                g = min(255, int(bg.green() + (255 - bg.green()) * ratio))
                b = min(255, int(bg.blue() + (255 - bg.blue()) * ratio))
            else:
                # 浅色背景下，参考线比背景稍暗
                ratio = 0.15
                r = int(bg.red() * (1 - ratio))
                g = int(bg.green() * (1 - ratio))
                b = int(bg.blue() * (1 - ratio))
                
            self.guide_color = QColor(r, g, b)
            
        pen = QPen(self.guide_color)
        pen.setWidthF(1.1)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # 获取可见行范围
        first_line = self.SendScintilla(QsciScintilla.SCI_GETFIRSTVISIBLELINE)
        lines_on_screen = self.SendScintilla(2370)
        max_lines = self.SendScintilla(2154)
        last_line = min(first_line + lines_on_screen, max_lines - 1)
        
        tab_width = self.tabWidth() or 4
        line_height = self.SendScintilla(QsciScintilla.SCI_TEXTHEIGHT, 0)
        # 获取单字符宽度以计算空行的 X 坐标
        char_width = self.SendScintilla(QsciScintilla.SCI_TEXTWIDTH, QsciLexerPython.Default, b" ")
        
        # 遍历行进行绘制
        for line in range(first_line, last_line + 1):
            # 获取实际逻辑缩进（不受光标或虚拟空格影响）
            indent = self.SendScintilla(QsciScintilla.SCI_GETLINEINDENTATION, line)
            
            # 判断是否为空行
            end_pos = self.SendScintilla(QsciScintilla.SCI_GETLINEENDPOSITION, line)
            indent_end_pos = self.SendScintilla(QsciScintilla.SCI_GETLINEINDENTPOSITION, line)
            is_empty = (indent_end_pos == end_pos)
            
            draw_indent = indent
            if is_empty:
                # 向上/向下寻找非空行以确定稳定的参考线深度
                prev_indent = self._get_nearby_non_empty_indent(line, -1)
                next_indent = self._get_nearby_non_empty_indent(line, 1)
                # 取最小值确保参考线在块结束时正确收拢
                draw_indent = min(prev_indent, next_indent) if next_indent > 0 else prev_indent
            
            if draw_indent > 0:
                first_char_col = self.SendScintilla(QsciScintilla.SCI_GETCOLUMN, indent_end_pos)
                line_start_pos = self.SendScintilla(QsciScintilla.SCI_POSITIONFROMLINE, line)
                y_window = self.SendScintilla(QsciScintilla.SCI_POINTYFROMPOSITION, 0, line_start_pos)
                y = self.viewport().mapFrom(self, QPoint(0, y_window)).y()
                
                # 获取该行起始位置的 X 坐标 (即列 0 的 X)
                x_start_window = self.SendScintilla(QsciScintilla.SCI_POINTXFROMPOSITION, 0, line_start_pos)
                x_start_vp = self.viewport().mapFrom(self, QPoint(x_start_window, 0)).x()

                for col in range(0, draw_indent, tab_width):
                    # 关键：非空行时，参考线绝不绘制在首个字符及以后
                    if not is_empty and col >= first_char_col:
                        break
                        
                    # 直接计算 X 坐标，避免空行时 SCI_FINDCOLUMN 返回错误位置
                    x_vp = x_start_vp + int(col * char_width)
                    
                    # 绘制垂直线
                    painter.drawLine(x_vp - 1, y, x_vp - 1, y + line_height)
        
        painter.end()

    def _get_nearby_non_empty_indent(self, line, direction):
        """寻找附近非空行的缩进量"""
        max_lines = self.SendScintilla(2154)
        for i in range(1, 50):
            target = line + i * direction
            if 0 <= target < max_lines:
                end = self.SendScintilla(QsciScintilla.SCI_GETLINEENDPOSITION, target)
                indent_end = self.SendScintilla(QsciScintilla.SCI_GETLINEINDENTPOSITION, target)
                if indent_end < end:
                    return self.SendScintilla(QsciScintilla.SCI_GETLINEINDENTATION, target)
            else:
                break
        return 0

    def update_preferences(self):
        """更新编辑器配置"""
        # 更新字体和主题色
        self.font_family = config.get('font_family', 'Consolas')
        self.font_size = config.get('font_size', 12)
        theme_color_str = config.get('theme_color', '#ffffff')
        theme_color = QColor(theme_color_str)
        is_dark = self._is_dark(theme_color)
        default_fg = QColor("#D4D4D4") if is_dark else QColor("#000000")
        
        # 1. 设置默认样式 (style 32) 并清除所有样式以实现继承
        # 这确保了所有样式首先继承正确的背景色和字体
        font_name_bytes = self.font_family.encode('utf-8')
        self.SendScintilla(QsciScintilla.SCI_STYLESETFONT, 32, font_name_bytes)
        self.SendScintilla(QsciScintilla.SCI_STYLESETSIZE, 32, self.font_size)
        self.SendScintilla(QsciScintilla.SCI_STYLESETBACK, 32, theme_color)
        self.SendScintilla(QsciScintilla.SCI_STYLESETFORE, 32, default_fg)
        self.SendScintilla(QsciScintilla.SCI_STYLECLEARALL)
        
        # 2. 应用 Lexer 样式
        font = QFont(self.font_family, self.font_size)
        self.lexer.setDefaultFont(font)
        self.lexer.setFont(font)
        # 为所有可能样式设置字体
        for i in range(128):
            self.lexer.setFont(font, i)
        
        # 重新应用具体的语法高亮颜色
        self.setup_styles()

        # 更新背景颜色
        self.setPaper(theme_color)
        self.lexer.setDefaultPaper(theme_color)
        for i in range(128):
            self.lexer.setPaper(theme_color, i)

        # 3. 辅助组件设置
        self.setMarginsBackgroundColor(QColor("#f0f0f0"))
        self.setMarginsForegroundColor(QColor("black"))
        self.setMarginWidth(0, "0000")

        show_guides = config.get('show_indent_guides', True)
        self.setIndentationGuides(False)
        self.SendScintilla(2132, 0)
        
        # 4. 强制重新着色所有文本并重绘
        self.SendScintilla(QsciScintilla.SCI_COLOURISE, 0, -1)
        self.viewport().update()
        self.update()

    def show_context_menu(self, pos):
        menu = self.createStandardContextMenu()
        menu.clear() # 清除默认的英文菜单
        
        # 撤销/重做
        action_undo = QAction(translator.get("menu.undo"), self)
        action_undo.setShortcut("Ctrl+Z")
        action_undo.triggered.connect(self.undo)
        action_undo.setEnabled(self.isUndoAvailable())
        menu.addAction(action_undo)
        
        action_redo = QAction(translator.get("menu.redo"), self)
        action_redo.setShortcut("Ctrl+Y")
        action_redo.triggered.connect(self.redo)
        action_redo.setEnabled(self.isRedoAvailable())
        menu.addAction(action_redo)
        
        menu.addSeparator()
        
        # 剪切/复制/粘贴
        action_cut = QAction(translator.get("menu.cut"), self)
        action_cut.setShortcut("Ctrl+X")
        action_cut.triggered.connect(self.cut)
        action_cut.setEnabled(self.hasSelectedText())
        menu.addAction(action_cut)
        
        action_copy = QAction(translator.get("menu.copy"), self)
        action_copy.setShortcut("Ctrl+C")
        action_copy.triggered.connect(self.copy)
        action_copy.setEnabled(self.hasSelectedText())
        menu.addAction(action_copy)
        
        action_paste = QAction(translator.get("menu.paste"), self)
        action_paste.setShortcut("Ctrl+V")
        action_paste.triggered.connect(self.paste)
        # 简单起见，粘贴总是启用
        menu.addAction(action_paste)
        
        action_delete = QAction(translator.get("menu.delete"), self)
        action_delete.triggered.connect(self.removeSelectedText)
        action_delete.setEnabled(self.hasSelectedText())
        menu.addAction(action_delete)
        
        menu.addSeparator()
        
        # 全选
        action_select_all = QAction(translator.get("menu.select_all"), self)
        action_select_all.setShortcut("Ctrl+A")
        action_select_all.triggered.connect(self.selectAll)
        menu.addAction(action_select_all)
        
        menu.exec_(self.mapToGlobal(pos))

    def removeSelectedText(self):
        self.replaceSelectedText("")

    def set_text(self, text):
        self.setText(text)

    def get_text(self):
        return self.text()
