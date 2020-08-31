import unittest

from luafile import LuaEncoder, LuaObj, LuaNumber


class TestLuaEncoder(unittest.TestCase):
    def test_write_simple_exp(self):
        s = LuaEncoder._write_exp("string")
        self.assertEqual(s, '"string"')
        s = LuaEncoder._write_exp(True)
        self.assertEqual(s, "true")
        s = LuaEncoder._write_exp(False)
        self.assertEqual(s, "false")
        s = LuaEncoder._write_exp(None)
        self.assertEqual(s, "nil")

    def test_write_number(self):
        s = LuaEncoder._write_exp(LuaNumber("1"))
        self.assertEqual(s, "1")
        s = LuaEncoder._write_exp(LuaNumber("9.5"))
        self.assertEqual(s, "9.5")
        s = LuaEncoder._write_exp(LuaNumber("-9.5"))
        self.assertEqual(s, "-9.5")
        s = LuaEncoder._write_exp(LuaNumber("-9.5000"))
        self.assertEqual(s, "-9.5000")

    def test_write_obj(self):
        s = LuaEncoder._write_obj(LuaObj("Point", [8, -1]))
        self.assertEqual(s, "Point( 8, -1 )")
        s = LuaEncoder._write_obj(LuaObj("Effect", {"one": 1}))
        self.assertEqual(s, "Effect({one = 1,})")
        s = LuaEncoder._write_obj(LuaObj("Effect", {}))
        self.assertEqual(s, "Effect({})")

    def test_write_tables(self):
        s = LuaEncoder._write_list_table([0, "one", 2])
        self.assertEqual(s, '{0, "one", 2, }')
        s = LuaEncoder._write_dict_table({1: "one", 2: "two", 3: "three", 5: "five", "4": "four"})
        self.assertEqual(
            s,
            '{[1] = "one", [2] = "two", [3] = "three", [5] = "five", ["4"] = "four", }',
        )
        s = LuaEncoder._write_list_table([])
        self.assertEqual(s, "{}")
