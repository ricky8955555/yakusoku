import re


_NORM_REGEXES: list[str] = [
    r"([a-zA-z])(?=[^\Wa-zA-Z])",  # foo先生 => foo 先生
    r"([^\Wa-zA-Z])(?=[a-zA-z])",  # 你好foo => 你好 foo
    r"([,.!?:;])(?=\w)",  # foo,bar => foo, bar
    r"([\d\w])(?=[#$%&*+/=?\\^`~])",  # foo &bar => foo & bar
    r"([#$%&*+/=?\\^`~])(?=[\d\w])",  # #foo => # foo
]


def normalize_string(s: str) -> str:
    for regex in _NORM_REGEXES:
        s = re.sub(regex, r"\g<1> ", s)
    return s


def complete_ul(s: str) -> str:
    if "了" in s:
        return s
    return s + "了"
