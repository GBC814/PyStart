from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import EditableComboBox, SubtitleLabel, CaptionLabel, CardWidget
from src.config import config
from src.core.translator import translator

class FontSettingsInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("fontSettingsInterface")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        self.title = SubtitleLabel(translator.get("font_settings.title", "Font Settings"), self)
        self.layout.addWidget(self.title)

        self.card = CardWidget(self)
        self.card_layout = QVBoxLayout(self.card)

        self.size_row = QHBoxLayout()
        self.size_label = CaptionLabel(translator.get("font_settings.size", "Font Size"), self)
        
        self.size_combo = EditableComboBox(self)
        # 添加常用字体大小
        sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        for size in sizes:
            self.size_combo.addItem(str(size))
            
        current_size = config.get('font_size', 12)
        self.size_combo.setText(str(current_size))
        
        # 如果当前值不在列表中，确保显示正确
        if str(current_size) not in [str(s) for s in sizes]:
             self.size_combo.setCurrentText(str(current_size))
        
        self.size_combo.textChanged.connect(self.on_size_changed)

        self.size_row.addWidget(self.size_label)
        self.size_row.addStretch(1)
        self.size_row.addWidget(self.size_combo)

        self.card_layout.addLayout(self.size_row)
        self.layout.addWidget(self.card)
        
        self.layout.addStretch(1)

        translator.languageChanged.connect(self.update_texts)

    def update_texts(self):
        self.title.setText(translator.get("font_settings.title", "Font Settings"))
        self.size_label.setText(translator.get("font_settings.size", "Font Size"))

    def on_size_changed(self, text):
        try:
            value = int(text)
            if 8 <= value <= 72:
                config.set('font_size', value)
                if self.window() and hasattr(self.window(), 'update_editor_settings'):
                    self.window().update_editor_settings()
        except ValueError:
            pass # 忽略非数字输入
