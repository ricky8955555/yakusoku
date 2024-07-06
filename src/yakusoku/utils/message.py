from typing import Generator


def cut_message(
    message: str,
    pattern: str = "\n",
    with_pattern: bool = True,
    max_length: int = 2048,
    force_cut: bool = True,
) -> Generator[str, None, None]:
    pattern_length = len(pattern)

    while message:
        if len(message) <= max_length:
            yield message
            return

        try:
            if pattern:
                end = message.rindex(pattern, 0, max_length)
            else:
                end = max_length
        except ValueError:
            if not force_cut:
                raise
            end = max_length

        if with_pattern:
            yield message[: end + pattern_length]
        else:
            yield message[:end]

        message = message[end + pattern_length :]
