"""A very simple Lua reader and writer.

Tested only with Into The Breach files!"""
from collections import namedtuple

LuaObj = namedtuple("LuaObj", ["name", "params"])


class LuaNumber:
    def __init__(self, s):
        self.s = str(s)
        try:
            self.n = int(s)
        except ValueError:
            self.n = float(s)

    def __str__(self):
        return self.s

    def __eq__(self, other):
        if isinstance(other, LuaNumber):
            return other.s == self.s
        if isinstance(other, int):
            try:
                return int(self.s) == other
            except ValueError:
                return False
        if isinstance(other, float):
            try:
                return float(self.s) == other
            except ValueError:
                return False
        if isinstance(other, str):
            return other == self.s
        return False

    def __hash__(self):
        return hash(self.n)

    def __repr__(self):
        return repr(self.n)


class LuaDecodeError(ValueError):
    def __init__(self, msg, string, idx):
        lineno = string.count("\n", 0, idx) + 1
        colno = idx - string.rfind("\n", 0, idx)
        errmsg = "%s: line %d column %d (char %d)" % (msg, lineno, colno, idx)
        ValueError.__init__(self, errmsg)
        self.msg = msg
        self.idx = idx
        self.lineno = lineno
        self.colno = colno


class LuaDecoder:
    def __init__(self, s):
        self.s = str(s)
        self.idx = 0

    def _raise(self, msg, delta=0):
        """Utility method to raise an exception"""
        raise LuaDecodeError(msg, self.s, self.idx + delta)

    def _consume_whitespace(self):
        """Move idx foward, to the next non-space character"""
        try:
            while self.s[self.idx] in " \t\n\r":
                self.idx += 1
        except IndexError:
            pass

    def _expect(self, c, msg, consume=True):
        """Check if the next char is `c` and move foward, or raise an error"""
        if self.s[self.idx] != c:
            self._raise("Expecting '{}' {}".format(c, msg))
        self.idx += 1
        if consume:
            self._consume_whitespace()

    def _comma_or_end(self):
        """Check if the next char is a comma or the end of a list (ie: `}` or `{`)"""
        if self.s[self.idx] == ",":
            self.idx += 1
            self._consume_whitespace()
        else:
            if self.s[self.idx] not in "})":
                self._raise("Expecting '}' or ')' end")

    def _read_var_name(self):
        """Read until `=` or `(`"""
        var_name = ""
        i = self.idx
        while self.s[i] not in "=( ":
            i += 1
        var_name = self.s[self.idx : i]
        self.idx = i
        self._consume_whitespace()
        return var_name

    def _read_string(self):
        """Read a string, between `"`."""
        self._expect('"', "separator", False)
        i = self.idx
        # TODO escaped quote
        while self.s[i] != '"':  # or (self.s[i] == '"' and self.s[i-1] != "\\"):
            i += 1
        string = self.s[self.idx : i]
        self.idx = i + 1
        return string

    def _read_number(self):
        """Read a signed integer or float"""
        snumber = ""
        i = self.idx
        if self.s[i] == "-":
            i += 1
        while self.s[i] in ("0123456789"):
            i += 1
        if self.s[i] == ".":
            i += 1
            if self.s[i] not in ("0123456789"):
                self._raise("Expecting a number after '.' separator", delta=i - self.idx)
            while self.s[i] in ("0123456789"):
                i += 1
        snumber = self.s[self.idx : i]
        pnumber = LuaNumber(snumber)
        self.idx = i
        self._consume_whitespace()
        return pnumber

    def _read_table_dict(self):
        """Read a Lua table with keys."""
        data = {}
        while self.s[self.idx] != "}":
            self._expect("[", "dict table key")
            if self.s[self.idx] == '"':
                k = self._read_string()
            else:
                k = self._read_number()
            self._expect("]", "dict table key")
            self._expect("=", "separator")
            v = self._read_exp()
            self._consume_whitespace()
            data[k] = v
            self._comma_or_end()
        self.idx += 1
        return data

    def _read_table_list(self):
        """Read a Lua table as a array."""
        data = []
        while self.s[self.idx] not in "})":
            v = self._read_exp()
            self._consume_whitespace()
            data.append(v)
            self._comma_or_end()
        self.idx += 1
        return data

    def _read_table(self):
        """Read a Lua table, any type."""
        self._expect("{", "separator")
        if self.s[self.idx] == "[":
            return self._read_table_dict()
        else:
            return self._read_table_list()
        self._expect("}", "separator")

    def _read_reserved(self):
        """Read nil, false or true."""
        if self.s[self.idx : self.idx + 3] == "nil":
            self.idx += 3
            self._consume_whitespace()
            return None
        if self.s[self.idx : self.idx + 4] == "true":
            self.idx += 4
            self._consume_whitespace()
            return True
        if self.s[self.idx : self.idx + 5] == "false":
            self.idx += 5
            self._consume_whitespace()
            return False
        raise self._raise("Unkown reserved word")

    def _read_obj(self):
        """Read a custom Lua object creation."""
        obj_name = self._read_var_name()
        self._expect("(", "separator")
        if self.s[self.idx] == "{":
            obj_params = {}
            self._expect("{", "separator")
            while self.s[self.idx] != "}":
                k = self._read_var_name()
                self._expect("=", "separator")
                v = self._read_exp()
                obj_params[k] = v
                self._comma_or_end()
            self._expect("}", "separator")
            self._expect(")", "separator")
        else:
            obj_params = self._read_table_list()
        return LuaObj(obj_name, obj_params)

    def _read_exp(self):
        """Read a Lua expression"""
        if self.s[self.idx] == "{":
            return self._read_table()
        if self.s[self.idx] == '"':
            return self._read_string()
        if self.s[self.idx] in "-0123456789":
            return self._read_number()
        try:
            return self._read_reserved()
        except ValueError:
            return self._read_obj()

    def parse(self):
        """Parse a string composed of (multiple) varibile=expression"""
        data = {}
        while self.idx < len(self.s):
            k = self._read_var_name()
            self._expect("=", "separator")
            v = self._read_exp()
            data[k] = v
            self._consume_whitespace()
        return data


class LuaEncoder:
    @classmethod
    def _write_list_table(cls, obj):
        return "{" + ", ".join([cls._write_exp(v) for v in obj]) + ", }"

    @classmethod
    def _write_dict_table(cls, obj):
        return (
            "{"
            + ", ".join(
                ["[{}] = {}".format(cls._write_exp(k), cls._write_exp(v)) for k, v in obj.items()]
            )
            + ", }"
        )

    @classmethod
    def _write_obj(cls, obj):
        if isinstance(obj.params, list):
            return obj.name + "( " + ", ".join([cls._write_exp(v) for v in obj.params]) + " )"
        if isinstance(obj.params, dict):
            return (
                obj.name
                + "({"
                + ", ".join(["{} = {}".format(k, cls._write_exp(v)) for k, v in obj.params.items()])
                + ",})"
            )
        raise ValueError(obj.params)

    @classmethod
    def _write_exp(cls, obj):
        if isinstance(obj, str):
            return '"' + obj + '"'
        if isinstance(obj, LuaNumber):
            return obj.s
        if isinstance(obj, bool):
            # bool before int
            if obj:
                return "true"
            return "false"
        if isinstance(obj, int) or isinstance(obj, float):
            return str(obj)
        if isinstance(obj, dict):
            return cls._write_dict_table(obj)
        if isinstance(obj, list):
            return cls._write_list_table(obj)
        if isinstance(obj, LuaObj):
            return cls._write_obj(obj)
        if obj is None:
            return "nil"
        raise ValueError(obj)

    @classmethod
    def dumps(cls, data):
        s = ""
        for k, v in data.items():
            s += k
            s += " = "
            s += cls._write_exp(v)
        return s


def dumps(obj):
    """Serialize obj as a Lua object."""
    return LuaEncoder.dumps(obj)


def loads(s):
    """"Deserialize a Lua content to a Python object."""
    return LuaDecoder(s).parse()
