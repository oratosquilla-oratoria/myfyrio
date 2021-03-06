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

Module implementing widget viewing a group of similar (duplicate) images
'''


from typing import TYPE_CHECKING, Callable, List

from PyQt5 import QtCore, QtWidgets

from myfyrio import core
from myfyrio.gui import duplicatewidget

if TYPE_CHECKING:
    from myfyrio import config


class ImageGroupWidget(QtWidgets.QWidget):
    '''Widget rendering a group of similar (duplicate) images
    as "DuplicateWidget"s

    :param image_group: iterable with duplicate images as "Image" objects,
    :param conf:        programme's preferences as a "Config" object,
    :param parent:      widget's parent (optional),

    :signal error:      error message: str
    '''

    error = QtCore.pyqtSignal(str)

    def __init__(self, conf: 'config.Config',
                 image_group: List[core.Image] = None,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)

        self._conf = conf
        self.widgets: List[duplicatewidget.DuplicateWidget] = []

        self._visible_num = 0

        self._layout = QtWidgets.QHBoxLayout(self)
        self._layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(10)

        if image_group is not None:
            for image in image_group:
                self.addDuplicateWidget(image)

        self.setLayout(self._layout)

    def addDuplicateWidget(self, image: core.Image) \
        -> duplicatewidget.DuplicateWidget:
        dupl_w = duplicatewidget.DuplicateWidget(image, self._conf)
        dupl_w.error.connect(self.error)
        dupl_w.hidden.connect(self._duplicateWidgetHidden)

        self._visible_num += 1

        i = self._insertIndex(dupl_w)
        self.widgets.insert(i, dupl_w)
        self._layout.insertWidget(i, dupl_w)
        self._layout.setAlignment(dupl_w, QtCore.Qt.AlignTop)

        return dupl_w

    def _insertIndex(self, new_w: duplicatewidget.DuplicateWidget) -> int:
        key = core.Sort(self._conf['sort']).key()

        left, right = 0, len(self.widgets) - 1
        new_w_key = key(new_w.image)

        while left <= right:
            middle = (right + left) // 2

            if new_w_key < key(self.widgets[middle].image):
                right = middle - 1
            else:
                left = middle + 1

        return left

    def hasSelected(self) -> bool:
        '''Check if there are any selected "DuplicateWidget"s in the widget

        :return: True - there are selected "DuplicateWidget"s,
                 False - otherwise
        '''

        for dupl_w in self.widgets:
            if dupl_w.selected:
                return True
        return False

    def autoSelect(self) -> None:
        '''Select all "DuplicateWidget"s in the widget except the first one'''

        for i in range(1, len(self)):
            self.widgets[i].selected = True

    def unselect(self) -> None:
        '''Unselect all selected "DuplicateWidget"s in the widget'''

        for dupl_w in self.widgets:
            dupl_w.selected = False

    def _duplicateWidgetHidden(self) -> None:
        self._visible_num -= 1

    def _callOnSelected(self, func: Callable[..., None], *args,
                        **kwargs) -> None:
        for dupl_w in self.widgets:
            if dupl_w.selected:
                func(dupl_w, *args, **kwargs)

        if self._visible_num <= 1:
            self.hide()

    def delete(self) -> None:
        '''Delete the selected images from the disk, hide its "DuplicateWidget"
        instances. Hide the whole group widget if less than 2 images left in
        the group. If the preference "Delete folders if they are empty..." is
        on, also delete empty folders
        '''

        self._callOnSelected(duplicatewidget.DuplicateWidget.delete)

    def move(self, dst: core.FolderPath) -> None:
        '''Move the selected images into the folder :dst:, hide its
        "DuplicateWidget" instances. Hide the whole group widget if
        less than 2 images left in the group. If the preference "Delete
        folders if they are empty..." is on, also delete empty folders

        :param dst: folder to move the images into
        '''

        self._callOnSelected(duplicatewidget.DuplicateWidget.move, dst)

    def __len__(self) -> int:
        return len(self.widgets)
