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
'''

import logging
import sys
from subprocess import CalledProcessError
from unittest import TestCase, mock

from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from myfyrio import core
from myfyrio.gui import duplicatewidget, infolabel, thumbnailwidget

# Configure a logger for testing purposes
logger = logging.getLogger('main')
logger.setLevel(logging.WARNING)
if not logger.handlers:
    nh = logging.NullHandler()
    logger.addHandler(nh)

# Check if there's QApplication instance already
app = QtWidgets.QApplication.instance()
if app is None:
    app = QtWidgets.QApplication([])

DW_MODULE = 'myfyrio.gui.duplicatewidget.'

# pylint: disable=unused-argument,missing-class-docstring


class TestDuplicateWidget(TestCase):

    DW = DW_MODULE + 'DuplicateWidget.'

    def setUp(self):
        self.conf = {'size': 200,
                     'size_format': 1,
                     'show_similarity': False,
                     'show_size': False,
                     'show_path': False,
                     'delete_dirs': False}
        self.mock_image = mock.Mock(spec=core.Image)

        with mock.patch(self.DW+'_setThumbnailWidget'):
            self.w = duplicatewidget.DuplicateWidget(
                self.mock_image, self.conf
            )


class TestDuplicateWidgetMethodInit(TestDuplicateWidget):

    def test_init_values(self):
        self.assertEqual(self.w.image, self.mock_image)
        self.assertEqual(self.w._conf, self.conf)
        self.assertFalse(self.w._selected)

        self.assertEqual(self.w.minimumWidth(), self.conf['size'])
        self.assertEqual(self.w.maximumWidth(), self.conf['size'])

    def test_layout(self):
        margins = self.w._layout.contentsMargins()
        self.assertEqual(margins.top(), 0)
        self.assertEqual(margins.right(), 0)
        self.assertEqual(margins.bottom(), 0)
        self.assertEqual(margins.left(), 0)

        self.assertIsInstance(self.w._layout, QtWidgets.QVBoxLayout)

    def test_setThumbnailWidget_called(self):
        with mock.patch(self.DW+'_setThumbnailWidget') as mock_th_call:
            self.w = duplicatewidget.DuplicateWidget(
                self.mock_image, self.conf
            )

        mock_th_call.assert_called_once_with()

    def test_setSimilarityLabel_called_if_show_similarity_True(self):
        self.conf['show_similarity'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setSimilarityLabel') as mock_sim_call:
                self.w = duplicatewidget.DuplicateWidget(
                    self.mock_image, self.conf
                )

        mock_sim_call.assert_called_once_with()

    def test_setImageSizeLabel_called_if_show_size_True(self):
        self.conf['show_size'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setImageSizeLabel') as mock_size_call:
                self.w = duplicatewidget.DuplicateWidget(
                    self.mock_image, self.conf
                )

        mock_size_call.assert_called_once_with()

    def test_setImagePathLabel_called_if_show_path_True(self):
        self.conf['show_path'] = True
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'_setImagePathLabel') as mock_path_call:
                self.w = duplicatewidget.DuplicateWidget(
                    self.mock_image, self.conf
                )

        mock_path_call.assert_called_once_with()

    def test_setFixedWidth_called_with_conf_size_arg(self):
        with mock.patch(self.DW+'_setThumbnailWidget'):
            with mock.patch(self.DW+'setFixedWidth') as mock_width_call:
                self.w = duplicatewidget.DuplicateWidget(
                    self.mock_image, self.conf
                )

        mock_width_call.assert_called_once_with(self.conf['size'])


class TestMethodSetThumbnailWidget(TestDuplicateWidget):

    ThW = 'myfyrio.gui.thumbnailwidget.ThumbnailWidget'

    def setUp(self):
        super().setUp()

        self.conf['lazy'] = True

        self.w._layout = mock.Mock(spec=QtWidgets.QVBoxLayout)

        self.mock_thumbnailW = mock.Mock(spec=thumbnailwidget.ThumbnailWidget)

    def test_ThumbnailWidget_called_with_image__conf_size_and_lazy_args(self):
        with mock.patch(self.ThW) as mock_th_call:
            self.w._setThumbnailWidget()

        mock_th_call.assert_called_once_with(
            self.mock_image, self.conf['size'], self.conf['lazy']
        )

    def test_addWidget_called_with_ThumbnailWidget_result(self):
        with mock.patch(self.ThW, return_value=self.mock_thumbnailW):
            self.w._setThumbnailWidget()

        self.w._layout.addWidget.assert_called_once_with(self.mock_thumbnailW)

    def test_horizontal_alignment(self):
        with mock.patch(self.ThW, return_value=self.mock_thumbnailW):
            self.w._setThumbnailWidget()

        self.w._layout.setAlignment.assert_called_once_with(
            self.mock_thumbnailW, QtCore.Qt.AlignHCenter
        )

    def test_return_ThumbnailWidget_result(self):
        with mock.patch(self.ThW, return_value=self.mock_thumbnailW):
            res = self.w._setThumbnailWidget()

        self.assertEqual(res, self.mock_thumbnailW)


class TestMethodSetSimilarityLabel(TestDuplicateWidget):

    SL = 'myfyrio.gui.infolabel.SimilarityLabel'

    def setUp(self):
        super().setUp()

        self.w._layout = mock.Mock(spec=QtWidgets.QVBoxLayout)

        self.mock_similarityL = mock.Mock(spec=infolabel.SimilarityLabel)

    def test_SimilarityLabel_called_with_similarity_and_conf_size_args(self):
        self.mock_image.similarity.return_value = 13
        with mock.patch(self.SL,
                        return_value=self.mock_similarityL) as mock_label_call:
            self.w._setSimilarityLabel()

        mock_label_call.assert_called_once_with('13%', self.conf['size'])

    def test_addWidget_called_with_SimilarityLabel_result(self):
        with mock.patch(self.SL, return_value=self.mock_similarityL):
            self.w._setSimilarityLabel()

        self.w._layout.addWidget.assert_called_once_with(self.mock_similarityL)

    def test_return_SimilarityLabel_result(self):
        with mock.patch(self.SL, return_value=self.mock_similarityL):
            res = self.w._setSimilarityLabel()

        self.assertEqual(res, self.mock_similarityL)


class TestMethodSetImageSizeLabel(TestDuplicateWidget):

    ISL = 'myfyrio.gui.infolabel.ImageSizeLabel'

    def setUp(self):
        super().setUp()

        self.conf['size_format'] = 0 # Bytes
        self.w._layout = mock.Mock(spec=QtWidgets.QVBoxLayout)

        self.mock_sizeL = mock.Mock(spec=infolabel.ImageSizeLabel)

        type(self.mock_image).width = mock.PropertyMock(return_value=33)
        type(self.mock_image).height = mock.PropertyMock(return_value=55)

    def test_ImageSizeLabel_called_with_w_h_Fsize_units_conf_size_args(self):
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL,
                        return_value=self.mock_sizeL) as mock_label_call:
            self.w._setImageSizeLabel()

        mock_label_call.assert_called_once_with(33, 55, 5000, 'B', 200)

    def test_image_filesize_called_with_SizeFormat_B(self):
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL, return_value=self.mock_sizeL):
            self.w._setImageSizeLabel()

        self.mock_image.filesize.assert_called_once_with(core.SizeFormat.B)

    def test_ImageSizeLabel_called_with_w_0_h_0_if_width_raise_OSError(self):
        type(self.mock_image).width = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL,
                        return_value=self.mock_sizeL) as mock_label_call:
            self.w._setImageSizeLabel()

        mock_label_call.assert_called_once_with(0, 0, 5000, 'B', 200)

    def test_logging_if_width_raise_OSError(self):
        type(self.mock_image).width = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL, return_value=self.mock_sizeL):
            with self.assertLogs('main.duplicatewidget', 'ERROR'):
                self.w._setImageSizeLabel()

    def test_ImageSizeLabel_called_with_w_0_h_0_if_height_raise_OSError(self):
        type(self.mock_image).height = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL,
                        eturn_value=self.mock_sizeL) as mock_label_call:
            self.w._setImageSizeLabel()

        mock_label_call.assert_called_once_with(0, 0, 5000, 'B', 200)

    def test_logging_if_height_raise_OSError(self):
        type(self.mock_image).height = mock.PropertyMock(side_effect=OSError)
        self.mock_image.filesize.return_value = 5000
        with mock.patch(self.ISL, return_value=self.mock_sizeL):
            with self.assertLogs('main.duplicatewidget', 'ERROR'):
                self.w._setImageSizeLabel()

    def test_ImageSizeLabel_called_with_size_0_if_filesize_raise_OSError(self):
        self.mock_image.filesize.side_effect = OSError
        with mock.patch(self.ISL,
                        return_value=self.mock_sizeL) as mock_label_call:
            self.w._setImageSizeLabel()

        mock_label_call.assert_called_once_with(33, 55, 0, 'B', 200)

    def test_logging_if_filesize_raise_OSError(self):
        self.mock_image.filesize.side_effect = OSError
        with mock.patch(self.ISL, return_value=self.mock_sizeL):
            with self.assertLogs('main.duplicatewidget', 'ERROR'):
                self.w._setImageSizeLabel()

    def test_addWidget_called_with_ImageSizeLabel_result(self):
        with mock.patch(self.ISL, return_value=self.mock_sizeL):
            self.w._setImageSizeLabel()

        self.w._layout.addWidget.assert_called_once_with(self.mock_sizeL)

    def test_return_ImageSizeLabel_result(self):
        with mock.patch(self.ISL, return_value=self.mock_sizeL):
            res = self.w._setImageSizeLabel()

        self.assertEqual(res, self.mock_sizeL)


class TestMethodSetImagePathLabel(TestDuplicateWidget):

    IPL = 'myfyrio.gui.infolabel.ImagePathLabel'

    def setUp(self):
        super().setUp()

        self.mock_image.path = 'image_path'

        self.w._layout = mock.Mock(spec=QtWidgets.QVBoxLayout)

        self.mock_pathL = mock.Mock(spec=infolabel.ImagePathLabel)

    def test_ImagePathLabel_called_with_image_path_and_conf_size_args(self):
        with mock.patch(self.IPL,
                        return_value=self.mock_pathL) as mock_label_call:
            self.w._setImagePathLabel()

        mock_label_call.assert_called_once_with(
            self.mock_image.path, self.conf['size']
        )

    def test_addWidget_called_with_ImagePathLabel_result(self):
        with mock.patch(self.IPL, return_value=self.mock_pathL):
            self.w._setImagePathLabel()

        self.w._layout.addWidget.assert_called_once_with(self.mock_pathL)

    def test_return_ImagePathLabel_result(self):
        with mock.patch(self.IPL, return_value=self.mock_pathL):
            res = self.w._setImagePathLabel()

        self.assertEqual(res, self.mock_pathL)


class TestDuplicateWidgetMethodOpenImage(TestDuplicateWidget):

    PATCH_ERRM = 'myfyrio.gui.errornotifier.errorMessage'
    PATCH_OPENFILE = 'myfyrio.gui.utils.openFile'

    def setUp(self):
        super().setUp()

        self.real_platform = sys.platform

        self.mock_image.path = 'path'

    def tearDown(self):
        sys.platform = self.real_platform

    def test_openFile_called_with_image_path_arg(self):
        with mock.patch(self.PATCH_OPENFILE) as mock_openFile:
            self.w.openImage()

        mock_openFile.assert_called_once_with('path')

    def test_log_error_if_subprocess_run_raise_CalledProcessError(self):
        with mock.patch(self.PATCH_OPENFILE,
                        side_effect=CalledProcessError(0, 'cmd')):
            with mock.patch(self.PATCH_ERRM):
                with self.assertLogs('main.duplicatewidget', 'ERROR'):
                    self.w.openImage()

    def test_call_errorMessage_if_raise_CalledProcessError_and_not_Win(self):
        with mock.patch(self.PATCH_OPENFILE,
                        side_effect=CalledProcessError(0, 'cmd')):
            with mock.patch(self.PATCH_ERRM) as mock_msg_call:
                self.w.openImage()

        err_msg = ["Something went wrong while opening 'path'"]
        mock_msg_call.assert_called_once_with(err_msg)

    def test_not_call_errorMessage_if_raise_CalledProcessError_and_Win(self):
        sys.platform = 'win32'
        with mock.patch(self.PATCH_OPENFILE,
                        side_effect=CalledProcessError(0, 'cmd')):
            with mock.patch(self.PATCH_ERRM) as mock_msg_call:
                self.w.openImage()

        mock_msg_call.assert_not_called()


class TestDuplicateWidgetMethodRenameImage(TestDuplicateWidget):

    PATCH_INPUT = 'PyQt5.QtWidgets.QInputDialog.getText'
    PATCH_ERRN = 'myfyrio.gui.errornotifier.'

    def setUp(self):
        super().setUp()

        self.mock_image.path = '/folder/file'
        self.w.imagePathLabel = mock.Mock(spec=infolabel.ImagePathLabel)

    def test_QInputDialog_called_with_image_file_name(self):
        with mock.patch(self.PATCH_INPUT,
                        return_value=('new_name', False)) as mock_dialog_call:
            self.w.renameImage()

        mock_dialog_call.assert_called_once_with(
            self.w,
            'New name',
            'Input a new name of the image:',
            text='file'
        )

    def test_nothing_happens_if_QInputDialog_not_return_ok(self):
        with mock.patch(self.PATCH_INPUT, return_value=('new_name', False)):
            self.w.renameImage()

        self.mock_image.rename.assert_not_called()

    def test_image_rename_called_with_new_name_arg(self):
        with mock.patch(self.PATCH_INPUT, return_value=('new_name', True)):
            self.w.renameImage()

        self.mock_image.rename.assert_called_once_with('new_name')

    def test_ImagePathLabel_text_changed_if_image_name_is_changed(self):
        with mock.patch(self.PATCH_INPUT, return_value=('new_name', True)):
            self.w.renameImage()

        self.w.imagePathLabel.setText.assert_called_once_with(
            self.mock_image.path
        )

    def test_log_error_if_image_rename_raise_FileExistsError(self):
        self.mock_image.rename.side_effect = FileExistsError
        with mock.patch(self.PATCH_INPUT, return_value=('new_name', True)):
            with mock.patch(self.PATCH_ERRN+'errorMessage'):
                with self.assertLogs('main.duplicatewidget', 'ERROR'):
                    self.w.renameImage()

    def test_call_errorMessage_if_image_rename_raise_FileExistsError(self):
        self.mock_image.rename.side_effect = FileExistsError
        with mock.patch(self.PATCH_INPUT, return_value=('new_name', True)):
            with mock.patch(self.PATCH_ERRN+'errorMessage') as mock_msg_call:
                self.w.renameImage()

        err_msg = ['File with the name "new_name" already exists']
        mock_msg_call.assert_called_once_with(err_msg)

    def test_log_error_if_image_rename_raise_FileNotFoundError(self):
        self.mock_image.rename.side_effect = FileNotFoundError
        with mock.patch(self.PATCH_INPUT, return_value=('new_name', True)):
            with mock.patch(self.PATCH_ERRN+'errorMessage'):
                with self.assertLogs('main.duplicatewidget', 'ERROR'):
                    self.w.renameImage()

    def test_call_errorMessage_if_image_rename_raise_FileNotFoundError(self):
        self.mock_image.rename.side_effect = FileNotFoundError
        with mock.patch(self.PATCH_INPUT, return_value=('new_name', True)):
            with mock.patch(self.PATCH_ERRN+'errorMessage') as mock_msg_call:
                self.w.renameImage()

        err_msg = ['File with the name "file" does not exist']
        mock_msg_call.assert_called_once_with(err_msg)


class TestDuplicateWidgetMethodContextMenuEvent(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_menu = mock.Mock(spec=QtWidgets.QMenu)
        self.mock_menu.addAction.side_effect = ['Open', 'Rename']
        self.mock_event = mock.Mock(spec=QtGui.QContextMenuEvent)

    @mock.patch(DW_MODULE+'DuplicateWidget.mapToGlobal')
    @mock.patch(DW_MODULE+'DuplicateWidget.openImage')
    def test_openImage_called(self, mock_open, mock_map):
        action = 'Open'
        self.mock_menu.exec_.return_value = action
        with mock.patch('PyQt5.QtWidgets.QMenu', return_value=self.mock_menu):
            self.w.contextMenuEvent(self.mock_event)

        mock_open.assert_called_once_with()

    @mock.patch(DW_MODULE+'DuplicateWidget.mapToGlobal')
    @mock.patch(DW_MODULE+'DuplicateWidget.renameImage')
    def test_renameImage_called(self, mock_rename, mock_map):
        action = 'Rename'
        self.mock_menu.exec_.return_value = action
        with mock.patch('PyQt5.QtWidgets.QMenu', return_value=self.mock_menu):
            self.w.contextMenuEvent(self.mock_event)

        mock_rename.assert_called_once_with()


class TestDuplicateWidgetMethodSelected_Setter(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.w.thumbnailWidget = mock.Mock(
            spec=thumbnailwidget.ThumbnailWidget
        )

    def test_select_widget_if_pass_True(self):
        self.w.selected = True

        self.assertTrue(self.w._selected)

    def test_thumbnailWidget_mark_called_if_pass_True(self):
        self.w.selected = True

        self.w.thumbnailWidget.setMarked.assert_called_once_with(True)

    def test_unselect_widget_if_pass_False(self):
        self.w.selected = False

        self.assertFalse(self.w._selected)

    def test_thumbnailWidget_unmark_called_if_pass_False(self):
        self.w.selected = False

        self.w.thumbnailWidget.setMarked.assert_called_once_with(False)

    def test_emit_signal_clicked_if_pass_True(self):
        spy = QtTest.QSignalSpy(self.w.clicked)
        self.w.selected = True

        self.assertEqual(len(spy), 1)

    def test_emit_signal_clicked_if_pass_False(self):
        spy = QtTest.QSignalSpy(self.w.clicked)
        self.w.selected = False

        self.assertEqual(len(spy), 1)


class TestDuplicateWidgetMethodHideEvent(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.mock_event = mock.Mock(spec=QtGui.QHideEvent)

    def test_hidden_signal_emitted(self):
        spy = QtTest.QSignalSpy(self.w.hidden)
        self.w.hideEvent(self.mock_event)

        self.assertEqual(len(spy), 1)


class TestDuplicateWidgetMethodCallOnImage(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.func = mock.Mock()
        self.arg = 'arg'
        self.kwarg = 'kwarg'

    def test_func_called_with_args_kwargs(self):
        self.w._callOnImage(self.func, self.arg, kwarg=self.kwarg)

        self.func.assert_called_once_with(self.mock_image, self.arg,
                                          kwarg=self.kwarg)

    def test_attr_selected_set_to_False_if_no_exception(self):
        self.w.selected = True
        self.w._callOnImage(self.func, self.arg, kwarg=self.kwarg)

        self.assertFalse(self.w.selected)

    def test_hide_called_if_no_exception(self):
        with mock.patch(self.DW+'hide') as mock_hide_call:
            self.w._callOnImage(self.func, self.arg, kwarg=self.kwarg)

        mock_hide_call.assert_called_once_with()

    def test_image_del_parent_dir_not_called_if_conf_param_False(self):
        self.w._callOnImage(self.func, self.arg, kwarg=self.kwarg)

        self.mock_image.del_parent_dir.assert_not_called()

    def test_image_del_parent_dir_called_if_conf_param_True(self):
        self.conf['delete_dirs'] = True
        self.w._callOnImage(self.func, self.arg, kwarg=self.kwarg)

        self.mock_image.del_parent_dir.assert_called_once_with()

    def test_logging_if_func_raise_OSError(self):
        self.func.side_effect = OSError
        with self.assertLogs('main.duplicatewidget', 'ERROR'):
            self.w._callOnImage(self.func, self.arg, kwarg=self.kwarg)

    def test_emit_error_signal_with_err_msg_if_func_raise_OSError(self):
        self.func.side_effect = OSError('Error message')
        spy = QtTest.QSignalSpy(self.w.error)
        self.w._callOnImage(self.func, self.arg, kwarg=self.kwarg)

        self.assertEqual(len(spy), 1)
        self.assertEqual(spy[0][0], 'Error message')


class TestDuplicateWidgetMethodDelete(TestDuplicateWidget):

    def test_callOnImage_called_with_Image_delete_func_arg(self):
        with mock.patch(self.DW+'_callOnImage') as mock_call:
            self.w.delete()

        mock_call.assert_called_once_with(core.Image.delete)


class TestDuplicateWidgetMethodMove(TestDuplicateWidget):

    def setUp(self):
        super().setUp()

        self.new_dst = 'new_folder'

    def test_callOnImage_called_with_Image_move_func_and_dst_args(self):
        with mock.patch(self.DW+'_callOnImage') as mock_call:
            self.w.move(self.new_dst)

        mock_call.assert_called_once_with(core.Image.move, self.new_dst)
