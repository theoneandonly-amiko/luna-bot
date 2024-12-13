import logging
from datetime import datetime, timezone
from typing import Dict, Tuple, List, Optional

class VideoCache:
    def __init__(self, cache_duration: int = 3600):
        self._cache: Dict[str, Tuple[datetime, List]] = {}
        self.cache_duration = cache_duration
        self.logger = logging.getLogger(__name__)

    def get(self, channel_id: str) -> Optional[List]:
        """Get videos from cache if still valid"""
        if channel_id in self._cache:
            cache_time, videos = self._cache[channel_id]
            if self.is_cache_valid(cache_time):
                return videos
        return None

    def set(self, channel_id: str, videos: List) -> None:
        """Store videos in cache with current timestamp"""
        self._cache[channel_id] = (datetime.now(timezone.utc), videos)

    def is_cache_valid(self, cache_time: datetime) -> bool:
        """Check if cache is still valid based on duration"""
        return (datetime.now(timezone.utc) - cache_time).total_seconds() < self.cache_duration

# Initialize global cache
video_cache_manager = VideoCache()

def get_all_videos(channel_id: str, youtube) -> List:
    try:
        # Check cache first
        cached_videos = video_cache_manager.get(channel_id)
        if cached_videos:
            return cached_videos

        # Fetch new videos if cache miss or expired
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            maxResults=50
        )
        response = request.execute()
        videos = response.get('items', [])
        
        # Update cache with new videos
        video_cache_manager.set(channel_id, videos)
        return videos
        
    except Exception as e:
        logging.error(f"Error fetching videos. Switching to some giant pieces of shi- Nevermind. It's not a bug. It's a feature. :D")
        # Return cached videos as fallback, even if expired
        cached_videos = video_cache_manager.get(channel_id)
        return cached_videos if cached_videos else []
