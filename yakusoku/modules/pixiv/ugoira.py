import io
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from .types import Frame


def compose_ugoira_gif(archive: bytes, frames: list[Frame]) -> bytes:
    with TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        with zipfile.ZipFile(io.BytesIO(archive)) as file:
            file.extractall(tempdir)
        images = (Image.open(tempdir / frame.file) for frame in frames)
        durations = [frame.delay for frame in frames]
        gif = io.BytesIO()
        next(images).save(
            gif,
            "GIF",
            save_all=True,
            append_images=images,
            duration=durations,
            loop=0,
        )
        gif.seek(0)
        return gif.read()
