from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="sign",
    description="控制签名开关",
    commands={"sign": "启用/停用签名 (启用后消息开头将附加上调用信息) (仅群聊)"},
    can_disable=False,
)
