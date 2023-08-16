from typing import Hashable


class MutexManager():
    _keys: set[Hashable]

    def __init__(self):
        self._keys = set()

    def lock(self, key: Hashable) -> bool:
        original = len(self._keys)
        self._keys.add(key)
        return len(self._keys) == original + 1

    def unlock(self, key: Hashable) -> bool:
        try:
            self._keys.remove(key)
            return True
        except KeyError:
            return False

    def lock_all(self, *keys: Hashable) -> bool:
        failed = None
        for index, key in enumerate(keys):
            if not self.lock(key):
                failed = index
                break
        if failed is None:
            return True
        for key in keys[:failed]:
            self.unlock(key)
        return False

    def unlock_all(self, *keys: Hashable) -> bool:
        failed = None
        for index, key in enumerate(keys):
            if not self.unlock(key):
                failed = index
                break
        if failed is None:
            return True
        for key in keys[:failed]:
            self.lock(key)
        return False
