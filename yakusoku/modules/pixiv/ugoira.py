import io
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import imageio
from aiofile import async_open
from imageio.typing import ArrayLike

from .types import Frame


async def compose_ugoira_gif(archive: bytes, frames: list[Frame]) -> bytes:
    with TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)
        with zipfile.ZipFile(io.BytesIO(archive)) as file:
            file.extractall(tempdir)
        images: list[ArrayLike] = []
        for frame in frames:
            image_path = tempdir / frame.file
            if not image_path.exists():
                raise FileNotFoundError(f"image {frame.file} was not found which ugoira needs.")
            async with async_open(image_path, "rb") as afp:
                data = await afp.read()
            image = imageio.imread(data)
            images.append(image)
        durations = [frame.delay for frame in frames]
        gif = imageio.mimwrite(
            "<bytes>",
            images,
            ".gif",  # type: ignore
            duration=durations,
        )
        return gif
