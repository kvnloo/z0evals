import unittest
from report import total_by_category
class T(unittest.TestCase):
    def test_quoted(self):
        text = 'category,amount\n"Food, drinks",2.5\nRent,10\n"Food, drinks",1\n'
        self.assertEqual(total_by_category(text), {"Food, drinks": 3.5, "Rent": 10.0})
if __name__ == "__main__": unittest.main()
