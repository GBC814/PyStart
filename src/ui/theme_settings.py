import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QHBoxLayout
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QPixmap, QPainter, QBrush, QPen
from qfluentwidgets import SubtitleLabel, CaptionLabel, CardWidget, FlowLayout, TransparentToolButton, SwitchButton, setTheme, Theme, BodyLabel, isDarkTheme
from src.config import config
from src.core.translator import translator

class ThemeColorButton(TransparentToolButton):
    """主题颜色选择按钮"""
    def __init__(self, color_hex, text="", is_add_btn=False, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.is_add_btn = is_add_btn
        self.setFixedSize(100, 120)
        self.button_text = text
        # 不调用 self.setText(text)，避免基类 TransparentToolButton 绘制文字导致重复
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制颜色方块区域
        rect = self.rect()
        color_rect_size = 60
        color_rect = QRect((rect.width() - color_rect_size) // 2, 10, color_rect_size, color_rect_size)
        
        if self.is_add_btn:
            # 绘制虚线圆角正方形
            pen = QPen(QColor('#cccccc'))
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(color_rect, 8, 8)
            
            # 绘制 "+" 号
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setWidth(3)
            pen.setColor(QColor('#999999'))
            painter.setPen(pen)
            margin = 20
            # 横线
            painter.drawLine(color_rect.left() + margin, color_rect.center().y(),
                             color_rect.right() - margin, color_rect.center().y())
            # 竖线
            painter.drawLine(color_rect.center().x(), color_rect.top() + margin,
                             color_rect.center().x(), color_rect.bottom() - margin)
        else:
            # 绘制颜色方块
            # 如果是图片主题（特殊处理）
            if self.color_hex.startswith('image:'):
                image_path = self.color_hex[6:]
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    painter.setBrush(QBrush(pixmap.scaled(color_rect.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)))
                else:
                    painter.setBrush(QColor('#cccccc'))
            else:
                painter.setBrush(QColor(self.color_hex))
                
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(color_rect, 8, 8)
        
        # 绘制文本
        painter.setPen(Qt.GlobalColor.white if isDarkTheme() else Qt.GlobalColor.black)
        text_rect = QRect(0, 80, rect.width(), 30)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.button_text)

    def set_text(self, text):
        self.button_text = text
        self.update()

class ThemeSettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("themeSettingsInterface")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        self.title = SubtitleLabel(translator.get("theme.title"), self)
        self.layout.addWidget(self.title)
        
        # 主题颜色选择区域
        self.theme_card = CardWidget(self)
        self.theme_layout = QVBoxLayout(self.theme_card)
        
        self.theme_label = CaptionLabel(translator.get("theme.title"), self)
        self.theme_layout.addWidget(self.theme_label)
        
        self.flow_layout = FlowLayout()
        self.theme_layout.addLayout(self.flow_layout)
        
        # 预设颜色
        self.presets = [
            ("#ffffff", "theme.preset.white"),
            ("#f5f5f5", "theme.preset.gray"),
            ("#e1f5fe", "theme.preset.blue"),
            ("#e8f5e9", "theme.preset.green"),
            ("#fff3e0", "theme.preset.orange"),
            ("#fce4ec", "theme.preset.pink"),
            ("#f3e5f5", "theme.preset.purple"),
            ("#2d2d2d", "theme.preset.dark_gray"),
            ("#1e1e1e", "theme.preset.black"),
        ]
        
        self.setup_presets()
        
        # 添加自定义图片按钮
        self.add_theme_btn = ThemeColorButton("#cccccc", translator.get("theme.add_theme"), is_add_btn=True, parent=self)
        self.add_theme_btn.clicked.connect(self.select_background_image)
        self.flow_layout.addWidget(self.add_theme_btn)
        
        self.layout.addWidget(self.theme_card)
        
        # 明暗主题切换区域
        self.mode_card = CardWidget(self)
        self.mode_layout = QHBoxLayout(self.mode_card)
        self.mode_layout.setContentsMargins(16, 12, 16, 12)
        
        self.mode_info_layout = QVBoxLayout()
        self.mode_title_label = BodyLabel(translator.get("theme.mode"), self.mode_card)
        self.mode_desc_label = CaptionLabel(translator.get("theme.mode.description"), self.mode_card)
        self.mode_info_layout.addWidget(self.mode_title_label)
        self.mode_info_layout.addWidget(self.mode_desc_label)
        self.mode_layout.addLayout(self.mode_info_layout)
        
        self.mode_layout.addStretch(1)
        
        self.mode_switch = SwitchButton(self.mode_card)
        self.mode_switch.setOnText(translator.get("settings.on"))
        self.mode_switch.setOffText(translator.get("settings.off"))
        # 根据配置设置初始状态
        is_dark = config.get('theme_mode') == 'Dark'
        self.mode_switch.setChecked(is_dark)
        self.mode_switch.checkedChanged.connect(self.toggle_theme_mode)
        self.mode_layout.addWidget(self.mode_switch)
        
        self.layout.addWidget(self.mode_card)
        
        self.layout.addStretch(1)
        
        # 连接语言更改信号
        translator.languageChanged.connect(self.update_texts)

    def setup_presets(self):
        self.preset_buttons = []
        for color, key in self.presets:
            btn = ThemeColorButton(color, translator.get(key), is_add_btn=False, parent=self)
            btn.clicked.connect(lambda checked, c=color: self.set_theme_color(c))
            self.flow_layout.addWidget(btn)
            self.preset_buttons.append((btn, key))

    def set_theme_color(self, color):
        config.set('theme_color', color)
        # 切换到预设颜色时，清除背景图片以确保颜色正常显示
        config.set('background_image', '')
        self.update_app_theme()

    def set_background_image(self, image_path):
        config.set('background_image', image_path)
        # 设置背景图片时，强制设置一个底色（白色），确保图片显示正常且不与之前的预设颜色冲突
        config.set('theme_color', '#ffffff')
        self.update_app_theme()

    def select_background_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, translator.get("theme.add_theme"), "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            # 设置当前背景
            self.set_background_image(file_path)

    def clear_background_image(self):
        config.set('background_image', '')
        self.update_app_theme()

    def toggle_theme_mode(self, is_checked):
        mode = 'Dark' if is_checked else 'Light'
        config.set('theme_mode', mode)
        setTheme(Theme.DARK if is_checked else Theme.LIGHT)
        self.update_app_theme()
        self.update() # 刷新当前界面以更新颜色按钮文字颜色

    def update_app_theme(self):
        main_window = self.window()
        if hasattr(main_window, 'update_editor_settings'):
            main_window.update_editor_settings()

    def update_texts(self):
        self.title.setText(translator.get("theme.title"))
        self.theme_label.setText(translator.get("theme.title"))
        self.add_theme_btn.set_text(translator.get("theme.add_theme"))
        # 更新预设按钮文字
        for btn, key in self.preset_buttons:
            btn.set_text(translator.get(key))
        
        # 更新明暗模式文字
        self.mode_title_label.setText(translator.get("theme.mode"))
        self.mode_desc_label.setText(translator.get("theme.mode.description"))
        self.mode_switch.setOnText(translator.get("settings.on"))
        self.mode_switch.setOffText(translator.get("settings.off"))
