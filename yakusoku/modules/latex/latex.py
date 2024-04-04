import io
from typing import Any

from matplotlib import pyplot


def render(expression: str, *, format: str | None = None, dpi: int | None = None) -> bytes:
    fig = pyplot.figure(figsize=(0.01, 0.01))
    try:
        fig.text(0, 0, f"${expression}$")
        args: dict[str, Any] = {}
        if format:
            args["format"] = format
        if dpi:
            args["dpi"] = dpi
        buf = io.BytesIO()
        pyplot.savefig(buf, bbox_inches="tight", pad_inches=0.1, **args)
        buf.seek(0)
        return buf.read()
    finally:
        pyplot.close(fig)
