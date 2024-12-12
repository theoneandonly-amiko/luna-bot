import logging

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
        return response.get('items', [])
    except Exception:
        logging.error(f"Error fetching videos. Switching to some giant pieces of shi- nevermind.")
        return []

