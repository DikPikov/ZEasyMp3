import sys
from PyQt6.QtCore import *
from PyQt6.QtMultimedia import *
from PyQt6.QtWidgets import QApplication
from mutagen.mp3 import MP3
from mutagen import File
from os import path
import time

class Mp3Player(QObject):
    track_finished = pyqtSignal()
    track_step = pyqtSignal()
    
    def __init__(self, track, pitch, channel): #channel = [0 seek, 1 playing, 2 length, 3 position, 4 dispose, 5 fileLength, 6 track]
        super().__init__()
        self._channel = channel

        self._track = track
        self._pitch = pitch

        self._mutex = QMutex()
        
        self._pcm = None
        if(self._pcm == None):
            self._pcm = bytearray()
        self._pcm_index = 0

        self._disposed = False;

        self._last_step = time.time()
        
        self._audio_sink = None
        self._audio_device = None
        self._decoder = None

    def run(self):
        self.set_track(self._track)

    def buffer_ready(self):
        try:
            if(self._disposed):
                return
        
            if(self._pcm == None):
                self._pcm = bytearray()
        
            buffer = self._decoder.read()
            if(buffer.isValid()):
                self._pcm.extend(bytes(buffer.constData()))

                if(self._channel[4]):
                    if(self._disposed):
                        return
                    self.dispose()
                    return
            
                if(self._channel[1]):
                    to_write =self._audio_device.bytesToWrite() 
            
                    written = self._audio_device.write(self._pcm[self._pcm_index:self._pcm_index + to_write])
                    self._pcm_index += written

                if(self._channel[0] != -1):
                    self._channel[3] = self._channel[0]
                else:
                    self._channel[3] = self._pcm_index / self._channel[5]

                if(time.time() - self._last_step > 0.15):
                    self._last_step = time.time()
                    self.track_step.emit()
        except Exception as ex:
            print(ex)

    def dispose(self):
        if(self._disposed ):
            return
        
        self._disposed = True;
        self._audio_sink.stop()
        self._audio_sink.deleteLater()

        self._audio_device.close()
                
        self._decoder.stop()
        self._decoder.deleteLater()
        self._pcm = None

        self.thread().quit()
        self.thread().wait()        

    def decode_finish(self):
        if(self._disposed):
            return
        
        written = 1
        
        while self._pcm_index < len(self._pcm):
            if(self._channel[4]):
                if(self._disposed ):
                    return
                
                self.dispose()
                return
            
            if(self._channel[1]):
                to_write =self._audio_device.bytesToWrite() 
            
                written = self._audio_device.write(self._pcm[self._pcm_index:self._pcm_index + to_write])
                self._pcm_index += written
                
            
            self._channel[3] = self._pcm_index / self._channel[5]
            
            while(self._channel[0] != -1):
                self._channel[3] = self._channel[0]
                self._pcm_index = int((self._channel[0] * self._channel[5] // 8) * 8)
                self._channel[0] = -1
                QThread.msleep(200)
            
            self.track_step.emit()
            QThread.msleep(50)
            
            if(self._disposed ):
                return

        self.dispose()
        self.track_finished.emit()

    def set_track(self, track):
        audio = File(track)
        
        a_format = QAudioFormat()
        a_format.setSampleRate(int(audio.info.sample_rate * self._pitch))
        a_format.setChannelCount(audio.info.channels)
        a_format.setSampleFormat(QAudioFormat.SampleFormat.Float)

        self._audio_sink = QAudioSink(a_format)
        self._audio_device = self._audio_sink.start()

        self._decoder = QAudioDecoder()
        self._decoder.setSource(QUrl.fromLocalFile(track))
        self._decoder.bufferReady.connect(self.buffer_ready)
        self._decoder.finished.connect(self.decode_finish)
        
        self._decoder.start()
        self._channel[2] = audio.info.length / self._pitch
        self._channel[1] = True
        self._channel[5] = total_bytes = audio.info.length * audio.info.sample_rate * audio.info.channels * 4
        

