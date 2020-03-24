# Copyright 2014 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest

import mock


class Test__get_storage_host(unittest.TestCase):
    @staticmethod
    def _call_fut():
        from google.cloud.storage._helpers import _get_storage_host

        return _get_storage_host()

    def test_wo_env_var(self):
        from google.cloud.storage._helpers import _DEFAULT_STORAGE_HOST

        with mock.patch("os.environ", {}):
            host = self._call_fut()

        self.assertEqual(host, _DEFAULT_STORAGE_HOST)

    def test_w_env_var(self):
        from google.cloud.storage._helpers import STORAGE_EMULATOR_ENV_VAR

        HOST = "https://api.example.com"

        with mock.patch("os.environ", {STORAGE_EMULATOR_ENV_VAR: HOST}):
            host = self._call_fut()

        self.assertEqual(host, HOST)


class Test_PropertyMixin(unittest.TestCase):
    @staticmethod
    def _get_default_timeout():
        from google.cloud.storage.constants import _DEFAULT_TIMEOUT

        return _DEFAULT_TIMEOUT

    @staticmethod
    def _get_target_class():
        from google.cloud.storage._helpers import _PropertyMixin

        return _PropertyMixin

    def _make_one(self, *args, **kw):
        return self._get_target_class()(*args, **kw)

    def _derivedClass(self, path=None, user_project=None):
        class Derived(self._get_target_class()):

            client = None

            @property
            def path(self):
                return path

            @property
            def user_project(self):
                return user_project

        return Derived

    def test_path_is_abstract(self):
        mixin = self._make_one()
        with self.assertRaises(NotImplementedError):
            mixin.path

    def test_client_is_abstract(self):
        mixin = self._make_one()
        with self.assertRaises(NotImplementedError):
            mixin.client

    def test_user_project_is_abstract(self):
        mixin = self._make_one()
        with self.assertRaises(NotImplementedError):
            mixin.user_project

    def test__encryption_headers(self):
        mixin = self._make_one()
        self.assertEqual(mixin._encryption_headers(), {})

    def test__query_params_wo_user_project(self):
        derived = self._derivedClass("/path", None)()
        self.assertEqual(derived._query_params, {})

    def test__query_params_w_user_project(self):
        user_project = "user-project-123"
        derived = self._derivedClass("/path", user_project)()
        self.assertEqual(derived._query_params, {"userProject": user_project})

    def test_reload(self):
        connection = _Connection({"foo": "Foo"})
        client = _Client(connection)
        derived = self._derivedClass("/path")()
        # Make sure changes is not a set instance before calling reload
        # (which will clear / replace it with an empty set), checked below.
        derived._changes = object()
        derived.reload(client=client, timeout=42)
        self.assertEqual(derived._properties, {"foo": "Foo"})
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "GET",
                "path": "/path",
                "query_params": {"projection": "noAcl"},
                "headers": {},
                "_target_object": derived,
                "timeout": 42,
            },
        )
        self.assertEqual(derived._changes, set())

    def test_reload_w_user_project(self):
        user_project = "user-project-123"
        connection = _Connection({"foo": "Foo"})
        client = _Client(connection)
        derived = self._derivedClass("/path", user_project)()
        # Make sure changes is not a set instance before calling reload
        # (which will clear / replace it with an empty set), checked below.
        derived._changes = object()
        derived.reload(client=client)
        self.assertEqual(derived._properties, {"foo": "Foo"})
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "GET",
                "path": "/path",
                "query_params": {"projection": "noAcl", "userProject": user_project},
                "headers": {},
                "_target_object": derived,
                "timeout": self._get_default_timeout(),
            },
        )
        self.assertEqual(derived._changes, set())

    def test__set_properties(self):
        mixin = self._make_one()
        self.assertEqual(mixin._properties, {})
        VALUE = object()
        mixin._set_properties(VALUE)
        self.assertEqual(mixin._properties, VALUE)

    def test__patch_property(self):
        derived = self._derivedClass()()
        derived._patch_property("foo", "Foo")
        self.assertEqual(derived._properties, {"foo": "Foo"})

    def test_patch(self):
        connection = _Connection({"foo": "Foo"})
        client = _Client(connection)
        derived = self._derivedClass("/path")()
        # Make sure changes is non-empty, so we can observe a change.
        BAR = object()
        BAZ = object()
        derived._properties = {"bar": BAR, "baz": BAZ}
        derived._changes = set(["bar"])  # Ignore baz.
        derived.patch(client=client, timeout=42)
        self.assertEqual(derived._properties, {"foo": "Foo"})
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "PATCH",
                "path": "/path",
                "query_params": {"projection": "full"},
                # Since changes does not include `baz`, we don't see it sent.
                "data": {"bar": BAR},
                "_target_object": derived,
                "timeout": 42,
            },
        )
        # Make sure changes get reset by patch().
        self.assertEqual(derived._changes, set())

    def test_patch_w_user_project(self):
        user_project = "user-project-123"
        connection = _Connection({"foo": "Foo"})
        client = _Client(connection)
        derived = self._derivedClass("/path", user_project)()
        # Make sure changes is non-empty, so we can observe a change.
        BAR = object()
        BAZ = object()
        derived._properties = {"bar": BAR, "baz": BAZ}
        derived._changes = set(["bar"])  # Ignore baz.
        derived.patch(client=client)
        self.assertEqual(derived._properties, {"foo": "Foo"})
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(
            kw[0],
            {
                "method": "PATCH",
                "path": "/path",
                "query_params": {"projection": "full", "userProject": user_project},
                # Since changes does not include `baz`, we don't see it sent.
                "data": {"bar": BAR},
                "_target_object": derived,
                "timeout": self._get_default_timeout(),
            },
        )
        # Make sure changes get reset by patch().
        self.assertEqual(derived._changes, set())

    def test_update(self):
        connection = _Connection({"foo": "Foo"})
        client = _Client(connection)
        derived = self._derivedClass("/path")()
        # Make sure changes is non-empty, so we can observe a change.
        BAR = object()
        BAZ = object()
        derived._properties = {"bar": BAR, "baz": BAZ}
        derived._changes = set(["bar"])  # Update sends 'baz' anyway.
        derived.update(client=client, timeout=42)
        self.assertEqual(derived._properties, {"foo": "Foo"})
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "PUT")
        self.assertEqual(kw[0]["path"], "/path")
        self.assertEqual(kw[0]["query_params"], {"projection": "full"})
        self.assertEqual(kw[0]["data"], {"bar": BAR, "baz": BAZ})
        self.assertEqual(kw[0]["timeout"], 42)
        # Make sure changes get reset by patch().
        self.assertEqual(derived._changes, set())

    def test_update_w_user_project(self):
        user_project = "user-project-123"
        connection = _Connection({"foo": "Foo"})
        client = _Client(connection)
        derived = self._derivedClass("/path", user_project)()
        # Make sure changes is non-empty, so we can observe a change.
        BAR = object()
        BAZ = object()
        derived._properties = {"bar": BAR, "baz": BAZ}
        derived._changes = set(["bar"])  # Update sends 'baz' anyway.
        derived.update(client=client)
        self.assertEqual(derived._properties, {"foo": "Foo"})
        kw = connection._requested
        self.assertEqual(len(kw), 1)
        self.assertEqual(kw[0]["method"], "PUT")
        self.assertEqual(kw[0]["path"], "/path")
        self.assertEqual(
            kw[0]["query_params"], {"projection": "full", "userProject": user_project}
        )
        self.assertEqual(kw[0]["data"], {"bar": BAR, "baz": BAZ})
        self.assertEqual(kw[0]["timeout"], self._get_default_timeout())
        # Make sure changes get reset by patch().
        self.assertEqual(derived._changes, set())


class Test__scalar_property(unittest.TestCase):
    def _call_fut(self, fieldName):
        from google.cloud.storage._helpers import _scalar_property

        return _scalar_property(fieldName)

    def test_getter(self):
        class Test(object):
            def __init__(self, **kw):
                self._properties = kw.copy()

            do_re_mi = self._call_fut("solfege")

        test = Test(solfege="Latido")
        self.assertEqual(test.do_re_mi, "Latido")

    def test_setter(self):
        class Test(object):
            def _patch_property(self, name, value):
                self._patched = (name, value)

            do_re_mi = self._call_fut("solfege")

        test = Test()
        test.do_re_mi = "Latido"
        self.assertEqual(test._patched, ("solfege", "Latido"))


class Test__base64_md5hash(unittest.TestCase):
    def _call_fut(self, bytes_to_sign):
        from google.cloud.storage._helpers import _base64_md5hash

        return _base64_md5hash(bytes_to_sign)

    def test_it(self):
        from io import BytesIO

        BYTES_TO_SIGN = b"FOO"
        BUFFER = BytesIO()
        BUFFER.write(BYTES_TO_SIGN)
        BUFFER.seek(0)

        SIGNED_CONTENT = self._call_fut(BUFFER)
        self.assertEqual(SIGNED_CONTENT, b"kBiQqOnIz21aGlQrIp/r/w==")

    def test_it_with_stubs(self):
        import mock

        class _Buffer(object):
            def __init__(self, return_vals):
                self.return_vals = return_vals
                self._block_sizes = []

            def read(self, block_size):
                self._block_sizes.append(block_size)
                return self.return_vals.pop()

        BASE64 = _Base64()
        DIGEST_VAL = object()
        BYTES_TO_SIGN = b"BYTES_TO_SIGN"
        BUFFER = _Buffer([b"", BYTES_TO_SIGN])
        MD5 = _MD5(DIGEST_VAL)

        patch = mock.patch.multiple(
            "google.cloud.storage._helpers", base64=BASE64, md5=MD5
        )
        with patch:
            SIGNED_CONTENT = self._call_fut(BUFFER)

        self.assertEqual(BUFFER._block_sizes, [8192, 8192])
        self.assertIs(SIGNED_CONTENT, DIGEST_VAL)
        self.assertEqual(BASE64._called_b64encode, [DIGEST_VAL])
        self.assertEqual(MD5._called, [None])
        self.assertEqual(MD5.hash_obj.num_digest_calls, 1)
        self.assertEqual(MD5.hash_obj._blocks, [BYTES_TO_SIGN])


class Test__base64_crc32chash(unittest.TestCase):
    def _call_fut(self, bytes_to_sign):
        from google.cloud.storage._helpers import _base64_crc32chash

        return _base64_crc32chash(bytes_to_sign)

    def test_it(self):
        from io import BytesIO

        BYTES_TO_SIGN = b"FOO"
        BUFFER = BytesIO()
        BUFFER.write(BYTES_TO_SIGN)
        BUFFER.seek(0)

        SIGNED_CONTENT = self._call_fut(BUFFER)
        self.assertEqual(SIGNED_CONTENT, b"cbY41Q==")

    def test_it_with_stubs(self):
        import mock

        class _Buffer(object):
            def __init__(self, return_vals):
                self.return_vals = return_vals
                self._block_sizes = []

            def read(self, block_size):
                self._block_sizes.append(block_size)
                return self.return_vals.pop()

        BASE64 = _Base64()
        DIGEST_VAL = object()
        BYTES_TO_SIGN = b"BYTES_TO_SIGN"
        BUFFER = _Buffer([b"", BYTES_TO_SIGN])
        CRC32C = _CRC32C(DIGEST_VAL)

        patch = mock.patch.multiple(
            "google.cloud.storage._helpers", base64=BASE64, _get_crc32c_object=CRC32C
        )
        with patch:
            SIGNED_CONTENT = self._call_fut(BUFFER)

        self.assertEqual(BUFFER._block_sizes, [8192, 8192])
        self.assertIs(SIGNED_CONTENT, DIGEST_VAL)
        self.assertEqual(BASE64._called_b64encode, [DIGEST_VAL])
        self.assertEqual(CRC32C._called, [None])
        self.assertEqual(CRC32C.hash_obj.num_digest_calls, 1)
        self.assertEqual(CRC32C.hash_obj._blocks, [BYTES_TO_SIGN])

    def test_crc32c_throws_import_error(self):
        import mock
        from google.cloud.storage._helpers import _get_crc32c_object

        try:
            import builtins
        except ImportError:
            import __builtin__ as builtins
        orig_import = builtins.__import__

        # Raises ImportError for name == "crc32c" or name == "crcmod"
        def mock_import(name, globals, locals, fromlist, level=None):
            raise ImportError

        builtins.__import__ = mock_import

        try:
            with self.assertRaises(ImportError):
                _get_crc32c_object()
        finally:
            builtins.__import__ = orig_import


    def test_crc32c_warning_on_slow_crcmod(self):
        import mock
        from google.cloud.storage._helpers import _is_fast_crcmod

        try:
            import builtins
        except ImportError:
            import __builtin__ as builtins

        orig_import = builtins.__import__

        # crcmod.crcmod is the only import.
        def mock_import(name, globals, locals, fromlist, level):
            crcmod = mock.MagicMock()
            crcmod._usingExtension = False
            return crcmod

        builtins.__import__ = mock_import

        try:
            self.assertFalse(_is_fast_crcmod())
        finally:
            builtins.__import__ = orig_import


class _Connection(object):
    def __init__(self, *responses):
        self._responses = responses
        self._requested = []

    def api_request(self, **kw):
        self._requested.append(kw)
        response, self._responses = self._responses[0], self._responses[1:]
        return response


class _Hash(object):
    def __init__(self, digest_val):
        self.digest_val = digest_val
        self.num_digest_calls = 0
        self._blocks = []

    def update(self, block):
        self._blocks.append(block)

    def digest(self):
        self.num_digest_calls += 1
        return self.digest_val


class _MD5(object):
    def __init__(self, digest_val):
        self.hash_obj = _Hash(digest_val)
        self._called = []

    def __call__(self, data=None):
        self._called.append(data)
        return self.hash_obj


class _CRC32C(object):
    def __init__(self, digest_val):
        self.hash_obj = _Hash(digest_val)
        self._called = []

    def __call__(self, data=None):
        self._called.append(data)
        return self.hash_obj


class _Base64(object):
    def __init__(self):
        self._called_b64encode = []

    def b64encode(self, value):
        self._called_b64encode.append(value)
        return value


class _Client(object):
    def __init__(self, connection):
        self._connection = connection
