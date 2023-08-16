from typing import Hashable


class MutexManager:
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
        if self._keys.intersection(keys):
            return False
        self._keys.update(keys)
        return True

    def lock_all_unchecked(self, *keys: Hashable) -> None:
        self._keys.update(keys)

    def unlock_all(self, *keys: Hashable) -> bool:
        if len(self._keys.intersection(keys)) < len(keys):
            return False
        self._keys.difference_update(keys)
        return True

    def unlock_all_unchecked(self, *keys: Hashable) -> None:
        self._keys.difference_update(keys)
