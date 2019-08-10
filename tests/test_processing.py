import sys
from unittest import TestCase, mock

from PyQt5 import QtCore, QtGui, QtTest, QtWidgets

from doppelganger import core, exception, processing


class TestThumbnailFunction(TestCase):

    def setUp(self):
        self.image = core.Image('image.png', suffix='.png')

    @mock.patch('doppelganger.core.Image.get_scaling_dimensions', side_effect=OSError)
    def test_thumbnail_returns_None_if_OSError(self, mock_dim):
        th = processing.thumbnail(self.image)
        self.assertIsNone(th)

    @mock.patch('doppelganger.processing._scaled_image', return_value=None)
    @mock.patch('doppelganger.core.Image.get_scaling_dimensions', return_value=(1, 1))
    def test_thumbnail_returns_None_if_scaled_image_is_None(self, mock_dim, mock_scaled):
        th = processing.thumbnail(self.image)
        self.assertIsNone(th)

    @mock.patch('doppelganger.processing._QImage_to_QByteArray', return_value='return')
    @mock.patch('doppelganger.processing._scaled_image', return_value='image')
    @mock.patch('doppelganger.core.Image.get_scaling_dimensions', return_value=(1, 1))
    def test_thumbnail_returns_QImage_to_QByteArray_result(self, mock_dim, mock_scaled, mock_QBA):
        th = processing.thumbnail(self.image)
        self.assertEqual(th, 'return')

    @mock.patch('PyQt5.QtGui.QImageReader.canRead', return_value=False)
    def test_scaled_image_returns_None_if_canRead_returns_False(self, mock_read):
        th = processing._scaled_image(self.image.path, 10, 10)
        self.assertIsNone(th)

    @mock.patch('PyQt5.QtGui.QImage.isNull', return_value=True)
    @mock.patch('PyQt5.QtGui.QImageReader.canRead', return_value=True)
    def test_scaled_image_returns_None_if_isNull_returns_False(self, mock_canRead, mock_isNull):
        th = processing._scaled_image(self.image.path, 10, 10)
        self.assertIsNone(th)

    @mock.patch('PyQt5.QtGui.QImage.isNull', return_value=False)
    @mock.patch('PyQt5.QtGui.QImageReader.canRead', return_value=True)
    def test_scaled_image_returns_QImage_object(self, mock_canRead, mock_isNull):
        th = processing._scaled_image(self.image.path, 10, 10)
        self.assertIsInstance(th, QtGui.QImage)

    @mock.patch('PyQt5.QtCore.QBuffer.open', return_value=False)
    def test_QImage_to_QByteArray_returns_None_if_open_returns_False(self, mock_open):
        ba = processing._QImage_to_QByteArray(QtGui.QImage(), 'png')
        self.assertIsNone(ba)

    @mock.patch('PyQt5.QtGui.QImage.save', return_value=False)
    def test_QImage_to_QByteArray_returns_None_if_save_returns_False(self, mock_save):
        ba = processing._QImage_to_QByteArray(QtGui.QImage(), 'png')
        self.assertIsNone(ba)

    @mock.patch('PyQt5.QtGui.QImage.save', return_value=True)
    @mock.patch('PyQt5.QtCore.QBuffer.open', return_value=True)
    def test_QImage_to_QByteArray_returns_QByteArray(self, mock_open, mock_save):
        ba = processing._QImage_to_QByteArray(QtGui.QImage(), 'png')
        self.assertIsInstance(ba, QtCore.QByteArray)


class TestImageProcessingClass(TestCase):

    @classmethod
    def setUpClass(cls):
        app = QtWidgets.QApplication(sys.argv)
        cls.mw = QtWidgets.QMainWindow()
        cls.mw.signals = processing.Signals()

    def setUp(self):
        self.im_pr = processing.ImageProcessing(self.mw, [], 0)

    def test_attributes_initial_values(self):
        self.assertEqual(self.im_pr.progress_bar_value, 0)
        self.assertFalse(self.im_pr.interrupt)
        self.assertEqual(self.im_pr.sensitivity, 0)

    @mock.patch('doppelganger.processing.core.get_images_paths', return_value='paths')
    def test_paths_return(self, mock_paths):
        p = self.im_pr.paths([])

        self.assertEqual(p, 'paths')

    def test_paths_emits_update_info_signal(self):
        spy = QtTest.QSignalSpy(self.im_pr.signals.update_info)

        p = self.im_pr.paths([])

        self.assertEqual(spy[0][0], 'loaded_images')
        self.assertEqual(spy[0][1], str(len(p)))

    def test_paths_updates_progress_bar_value(self):
        self.im_pr.paths([])

        self.assertEqual(self.im_pr.progress_bar_value, 5)

    @mock.patch('doppelganger.processing.core.load_cached_hashes', return_value='cache')
    def test_load_cache_return(self, mock_cache):
        c = self.im_pr.load_cache()

        self.assertEqual(c, 'cache')

    def test_load_cache_updates_progress_bar_value(self):
        self.im_pr.load_cache()

        self.assertEqual(self.im_pr.progress_bar_value, 10)

    @mock.patch('doppelganger.processing.core.check_cache', return_value=('cached', 'not_cached'))
    def test_check_cache_return(self, mock_check):
        c, n = self.im_pr.check_cache([], {})

        self.assertEqual(c, 'cached')
        self.assertEqual(n, 'not_cached')

    def test_check_cache_emits_update_info_signal(self):
        spy = QtTest.QSignalSpy(self.im_pr.signals.update_info)

        c, _ = self.im_pr.check_cache([], {})

        self.assertEqual(spy[0][0], 'found_in_cache')
        self.assertEqual(spy[0][1], str(len(c)))

    @mock.patch('doppelganger.processing.core.check_cache', return_value=('', 'not_cached'))
    def test_check_cache_updates_progress_bar_value_if_not_cached_not_empty(self, mock_check):
        self.im_pr.check_cache([], {})

        self.assertEqual(self.im_pr.progress_bar_value, 15)

    def test_check_cache_updates_progress_bar_value_if_not_cached_empty(self):
        self.im_pr.check_cache([], {})

        self.assertEqual(self.im_pr.progress_bar_value, 55)

    @mock.patch('doppelganger.processing.ImageProcessing._imap', return_value='calculated')
    def test_calculating_return(self, mock_calc):
        c = self.im_pr.calculating([])

        self.assertEqual(c, 'calculated')

    @mock.patch('doppelganger.processing.core.caching_images')
    def test_caching_core_func_called(self, mock_caching):
        self.im_pr.caching([], {})

        self.assertTrue(mock_caching.called)

    @mock.patch('doppelganger.processing.core.caching_images')
    def test_caching_updates_progress_bar(self, mock_caching):
        '''Use patch here so 'core.caching_images' isn't
        called and doesn't mess up our real cache (if exists)
        '''

        self.im_pr.caching([], {})

        self.assertEqual(self.im_pr.progress_bar_value, 55)

    @mock.patch('doppelganger.processing.core.images_grouping', return_value='groups')
    def test_grouping_return(self, mock_group):
        g = self.im_pr.grouping([], 0)

        self.assertEqual(g, 'groups')

    def test_grouping_emits_update_info_signal(self):
        spy = QtTest.QSignalSpy(self.im_pr.signals.update_info)

        g = self.im_pr.grouping([], 0)

        self.assertEqual(spy[0][0], 'image_groups')
        self.assertEqual(spy[0][1], str(len(g)))

    def test_grouping_updates_progress_bar(self):
        self.im_pr.grouping([], 0)

        self.assertEqual(self.im_pr.progress_bar_value, 65)

    def test_thumbnails_processing_if_pass_empty_image_groups(self):
        g = self.im_pr.thumbnails_generating([])

        self.assertListEqual(g, [])

    @mock.patch('doppelganger.processing.ImageProcessing._imap')
    def test_thumbnails_processing_emit_result(self, mock_thumbs):
        image_groups = [[core.Image(path=f'{i}{j}') for j in range(2)]
                        for i in range(2)]
        thumbnails = [i for i in range(4)]
        mock_thumbs.return_value = thumbnails

        result = self.im_pr.thumbnails_generating(image_groups)

        k = 0
        for i, group in enumerate(result):
            for j, image in enumerate(group):
                self.assertEqual(image.path, image_groups[i][j].path)
                self.assertEqual(image.thumbnail, thumbnails[k])
                k += 1

    def test_update_progress_bar(self):
        value = 5
        spy = QtTest.QSignalSpy(self.im_pr.signals.update_progressbar)
        self.im_pr._update_progress_bar(value)

        self.assertEqual(self.im_pr.progress_bar_value, value)
        self.assertEqual(spy[0][0], value)

    def test_imap_returns_empty_list_if_pass_empty_collection(self):
        result = self.im_pr._imap(len, [], 'label')

        self.assertListEqual(result, [])

    def test_imap_emits_update_info_signal(self):
        spy = QtTest.QSignalSpy(self.im_pr.signals.update_info)

        label = 'label'
        collection = ['a']
        num = len(collection)
        self.im_pr._imap(len, collection, label)

        for i in range(0, num+1):
            self.assertEqual(spy[i][0], label)
            self.assertEqual(spy[i][1], str(num))

            num -= 1

    @mock.patch('doppelganger.processing.ImageProcessing._update_progress_bar')
    def test_imap_emits_update_progress_bar_calls_number(self, mock_bar):
        collection = ['a']
        self.im_pr._imap(len, collection, 'label')

        self.assertEqual(mock_bar.call_count, len(collection))

    def test_imap_emits_final_progress_bar_value(self):
        self.im_pr._imap(len, ['a'], 'label')

        self.assertEqual(self.im_pr.progress_bar_value, 35)

    def test_imap_raises_InterruptProcessing_if_interrupt_True(self):
        self.im_pr.interrupt = True
        with self.assertRaises(exception.InterruptProcessing):
            self.im_pr._imap(len, ['a'], 'label')

    def test_imap_return(self):
        result = self.im_pr._imap(len, ['a', 'bb', 'ccc'], 'label')
        expected = [1, 2, 3]
        self.assertListEqual(result, expected)

    @mock.patch('doppelganger.processing.ImageProcessing.paths')
    def test_run_if_raise_InterruptProcessing(self, mock):
        mock.side_effect = exception.InterruptProcessing
        spy = QtTest.QSignalSpy(self.im_pr.signals.finished)

        self.im_pr.run()

        self.assertEqual(len(spy), 1)

    @mock.patch('doppelganger.processing.ImageProcessing.paths')
    def test_run_if_raise_Exception(self, mock):
        mock.side_effect = Exception('General exception')
        spy_finished = QtTest.QSignalSpy(self.im_pr.signals.finished)
        spy_error = QtTest.QSignalSpy(self.im_pr.signals.error)

        self.im_pr.run()

        self.assertEqual(len(spy_error), 1)
        self.assertEqual(len(spy_finished), 1)

    def test_run_emits_result_signal(self):
        spy_finished = QtTest.QSignalSpy(self.im_pr.signals.finished)
        spy_result = QtTest.QSignalSpy(self.im_pr.signals.result)

        self.im_pr.run()

        self.assertListEqual(spy_result[0][0], [])
        self.assertEqual(len(spy_finished), 1)