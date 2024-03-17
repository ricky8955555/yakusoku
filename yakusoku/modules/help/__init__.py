from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="help",
    description="帮助",
    commands={"help": "帮助菜单"},
    can_disable=False,
)
