import string


def formatted_join(*strs: str) -> str:
    buffer = " "
    for s in strs:
        if buffer[-1] != " " and (buffer[-1] in string.printable) != (s[0] in string.printable):
            buffer += " "
        buffer += s
    return buffer[1:]
