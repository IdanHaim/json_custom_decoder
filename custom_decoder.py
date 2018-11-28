from json.decoder import py_scanstring, JSONDecodeError, WHITESPACE, WHITESPACE_STR
import custom_scanner
import base64
import json

"""
This is a custom decoder for JsonDecoder.
Override JsonDecoder and JsonObject to be able to parse json back to object
For doing this we only need to add 2 more properties to json.load:
1) object_type the main type of the json
2) object_mapper = A method that decode the value of the string by key, value
    Example:
    def object_mapper(key, value):
        if key == "address":
            return Address(**value)
            
To use this custom decoder just import the JsonDecoder and use with json:
json.loads(json_string, cls=JsonDecoder, object_type=Owner, object_mapper=object_mapper)
"""


def _parse_string(*args, **kwargs):
    s, idx = py_scanstring(*args, **kwargs)
    if s and s[0] == u'\x00':
        s = base64.b64decode(s[1:])
    return s, idx


def JsonObject(s_and_end, strict, scan_once, object_hook, object_pairs_hook, object_mapper,
               memo=None, _w=WHITESPACE.match, _ws=WHITESPACE_STR):
    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    # Backwards compatibility
    if memo is None:
        memo = {}
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end:end + 1]
    # Normally we expect nextchar == '"'
    if nextchar != '"':
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end:end + 1]
        # Trivial empty object
        if nextchar == '}':
            if object_pairs_hook is not None:
                result = object_pairs_hook(pairs)
                return result, end + 1
            pairs = {}
            if object_hook is not None:
                pairs = object_hook(pairs)
            return pairs, end + 1
        elif nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end)
    end += 1
    while True:
        key, end = py_scanstring(s, end, strict)
        key = memo_get(key, key)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end:end + 1] != ':':
            end = _w(s, end).end()
            if s[end:end + 1] != ':':
                raise JSONDecodeError("Expecting ':' delimiter", s, end)
        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        try:
            value, end = scan_once(s, end)
        except StopIteration as err:
            raise JSONDecodeError("Expecting value", s, err.value) from None
        pairs_append((key, value))
        try:
            nextchar = s[end]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end]
        except IndexError:
            nextchar = ''
        end += 1

        if nextchar == '}':
            break
        elif nextchar != ',':
            raise JSONDecodeError("Expecting ',' delimiter", s, end - 1)
        end = _w(s, end).end()
        nextchar = s[end:end + 1]
        end += 1
        if nextchar != '"':
            raise JSONDecodeError(
                "Expecting property name enclosed in double quotes", s, end - 1)
    if object_pairs_hook is not None:
        result = object_pairs_hook(pairs)
        return result, end
    pairs = dict(pairs)
    if object_hook is not None:
        pairs = object_hook(pairs)
    o = object_mapper(key, value)
    if o is not None:
        pairs[key] = o
    return pairs, end


class JsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        self._object_type = kwargs.pop("object_type", None)
        self.object_mapper = kwargs.pop("object_mapper", lambda key, value: None)
        super(JsonDecoder, self).__init__(*args, **kwargs)
        self.parse_string = _parse_string
        # we need to use our custom JsonObject to be able to return objects from mapper
        self.parse_object = JsonObject
        # we need to use a custom scanner only to be able to give the mapper method to the JsonObject
        self.scan_once = custom_scanner.py_make_scanner(self)

    def decode(self, s, _w=WHITESPACE.match):
        obj = super(JsonDecoder, self).decode(s, _w)
        if self._object_type:
            try:
                return self._object_type(**obj)
            except TypeError as e:
                raise TypeError("Failed to decode json_string to {0}".format(self._object_type), s, e)
        return obj
