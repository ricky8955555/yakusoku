import os

from yakusoku.archive.avatar import AvatarManager
from yakusoku.archive.filecache import FileCacheManager
from yakusoku.archive.group import GroupManager
from yakusoku.archive.user import UserManager
from yakusoku.constants import DATA_PATH
from yakusoku.context import sql

_FILE_CACHE_PATH = os.path.join(DATA_PATH, "filecache")
os.makedirs(_FILE_CACHE_PATH, exist_ok=True)

avatar_manager = AvatarManager()
file_cache_manager = FileCacheManager(_FILE_CACHE_PATH)
group_manager = GroupManager(sql)
user_manager = UserManager(sql)
