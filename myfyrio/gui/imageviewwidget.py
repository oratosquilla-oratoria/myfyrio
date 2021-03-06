'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Myfyrio.

Myfyrio is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Myfyrio is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Myfyrio. If not, see <https://www.gnu.org/licenses/>.

-------------------------------------------------------------------------------

Module implementing widget rendering found duplicate images
'''

from typing import TYPE_CHECKING, Callable, List, Tuple

from PyQt5 import QtCore, QtWidgets

from myfyrio.gui import errornotifier, imagegroupwidget
from myfyrio.logger import Logger

if TYPE_CHECKING:
    from myfyrio import config, core

logger = Logger.getLogger('imageviewwidget')


class ImageViewWidget(QtWidgets.QWidget):
    '''Widget rendering found duplicate images

    :param conf:                programme's preferences as a "Config" object,
    :param parent:              widget's parent (optional),

    :signal selected:           True - there are selected "DuplicateWidget"s,
                                False - otherwise, emitted when any
                                "DuplicateWidget" is clicked,
    :signal finished:           widgets rendering has been finished,
    :signal interrupted:        widgets rendering has been interrupted because
                                of an error,
    :signal error:              error message: str
    '''

    selected = QtCore.pyqtSignal(bool)
    finished = QtCore.pyqtSignal()
    interrupted = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, conf: 'config.Config',
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent=parent)

        self._conf = conf
        self.widgets: List[imagegroupwidget.ImageGroupWidget] = []

        self._errors: List[str] = []

        self._layout = QtWidgets.QVBoxLayout()
        self._layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self._layout.setContentsMargins(9, 9, 9, 9)
        self._layout.setSpacing(10)
        self.setLayout(self._layout)

    def addGroup(self, image_group: Tuple['core.GroupIndex', 'core.Group']) \
        -> None:
        '''Add a new "ImageGroupWidget" with grouped duplicate images or
        change existing one

        :param image_group: tuple with the group index and list of grouped
                            duplicate images
        '''

        if image_group[1]:
            try:
                self._render(image_group)

            except Exception as e:
                logger.exception(e)
                self.error.emit(str(e))
                self.interrupted.emit()

        else:
            self.finished.emit()

            if not self.widgets:
                msg_box = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Information,
                    'No duplicate images found',
                    ('No duplicate images have been found '
                     'in the selected folders')
                )
                msg_box.exec()

    def _render(self, image_group: Tuple['core.GroupIndex', 'core.Group']) \
        -> None:
        if len(self.widgets) == image_group[0]:
            group_w = imagegroupwidget.ImageGroupWidget(self._conf)
            group_w.error.connect(self._errors.append)

            self._layout.addWidget(group_w)
            self.widgets.append(group_w)

            new_images = image_group[1]

        else:
            new_images = [image_group[1][-1]]

        for img in new_images:
            dupl_w = self.widgets[image_group[0]].addDuplicateWidget(img)
            dupl_w.clicked.connect(self._hasSelected)

    def _hasSelected(self) -> None:
        for group_w in self.widgets:
            if group_w.hasSelected():
                self.selected.emit(True)
                return

        self.selected.emit(False)

    def clear(self) -> None:
        '''Clear the widget from the found duplicate images'''

        threadpool = QtCore.QThreadPool.globalInstance()
        threadpool.clear()
        threadpool.waitForDone()

        for group_w in self.widgets:
            group_w.deleteLater()

        self.widgets.clear()

    def _callOnSelected(self, func: Callable[..., None], *args,
                        **kwargs) -> None:
        for group_w in self.widgets:
            func(group_w, *args, **kwargs)

        errornotifier.errorMessage(self._errors)
        self._errors.clear()

    def delete(self) -> None:
        '''Delete the selected images'''

        confirm = QtWidgets.QMessageBox.question(
            self,
            'Deletion confirmation',
            'Do you really want to remove the selected images?',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel
        )

        if confirm == QtWidgets.QMessageBox.Yes:
            self._callOnSelected(imagegroupwidget.ImageGroupWidget.delete)

    def move(self) -> None:
        '''Move the selected images into another folder

        :param dst: folder to move the images into
        '''

        dialog = QtWidgets.QFileDialog(self, 'Open Folder', '')
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOptions(QtWidgets.QFileDialog.DontUseNativeDialog
                          | QtWidgets.QFileDialog.ReadOnly)

        if dialog.exec():
            dst = dialog.selectedFiles()[0]
            self._callOnSelected(imagegroupwidget.ImageGroupWidget.move, dst)

    def autoSelect(self) -> None:
        '''Automatic selection of "DuplicateWidget"s'''

        for group_w in self.widgets:
            group_w.autoSelect()

    def unselect(self) -> None:
        '''Unselect all selected "DuplicateWidget"s'''

        for group_w in self.widgets:
            group_w.unselect()
