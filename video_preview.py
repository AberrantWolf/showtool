import platform

from PyQt6.QtCore import QObject, QSettings
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QDoubleSpinBox

import vlc


class VideoPreview(QWidget):
    # TODO: on shutdown, shutdown VLC stuff cleanly to prevent errors getting logged

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        settings = QSettings()

        v_layout = QVBoxLayout(self)

        self.media = None
        self.mediaPlayer = vlc.MediaPlayer()
        self.media_event_manager: vlc.EventManager = self.mediaPlayer.event_manager()
        self.media_event_manager.event_attach(vlc.EventType.MediaPlayerPositionChanged, self.pause_video)

        self.videoWidget = QFrame()
        self.videoWidget.setMinimumSize(400, 300)
        self.palette = self.videoWidget.palette()
        self.palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        self.videoWidget.setPalette(self.palette)
        self.videoWidget.setAutoFillBackground(True)

        timecode_layout = QHBoxLayout(self)
        timecode_layout.addWidget(QLabel("Jump to (timecode):"))
        self.timecode_field = QDoubleSpinBox()
        self.timecode_field.setValue(settings.value("lasttimecode", 0, int))
        self.timecode_field.setMinimum(0.0)
        self.timecode_field.setSuffix(" sec")
        self.timecode_field.setSingleStep(1.0)
        self.timecode_field.valueChanged.connect(self.set_timecode)
        timecode_layout.addWidget(self.timecode_field)

        v_layout.addWidget(QLabel("Video Preview"), 0)
        v_layout.addLayout(timecode_layout, 0)
        v_layout.addWidget(self.videoWidget, 1)
        self.setLayout(v_layout)

    def pause_video(self, _):
        self.mediaPlayer.set_pause(True)

    def change_current_video(self, filename: str):
        # NOTE: Changing the video too quickly seems to cause errors to log from VLC,
        # but it doesn't seem to cause long-term problems.
        self.media = vlc.Media(filename)
        self.mediaPlayer.set_media(self.media)
        self.media.parse()

        if platform.system() == "Linux":  # for Linux using the X Server
            self.mediaPlayer.set_xwindow(int(self.videoWidget.winId()))
        elif platform.system() == "Windows":  # for Windows
            self.mediaPlayer.set_hwnd(int(self.videoWidget.winId()))
        elif platform.system() == "Darwin":  # for MacOS
            self.mediaPlayer.set_nsobject(int(self.videoWidget.winId()))

        self.set_timecode(-1)

    def set_timecode(self, value):
        if value < 0:
            value = self.timecode_field.value()
        settings = QSettings()
        settings.setValue("lasttimecode", value)

        if self.media is None:
            return

        # VLC lib gives duration in milliseconds, and position as a [0 - 1] ratio of
        # the total duration; so we have to convert from seconds to milliseconds, and
        # then divide that by the total number of milliseconds for the video length.
        ms = value * 1000
        duration = self.media.get_duration()
        pos_ratio = ms/duration

        self.mediaPlayer.play()
        self.mediaPlayer.set_position(pos_ratio)
