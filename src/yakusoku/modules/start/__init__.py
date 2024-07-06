from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="start",
    description="yakusoku, 启动!",
    commands={"start": "yakusoku!"},
    can_disable=False,
)
