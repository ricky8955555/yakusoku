import re

_NORM_REGEXES: list[str] = [
    r"([a-zA-z0-9])(?=[^\Wa-zA-Z0-9])",  # foo先生 => foo 先生
    r"([^\Wa-zA-Z0-9])(?=[a-zA-z0-9])",  # 你好foo => 你好 foo
    r"([,.!?:;])(?=\w)",  # foo,bar => foo, bar
    r"([^\W\da-zA-Z])(?=\d)",  # 正在0721 => 正在 0721
    r"(\d)(?=[^\W\da-zA-Z])",  # 0721对身体好 => 0721 对身体好
]


def normalize_string(s: str) -> str:
    for regex in _NORM_REGEXES:
        s = re.sub(regex, r"\g<1> ", s)
    return s


def complete_ul(s: str) -> str:
    if "了" in s:
        return s
    return s + "了"
