import os
import string
import random
import sys
from collections.abc import Iterable

from PyQt6.QtCore import QModelIndex, QSettings, QCoreApplication
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFileDialog,
    QTableView,
    QHBoxLayout,
    QAbstractItemView,
    QVBoxLayout,
    QPushButton,
)

from tv_table_model import TVTableModel, TVModelEntry
from video_preview import VideoPreview


def random_string(length: int):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for _ in range(length))


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

        files_vbox = QVBoxLayout()
        table = QTableView()
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setModel(self.items_model)
        table.clicked.connect(self.selection_changed)

        apply_hbox = QHBoxLayout()
        apply_button = QPushButton("Apply...")
        apply_button.clicked.connect(self._apply_file_names)
        apply_hbox.addStretch(1)
        apply_hbox.addWidget(apply_button)

        files_vbox.addWidget(table)
        files_vbox.addLayout(apply_hbox)

        self.videoPreview = VideoPreview(None)

        main_hbox.addLayout(files_vbox, 2)
        main_hbox.addWidget(self.videoPreview, 3)

        self.setCentralWidget(main_widget)

    def selection_changed(self, selected: QModelIndex):
        print(f"selection is {str(self.items_model.path_at_index(selected.row()))}")
        self.videoPreview.change_current_video(
            self.items_model.path_at_index(selected.row())
        )

    def open_files(self):
        settings = QSettings()
        default_dir = settings.value("default directory", "", str)
        print(f"default dir: {default_dir}")
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Open files",
            directory=default_dir,
            filter=self.tr("Video Files (*.mp4, *.mkv)"),
        )
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

    def _apply_file_names(self):
        # TODO: generate a script you can run to revert the file name changes in case you screwed up
        # Get a list of all the files, go through them and rename
        # To avoid name conflicts, do this in two passes -- first the name with a random string,
        # then remove the random string. Otherwise, if the files are already in the used format
        # you can end up with naming conflicts when renumbering the episodes.
        self.videoPreview.stop_video()

        files = self.items_model.get_all_items()
        names_list = []

        idx = 0
        for f in files:
            root_path = f.parent_dir
            extension = f.extension

            old_path = f.full_path
            new_path = (
                root_path
                + "\\S"
                + str(f.season).zfill(2)
                + "E"
                + str(f.derived_episode).zfill(2)
                + "."
                + extension
            )
            temp_path = new_path + random_string(6)
            names_list.append((old_path, temp_path, new_path, idx))
            idx = idx + 1

        for names in names_list:
            os.rename(names[0], names[1])

        for names in names_list:
            os.rename(names[1], names[2])
            # Create new model entry based on the new name
            files[names[3]] = TVModelEntry(names[2])

        self.items_model.consume_data(files)


# When running as a standalone application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ShowToolApp()
    win.show()
    sys.exit(app.exec())
