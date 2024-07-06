import ipaddress

from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from yakusoku.context import module_manager

from .utils import humanize_network_flags

router = module_manager.create_router()


@router.message(Command("net"))
async def net(message: Message, command: CommandObject):
    ip = command.args
    if not ip:
        return await message.reply("啥都没有算不了捏xwx")
    try:
        network = ipaddress.ip_network(ip)
    except Exception as ex:
        return await message.reply(f"你给的是什么东西啊, 算不出来啊, 人家都报错了 (恼\n{ex}")
    flags = ", ".join(humanize_network_flags(network))
    await message.reply(
        f"""
CIDR: <code>{network.exploded}</code>
前缀长度 (Prefix Length): <code>{network.prefixlen}</code>
IP 版本 (IP Version): <code>IPv{network.version}</code>
地址数量 (Number of Addresses): <code>2^{network.max_prefixlen - network.prefixlen} = {network.num_addresses}</code>
广播地址 (Broadcast): <code>{network.broadcast_address}</code>
子网掩码 (Netmask): <code>{network.netmask}</code>
反向 DNS (RDNS): <code>{network.reverse_pointer}</code>
标记 (Flags): {flags}
        """.strip()
    )
