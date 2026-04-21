import sys, io
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from pathlib import Path

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, text):
        super().__init__(text)
        self.rmb_clicked = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)  # 👈 Палец
        self.setStyleSheet("""
            QLabel {
                color: #000000;
            }
            QLabel:hover {
                color: blue;
                text-decoration: underline;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.rmb_clicked()
            
        super().mousePressEvent(event)


class TrackCard(QWidget):
    def __init__(self, window):
        super().__init__()

        self._window = window
        self._track = ""
        self.btn_icon_pause = False
        
        grid = QGridLayout(self)
        self._grid = grid
        
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)
        
        grid.setColumnMinimumWidth(0, 40)
        grid.setColumnMinimumWidth(1, 40)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        
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
            margin: 0px 0px 0px 10px
        """)
        font = self._name.font()
        font.setPointSize(12)
        self._name.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._name.setFont(font)
        self._name.clicked.connect(self.enqueue)
        self._name.rmb_clicked = self.show_options

        self._play_btn = QPushButton()
        self._play_btn.setIcon(self._window.resume_icon)
        self._play_btn.clicked.connect(self.play)
        self._play_btn.setStyleSheet("margin: 0px 5px 0px 5px; padding: 5px 0px 5px 0px;")
        self._play_btn .setFocusPolicy(Qt.FocusPolicy.NoFocus)
       
        self._enqueue_btn = QPushButton()
        self._enqueue_btn.setIcon(self._window.add_icon)
        self._enqueue_btn.clicked.connect(self.enqueue)
        self._enqueue_btn.setStyleSheet("margin: 0px 5px 0px 5px; padding: 5px 0px 5px 0px;")
        self._enqueue_btn .setFocusPolicy(Qt.FocusPolicy.NoFocus)

        grid.addWidget(self._play_btn, 0 ,0)
        grid.addWidget(self._enqueue_btn, 0 ,1)
        grid.addWidget(self._name, 0 ,2)

    @property
    def track(self):
        return self._track

    def set_pause_icon(self, state):
        self.btn_icon_pause = state
        if(state):
            self._play_btn.setIcon(self._window.pause_icon)
        else:
            self._play_btn.setIcon(self._window.resume_icon)
    
    def set_track(self, track):
        self._track = track
        self._name.setText(Path(track).stem)
    
    def play(self):
        self._window.play(self._track)
    
    def enqueue(self):
        self._window.enqueue(self._track)
    
    def show_options(self):
        self._window.options(self._track)


class QueueTrackCard(QWidget):
    def __init__(self, window):
        super().__init__()

        self._window = window
        self._track = ""
        self._queue_id = -1
        self.btn_icon_pause = False
        
        grid = QGridLayout(self)
        self._grid = grid
        
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)
        
        grid.setColumnMinimumWidth(0, 40)
        grid.setColumnMinimumWidth(1, 40)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)
        
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
            margin: 0px 0px 0px 10px
        """)
        font = self._name.font()
        font.setPointSize(12)
        self._name.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._name.setFont(font)
        self._name.rmb_clicked = self.show_options

        self._play_btn = QPushButton()
        self._play_btn.setIcon(self._window.resume_icon)
        self._play_btn.clicked.connect(self.play)
        self._play_btn.setStyleSheet("margin: 0px 5px 0px 5px; padding: 5px 0px 5px 0px;")
        self._play_btn .setFocusPolicy(Qt.FocusPolicy.NoFocus)
       
        self._remove_btn = QPushButton()
        self._remove_btn.setIcon(self._window.remove_icon)
        self._remove_btn.clicked.connect(self.remove)
        self._remove_btn.setStyleSheet("margin: 0px 5px 0px 5px; padding: 5px 0px 5px 0px;")
        self._remove_btn .setFocusPolicy(Qt.FocusPolicy.NoFocus)

        grid.addWidget(self._play_btn, 0 ,0)
        grid.addWidget(self._remove_btn, 0 ,1)
        grid.addWidget(self._name, 0 ,2)

    @property
    def track(self):
        return self._track

    @property
    def order_id(self):
        return self._queue_id
    
    def set_pause_icon(self, state):
        self.btn_icon_pause = state
        if(state):
            self._play_btn.setIcon(self._window.pause_icon)
        else:
            self._play_btn.setIcon(self._window.resume_icon)
    
    def set_track(self, track, queue_id):
        self._track = track
        self._name.setText(Path(track).stem)
        self._queue_id = queue_id
    
    def play(self):
        self._window.play_order(self._queue_id)
    
    def remove(self):
        self._window.dequeue(self._queue_id)
    
    def show_options(self):
        self._window.options(self._track)
