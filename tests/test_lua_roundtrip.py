import unittest

from luafile import LuaEncoder, LuaDecoder


class TestLuaRoundtrip(unittest.TestCase):
    def test_roundtrip(self):
        test = """
GameData = {
    ["version"] = 1,
    ["lang"] = 1,
    ["info"] = {
        ["squad"] = "B",
        ["trackers"] = {
            ["B_2"] = 0,
            ["A_1"] = 0,
        },
    },

    ["current"] = {
        ["score"] = 6459,
        ["time"] = 3316446.500000,
        ["victory"] = false,
        ["mechs"] = {
            "FlameMech",
            "IgniteMech",
            "TeleMech",
        },
        ["colors"] = {
            5,
            5,
            5,
        },
        ["weapons"] = {
            "A",
            "Passive",
            "",
            "Science",
            "",
        },
    },
    ["current_squad"] = 5,
}
""".replace(
            "\n", ""
        ).replace(
            "\r", ""
        )

        data = LuaDecoder(test).parse()
        self.assertEqual(test.replace(" ", ""), LuaEncoder.dumps(data).replace(" ", ""))
