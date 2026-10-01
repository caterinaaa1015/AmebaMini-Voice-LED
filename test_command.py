"""Core tests that do not need an Ameba board."""

import unittest

from command import Command, parse_command
from serial_controller import CommunicationError, MockAmebaController


class CommandParserTests(unittest.TestCase):
    def test_chinese_commands(self) -> None:
        self.assertEqual(parse_command("\u5de6\u908a\u958b\u71c8"), Command.BLUE_ON)
        self.assertEqual(parse_command("\u53f3\u908a\u958b\u71c8"), Command.GREEN_ON)
        self.assertEqual(parse_command("\u5de6\u908a\u95dc\u71c8"), Command.BLUE_OFF)
        self.assertEqual(parse_command("\u53f3\u908a\u95dc\u71c8"), Command.GREEN_OFF)
        self.assertEqual(parse_command("\u5de6\u908a\u9583\u723d\u4e09\u6b21"), Command.BLUE_BLINK_3)
        self.assertEqual(parse_command("\u5de6\u908a\u9583\u723d3\u6b21"), Command.BLUE_BLINK_3)
        self.assertEqual(parse_command("\u5de6\u908a\u9583\u720d3\u6b21"), Command.BLUE_BLINK_3)
        self.assertEqual(parse_command("\u53f3\u908a\u9583\u723d\u4e09\u6b21"), Command.GREEN_BLINK_3)
        self.assertEqual(parse_command("\u53f3\u908a\u9583\u723d3\u6b21"), Command.GREEN_BLINK_3)

    def test_english_commands(self) -> None:
        self.assertEqual(parse_command("turn on left light"), Command.BLUE_ON)
        self.assertEqual(parse_command("turn on right light"), Command.GREEN_ON)
        self.assertEqual(parse_command("blink left three times"), Command.BLUE_BLINK_3)
        self.assertEqual(parse_command("blink green light three times"), Command.GREEN_BLINK_3)

    def test_punctuation_and_spaces_are_allowed(self) -> None:
        self.assertEqual(parse_command(" Turn on blue light. "), Command.BLUE_ON)
        self.assertEqual(parse_command("\u5de6\u908a\u9583\u723d\u200b\u4e09\u6b21"), Command.BLUE_BLINK_3)

    def test_non_control_text_never_creates_a_command(self) -> None:
        self.assertEqual(parse_command("\u4eca\u5929\u5929\u6c23\u5f88\u597d"), Command.UNKNOWN)
        self.assertEqual(parse_command("turn on every light"), Command.UNKNOWN)


class MockControllerTests(unittest.TestCase):
    def test_state_is_returned_by_mock(self) -> None:
        controller = MockAmebaController()
        self.assertEqual(controller.send(Command.BLUE_ON), {"blue": True, "green": False})
        self.assertEqual(controller.send(Command.GREEN_ON), {"blue": True, "green": True})
        self.assertEqual(controller.send(Command.BLUE_BLINK_3), {"blue": False, "green": True})

    def test_disconnection_is_reported(self) -> None:
        controller = MockAmebaController(disconnected=True)
        with self.assertRaises(CommunicationError):
            controller.send(Command.BLUE_ON)


if __name__ == "__main__":
    unittest.main(verbosity=2)
