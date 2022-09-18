import operator
import re
from collections.abc import Iterable, Sequence, MutableSequence
from functools import cmp_to_key, total_ordering
from pathlib import Path
from typing import Union, List, Callable, Any

from PyQt6 import QtGui
from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant, QAbstractListModel
from PyQt6.QtGui import QColor, QBrush, QColorConstants


# ---------------------------------------------------------------------
# TV Model Entry class
@total_ordering
class TVModelEntry:
    _file_path: Path
    _title: str
    _season: int
    _episode: int
    _manual_episode: int = None
    _derived_episode: int

    def __init__(self, path: str, title: str = "unknown", season: int = -1, episode: int = -1):
        self._file_path = Path(path)
        # TODO: Try to use parent folder to derive season number

        self._title = "unknown"
        self._season = -1
        self._episode = -1
        self._derived_episode = -1

        filename = self._file_path.name
        season_pattern = r"[sS]([0-9]+)"
        episode_pattern = r"[eE]([0-9]+)"

        season_matches = re.finditer(season_pattern, filename)
        for match in season_matches:
            try:
                number = match.group(1)
                self._season = int(number)
            except ValueError:
                print("couldn't turn found pattern " + match.group(1) + " into a number")

        episode_matches = re.finditer(episode_pattern, filename)
        for match in episode_matches:
            try:
                number = match.group(1)
                self._episode = int(number)
            except ValueError:
                print("couldn't turn found pattern " + match.group(1) + " into a number")

    def __eq__(self, other):
        if self._season != other._season:
            return False

        my_ep = self._manual_episode if self._manual_episode is not None else self._episode
        ot_ep = other._manual_episode if other._manual_episode is not None else other._episode

        if my_ep != ot_ep:
            return False

        # they are "equal"
        if self._manual_episode is None and other._manual_episode is None:
            return True

        if self._manual_episode is not None and other._manual_episode is not None:
            return True

        return False

    def __lt__(self, other):
        if self._season < other._season:
            return True

        my_ep = self._manual_episode if self._manual_episode is not None else self._episode
        ot_ep = other._manual_episode if other._manual_episode is not None else other._episode

        if my_ep == ot_ep:
            return self._manual_episode is None and other._manual_episode is not None

        return my_ep < ot_ep

    def __gt__(self, other):
        if self._season > other._season:
            return True

        my_ep: int = self._manual_episode if self._manual_episode is not None else self._episode
        ot_ep: int = other._manual_episode if other._manual_episode is not None else other._episode

        if my_ep == ot_ep:
            return self._manual_episode is not None and other._manual_episode is None

        return my_ep > ot_ep

    # full_path --------------------
    @property
    def full_path(self) -> str:
        return str(self._file_path.absolute())

    # filename --------------------
    @property
    def filename(self) -> str:
        return self._file_path.name

    # filename --------------------
    @property
    def parent_dir(self) -> str:
        return str(self._file_path.parent.absolute())

    # title --------------------
    @property
    def title(self) -> str:
        return self._title

    # season --------------------
    @property
    def season(self) -> int:
        return self._season

    # episode --------------------
    @property
    def episode(self) -> int:
        return self._episode

    # manual_episode --------------------
    @property
    def manual_episode(self) -> int:
        return self._manual_episode

    @manual_episode.setter
    def manual_episode(self, val: int):
        self._manual_episode = val

    # derived_episode --------------------
    @property
    def derived_episode(self):
        return self._derived_episode

    @derived_episode.setter
    def derived_episode(self, val: int):
        self._derived_episode = val


# ---------------------------------------------------------------------
# Model Column class
class ModelColumn:
    name: str
    func: Callable

    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func


# ---------------------------------------------------------------------
# TV Table Model class
class TVTableModel(QAbstractTableModel):
    # TODO: Accept (or detect?) a "root" path, and display all files as relative to the root path
    # TODO: Use selection change event rather than "click" event to respond when up/down keys are used as well

    entries: List[TVModelEntry]
    columns = Sequence[ModelColumn]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.entries = list()
        self.columns = [
            ModelColumn("Filename", lambda entry: entry.filename),
            ModelColumn("Season", lambda entry: entry.season),
            ModelColumn("Episode", lambda entry: entry.episode),
            ModelColumn("Fixed", lambda entry: str(entry.derived_episode) + "(" + str(entry.derived_episode) + ")"),
        ]

    # ----------------------- #
    # Custom funcs
    # ----------------------- #
    def consume_data(self, entries: List[TVModelEntry]):
        self.beginResetModel()
        self.entries = sorted(entries)
        self._renumber_entries()
        self.endResetModel()

    def _renumber_entries(self):
        # TODO: Sort by matching seasons
        entries = [None] * len(self.entries)
        for e in self.entries:
            if e.manual_episode is None:
                continue
            ep = e.manual_episode
            entries[ep-1] = e

        idx = 0
        for i in range(len(entries)):
            if entries[i] is not None:
                continue

            while self.entries[idx].manual_episode is not None:
                idx = idx + 1

            entries[i] = self.entries[idx]
            idx = idx + 1

        self.entries = entries
        idx = 1
        for e in self.entries:
            e.derived_episode = idx
            idx = idx + 1

    def path_at_index(self, index: int):
        return self.entries[index].full_path

    # ----------------------- #
    # Qt Overrides
    # ----------------------- #
    def rowCount(self, parent: QModelIndex = ...) -> Union[QVariant, int]:
        if self.entries is None:
            return QVariant()
        return len(self.entries)

    def columnCount(self, parent: QModelIndex = ...) -> Union[QVariant, int]:
        return len(self.columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if orientation == Qt.Orientation.Vertical:
            return QVariant()

        if role == Qt.ItemDataRole.DisplayRole:
            return self.columns[section].name
        return QVariant()

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        row = index.row()
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self.columns[col].func(self.entries[row])

        # TODO: colorize manual episode numbers based on default, manual, or derived
        if role == Qt.ItemDataRole.ForegroundRole and col == 3:
            entry = self.entries[row]
            if entry.manual_episode is None:
                return QColorConstants.Gray
            else:
                return QColorConstants.Green

        return QVariant()

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

        if index.column() == 3:
            flags = flags | Qt.ItemFlag.ItemIsEditable

        return flags

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        # TODO: Don't allow duplicate manual episode numbers
        try:
            val = int(value)
            if val < 1:
                return False
            entry = self.entries[index.row()]
            self.beginResetModel()
            entry.manual_episode = val
            self.entries.sort()
            self._renumber_entries()
            self.endResetModel()
            return True
        except ValueError:
            return False