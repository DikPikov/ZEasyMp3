import sys, os, io
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QMessageBox, QApplication
from PyQt6.QtGui import QIcon, QFont
from gui import MainWindow
from mp3_player import Mp3Player
from glob import glob
from PyQt6.QtCore import QThread
import time
import sqlite3
from random import shuffle
from localization import Localization

class MainProgram():
    def __init__(self):
        self.tracks = []
        self.volume = 1
        self.pitch = 1
        self.language = "english"
        self.folders = []
        self.workdir = os.getcwd()
        self._window = None

        self._repeat = False
        
        self._channel = None

        self._threads = []
        self._increment_id = 0
        self._track_order = []
        self._track_index = 0
        self._player_thread = None
        self._mp3_player = None
        
        self.load_config()
            
        self.search_tracks()

        self.localization = Localization(self.language)
        self.init_window()

    @property
    def orders(self):
        return self._track_order
    @property
    def order_id(self):
        if(len(self._track_order) <= self._track_index):
            return -1
        return self._track_order[self._track_index][0]
    @property
    def current_track(self):
        if(self._channel == None or len(self._track_order) <= self._track_index):
            return None
        return self._track_order[self._track_index]
    @property
    def paused(self):
        
        if(self._channel == None):
            return True
        return not self._channel[1]
    
    def load_config(self):
        try:
            path = Path(f"{self.workdir}/config.txt")
            if(not path.is_file()):
                return
        
            f = open("config.txt", "r")

            folders = False
            for line in f:
                l = line.replace('\n', '')
                if(l == "folders:"):
                    folders = True
                elif(folders):
                    self.folders.append(l)
                else:
                    tokens = l.split("=")
                    if(len(tokens) == 2):
                        if(tokens[0] == "pitch"):
                            self.pitch = float(tokens[1])
                        elif(tokens[0] == "volume"):
                            self.volume = float(tokens[1])
                        elif(tokens[0] == "language"):
                            self.language = tokens[1]
                    pass
        except Exception as ex:
            print (ex)
            

    def save_config(self):
        f = open("config.txt", "w")
        f.write(f"volume={self.volume}\n")
        f.write(f"pitch={self.pitch}\n")
        f.write(f"language={self.language}\n")
        f.write("folders:")
        for folder in self.folders:
            f.write(f"\n{folder}");
        f.flush()
        f.close()

    def search_tracks(self, fully = False):
        tracks = []
        unique_dirs = []
        skip_patterns = ['System Volume Information', '$Recycle.Bin', 'Windows', 'Program Files']
        if(fully):
            print("search for music directories")
            for drive in Path('/').iterdir():
                if not (drive.is_dir() and os.path.exists(drive)):
                    continue
                
                for file in drive.glob("**/*.mp3"):
                    if(file.stat().st_size < 512000):
                        continue
                    if any(skip_pattern in str(file).lower() for skip_pattern in skip_patterns):
                        continue
                    
                    tracks.append(str(file))
                    print(str(file))
                    
                    directory = str(file.parent)
                    if not unique_dirs or unique_dirs[-1] != directory:
                        unique_dirs.append(directory)
    
            self.tracks = tracks
            self.folders = unique_dirs
            self.save_config()
        else:
            for directory in self.folders:
                dir_ref = Path(directory)
                for file in dir_ref.glob("*.mp3"):
                    if any(skip_pattern in str(file).lower() for skip_pattern in skip_patterns):
                        continue
                    
                    tracks.append(str(file))
            self.tracks = tracks
        if(self._window != None):
            self._window.update_tracklist()

    def shuffle_order(self):
        if(len(self._track_order) == 0):
            return

        if(len(self._track_order) <= self._track_index):
            self._track_index = 0

       
        queue_id = self._track_order[self._track_index][0]
        
        shuffle(self._track_order)
        ind = 0
        for index, track in enumerate(self._track_order):
            if(track[0] == queue_id):
                tr = track[0]
                ind = index

        self._track_order[ind], self._track_order[0] = self._track_order[0], self._track_order[ind]
        self._track_index = 0
        
        if(self._mp3_player == None):
            self.play_by_id(queue_id)

    def set_pitch(self, value):
        if(value < 0.1):
            value = 0.1
        elif(value > 2):
            value = 2

        self.pitch = value
        self.save_config()

    def set_volume(self, value):
        if(value < 0):
            value = 0
        elif(value > 1):
            value = 1

        self.volume = value
        self.save_config()

        if(self._mp3_player != None):
            self._channel[6] = self.volume

    def set_repeat(self):
        self._repeat = not self._repeat
    
    def add_folder(self, folder):
        self.folders.append(folder)
        self.save_config()
        self.search_tracks()

    def remove_folder(self, folder):
       
        self.folders.remove(folder)
        self.save_config()
        self.search_tracks()

    def track_step(self):
        self._window.track_step(self._channel)

    def track_finished(self):
        self._mp3_player.dispose()
        self._mp3_player = None
        
        self._track_index += 1
        if(len(self._track_order) > self._track_index):
            self.play(self._track_order[self._track_index][1])
        elif(self._repeat and len(self._track_order) > 0):
            self._track_index = 0;
            self.play(self._track_order[self._track_index][1])
        else:
            self._window.check_pause()

    def enqueue(self, track):
        self._track_order.append((self._increment_id, track))
        self._increment_id += 1
        if(self._mp3_player == None):
            self._track_index = len(self._track_order) - 1
            self.play(self._track_order[self._track_index][1])

    def dequeue(self, queue_id):
        tr = None
        ind = 0
        for index, track in enumerate(self._track_order):
            if(track[0] == queue_id):
                tr = track[0]
                ind = index
        if(tr != None):
            self._track_order.pop(ind)
            if(self._track_index == ind):
                self._track_index -= 1
                self.track_finished()

    def enqueue_single(self, track):
        if(self._mp3_player != None and self._channel[5] == track):
            entry = self._track_order[self._track_index]
            self._increment_id = entry[0] + 1
            self._track_order.clear()
            self._track_order.append(entry)
            self._track_index = 0

            self.pause()
            return
            
        self._increment_id = 0
        self._track_order.clear()
        
        if(self._mp3_player != None):
            self._mp3_player.dispose()
            self._mp3_player = None
            
        self.enqueue(track)

    def next_track(self):
        if(self._track_index + 1 >= len(self._track_order)):
            if(self._repeat):
                self._track_index = -1
            else:
                return
        
        self.track_finished()
    
    def previos_track(self):
        if(self._track_index - 1 < 0):
            return
        
        self._track_index -= 2
        self.track_finished()
    
    def play_by_id(self, order_id):
        ind = 0
        for index, track in enumerate(self._track_order):
            if(track[0] == order_id):
                tr = track[0]
                ind = index
                
        if(self._track_index == ind):
            self.pause()
            return
        
        self._track_index = ind
        self.play(self._track_order[ind][1])
        
    def play_all(self):
        self._increment_id = 0
        self._track_order.clear()
        
        if(self._mp3_player != None):
            self._mp3_player.dispose()
            self._mp3_player = None
            
        for x in self.tracks:
            self.enqueue(x)
    
    def play(self, track):
        
        self._window.track_changed(track)

        if(self._mp3_player != None):
            self._mp3_player.dispose()
                
        self._channel = [-1, True, 0, 0, 0, track, self.volume]
        self._current_track = track
            
        self._threads.append(QThread())
        self._mp3_player = Mp3Player(track, self.pitch, self._channel)
        self._mp3_player.moveToThread(self._threads[-1])
        self._mp3_player.track_step.connect(self.track_step)
        self._mp3_player.track_finished.connect(self.track_finished)
        self._threads[-1].started.connect(self._mp3_player.run)
        self._threads[-1].start()
        
        self._window.check_pause()
        for x in self._threads:
            if(not x.isRunning()):
                self._threads.remove(x)

    def track_seek(self, position):
        if(len(self._track_order) == 0):
            if(self._channel != None and self._mp3_player == None):
                self.enqueue_single(self._channel[5]);
                self._window.update_queue()
            return
        
        if(self._mp3_player == None):
            self._track_index = len(self._track_order) - 1
            self.play(self._track_order[self._track_index][1])
            return
            
        self._channel[0] = position
        
    def pause(self):
        if(len(self._track_order) == 0):
            if(self._channel != None and self._mp3_player == None):
                self.enqueue_single(self._channel[5]);
                self._window.update_queue()
            return
        
        if(self._mp3_player == None):
            self._track_index = len(self._track_order) - 1
            self.play(self._track_order[self._track_index][1])
            return
        
        self._channel[1] = not self._channel[1]
        self._window.check_pause()
    
    def init_window(self):
        app = QApplication(sys.argv)
        app.setFont(QFont("Times New Roman", 10))
        app.setWindowIcon(QIcon('main.ico'))
        self._window = MainWindow(self)
        sys.exit(app.exec())

if __name__ == "__main__":
    main = MainProgram()
