from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="status",
    description="状态",
    commands={"status": "查看 Bot 状态"},
    can_disable=False,
)
