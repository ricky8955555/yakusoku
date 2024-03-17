from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="greeting",
    description="问候",
    commands={"greet": "启用/禁用问候功能"},
    default_enabled=False,
)
