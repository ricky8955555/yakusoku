from yakusoku.config import Config


class LatexConfig(Config):
    math_fontfamily: str | None = None
    dpi: int | None = None


config = LatexConfig.load("latex")
