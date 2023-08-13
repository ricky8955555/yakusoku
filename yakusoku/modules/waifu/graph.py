import contextlib
import textwrap

from aiogram import Bot
from graphviz import Digraph

from yakusoku.archive import avatar_manager, file_cache_manager, user_manager


async def render(bot: Bot, mapping: dict[int, int], format: str | None = None) -> bytes:
    graph = Digraph()
    for member in set(mapping.keys()).union(mapping.values()):
        avatar = None
        user = await user_manager.get_user(member)
        label = textwrap.shorten(
            user.name or (f"@{next(iter(user.usernames))}" if user.usernames else str(member)),
            width=15,
            placeholder="...",
        )
        with contextlib.suppress(Exception):
            avatar = await avatar_manager.get_avatar_file(bot, member)
        if avatar:
            avatar_file = await file_cache_manager.get_file(avatar)
            with graph.subgraph(name=f"cluster_{member}") as subgraph:  # type: ignore
                subgraph.attr(label=label, labelloc="b")
                # fmt: off
                subgraph.node(
                    str(member), label="",
                    shape="none", fixedsize="true", width="1", height="1",
                    image=avatar_file, imagescale="true"
                )
                # fmt: on
        else:
            graph.node(str(member), label=label)
    for member, waifu in mapping.items():
        graph.edge(str(member), str(waifu))

    return graph.pipe(format)
