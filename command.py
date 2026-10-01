"""Convert recognised Chinese or English speech into a strict LED command."""

from __future__ import annotations

from enum import Enum
import unicodedata


class Command(Enum):
    BLUE_ON = "LED,BLUE,ON"
    BLUE_OFF = "LED,BLUE,OFF"
    GREEN_ON = "LED,GREEN,ON"
    GREEN_OFF = "LED,GREEN,OFF"
    BLUE_BLINK_3 = "LED,BLUE,BLINK,3"
    GREEN_BLINK_3 = "LED,GREEN,BLINK,3"
    UNKNOWN = ""

    @property
    def protocol_message(self) -> str:
        """One newline-delimited serial command."""
        return f"{self.value}\n" if self.value else ""


# Whitelist only: every phrase not listed here becomes UNKNOWN and changes nothing.
# Unicode escapes keep this Python source portable across Windows code pages.
_COMMAND_ALIASES: dict[Command, set[str]] = {
    Command.BLUE_ON: {
        "\u5de6\u908a\u958b\u71c8", "\u5de6\u908a\u958b\u71c8\u85cd\u71c8", "\u85cd\u71c8\u958b", "\u958b\u85cd\u71c8",
        "turnonleftlight", "turnonbluelight", "leftlighton", "bluelighton",
    },
    Command.BLUE_OFF: {
        "\u5de6\u908a\u95dc\u71c8", "\u5de6\u908a\u95dc\u71c8\u85cd\u71c8", "\u85cd\u71c8\u95dc", "\u95dc\u85cd\u71c8",
        "turnoffleftlight", "turnoffbluelight", "leftlightoff", "bluelightoff",
    },
    Command.GREEN_ON: {
        "\u53f3\u908a\u958b\u71c8", "\u53f3\u908a\u958b\u71c8\u7da0\u71c8", "\u7da0\u71c8\u958b", "\u958b\u7da0\u71c8",
        "turnonrightlight", "turnongreenlight", "rightlighton", "greenlighton",
    },
    Command.GREEN_OFF: {
        "\u53f3\u908a\u95dc\u71c8", "\u53f3\u908a\u95dc\u71c8\u7da0\u71c8", "\u7da0\u71c8\u95dc", "\u95dc\u7da0\u71c8",
        "turnoffrightlight", "turnoffgreenlight", "rightlightoff", "greenlightoff",
    },
    Command.BLUE_BLINK_3: {
        "\u5de6\u908a\u9583\u723d\u4e09\u6b21", "\u5de6\u908a\u9583\u4e09\u6b21", "\u85cd\u71c8\u9583\u723d\u4e09\u6b21",
        "\u5de6\u908a\u9583\u723d3\u6b21", "\u5de6\u908a\u9583\u4e09\u4e0b", "\u5de6\u908a\u9583\u723d3\u4e0b",
        "blinkleftthreetimes", "leftblinkthreetimes", "blinkbluelightthreetimes", "blinkblue3times",
    },
    Command.GREEN_BLINK_3: {
        "\u53f3\u908a\u9583\u723d\u4e09\u6b21", "\u53f3\u908a\u9583\u4e09\u6b21", "\u7da0\u71c8\u9583\u723d\u4e09\u6b21",
        "\u53f3\u908a\u9583\u723d3\u6b21", "\u53f3\u908a\u9583\u4e09\u4e0b", "\u53f3\u908a\u9583\u723d3\u4e0b",
        "blinkrightthreetimes", "rightblinkthreetimes", "blinkgreenlightthreetimes", "blinkgreen3times",
    },
}


def normalise(text: str) -> str:
    """Ignore casing, spaces, punctuation, and invisible formatting characters."""
    normalised = unicodedata.normalize("NFKC", text).lower()
    # Google speech recognition has returned U+720D for the spoken word "閃爍".
    # Treat that observed transcription variant as the intended U+723D before whitelist matching.
    normalised = normalised.replace("\u720d", "\u723d")
    return "".join(character for character in normalised if character.isalnum())


def parse_command(text: str) -> Command:
    """Return a command only when the complete phrase matches the whitelist."""
    clean_text = normalise(text)
    for command, aliases in _COMMAND_ALIASES.items():
        if clean_text in aliases:
            return command
    return Command.UNKNOWN
