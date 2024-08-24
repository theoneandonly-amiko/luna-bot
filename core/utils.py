# Function to get the latest video details from a channel
def get_all_videos(channel_id, youtube):
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            maxResults=50
        )
        response = request.execute()
        if 'items' in response and response['items']:
            return response['items']  # Return all videos
        return []
    except Exception as e:
        logging.error(f"Error fetching videos: {e}")
        return []

