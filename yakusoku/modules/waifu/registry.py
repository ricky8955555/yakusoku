from .manager import WaifuManager


class MarriageStateError(Exception):
    pass


class QueueingError(Exception):
    pass


class TargetUnmatchedError(Exception):
    pass


class InvalidTargetError(Exception):
    pass


class Registry:
    _manager: WaifuManager
    _proposals: dict[tuple[int, int], int]
    _divorce_requests: list[tuple[int, int]]

    def __init__(self, manager: WaifuManager):
        self._manager = manager
        self._proposals = {}
        self._divorce_requests = []

    async def marry(self, chat: int, first: int, second: int) -> None:
        first_data = await self._manager.get_waifu_data(chat, first)
        second_data = await self._manager.get_waifu_data(chat, second)
        if first_data.forced or second_data.forced:
            raise MarriageStateError
        first_data.partner = second
        second_data.partner = first
        await self._manager.update_waifu_data(first_data)
        await self._manager.update_waifu_data(second_data)

    async def divorce(self, chat: int, originator: int) -> None:
        originator_data = await self._manager.get_waifu_data(chat, originator)
        if not originator_data.partner:
            raise MarriageStateError
        target_data = await self._manager.get_waifu_data(chat, originator_data.partner)
        originator_data.partner = None
        target_data.partner = None
        await self._manager.update_waifu_data(originator_data)
        await self._manager.update_waifu_data(target_data)

    async def propose(self, chat: int, originator: int, target: int) -> bool:
        if originator == target:
            raise InvalidTargetError
        originator_data = await self._manager.get_waifu_data(chat, originator)
        target_data = await self._manager.get_waifu_data(chat, target)
        if originator_data.forced or target_data.forced:
            raise MarriageStateError
        if self._proposals.get((chat, originator)):
            raise QueueingError
        if (proposal := self._proposals.get((chat, target))) is not None:
            if proposal != originator:
                raise TargetUnmatchedError
            del self._proposals[(chat, target)]
            await self.marry(chat, originator, target)
            return True
        self._proposals[(chat, originator)] = target
        return False

    async def request_divorce(self, chat: int, originator: int) -> bool:
        data = await self._manager.get_waifu_data(chat, originator)
        if not data.partner:
            raise MarriageStateError
        if (chat, originator) in self._divorce_requests:
            raise QueueingError
        if (chat, data.partner) in self._divorce_requests:
            self._divorce_requests.remove((chat, data.partner))
            await self.divorce(chat, originator)
            return True
        self._divorce_requests.append((chat, originator))
        return False

    def get_proposal(self, chat: int, originator: int) -> int:
        return self._proposals[(chat, originator)]

    def revoke_proposal(self, chat: int, originator: int) -> None:
        del self._proposals[(chat, originator)]

    async def revoke_divorce_request(self, chat: int, originator: int) -> None:
        data = await self._manager.get_waifu_data(chat, originator)
        if not data.partner:
            raise MarriageStateError
        if (chat, originator) not in self._divorce_requests:
            originator = data.partner
        self._divorce_requests.remove((chat, originator))
