from yakusoku.config import Config


class SlashConfig(Config):
    prpr_verbs: list[str] = []
    overwritten_prpr_verbs: bool = False


config = SlashConfig.load("slash")
