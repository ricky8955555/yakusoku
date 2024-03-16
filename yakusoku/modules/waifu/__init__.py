from yakusoku.module import ModuleConfig
from yakusoku.modules.waifu.models import WAIFU_MAX_RARITY, WAIFU_MIN_RARITY

__module_config__ = ModuleConfig(
    name="waifu",
    description="抽老婆!",
    commands={
        "waifu": "获取每日老婆 (仅群聊)",
        "waifurs": f"修改老婆稀有度 (仅管理员) (稀有度范围 N, [{WAIFU_MIN_RARITY}, {WAIFU_MAX_RARITY}])",
        "waifurg": "获取老婆稀有度 (仅群聊)",
        "divorce": "提出离婚申请 (仅群聊)",
        "propose": "提出求婚 (仅群聊)",
        "waifum": "允许/禁止 waifu 功能的提及 (默认禁止)",
        "waifug": "老婆关系图! (仅群聊)",
    },
)
