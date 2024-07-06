from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="magic",
    description="获取文件类型",
    commands={
        "magic": "获取文件类型详细信息",
        "mime": "获取文件 MIME",
    },
)
