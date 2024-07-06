from datetime import timedelta

from yakusoku.config import Config


class ArchiveConfig(Config):
    avatar_ttl: timedelta = timedelta(minutes=30)


config = ArchiveConfig.load("archive")
