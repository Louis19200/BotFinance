import unittest

class TestBasic(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(1 + 1, 2)

    def test_string(self):
        self.assertIn("bot", "botfinance")

if __name__ == '__main__':
    unittest.main()
