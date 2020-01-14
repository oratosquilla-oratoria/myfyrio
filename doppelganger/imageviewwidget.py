'''Copyright 2019-2020 Maxim Shpak <maxim.shpak@posteo.uk>

This file is part of Doppelgänger.

Doppelgänger is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Doppelgänger is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Doppelgänger. If not, see <https://www.gnu.org/licenses/>.

-------------------------------------------------------------------------------

Module implementing widget rendering duplicate images found
'''


import logging
import pathlib
import subprocess
import sys
from typing import Iterable, List, Optional, Tuple

from PyQt5 import QtCore, QtGui, QtWidgets

from doppelganger import config, core, signals

IMG_ERROR = str(pathlib.Path('doppelganger/resources/images/image_error.png'))
SIZE = 200

widgets_logger = logging.getLogger('main.widgets')


class InfoLabelWidget(QtWidgets.QLabel):
    '''Abstract Label class'''

    def __init__(self, text: str, widget_size: int, parent=None) -> None:
        super().__init__(parent)
        self.widget_size = widget_size

        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setText(text)

    def setText(self, text: str):
        new_text = self._word_wrap(text)
        super().setText(new_text)

    def _word_wrap(self, text: str) -> str:
        '''QLabel wraps words only at word-breaks but we need
        it to happen at any letter

        :param text: text,
        :return: wrapped text
        '''

        fontMetrics = QtGui.QFontMetrics(self.font())
        wrapped_text = ''
        line = ''

        for c in text:
            # We have 4 margins 9px each (I guess) so we take 40
            width = fontMetrics.size(QtCore.Qt.TextSingleLine, line+c).width()
            if width > self.widget_size - 40:
                wrapped_text += line + '\n'
                line = c
            else:
                line += c
        wrapped_text += line

        return wrapped_text


class SimilarityLabel(InfoLabelWidget):
    '''Widget to show info about images similarity'''


class ImageSizeLabel(InfoLabelWidget):
    '''Widget to show info about the image size'''


class ImagePathLabel(InfoLabelWidget):
    '''Widget to show the path to an image'''

    def __init__(self, text: core.ImagePath, widget_size: int,
                 parent=None) -> None:
        super().__init__(QtCore.QFileInfo(text).canonicalFilePath(),
                         widget_size, parent)

class ImageInfoWidget(QtWidgets.QWidget):
    '''Widget to show info about an image (its similarity
    rate, size and path)'''

    def __init__(self, path: core.ImagePath, difference: core.Distance,
                 dimensions: Tuple[core.Width, core.Height],
                 filesize: core.FileSize, conf: config.ConfigData,
                 parent=None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignBottom)

        if conf['show_similarity']:
            widget = SimilarityLabel(f'{difference}%', conf['size'], self)
            layout.addWidget(widget)
        if conf['show_size']:
            widget = ImageSizeLabel(
                self._get_image_size(dimensions, filesize,
                                     conf['size_format']),
                conf['size'],
                self
            )
            layout.addWidget(widget)
        if conf['show_path']:
            widget = ImagePathLabel(path, conf['size'], self)
            layout.addWidget(widget)

        self.setLayout(layout)

    @staticmethod
    def _get_image_size(dimensions: Tuple[core.Width, core.Height],
                        filesize: core.FileSize, size_format: int) -> str:
        '''Return info about image dimensions and file size

        :param dimensions: image dimensions,
        :param filesize: file size in bytes, kilobytes or megabytes,
                         rounded to the first decimal place,
        :return: string with format '{width}x{height}, {file_size} {units}'
        '''

        width, height = dimensions[0], dimensions[1]
        units = {0: 'B',
                 1: 'KB',
                 2: 'MB'}[size_format]

        return f'{width}x{height}, {filesize} {units}'


class ThumbnailWidget(QtWidgets.QLabel):
    '''Widget to render the thumbnail of an image'''

    def __init__(self, thumbnail: QtCore.QByteArray, size: int,
                 parent=None) -> None:
        super().__init__(parent)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.pixmap = self._QByteArray_to_QPixmap(thumbnail, size)
        self.setPixmap(self.pixmap)

    @staticmethod
    def _QByteArray_to_QPixmap(thumbnail: QtCore.QByteArray,
                               size: int) -> QtGui.QPixmap:
        '''Convert 'QByteArray' to 'QPixmap'

        :param thumbnails: image in format 'QByteArray',
        :param size: thumbnail size,
        :return: image in format 'QPixmap' or, if something's
                 wrong - error image
        '''

        # Pixmap can read BMP, GIF, JPG, JPEG, PNG, PBM, PGM, PPM, XBM, XPM
        if thumbnail is None:
            return QtGui.QPixmap(IMG_ERROR).scaled(size, size)

        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(thumbnail)

        if pixmap.isNull():
            err_msg = ('Something happened while converting '
                       'QByteArray into QPixmap')
            widgets_logger.error(err_msg)
            return QtGui.QPixmap(IMG_ERROR).scaled(size, size)

        return pixmap

    def mark(self) -> None:
        '''Mark the thumbnail as selected'''

        marked = self.pixmap.copy()
        width, height = marked.width(), marked.height()

        painter = QtGui.QPainter(marked)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        painter.setBrush(brush)
        painter.drawRect(0, 0, width, height)
        painter.end()
        self.setPixmap(marked)

    def unmark(self) -> None:
        '''Mark the thumbnail as not selected'''

        self.setPixmap(self.pixmap)


class DuplicateWidget(QtWidgets.QWidget, QtCore.QObject):
    '''Widget to render a duplicate image and all the info
    about it (its similarity rate, size and path)
    '''

    def __init__(self, image: core.HashedImage, conf: config.ConfigData,
                 parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self.conf = conf
        self.selected = False
        self.imageLabel, self.imageInfo = self._widgets()

        self.signals = signals.Signals()

        self.setFixedWidth(conf['size'])
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)
        for widget in (self.imageLabel, self.imageInfo):
            layout.addWidget(widget)
        self.setLayout(layout)

    def _widgets(self) -> Tuple[ThumbnailWidget, ImageInfoWidget]:
        '''Return ThumbnailWidget and ImageInfoWidget objects

        :return: tuple, ('ThumbnailWidget' obj, 'ImageInfoWidget' obj)
        '''

        imageLabel = ThumbnailWidget(self.image.thumbnail, self.conf['size'],
                                     self)

        try:
            dimensions = self.image.dimensions()
        except OSError as e:
            widgets_logger.error(e)
            dimensions = (0, 0)

        try:
            filesize = self.image.filesize(self.conf['size_format'])
        except OSError as e:
            widgets_logger.error(e)
            filesize = 0

        imageInfo = ImageInfoWidget(self.image.path, self.image.difference,
                                    dimensions, filesize, self.conf, self)

        return imageLabel, imageInfo

    def _open_image(self) -> None:
        '''Open the image in the OS default image viewer'''

        open_image_command = {'linux': 'xdg-open',
                              'win32': 'explorer',
                              'darwin': 'open'}[sys.platform]

        try:
            subprocess.run([open_image_command, self.image.path], check=True)
        except subprocess.CalledProcessError:
            msg = 'Something wrong happened while opening the image viewer'
            widgets_logger.error(msg, exc_info=True)

    def _rename_image(self) -> None:
        '''Rename the image'''

        name = pathlib.Path(self.image.path).name
        new_name, ok = QtWidgets.QInputDialog.getText(
            self,
            'New name',
            'Input a new name of the image:',
            text=name,
        )
        if ok:
            try:
                self.image.rename(new_name)
            except FileExistsError as e:
                widgets_logger.error(e)
                msgBox = QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Warning,
                    'Renaming image',
                    f"File with name '{new_name}' already exists"
                )
                msgBox.exec()
            else:
                pathLabel = self.findChild(ImagePathLabel)
                pathLabel.setText(self.image.path)


    def contextMenuEvent(self, event) -> None:
        menu = QtWidgets.QMenu(self)
        openAction = menu.addAction("Open")
        menu.addSeparator()
        renameAction = menu.addAction("Rename")
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == openAction:
            self._open_image()
        if action == renameAction:
            self._rename_image()

    def click(self) -> None:
        '''Select/unselect widget and emit signal about it'''

        if self.selected:
            self.selected = False
            self.imageLabel.unmark()
        else:
            self.selected = True
            self.imageLabel.mark()

        self.signals.clicked.emit()

    def mouseReleaseEvent(self, event) -> None:
        '''Function called on mouse release event'''

        super().mouseReleaseEvent(event)

        self.click()

    def delete(self) -> None:
        '''Delete the image from disk and its DuplicateWidget instance

        :raise OSError: something went wrong while removing the image
        '''

        try:
            self.image.delete()
        except OSError as e:
            raise OSError(e)
        else:
            self.selected = False
            self.deleteLater()

    def move(self, dst: core.FolderPath) -> None:
        '''Move the image to a new location and delete
        its DuplicateWidget instance

        :param dst: new location, eg. /new/location,
        :raise OSError: something went wrong while moving the image
        '''

        try:
            self.image.move(dst)
        except OSError as e:
            raise OSError(e)
        else:
            self.selected = False
            self.deleteLater()


class ImageGroupWidget(QtWidgets.QWidget):
    '''Widget to group similar images together'''

    def __init__(self, image_group: Iterable[core.HashedImage],
                 conf: config.ConfigData, parent=None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        self.duplicate_widgets = []
        for image in image_group:
            duplicate_widgets = DuplicateWidget(image, conf, self)
            self.duplicate_widgets.append(duplicate_widgets)
            layout.addWidget(duplicate_widgets)
        self.setLayout(layout)

    def getSelectedWidgets(self) -> List[DuplicateWidget]:
        '''Return a list of the selected DuplicateWidget instances

        :return: selected DuplicateWidget instances
        '''

        widgets = self.findChildren(
            DuplicateWidget,
            options=QtCore.Qt.FindDirectChildrenOnly
        )
        return [widget for widget in widgets if widget.selected]

    def auto_select(self) -> None:
        '''Automatic selection of DuplicateWidget's'''

        for i in range(1, len(self)):
            self.duplicate_widgets[i].click()

    def __len__(self) -> int:
        return len(self.duplicate_widgets)


class ImageViewWidget(QtWidgets.QWidget):
    '''Widget rendering duplicate images found'''

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

    def render(self, conf, image_groups: Iterable[core.Group]) -> None:
        '''Add 'ImageGroupWidget' to 'scrollArea'

        :param image_groups: groups of similar images
        '''

        if not image_groups:
            msg_box = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Information,
                'No duplicate images found',
                'No duplicate images have been found in the selected folders'
            )
            msg_box.exec()
        else:
            for group in image_groups:
                self.layout.addWidget(ImageGroupWidget(group, conf, self))

    def hasSelectedWidgets(self) -> bool:
        '''Check if there are selected 'DuplicateWidget' on the form

        :return: True if there are any selected ones
        '''

        for group_widget in self.findChildren(ImageGroupWidget):
            selected_widgets = group_widget.getSelectedWidgets()
            if selected_widgets:
                return True
        return False

    def clear(self) -> None:
        '''Clear the widget from the previous duplicate images'''

        groups = self.findChildren(ImageGroupWidget)
        for group_widget in groups:
            group_widget.deleteLater()

    def call_on_selected_widgets(
            self,
            conf,
            dst: Optional[core.FolderPath] = None
        ) -> None:
        '''Call 'move' or 'delete' on selected widgets

        :param dst: if None, 'delete' is called, otherwise - 'move'
        '''

        groups = self.findChildren(ImageGroupWidget)
        for group_widget in groups:
            selected_widgets = group_widget.getSelectedWidgets()
            for selected_widget in selected_widgets:
                try:
                    if dst:
                        selected_widget.move(dst)
                    else:
                        selected_widget.delete()
                except OSError as e:
                    widgets_logger.error(e)
                    msgBox = QtWidgets.QMessageBox(
                        QtWidgets.QMessageBox.Warning,
                        'Removing/Moving image',
                        ('Error occured while removing/moving '
                         f'image {selected_widget.image.path}')
                    )
                    msgBox.exec()
                else:
                    if conf['delete_dirs']:
                        selected_widget.image.del_parent_dir()
            # If we select all (or except one) the images in a group,
            if len(group_widget) - len(selected_widgets) <= 1:
                # and all the selected images were processed correctly (so
                # there are no selected images anymore), delete the whole group
                if not group_widget.getSelectedWidgets():
                    group_widget.deleteLater()

    def autoSelect(self) -> None:
        '''Automatic selection of DuplicateWidget's'''

        group_widgets = self.findChildren(ImageGroupWidget)
        for group in group_widgets:
            group.auto_select()

    def unselect(self) -> None:
        '''Unselect all the selected DuplicateWidget's'''

        duplicate_widgets = self.findChildren(DuplicateWidget)
        for w in duplicate_widgets:
            if w.selected:
                w.click()