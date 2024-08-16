from yakusoku.config import Config


class PixivConfig(Config):
    use_pixiv_cat_for_still: bool = True
    use_pixiv_cat_for_ugoira: bool = False
    pixiv_cat_base: str | None = None
    pximg_proxy: str | None = None
