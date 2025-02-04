# coding: UTF-8

"""This file contains examples of using `enum`. For its documentation, see
https://docs.python.org/3/library/enum.html
This document is referred to as `DOC` in the code.
"""

import enum
import unittest


# `Color` comes from the DOC.
class Color(enum.Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class TestEnum(unittest.TestCase):
    def test_member_type(self):
        """Test point: What is the type of an enum member (e.g., `RED`)?
        """
        # An `Enum`'s memeber is, of course, of the type of the enumeration
        # itself. It's not `int` even though it looks like an integer.
        for e in (Color.RED, Color.GREEN, Color.BLUE):
            self.assertNotIsInstance(e, int)
            self.assertIsInstance(e, Color)

    def test_member_name_and_value(self):
        """Test point: How to get the name and the integral value of an enum
        member (e.g., `RED`)?
        """
        for e, name_value in zip(
            # The enum members.
            [Color.RED, Color.GREEN, Color.BLUE],
            # The names and the integral values.
            [("RED", 1), ("GREEN", 2), ("BLUE", 3)],
        ):
            self.assertEqual(e.name, name_value[0])
            self.assertEqual(e.value, name_value[1])


NAME_ALICE = "Alice"
NAME_BOB = "Bob"


class Name(enum.StrEnum):
    ALICE = NAME_ALICE
    BOB = NAME_BOB

    @staticmethod
    def has_value(s):
        return s == Name.ALICE or s == Name.BOB


class TestEnum(unittest.TestCase):
    def test_has_value(self):
        self.assertTrue(Name.has_value(NAME_ALICE))
        self.assertTrue(Name.has_value(Name.ALICE))

        self.assertFalse(Name.has_value("alicE"))


if __name__ == "__main__":
    unittest.main()
