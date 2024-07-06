from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="switch",
    description="控制模块开关",
    commands={"switch": "启用/停用模块 (仅群聊)"},
    can_disable=False,
)
