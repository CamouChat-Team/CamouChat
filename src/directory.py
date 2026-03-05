from pathlib import Path

from platformdirs import PlatformDirs


class DirectoryManager:
    """Manages application-wide and profile-specific directory structures."""

    def __init__(self, app_name: str = "Tweakio_sdk"):
        """Initialize DirectoryManager with an application name."""
        self.dirs = PlatformDirs(
            appname=app_name,
            appauthor="BITS-Rohit"
        )

        self.root_dir = Path(self.dirs.user_data_dir)
        self.cache_dir = Path(self.dirs.user_cache_dir)
        self.log_dir = Path(self.dirs.user_log_dir)

        self.platforms_dir = self.root_dir / "platforms"

        self._ensure_base_dirs()

    def _ensure_base_dirs(self):
        """Ensure that base directories (root, cache, logs, platforms) exist."""
        for d in [self.root_dir, self.cache_dir, self.log_dir, self.platforms_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_platform_dir(self, platform: str) -> Path:
        """Returns the directory for a specific platform."""
        path = self.platforms_dir / platform.lower()
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_profile_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the base directory for a specific profile on a platform."""
        return self.get_platform_dir(platform) / profile_id

    def get_database_path(self, platform: str, profile_id: str) -> Path:
        """Returns the path to the messages database for a profile."""
        return self.get_profile_dir(platform, profile_id) / "messages.db"

    def get_error_trace_file(self) -> Path:
        """Returns the path to the global ErrorTrace log file."""
        return self.cache_dir / "ErrorTrace.log"

    # ----------------------------
    # Profile Subdirectories
    # ----------------------------

    def get_cache_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the cache directory for a specific profile."""
        path = self.get_profile_dir(platform, profile_id) / "cache"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_backup_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the backup directory for a specific profile."""
        path = self.get_profile_dir(platform, profile_id) / "backups"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_media_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the root media directory for a specific profile."""
        path = self.get_profile_dir(platform, profile_id) / "media"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_media_images_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the images media directory for a specific profile."""
        path = self.get_media_dir(platform, profile_id) / "images"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_media_videos_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the videos media directory for a specific profile."""
        path = self.get_media_dir(platform, profile_id) / "videos"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_media_voice_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the voice media directory for a specific profile."""
        path = self.get_media_dir(platform, profile_id) / "voice"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_media_documents_dir(self, platform: str, profile_id: str) -> Path:
        """Returns the documents media directory for a specific profile."""
        path = self.get_media_dir(platform, profile_id) / "documents"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # ----------------------------
    # Global paths
    # ----------------------------

    def get_cache_root(self) -> Path:
        """Returns the root cache directory."""
        return self.cache_dir

    def get_log_root(self) -> Path:
        """Returns the root log directory."""
        return self.log_dir


# should be removed with the custom_logger itself driven paths .
ErrorTrace_file = DirectoryManager().get_error_trace_file()
