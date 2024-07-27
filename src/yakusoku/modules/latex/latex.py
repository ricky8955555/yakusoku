import io
from typing import Any

from matplotlib import pyplot


def render(expression: str, *, format: str | None = None, dpi: int | None = None) -> bytes:
    expression = "\n".join(f"${line}$" for line in expression.splitlines() if line)
    fig = pyplot.figure(figsize=(0.01, 0.01))
    try:
        fig.text(0, 0, expression)
        args: dict[str, Any] = {}
        if format:
            args["format"] = format
        if dpi:
            args["dpi"] = dpi
        buf = io.BytesIO()
        fig.savefig(buf, bbox_inches="tight", pad_inches=0.1, **args)
        buf.seek(0)
        return buf.read()
    finally:
        pyplot.close(fig)
