from django.test import TestCase

from app.calc import substract


class  CalcTests(TestCase):

    def test_substract_numbers(self):
        """Test two number substraction"""
        self.assertEqual(substract(15, 6), 9, 'Substraction Failed')
