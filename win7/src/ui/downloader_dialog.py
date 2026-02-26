import os
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QWidget
from qfluentwidgets import SubtitleLabel, BodyLabel, ComboBox, LineEdit, ProgressBar, MessageBoxBase, ToolButton, FluentIcon
from src.core.downloader import PythonDownloader, DownloadWorker
from src.core.translator import translator
from src.config import config

class DownloaderDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(translator.get("downloader.title", "Download Python SDK"), self)
        
        # 中心布局内容
        self.viewLayout.addWidget(self.titleLabel)
        
        # 版本部分
        self.version_label = BodyLabel(translator.get("downloader.version", "Version"), self)
        self.viewLayout.addWidget(self.version_label)
        
        self.version_combo = ComboBox(self)
        self.viewLayout.addWidget(self.version_combo)
        
        # 位置部分
        self.location_label = BodyLabel(translator.get("downloader.location", "Location"), self)
        self.viewLayout.addWidget(self.location_label)
        
        self.location_layout = QHBoxLayout()
        
        self.location_edit = LineEdit(self)
        self.location_edit.setReadOnly(True)
        self.location_layout.addWidget(self.location_edit)
        
        self.btn_browse = ToolButton(FluentIcon.FOLDER, self)
        self.btn_browse.clicked.connect(self.browse_location)
        self.location_layout.addWidget(self.btn_browse)
        
        self.location_container = QWidget()
        self.location_container.setLayout(self.location_layout)
        self.location_layout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.addWidget(self.location_container)
        
        # 进度条（默认隐藏）
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.viewLayout.addWidget(self.progress_bar)
        
        self.status_label = BodyLabel("", self)
        self.status_label.setTextColor("#666666", "#aaaaaa")
        self.status_label.hide()
        self.viewLayout.addWidget(self.status_label)
        
        # 按钮
        self.yesButton.setText(translator.get("downloader.install", "Install"))
        self.cancelButton.setText(translator.get("cancel", "Cancel"))
        
        self.widget.setMinimumWidth(500)
        
        # 连接
        self.yesButton.clicked.disconnect() # 断开默认连接
        self.yesButton.clicked.connect(self.start_download)
        self.version_combo.currentIndexChanged.connect(self.update_location)
        
        self.worker = None
        
        self.populate_versions()

    def populate_versions(self):
        versions = PythonDownloader.get_available_versions()
        for ver in versions.keys():
            self.version_combo.addItem(f"Python {ver}", ver)
            
        if self.version_combo.count() > 0:
            self.version_combo.setCurrentIndex(0)
            # 默认位置
            self.custom_location = None
            self.update_location()

    def browse_location(self):
        try:
            directory = QFileDialog.getExistingDirectory(self, translator.get("downloader.select_dir", "Select Install Location"), os.getcwd())
            if directory:
                # 规范化路径分隔符
                directory = os.path.normpath(directory)
                self.custom_location = directory
                print(f"DEBUG: Selected directory: {directory}")
                self.update_location()
            else:
                print("DEBUG: No directory selected")
        except Exception as e:
            print(f"DEBUG: Error in browse_location: {e}")

    def update_location(self):
        try:
            version = self.version_combo.currentData()
            # 后备方案：如果数据丢失（似乎发生在某些 ComboBox 版本中）
            if not version:
                text = self.version_combo.currentText()
                if text and "Python" in text:
                    version = text.split(" ")[1]
                    print(f"DEBUG: Recovered version from text: {version}")
            
            print(f"DEBUG: Current version data: {version}")
            
            if version:
                if hasattr(self, 'custom_location') and self.custom_location:
                    base_dir = self.custom_location
                else:
                    base_dir = os.path.join(os.getcwd(), 'runtime')
                    
                install_path = os.path.join(base_dir, f"python-{version}")
                install_path = os.path.normpath(install_path)
                print(f"DEBUG: Setting location text to: {install_path}")
                
                self.location_edit.setText(install_path)
                self.location_edit.setCursorPosition(0)
                self.location_edit.repaint() # 强制重绘
        except Exception as e:
            print(f"DEBUG: Error in update_location: {e}")

    def start_download(self):
        version = self.version_combo.currentData()
        # 后备方案
        if not version:
            text = self.version_combo.currentText()
            if text and "Python" in text:
                version = text.split(" ")[1]

        if not version:
            return
            
        versions = PythonDownloader.get_available_versions()
        url = versions.get(version)
        
        if not url:
            return

        # UI 状态
        self.version_combo.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.yesButton.setEnabled(False)
        self.cancelButton.setEnabled(False)
        self.progress_bar.show()
        self.status_label.show()
        self.status_label.setText(translator.get("downloader.downloading", "Downloading Python {}...").format(version))
        
        # 启动工作线程
        target_dir = os.path.dirname(self.location_edit.text())
        
        self.worker = DownloadWorker(version, url, target_dir)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.download_finished)
        self.worker.error.connect(self.download_error)
        self.worker.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        if value == 100:
            self.status_label.setText(translator.get("downloader.extracting", "Extracting files..."))

    def download_finished(self, python_path):
        self.status_label.setText(translator.get("downloader.done", "Done!"))
        self.progress_bar.hide()
        
        # 配置
        config.set('interpreter', python_path)
        
        # 直接接受，不再弹窗
        self.accept()

    def download_error(self, error_msg):
        self.status_label.setText(f"{translator.get('error', 'Error')}: {error_msg}")
        self.progress_bar.hide()
        self.version_combo.setEnabled(True)
        self.btn_browse.setEnabled(True)
        self.yesButton.setEnabled(True)
        self.cancelButton.setEnabled(True)

    def reject(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        super().reject()
