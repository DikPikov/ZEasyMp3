import sys, io
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap, QKeySequence, QIcon, QIntValidator, QDesktopServices
from pathlib import Path
from track_cards import ClickableLabel
import os

class FolderCard(QWidget):
    def __init__(self, settings):
        super().__init__()

        self._window = settings
        self._folder = ""
        
        grid = QGridLayout(self)
        self._grid = grid
        
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)
        
        grid.setColumnMinimumWidth(1, 40)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)
        
        grid.setRowMinimumHeight(0, 40)

        self._name = ClickableLabel("")
        self._name.setStyleSheet("""
            QLabel {
                color: #000000;
            }
            QLabel:hover {
                color: blue;
                text-decoration: underline;
            };
            margin: 0px 10px 0px 10px
        """)
        font = self._name.font()
        font.setPointSize(12)
        self._name.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._name.setFont(font)
        self._name.clicked.connect(self.open_folder)

        self._remove_btn = QPushButton()
        self._remove_btn.setIcon(self._window._window.remove_icon)
        self._remove_btn.clicked.connect(self.remove)
        self._remove_btn.setStyleSheet("margin: 0px 5px 0px 5px; padding: 5px 0px 5px 0px;")
        self._remove_btn .setFocusPolicy(Qt.FocusPolicy.NoFocus)
       
        grid.addWidget(self._name, 0 ,0)
        grid.addWidget(self._remove_btn, 0 ,1)

    def set_pause_icon(self, state):
        self.btn_icon_pause = state
        if(state):
            self._play_btn.setIcon(self._window.pause_icon)
        else:
            self._play_btn.setIcon(self._window.resume_icon)
    
    def set_folder(self, folder):
        self._folder = folder
        self._name.setText(folder)
    
    def open_folder(self):
        self._window.open_folder(self._folder)
    
    def remove(self):
        self._window.remove_folder(self._folder)


class SettingsWindow(QMainWindow):
    def __init__(self, main_window):
        super().__init__();
        
        self._folders = []
        self._window = main_window
        self._main = main_window._main
        self._pitch = None
        self._pitch_slider = None
        try:
            self.init_elements()
            self.update_folders()
            self.init_window()
        except Exception as ex:
            print(ex)

    def set_pitch(self, text):

        if(text == ""):
            return
        
        value = int(text) / 100
        self._pitch_slider.setValue(int(value * 1000))
        self._window._main.set_pitch(value)

    def slide_pitch(self):
        value = self._pitch_slider.value()
        self._pitch.setText(str(int(value / 10)))
        self._window._main.set_pitch(value / 1000)
        

    def open_folder(self, folder):
        try:
            url = QUrl.fromLocalFile(folder)

            QDesktopServices.openUrl(url)
        except Exception as ex:
            print(ex)

    def remove_folder(self, folder):
        self._window._main.remove_folder(folder)
        self.update_folders();

    def add_folder(self):
        
        dir_path = QFileDialog.getExistingDirectory(parent=self, caption="Select directory", directory=self._window._main.workdir)
        if(dir_path != "" and dir_path != None):
            self._window._main.add_folder(dir_path)
            self.update_folders();

    def search(self):
        self._window._main.search_tracks()
        
    def full_search(self):
        self._window._main.search_tracks(True)
        self.update_folders();
    
    def init_elements(self):
        root = QWidget()

        grid = QGridLayout()
        
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)

        grid.setRowMinimumHeight(0, 30)
        grid.setRowMinimumHeight(1, 30)
        grid.setRowMinimumHeight(2, 40)
        grid.setRowMinimumHeight(3, 30)
        grid.setRowMinimumHeight(4, 30)
        grid.setRowMinimumHeight(5, 30)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 0)
        grid.setRowStretch(2, 0)
        grid.setRowStretch(3, 0)
        grid.setRowStretch(4, 0)
        grid.setRowStretch(5, 0)
        grid.setRowStretch(6, 1)

        pitch_label = QLabel("Pitch %")
        pitch_label.setStyleSheet("margin: 0px 10px 0px 10px")
        
        pitch = QLineEdit()
        pitch.setStyleSheet("margin: 0px 10px 0px 10px")
        pitch.setValidator(QIntValidator(0, 100))
        pitch.textEdited.connect(self.set_pitch)
        pitch.setText(str(int(self._window._main.pitch * 100)))

        pitch_slider = QSlider(Qt.Orientation.Horizontal)
        pitch_slider.setMinimum(100)
        pitch_slider.setMaximum(2000)
        pitch_slider.setTickInterval(0)
        pitch_slider.sliderMoved.connect(self.slide_pitch)
        pitch_slider.setStyleSheet("""
        QSlider::groove:horizontal {
        background: #ddd;
        height: 6px;
        left: 10px; right: 10px; /* Internal margins for the groove */
        }
        QSlider::handle:horizontal {
            background: #555;
            width: 13px;
            margin: -3px 0; /* Centers handle over the groove */
        }
        """)
        pitch_slider.setValue(int(self._window._main.pitch * 1000))
        
        search_btn = QPushButton("update tracks")
        search_btn.setStyleSheet("margin: 0px 10px 0px 10px; padding: 2px 0px 2px 0px;")
        search_btn.clicked.connect(self.search)
        
        full_search_btn = QPushButton("full scan")
        full_search_btn.setStyleSheet("margin: 0px 10px 0px 10px; padding: 2px 0px 2px 0px;")
        full_search_btn.clicked.connect(self.full_search)
        
        add_folder_btn = QPushButton("add directory")
        add_folder_btn.setStyleSheet("margin: 0px 10px 0px 10px; padding: 2px 0px 2px 0px;")
        add_folder_btn.clicked.connect(self.add_folder)
         
        folder_view = QListWidget()
        folder_view.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        folder_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        folder_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        folder_view.setSpacing(0)

        grid.addWidget(pitch_label, 0, 0)
        grid.addWidget(pitch, 1, 0)
        grid.addWidget(pitch_slider, 2, 0)
        grid.addWidget(search_btn, 3, 0)
        grid.addWidget(full_search_btn, 4, 0)
        grid.addWidget(add_folder_btn, 5, 0)
        grid.addWidget(folder_view, 6, 0)

        self._folder_view = folder_view
        self._pitch = pitch
        self._pitch_slider = pitch_slider
        
        root.setLayout(grid)
        self.setCentralWidget(root)

    def update_folders(self):
        folders = self._window._main.folders
        folders_len = len(folders)
        
        while(len(self._folders) < folders_len):
            new_folder = FolderCard(self)
            self._folders.append(new_folder)

            item = QListWidgetItem()
            size = new_folder.sizeHint()

            item.setSizeHint(size)
            
            self._folder_view.addItem(item)
            self._folder_view.setItemWidget(item, new_folder)

        for i in range(len(self._folders)):
            if(i >= folders_len):
                self._folders[i].hide()
            else:
                self._folders[i].set_folder(folders[i])
                self._folders[i].show()

    def init_window(self):
        self.setMinimumSize(200, 300)
        self.setWindowTitle('settings')
        self.show()
    
    
