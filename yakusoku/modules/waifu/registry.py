from .manager import WaifuManager


class MarriageStateError(Exception):
    pass


class InvalidTargetError(Exception):
    pass


class Registry:
    _manager: WaifuManager

    def __init__(self, manager: WaifuManager):
        self._manager = manager

    async def marry(self, chat: int, first: int, second: int) -> None:
        first_data = await self._manager.get_waifu_data(chat, first)
        second_data = await self._manager.get_waifu_data(chat, second)
        if first_data.restricted or second_data.restricted:
            raise MarriageStateError
        first_data.set_partner(second)
        second_data.set_partner(first)
        await self._manager.update_waifu_data(first_data)
        await self._manager.update_waifu_data(second_data)

    async def divorce(self, chat: int, originator: int) -> None:
        originator_data = await self._manager.get_waifu_data(chat, originator)
        if not (partner := originator_data.get_partner()):
            raise MarriageStateError
        target_data = await self._manager.get_waifu_data(chat, partner)
        originator_data.set_partner(None)
        target_data.set_partner(None)
        await self._manager.update_waifu_data(originator_data)
        await self._manager.update_waifu_data(target_data)

    async def validate_marriage(self, chat: int, originator: int, target: int) -> None:
        originator_data = await self._manager.get_waifu_data(chat, originator)
        target_data = await self._manager.get_waifu_data(chat, target)
        if originator_data.restricted or target_data.restricted:
            raise MarriageStateError

    async def validate_divorce(self, chat: int, originator: int) -> None:
        data = await self._manager.get_waifu_data(chat, originator)
        if not data.get_partner():
            raise MarriageStateError
