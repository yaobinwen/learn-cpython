import io
import mimetypes
import os
import sys
import unittest.mock

from test import support
from test.support import os_helper
from platform import win32_edition

try:
    import _winapi
except ImportError:
    _winapi = None


def setUpModule():
    global knownfiles
    knownfiles = mimetypes.knownfiles

    # Tell it we don't know about external files:
    mimetypes.knownfiles = []
    mimetypes.inited = False
    mimetypes._default_mime_types()


def tearDownModule():
    # Restore knownfiles to its initial state
    mimetypes.knownfiles = knownfiles


class MimeTypesTestCase(unittest.TestCase):
    def setUp(self):
        self.db = mimetypes.MimeTypes()

    def test_case_sensitivity(self):
        eq = self.assertEqual
        eq(self.db.guess_type("foobar.HTML"), self.db.guess_type("foobar.html"))
        eq(self.db.guess_type("foobar.TGZ"), self.db.guess_type("foobar.tgz"))
        eq(self.db.guess_type("foobar.tar.Z"), ("application/x-tar", "compress"))
        eq(self.db.guess_type("foobar.tar.z"), (None, None))

    def test_default_data(self):
        eq = self.assertEqual
        eq(self.db.guess_type("foo.html"), ("text/html", None))
        eq(self.db.guess_type("foo.HTML"), ("text/html", None))
        eq(self.db.guess_type("foo.tgz"), ("application/x-tar", "gzip"))
        eq(self.db.guess_type("foo.tar.gz"), ("application/x-tar", "gzip"))
        eq(self.db.guess_type("foo.tar.Z"), ("application/x-tar", "compress"))
        eq(self.db.guess_type("foo.tar.bz2"), ("application/x-tar", "bzip2"))
        eq(self.db.guess_type("foo.tar.xz"), ("application/x-tar", "xz"))

    def test_data_urls(self):
        eq = self.assertEqual
        guess_type = self.db.guess_type
        eq(guess_type("data:invalidDataWithoutComma"), (None, None))
        eq(guess_type("data:,thisIsTextPlain"), ("text/plain", None))
        eq(guess_type("data:;base64,thisIsTextPlain"), ("text/plain", None))
        eq(guess_type("data:text/x-foo,thisIsTextXFoo"), ("text/x-foo", None))

    def test_file_parsing(self):
        eq = self.assertEqual
        sio = io.StringIO("x-application/x-unittest pyunit\n")
        self.db.readfp(sio)
        eq(self.db.guess_type("foo.pyunit"),
           ("x-application/x-unittest", None))
        eq(self.db.guess_extension("x-application/x-unittest"), ".pyunit")

    def test_read_mime_types(self):
        eq = self.assertEqual

        # Unreadable file returns None
        self.assertIsNone(mimetypes.read_mime_types("non-existent"))

        with os_helper.temp_dir() as directory:
            data = "x-application/x-unittest pyunit\n"
            file = os.path.join(directory, "sample.mimetype")
            with open(file, 'w', encoding="utf-8") as f:
                f.write(data)
            mime_dict = mimetypes.read_mime_types(file)
            eq(mime_dict[".pyunit"], "x-application/x-unittest")

            data = "x-application/x-unittest2 pyunit2\n"
            file = os.path.join(directory, "sample2.mimetype")
            with open(file, 'w', encoding="utf-8") as f:
                f.write(data)
            mime_dict = mimetypes.read_mime_types(os_helper.FakePath(file))
            eq(mime_dict[".pyunit2"], "x-application/x-unittest2")

        # bpo-41048: read_mime_types should read the rule file with 'utf-8' encoding.
        # Not with locale encoding. _bootlocale has been imported because io.open(...)
        # uses it.
        data = "application/no-mans-land  Fran\u00E7ais"
        filename = "filename"
        fp = io.StringIO(data)
        with unittest.mock.patch.object(mimetypes, 'open',
                                        return_value=fp) as mock_open:
            mime_dict = mimetypes.read_mime_types(filename)
            mock_open.assert_called_with(filename, encoding='utf-8')
        eq(mime_dict[".Français"], "application/no-mans-land")

    def test_non_standard_types(self):
        eq = self.assertEqual
        # First try strict
        eq(self.db.guess_type('foo.xul', strict=True), (None, None))
        eq(self.db.guess_extension('image/jpg', strict=True), None)
        eq(self.db.guess_extension('image/webp', strict=True), None)
        # And then non-strict
        eq(self.db.guess_type('foo.xul', strict=False), ('text/xul', None))
        eq(self.db.guess_type('foo.XUL', strict=False), ('text/xul', None))
        eq(self.db.guess_type('foo.invalid', strict=False), (None, None))
        eq(self.db.guess_extension('image/jpg', strict=False), '.jpg')
        eq(self.db.guess_extension('image/JPG', strict=False), '.jpg')
        eq(self.db.guess_extension('image/webp', strict=False), '.webp')

    def test_filename_with_url_delimiters(self):
        # bpo-38449: URL delimiters cases should be handled also.
        # They would have different mime types if interpreted as URL as
        # compared to when interpreted as filename because of the semicolon.
        eq = self.assertEqual
        gzip_expected = ('application/x-tar', 'gzip')
        for name in (
                ';1.tar.gz',
                '?1.tar.gz',
                '#1.tar.gz',
                '#1#.tar.gz',
                ';1#.tar.gz',
                ';&1=123;?.tar.gz',
                '?k1=v1&k2=v2.tar.gz',
            ):
            for prefix in ('', '/', '\\',
                           'c:', 'c:/', 'c:\\', 'c:/d/', 'c:\\d\\',
                           '//share/server/', '\\\\share\\server\\'):
                path = prefix + name
                with self.subTest(path=path):
                    eq(self.db.guess_type(path), gzip_expected)
            expected = (None, None) if os.name == 'nt' else gzip_expected
            for prefix in ('//', '\\\\', '//share/', '\\\\share\\'):
                path = prefix + name
                with self.subTest(path=path):
                    eq(self.db.guess_type(path), expected)
        eq(self.db.guess_type(r" \"\`;b&b&c |.tar.gz"), gzip_expected)

    def test_url(self):
        result = self.db.guess_type('http://host.html')
        msg = 'URL only has a host name, not a file'
        self.assertSequenceEqual(result, (None, None), msg)
        result = self.db.guess_type('http://example.com/host.html')
        msg = 'Should be text/html'
        self.assertSequenceEqual(result, ('text/html', None), msg)
        result = self.db.guess_type('http://example.com/host.html#x.tar')
        self.assertSequenceEqual(result, ('text/html', None))
        result = self.db.guess_type('http://example.com/host.html?q=x.tar')
        self.assertSequenceEqual(result, ('text/html', None))

    def test_guess_all_types(self):
        # First try strict.  Use a set here for testing the results because if
        # test_urllib2 is run before test_mimetypes, global state is modified
        # such that the 'all' set will have more items in it.
        all = self.db.guess_all_extensions('text/plain', strict=True)
        self.assertTrue(set(all) >= {'.bat', '.c', '.h', '.ksh', '.pl', '.txt'})
        self.assertEqual(len(set(all)), len(all))  # no duplicates
        # And now non-strict
        all = self.db.guess_all_extensions('image/jpg', strict=False)
        self.assertEqual(all, ['.jpg'])
        # And now for no hits
        all = self.db.guess_all_extensions('image/jpg', strict=True)
        self.assertEqual(all, [])
        # And now for type existing in both strict and non-strict mappings.
        self.db.add_type('test-type', '.strict-ext')
        self.db.add_type('test-type', '.non-strict-ext', strict=False)
        all = self.db.guess_all_extensions('test-type', strict=False)
        self.assertEqual(all, ['.strict-ext', '.non-strict-ext'])
        all = self.db.guess_all_extensions('test-type')
        self.assertEqual(all, ['.strict-ext'])
        # Test that changing the result list does not affect the global state
        all.append('.no-such-ext')
        all = self.db.guess_all_extensions('test-type')
        self.assertNotIn('.no-such-ext', all)

    def test_encoding(self):
        filename = support.findfile("mime.types")
        mimes = mimetypes.MimeTypes([filename])
        exts = mimes.guess_all_extensions('application/vnd.geocube+xml',
                                          strict=True)
        self.assertEqual(exts, ['.g3', '.g\xb3'])

    def test_init_reinitializes(self):
        # Issue 4936: make sure an init starts clean
        # First, put some poison into the types table
        mimetypes.add_type('foo/bar', '.foobar')
        self.assertEqual(mimetypes.guess_extension('foo/bar'), '.foobar')
        # Reinitialize
        mimetypes.init()
        # Poison should be gone.
        self.assertEqual(mimetypes.guess_extension('foo/bar'), None)

    @unittest.skipIf(sys.platform.startswith("win"), "Non-Windows only")
    def test_guess_known_extensions(self):
        # Issue 37529
        # The test fails on Windows because Windows adds mime types from the Registry
        # and that creates some duplicates.
        from mimetypes import types_map
        for v in types_map.values():
            self.assertIsNotNone(mimetypes.guess_extension(v))

    def test_preferred_extension(self):
        def check_extensions():
            self.assertEqual(mimetypes.guess_extension('application/octet-stream'), '.bin')
            self.assertEqual(mimetypes.guess_extension('application/postscript'), '.ps')
            self.assertEqual(mimetypes.guess_extension('application/vnd.apple.mpegurl'), '.m3u')
            self.assertEqual(mimetypes.guess_extension('application/vnd.ms-excel'), '.xls')
            self.assertEqual(mimetypes.guess_extension('application/vnd.ms-powerpoint'), '.ppt')
            self.assertEqual(mimetypes.guess_extension('application/x-texinfo'), '.texi')
            self.assertEqual(mimetypes.guess_extension('application/x-troff'), '.roff')
            self.assertEqual(mimetypes.guess_extension('application/xml'), '.xsl')
            self.assertEqual(mimetypes.guess_extension('audio/mpeg'), '.mp3')
            self.assertEqual(mimetypes.guess_extension('image/avif'), '.avif')
            self.assertEqual(mimetypes.guess_extension('image/jpeg'), '.jpg')
            self.assertEqual(mimetypes.guess_extension('image/tiff'), '.tiff')
            self.assertEqual(mimetypes.guess_extension('message/rfc822'), '.eml')
            self.assertEqual(mimetypes.guess_extension('text/html'), '.html')
            self.assertEqual(mimetypes.guess_extension('text/plain'), '.txt')
            self.assertEqual(mimetypes.guess_extension('text/x-rst'), '.rst')
            self.assertEqual(mimetypes.guess_extension('video/mpeg'), '.mpeg')
            self.assertEqual(mimetypes.guess_extension('video/quicktime'), '.mov')

        check_extensions()
        mimetypes.init()
        check_extensions()

    def test_init_stability(self):
        mimetypes.init()

        suffix_map = mimetypes.suffix_map
        encodings_map = mimetypes.encodings_map
        types_map = mimetypes.types_map
        common_types = mimetypes.common_types

        mimetypes.init()
        self.assertIsNot(suffix_map, mimetypes.suffix_map)
        self.assertIsNot(encodings_map, mimetypes.encodings_map)
        self.assertIsNot(types_map, mimetypes.types_map)
        self.assertIsNot(common_types, mimetypes.common_types)
        self.assertEqual(suffix_map, mimetypes.suffix_map)
        self.assertEqual(encodings_map, mimetypes.encodings_map)
        self.assertEqual(types_map, mimetypes.types_map)
        self.assertEqual(common_types, mimetypes.common_types)

    def test_path_like_ob(self):
        filename = "LICENSE.txt"
        filepath = os_helper.FakePath(filename)
        filepath_with_abs_dir = os_helper.FakePath('/dir/'+filename)
        filepath_relative = os_helper.FakePath('../dir/'+filename)
        path_dir = os_helper.FakePath('./')

        expected = self.db.guess_type(filename)

        self.assertEqual(self.db.guess_type(filepath), expected)
        self.assertEqual(self.db.guess_type(
            filepath_with_abs_dir), expected)
        self.assertEqual(self.db.guess_type(filepath_relative), expected)
        self.assertEqual(self.db.guess_type(path_dir), (None, None))

    def test_keywords_args_api(self):
        self.assertEqual(self.db.guess_type(
            url="foo.html", strict=True), ("text/html", None))
        self.assertEqual(self.db.guess_all_extensions(
            type='image/jpg', strict=True), [])
        self.assertEqual(self.db.guess_extension(
            type='image/jpg', strict=False), '.jpg')


@unittest.skipUnless(sys.platform.startswith("win"), "Windows only")
class Win32MimeTypesTestCase(unittest.TestCase):
    def setUp(self):
        # ensure all entries actually come from the Windows registry
        self.original_types_map = mimetypes.types_map.copy()
        mimetypes.types_map.clear()
        mimetypes.init()
        self.db = mimetypes.MimeTypes()

    def tearDown(self):
        # restore default settings
        mimetypes.types_map.clear()
        mimetypes.types_map.update(self.original_types_map)

    @unittest.skipIf(win32_edition() in ('NanoServer', 'WindowsCoreHeadless', 'IoTEdgeOS'),
                                         "MIME types registry keys unavailable")
    def test_registry_parsing(self):
        # the original, minimum contents of the MIME database in the
        # Windows registry is undocumented AFAIK.
        # Use file types that should *always* exist:
        eq = self.assertEqual
        eq(self.db.guess_type("foo.txt"), ("text/plain", None))
        eq(self.db.guess_type("image.jpg"), ("image/jpeg", None))
        eq(self.db.guess_type("image.png"), ("image/png", None))

    @unittest.skipIf(not hasattr(_winapi, "_mimetypes_read_windows_registry"),
                     "read_windows_registry accelerator unavailable")
    def test_registry_accelerator(self):
        from_accel = {}
        from_reg = {}
        _winapi._mimetypes_read_windows_registry(
            lambda v, k: from_accel.setdefault(k, set()).add(v)
        )
        mimetypes.MimeTypes._read_windows_registry(
            lambda v, k: from_reg.setdefault(k, set()).add(v)
        )
        self.assertEqual(list(from_reg), list(from_accel))
        for k in from_reg:
            self.assertEqual(from_reg[k], from_accel[k])


class MiscTestCase(unittest.TestCase):
    def test__all__(self):
        support.check__all__(self, mimetypes)


class MimetypesCliTestCase(unittest.TestCase):

    def mimetypes_cmd(self, *args, **kwargs):
        support.patch(self, sys, "argv", [sys.executable, *args])
        with support.captured_stdout() as output:
            mimetypes._main()
            return output.getvalue().strip()

    def test_help_option(self):
        support.patch(self, sys, "argv", [sys.executable, "-h"])
        with support.captured_stdout() as output:
            with self.assertRaises(SystemExit) as cm:
                mimetypes._main()

        self.assertIn("Usage: mimetypes.py", output.getvalue())
        self.assertEqual(cm.exception.code, 0)

    def test_invalid_option(self):
        support.patch(self, sys, "argv", [sys.executable, "--invalid"])
        with support.captured_stdout() as output:
            with self.assertRaises(SystemExit) as cm:
                mimetypes._main()

        self.assertIn("Usage: mimetypes.py", output.getvalue())
        self.assertEqual(cm.exception.code, 1)

    def test_guess_extension(self):
        eq = self.assertEqual

        extension = self.mimetypes_cmd("-l", "-e", "image/jpg")
        eq(extension, ".jpg")

        extension = self.mimetypes_cmd("-e", "image/jpg")
        eq(extension, "I don't know anything about type image/jpg")

        extension = self.mimetypes_cmd("-e", "image/jpeg")
        eq(extension, ".jpg")

    def test_guess_type(self):
        eq = self.assertEqual

        type_info = self.mimetypes_cmd("-l", "foo.pic")
        eq(type_info, "type: image/pict encoding: None")

        type_info = self.mimetypes_cmd("foo.pic")
        eq(type_info, "I don't know anything about type foo.pic")

if __name__ == "__main__":
    unittest.main()
