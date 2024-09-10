from yakusoku.config import Config


class ModuleConfig(Config):
    use_rdap: bool = True


config = ModuleConfig.load("waifu")
