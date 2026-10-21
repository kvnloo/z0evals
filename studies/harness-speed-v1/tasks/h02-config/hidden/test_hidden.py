import os
import tempfile
import unittest
from cfg import load_file, load_string
from cfg.errors import ConfigError
from cfg.interp import expand


class H(unittest.TestCase):
    def test_expand(self):
        self.assertEqual(expand("a$$b ${X}", {"X": "1"}), "a$b 1")
        self.assertEqual(expand("${Y:-}", {}), "")

    def test_default_env_is_os_environ(self):
        os.environ["HSB_CFG_T"] = "zz"
        self.assertEqual(load_string("[s]\na=${HSB_CFG_T}"), {"s": {"a": "zz"}})

    def test_cycle(self):
        with tempfile.TemporaryDirectory() as t:
            open(os.path.join(t, "a.cfg"), "w").write("@include b.cfg\n")
            open(os.path.join(t, "b.cfg"), "w").write("@include a.cfg\n")
            with self.assertRaises(ConfigError):
                load_file(os.path.join(t, "a.cfg"), env={})

    def test_nested_relative_and_order(self):
        with tempfile.TemporaryDirectory() as t:
            os.makedirs(os.path.join(t, "sub"))
            open(os.path.join(t, "sub", "inner.cfg"), "w").write("[x]\nk=inner\nj=${J:-dj}\n")
            open(os.path.join(t, "sub", "mid.cfg"), "w").write("@include inner.cfg\n[y]\nm=1\n")
            open(os.path.join(t, "top.cfg"), "w").write("[x]\nk=top\n@include sub/mid.cfg\nl=after\n")
            got = load_file(os.path.join(t, "top.cfg"), env={})
            self.assertEqual(got, {"x": {"k": "inner", "j": "dj", "l": "after"}, "y": {"m": "1"}})

    def test_include_from_string_base_dir(self):
        with tempfile.TemporaryDirectory() as t:
            open(os.path.join(t, "b.cfg"), "w").write("[q]\nv=1\n")
            self.assertEqual(load_string("@include b.cfg", base_dir=t, env={}), {"q": {"v": "1"}})
