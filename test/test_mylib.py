import unittest
import mylib


class TestMyLib(unittest.TestCase):
    def test_add(self):
        self.assertEqual(mylib.add(1, 2), 3)

    def test_another_add(self):
        self.assertEqual(mylib.add(2, 2), 4)
