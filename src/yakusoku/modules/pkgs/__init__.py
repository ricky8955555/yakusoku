from yakusoku.module import ModuleConfig

__module_config__ = ModuleConfig(
    name="pkgs",
    description="Linux 软件包信息",
    commands={"pkgs": "获取 Linux 软件包信息", "pkgst": "获取 pkgs 状态"},
)
