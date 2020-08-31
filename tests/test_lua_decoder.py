import unittest

from luafile import LuaDecoder, LuaDecodeError, LuaObj


class TestLuaParser(unittest.TestCase):
    def test_consume_whitespace(self):
        d = LuaDecoder(" \n\t \r ")
        d._consume_whitespace()
        self.assertEqual(d.idx, len(d.s))
        d = LuaDecoder(" \n\t \r end")
        d._consume_whitespace()
        self.assertEqual(d.idx, len(d.s) - 3)

    def test_expect(self):
        d = LuaDecoder("{end")
        d._expect("{", "Error")
        self.assertEqual(d.idx, 1)
        d = LuaDecoder("error")
        with self.assertRaises(LuaDecodeError):
            d._expect("{", "Error")

    def test_comma_or_end(self):
        d = LuaDecoder(", other")
        d._comma_or_end()
        self.assertEqual(d.idx, 2)
        d = LuaDecoder(",}")
        d._comma_or_end()
        self.assertEqual(d.idx, 1)
        d = LuaDecoder("} ok")
        d._comma_or_end()
        self.assertEqual(d.idx, 0)
        d = LuaDecoder("error")
        with self.assertRaises(LuaDecodeError):
            d._comma_or_end()

    def test_read_var_name(self):
        d = LuaDecoder("varname=")
        self.assertEqual(d._read_var_name(), "varname")
        self.assertEqual(d.idx, len(d.s) - 1)
        d = LuaDecoder("classname(1)")
        self.assertEqual(d._read_var_name(), "classname")
        self.assertEqual(d.idx, len(d.s) - 3)

    def test_read_string(self):
        d = LuaDecoder('"text"')
        self.assertEqual(d._read_string(), "text")
        self.assertEqual(d.idx, len(d.s))

    def test_read_number(self):
        d = LuaDecoder("1258)")
        self.assertEqual(d._read_number(), 1258)
        self.assertEqual(d.idx, len(d.s) - 1)
        d = LuaDecoder("-90\n")
        self.assertEqual(d._read_number(), -90)
        self.assertEqual(d.idx, len(d.s))
        d = LuaDecoder("-45.1,")
        self.assertEqual(d._read_number(), -45.1)
        self.assertEqual(d.idx, len(d.s) - 1)

    def test_read_table(self):
        d = LuaDecoder(
            """{
[2] = "two", 
[3] = "three", 
[1] = "one", 
["4"] = "four", 
[5] = "five" 
}"""
        )
        table = d._read_table()
        self.assertEqual(table, {1: "one", 2: "two", 3: "three", 5: "five", "4": "four"})
        # check order
        self.assertEqual(list(table)[0], 2)
        self.assertEqual(d.idx, len(d.s))
        d = LuaDecoder('{ 0,\n"one",2,}, ')
        table = d._read_table()
        self.assertEqual(table, [0, "one", 2])
        # check order
        self.assertEqual(d.idx, len(d.s) - 2)

    def test_read_reserved(self):
        d = LuaDecoder("true")
        self.assertEqual(d._read_reserved(), True)
        self.assertEqual(d.idx, len(d.s))
        d = LuaDecoder("false ")
        self.assertEqual(d._read_reserved(), False)
        self.assertEqual(d.idx, len(d.s))
        d = LuaDecoder("nil,")
        self.assertEqual(d._read_reserved(), None)
        self.assertEqual(d.idx, len(d.s) - 1)
        d = LuaDecoder("error")
        with self.assertRaises(LuaDecodeError):
            d._read_reserved()

    def test_read_obj(self):
        d = LuaDecoder("Point( 8, -1 )")
        self.assertEqual(d._read_obj(), LuaObj("Point", [8, -1]))
        self.assertEqual(d.idx, len(d.s))
        d = LuaDecoder("Effect({one = 1,}),")
        self.assertEqual(d._read_obj(), LuaObj("Effect", {"one": 1}))
        self.assertEqual(d.idx, len(d.s) - 1)
