from datetime import timedelta

from yakusoku.config import Config


class ModuleConfig(Config):
    check_ttl: timedelta = timedelta(minutes=5)
    trigger_span: timedelta = timedelta(hours=6)
    initial_trigger_span: timedelta = timedelta(hours=1)
