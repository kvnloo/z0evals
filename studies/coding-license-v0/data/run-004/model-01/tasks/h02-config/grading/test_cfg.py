import os
import tempfile
import unittest
from cfg import load_file, load_string
from cfg.errors import ConfigError


class T(unittest.TestCase):
    def test_env(self):
        d = load_string("[s]\na=${HOME_X}/x\nb=${NOPE:-dflt}", env={"HOME_X": "/h"})
        self.assertEqual(d, {"s": {"a": "/h/x", "b": "dflt"}})

    def test_missing(self):
        with self.assertRaises(ConfigError):
            load_string("[s]\na=${NOPE}", env={})

    def test_include(self):
        with tempfile.TemporaryDirectory() as t:
            open(os.path.join(t, "base.cfg"), "w").write("[db]\nhost=localhost\nport=1\n")
            open(os.path.join(t, "main.cfg"), "w").write("@include base.cfg\n[db]\nport=2\n")
            self.assertEqual(load_file(os.path.join(t, "main.cfg"), env={}),
                             {"db": {"host": "localhost", "port": "2"}})
