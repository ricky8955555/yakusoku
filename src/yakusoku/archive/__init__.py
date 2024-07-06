import os

from yakusoku.archive.avatar import AvatarManager
from yakusoku.archive.filecache import FileCacheManager
from yakusoku.archive.group import GroupManager
from yakusoku.archive.user import UserManager
from yakusoku.context import sql
from yakusoku.environ import data_path

_FILE_CACHE_PATH = os.path.join(data_path, "filecache")
os.makedirs(_FILE_CACHE_PATH, exist_ok=True)

avatar_manager = AvatarManager()
file_cache_manager = FileCacheManager(_FILE_CACHE_PATH)
group_manager = GroupManager(sql)
user_manager = UserManager(sql)
