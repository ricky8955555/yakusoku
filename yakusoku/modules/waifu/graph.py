import contextlib

from aiogram import Bot
from graphviz import Digraph

from yakusoku.shared import user_factory


async def render(bot: Bot, mapping: dict[int, int], format: str | None = None) -> bytes:
    graph = Digraph()
    for member in set(mapping.keys()).union(mapping.values()):
        avatar = None
        info = user_factory.get_userinfo(member)
        label = info.name or (f"@{next(iter(info.usernames))}" if info.usernames else str(member))
        with contextlib.suppress(Exception):
            avatar = await user_factory.get_avatar_file((member, bot), True)
        if avatar:
            with graph.subgraph(name=f"cluster_{member}") as subgraph:  # type: ignore
                subgraph.attr(label=label, labelloc="b")
                # fmt: off
                subgraph.node(
                    str(member), label="",
                    shape="none", fixedsize="true", width="1", height="1",
                    image=avatar, imagescale="true"
                )
                # fmt: on
        else:
            graph.node(str(member), label=label)
    for member, waifu in mapping.items():
        graph.edge(str(member), str(waifu))

    return graph.pipe(format)
