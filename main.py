from collections.abc import Iterable

from PyQt6.QtCore import QModelIndex, QSettings, QCoreApplication
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QTableView, QHBoxLayout, \
    QAbstractItemView
import sys

from tv_table_model import TVTableModel, TVModelEntry
from video_preview import VideoPreview


class ShowToolApp(QMainWindow):
    # TODO: Support file drop to open

    items_model = TVTableModel()

    def __init__(self, parent=None):
        super().__init__(parent)

        QCoreApplication.setOrganizationName("AberrantWolf")
        QCoreApplication.setApplicationName("Show Tool")

        self.setWindowTitle("Show Tool")

        # Menu Bar stuff
        open_files_action = QAction("Open File(s)...", self)
        open_files_action.setShortcut(QKeySequence("Ctrl+O"))
        open_files_action.triggered.connect(self.open_files)

        open_directory_action = QAction("&Open Directory...", self)
        open_directory_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_directory_action.triggered.connect(self.open_directory)

        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        file_menu.addAction(open_files_action)
        file_menu.addAction(open_directory_action)

        # Window Layout
        main_widget = QWidget()
        main_hbox = QHBoxLayout(main_widget)

        table = QTableView()
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setModel(self.items_model)
        table.clicked.connect(self.selection_changed)

        self.videoPreview = VideoPreview(None)

        main_hbox.addWidget(table, 1)
        main_hbox.addWidget(self.videoPreview, 1)

        self.setCentralWidget(main_widget)

    def selection_changed(self, selected: QModelIndex):
        print("selection is " + str(self.items_model.path_at_index(selected.row())))
        self.videoPreview.change_current_video(self.items_model.path_at_index(selected.row()))

    def open_files(self):
        settings = QSettings()
        default_dir = settings.value("default directory", "", str)
        print("default dir: " + default_dir)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open files",
            directory=default_dir,
            filter=self.tr("Video Files (*.mp4, *.mkv)"))
        self._do_open_files(files)

    def open_directory(self):
        directory, _ = QFileDialog.getExistingDirectory(self, "Open directory")
        # TODO: Parse all the files in the folder to look for video files

    def _do_open_files(self, files_list: Iterable[str]):
        settings = QSettings()
        file_infos = []
        for path_str in files_list:
            entry = TVModelEntry(path_str)
            file_infos.append(entry)
        if len(file_infos):
            settings.setValue("default directory", file_infos[0].parent_dir)
        self.items_model.consume_data(file_infos)


# When running as a standalone application
if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ShowToolApp()
    win.show()
    sys.exit(app.exec())
