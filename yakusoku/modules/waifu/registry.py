from .factory import WaifuFactory


class MarriageStateError(Exception):
    pass


class QueueingError(Exception):
    pass


class TargetUnmatchedError(Exception):
    pass


class InvalidTargetError(Exception):
    pass


class Registry:
    _factory: WaifuFactory
    _proposals: dict[tuple[int, int], int]
    _divorce_requests: list[tuple[int, int]]

    def __init__(self, factory: WaifuFactory):
        self._factory = factory
        self._proposals = {}
        self._divorce_requests = []

    def marry(self, chat: int, first: int, second: int):
        first_property = self._factory.get_waifu_property(chat, first)
        second_property = self._factory.get_waifu_property(chat, second)
        if first_property.married or second_property.married:
            raise MarriageStateError
        self._factory.update_waifu_property(chat, first, married=second)
        self._factory.update_waifu_property(chat, second, married=first)
        self._factory.remove_waifu(chat, first)
        self._factory.remove_waifu(chat, second)

    def divorce(self, chat: int, originator: int):
        property = self._factory.get_waifu_property(chat, originator)
        if not property.married:
            raise MarriageStateError
        self._factory.update_waifu_property(chat, originator, married=None)
        self._factory.update_waifu_property(chat, property.married, married=None)

    def propose(self, chat: int, originator: int, target: int) -> bool:
        if originator == target:
            raise InvalidTargetError
        originator_property = self._factory.get_waifu_property(chat, originator)
        target_property = self._factory.get_waifu_property(chat, target)
        if originator_property.married or target_property.married:
            raise MarriageStateError
        if self._proposals.get((chat, originator)):
            raise QueueingError
        if (proposal := self._proposals.get((chat, target))) is not None:
            if proposal != originator:
                raise TargetUnmatchedError
            del self._proposals[(chat, target)]
            self.marry(chat, originator, target)
            return True
        self._proposals[(chat, originator)] = target
        return False

    def request_divorce(self, chat: int, originator: int) -> bool:
        property = self._factory.get_waifu_property(chat, originator)
        if not property.married:
            raise MarriageStateError
        if (chat, originator) in self._divorce_requests:
            raise QueueingError
        if (chat, property.married) in self._divorce_requests:
            self._divorce_requests.remove((chat, property.married))
            self.divorce(chat, originator)
            return True
        self._divorce_requests.append((chat, originator))
        return False

    def get_proposal(self, chat: int, originator: int) -> int:
        return self._proposals[(chat, originator)]

    def revoke_proposal(self, chat: int, originator: int) -> None:
        del self._proposals[(chat, originator)]

    def revoke_divorce_request(self, chat: int, originator: int) -> None:
        property = self._factory.get_waifu_property(chat, originator)
        if not property.married:
            raise MarriageStateError
        if (chat, originator) not in self._divorce_requests:
            originator = property.married
        self._divorce_requests.remove((chat, originator))
