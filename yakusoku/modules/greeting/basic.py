from datetime import time

GREETINGS = {
    time(0): "晚上好",
    time(6): "晚上好哦夜猫子",
    time(11): "早上好",
    time(13): "中午好",
    time(17): "傍晚好",
}


def basic_greeting(query: time) -> str:
    for t, greeting in GREETINGS.items():
        if query < t:
            return greeting
    return next(iter(GREETINGS.values()))
