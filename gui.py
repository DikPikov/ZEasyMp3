import sys, io
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QKeySequence, QIcon
from pathlib import Path
from track_cards import TrackCard, QueueTrackCard, ClickableLabel
from settings_window import SettingsWindow

def match(text, search):
    if len(search) <= 0:
        return 0
    elif len(text) <= 0:
        return -len(search) * 5
    
    search = search.lower()
    text = text.lower()
    
    mismatch = 0
    symbol = 0
    distance = 0
    
    for i in range(len(text)):
        matched = False
        for ii in range(3):
            if symbol + ii < len(search) and text[i] == search[symbol + ii]:
                mismatch += distance + ii
                distance = 0
                mismatch -= 10
                
                symbol += 1
                
                if symbol >= len(search):
                    if i + 1 < len(text):
                        mismatch += 1
                    break
                
                matched = True
                break
        
        if not matched:
            distance += 1
    
    mismatch += max(0, len(search) - symbol) * 5
    
    return -mismatch


class MainWindow(QMainWindow):
    def __init__(self, main_program):
        super().__init__();

        self._initialized = False;
        
        self._main = main_program
        
        self.make_window();

        self.resume_icon = QIcon("resume_btn.png")
        self.pause_icon = QIcon("pause_btn.png")
        self.add_icon = QIcon("add_btn.png")
        self.remove_icon = QIcon("remove_btn.png")
        self.repeat_icon = QIcon("repeat.png")
        self.no_repeat_icon = QIcon("no_repeat.png")
        self.shuffle_icon = QIcon("shuffle.png")
        self.next_icon = QIcon("next.png")
        self.prev_icon = QIcon("prev.png")

        self.locale = main_program.localization
        
        self._root_grid = None
        self._repeat_btn = None
        self._shuffle_btn = None
        self._main_track_duraction = None
        self._main_track_slider = None
        self._main_play_btn = None
        self._settings = None
        self.load_main_elements()

        self._search = ""
        self._tracks = []
        self._tracklist_page = None
        self._track_view = None
        self.load_tracklist_page()

        self._queues = []
        self._queue_page = None
        self._queue_view = None
        self.load_queue_page()

        self.set_tracklist_page()
        
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self._initialized = True;

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.escape()
        elif event.key() == Qt.Key.Key_Space:
            self._main.pause()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        if(self._settings != None):
            self._settings.close()
        event.accept()

    def resizeEvent(self, event):
        if(not self._initialized):
            super().resizeEvent(event)
            return
        self.update_tracklist()
        self.update_queue()
        super().resizeEvent(event)

    def escape(self):
        if(self._tracklist_page.isHidden()):
            self.set_tracklist_page()
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle(self.locale.string["Quitting"])
            dlg.setText(self.locale.string["Quit_sure"])
            dlg.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            dlg.setIcon(QMessageBox.Icon.Question)
            button = dlg.exec()

            if button == QMessageBox.StandardButton.Yes:
                self.close()
                
    def track_changed(self, track):
        self._main_track_name.setText(Path(track).stem)
        self.check_pause()
          
    def track_step(self, channel):
        self._main_track_duraction.setText(f"{int(channel[2] * channel[3])}/{int(channel[2])}")
        self._main_track_slider.setValue(int(channel[3] * 1000))
        
    def pause(self):
        self._main.pause()
        
    def check_pause(self):
        state = self._main.paused
        current_track = self._main.current_track
        if(not state and current_track != None):
            self._main_play_btn.setIcon(self.pause_icon)
            
            current_track = current_track[1]
                
            order_id = self._main.order_id

            for card in self._queues:
                if(card.order_id == order_id):
                    if(not card.btn_icon_pause):
                        card.set_pause_icon(True)
                else:
                    if(card.btn_icon_pause):
                        card.set_pause_icon(False)
            
            for card in self._tracks:
                if(card.track == current_track):
                    if(not card.btn_icon_pause):
                        card.set_pause_icon(True)
                else:
                    if(card.btn_icon_pause):
                        card.set_pause_icon(False)
        else:
            self._main_play_btn.setIcon(self.resume_icon)
            for card in self._tracks:
                if(card.btn_icon_pause):
                    card.set_pause_icon(False)
                    
            for card in self._queues:
                if(card.btn_icon_pause):
                    card.set_pause_icon(False)


    def track_seek(self):
        self._main.track_seek(self._main_track_slider.value() / 1000)

    def open_settings(self):
        if(self._settings == None):
            self._settings = SettingsWindow(self)
        else:
            if(not self._settings.isVisible()):
                self._settings.show()
                self._settings.update_folders()
            else:
                self._settings.hide()

    def play_all_tracklist(self):
        self._main.play_all()
        self.update_queue()
    
    def set_repeat(self):
        self._main.set_repeat()
        if(self._main._repeat):
            self._repeat_btn.setIcon(self.repeat_icon)
        else:
            self._repeat_btn.setIcon(self.no_repeat_icon)

    def shuffle(self):
        self._main.shuffle_order()
        self.update_queue()

    def next_track(self):
        self._main.next_track()
    
    def prev_track(self):
        self._main.previos_track()
        
    def load_main_elements(self):
        root = QWidget()

        grid = QGridLayout()
        
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)

        grid.setRowMinimumHeight(0, 40)
        grid.setRowMinimumHeight(2, 40)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 0)

        top_bar = QGridLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(0)

        top_bar.setColumnMinimumWidth(0, 80);
        top_bar.setColumnMinimumWidth(2, 100);
        top_bar.setColumnMinimumWidth(3, 80);
        top_bar.setColumnMinimumWidth(4, 80);
        top_bar.setColumnStretch(0, 0)
        top_bar.setColumnStretch(1, 1)
        top_bar.setColumnStretch(2, 0)
        top_bar.setColumnStretch(3, 0)
        top_bar.setColumnStretch(4, 0)

        config_btn = QPushButton(self.locale.string["config"])
        config_btn.setStyleSheet("margin: 0px 0px 0px 10px; padding: 5px 0px 5px 0px;")
        config_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        config_btn.clicked.connect(self.open_settings)

        play_tracklist_btn = QPushButton(self.locale.string["play_all"])
        play_tracklist_btn.setStyleSheet("margin: 0px 0px 0px 10px; padding: 5px 0px 5px 0px;")
        play_tracklist_btn.clicked.connect(self.play_all_tracklist)
        play_tracklist_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        tracklist_btn = QPushButton(self.locale.string["tracks"])
        tracklist_btn.setStyleSheet("margin: 0px 0px 0px 10px; padding: 5px 0px 5px 0px;")
        tracklist_btn.clicked.connect(self.set_tracklist_page)
        tracklist_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        queue_btn = QPushButton(self.locale.string["queue"])
        queue_btn.setStyleSheet("margin: 0px 10px 0px 10px; padding: 5px 0px 5px 0px;")
        queue_btn.clicked.connect(self.set_queue_page)
        queue_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        top_bar.addWidget(config_btn, 0, 0)
        top_bar.addWidget(play_tracklist_btn, 0, 2)
        top_bar.addWidget(tracklist_btn, 0, 3)
        top_bar.addWidget(queue_btn, 0, 4)

        bottom_bar = QGridLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        bottom_bar.setSpacing(0)

        bottom_bar.setColumnMinimumWidth(0, 40);
        bottom_bar.setColumnMinimumWidth(1, 40);
        bottom_bar.setColumnMinimumWidth(2, 40);
        bottom_bar.setColumnMinimumWidth(3, 60);
        bottom_bar.setColumnMinimumWidth(6, 40);
        bottom_bar.setColumnMinimumWidth(7, 40);
        bottom_bar.setColumnStretch(0, 0)
        bottom_bar.setColumnStretch(1, 0)
        bottom_bar.setColumnStretch(2, 0)
        bottom_bar.setColumnStretch(3, 1)
        bottom_bar.setColumnStretch(4, 1)
        bottom_bar.setColumnStretch(5, 0)
        bottom_bar.setColumnStretch(6, 0)
        bottom_bar.setColumnStretch(7, 0)

        bottom_bar.setRowMinimumHeight(0, 12)
        bottom_bar.setRowStretch(0, 0)
        bottom_bar.setRowStretch(1, 1)

        main_play_btn = QPushButton()
        main_play_btn.setIcon(self.resume_icon)
        main_play_btn.setStyleSheet("margin: 0px 0px 0px 10px; padding: 5px 0px 5px 0px;")
        main_play_btn.clicked.connect(self.pause)
        main_play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        repeat_btn = QPushButton()
        repeat_btn.setIcon(self.no_repeat_icon)
        repeat_btn.setStyleSheet("margin: 0px 0px 0px 10px; padding: 5px 0px 5px 0px;")
        repeat_btn.clicked.connect(self.set_repeat)
        repeat_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        shuffle_btn = QPushButton()
        shuffle_btn.setIcon(self.shuffle_icon)
        shuffle_btn.setStyleSheet("margin: 0px 0px 0px 10px; padding: 5px 0px 5px 0px;")
        shuffle_btn.clicked.connect(self.shuffle)
        shuffle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        
        main_track_name = QLabel(self.locale.string["need_folders"] if len(self._main.folders) == 0 else "")
        main_track_name.setStyleSheet("margin: 0px 0px 0px 10px; padding: 2px 0px 2px 0px")
        font = main_track_name.font()
        font.setPointSize(12)
        main_track_name.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        main_track_name.setFont(font)

        main_track_duraction = QLabel("0/0")
        main_track_duraction.setStyleSheet("margin: 0px 10px 0px 0px; padding: 2px 0px 2px 0px")
        font = main_track_name.font()
        font.setPointSize(12)
        main_track_duraction.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        main_track_duraction.setFont(font)


        main_track_slider = QSlider(Qt.Orientation.Horizontal)
        main_track_slider.setMinimum(0)
        main_track_slider.setMaximum(1000)
        main_track_slider.setTickInterval(0)
        main_track_slider.sliderMoved.connect(self.track_seek)
        main_track_slider.setStyleSheet("""
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

        
        next_btn = QPushButton()
        next_btn.setIcon(self.next_icon)
        next_btn.setStyleSheet("margin: 0px 10px 0px 0px; padding: 5px 0px 5px 0px;")
        next_btn.clicked.connect(self.next_track)
        next_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        
        prev_btn = QPushButton()
        prev_btn.setIcon(self.prev_icon)
        prev_btn.setStyleSheet("margin: 0px 10px 0px 0px; padding: 5px 0px 5px 0px;")
        prev_btn.clicked.connect(self.prev_track)
        prev_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        bottom_bar.addWidget(main_play_btn, 0, 0, 2, 1)
        bottom_bar.addWidget(repeat_btn, 0, 1, 2, 1)
        bottom_bar.addWidget(shuffle_btn, 0, 2, 2, 1)
        bottom_bar.addWidget(main_track_name, 0, 3)
        bottom_bar.addWidget(main_track_duraction, 0, 5)
        bottom_bar.addWidget(main_track_slider, 1, 3, 1, 3)
        bottom_bar.addWidget(prev_btn, 0, 6, 2, 1)
        bottom_bar.addWidget(next_btn, 0, 7, 2, 1)
        
        grid.addLayout(bottom_bar, 2, 0, 1, 2)
        grid.addLayout(top_bar, 0, 0, 1, 2)

        self._repeat_btn = repeat_btn
        self._shuffle_btn = shuffle_btn
        self._main_track_name = main_track_name
        self._main_track_duraction = main_track_duraction
        self._main_track_slider = main_track_slider
        self._main_play_btn = main_play_btn
        self._root_grid = grid
        
        root.setLayout(grid)
        self.setCentralWidget(root)

    def play_order(self, order_id):
        self._main.play_by_id(order_id)
        
    def play(self, track):
        self._main.enqueue_single(track)
        self.update_queue()

    def enqueue(self, track):
        self._main.enqueue(track)
        self.update_queue()

    def dequeue(self, queue_id):
        self._main.dequeue(queue_id)
        self.update_queue()

    def options(self, track):
        print(track)

    def search(self, text):
        try:
            self._search = text
            self.update_tracklist()
        except Exception as ex:
            print("ss", ex)
    
    def load_tracklist_page(self):
        tracklist = QWidget()
        grid = QGridLayout(tracklist)
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)

        grid.setRowMinimumHeight(0, 30)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)

        search = QLineEdit()
        search.setStyleSheet("margin: 0px 10px 0 10px")
        search.setPlaceholderText(self.locale.string["search"])
        search.setMaxLength(24)
        search.textEdited.connect(self.search)
        
        track_view = QListWidget()
        track_view.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        track_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        track_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        track_view.setSpacing(0)

        grid.addWidget(search, 0, 0)
        grid.addWidget(track_view, 1, 0)

        self._tracklist_page = tracklist
        self._track_view = track_view
        self._root_grid.addWidget(self._tracklist_page, 1, 0)
        self._tracklist_page.hide()

    def load_queue_page(self):
        queue = QWidget()
        grid = QGridLayout(queue)
        grid.setContentsMargins(0,0,0,0)
        grid.setSpacing(0)

        queue_view = QListWidget()
        queue_view.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        queue_view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        queue_view.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        queue_view.setSpacing(0)

        grid.addWidget(queue_view, 0, 0)

        self._queue_page = queue
        self._queue_view = queue_view
        self._root_grid.addWidget(self._queue_page, 1, 0)
        self._tracklist_page.hide()

    def set_tracklist_page(self):
        try:
            self._tracklist_page.show()
            self._queue_page.hide()
            self.update_tracklist()
        except Exception as ex:
            print(ex)

    def set_queue_page(self):
        try:
            self._tracklist_page.hide()
            self._queue_page.show()
            self.update_queue()
        except Exception as ex:
            print(ex)

    def update_tracklist(self):
        tracks = self._main.tracks
        track_len = len(tracks)
        
        if(self._search != ""):
            tracks = sorted(tracks, key=lambda f: match(Path(f).stem, self._search), reverse=True)
        
        while(len(self._tracks) < track_len):
            new_track = TrackCard(self)
            self._tracks.append(new_track)

            item = QListWidgetItem()
            size = new_track.sizeHint()

            item.setSizeHint(size)
            
            self._track_view.addItem(item)
            self._track_view.setItemWidget(item, new_track)

        for i in range(len(self._tracks)):
            if(i >= track_len):
                self._tracks[i].hide()
            else:
                self._tracks[i].set_track(tracks[i])
                self._tracks[i].show()
        self.check_pause()

    def update_queue(self):
        queues = self._main.orders
        queues_len = len(queues)

        while(len(self._queues) < queues_len):
            new_track = QueueTrackCard(self)
            self._queues.append(new_track)

            item = QListWidgetItem()
            size = new_track.sizeHint()

            item.setSizeHint(size)
            
            self._queue_view.addItem(item)
            self._queue_view.setItemWidget(item, new_track)

        for i in range(len(self._queues)):
            if(i >= queues_len):
                self._queues[i].hide()
            else:
                self._queues[i].set_track(queues[i][1], queues[i][0])
                self._queues[i].show()
        self.check_pause()
    
    def make_window(self):
        self.setMinimumSize(400, 300)
        self.setWindowTitle('ZEasyMp3')
        self.show()
