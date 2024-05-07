from typing import Generator


def cut_message(
    message: str, wrap_after: str = "\n", max_length: int = 2048, force_cut: bool = True
) -> Generator[str, None, None]:
    while message:
        if len(message) <= max_length:
            yield message
            return

        try:
            if wrap_after:
                end = message.rindex(wrap_after, 0, max_length)
            else:
                end = max_length
        except ValueError:
            if not force_cut:
                raise
            end = max_length

        end += 1
        yield message[:end]
        message = message[end:]
