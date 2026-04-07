import re

def youtube_video_url_validator(video_url):
    try:
        if not video_url:
            return {"text": "URL is required.", "is_valid": False}
        
        # Clean URL
        video_url = re.sub(r"\s{2,}", " ", str(video_url).strip())
        if len(video_url) < 25:
            return {"text": "URL is too short.", "is_valid": False}
            
        is_valid = False
        patterns = [
            r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}',
            r'^https?://youtu\.be/[\w-]{11}',
            r'^https?://(?:www\.)?youtube\.com/embed/[\w-]{11}',
            r'^https?://(?:www\.)?youtube\.com/v/[\w-]{11}',
        ]
        
        for pattern in patterns:
            if re.match(pattern, video_url):
                is_valid = True
                break
                
        if not is_valid:
            return {"text": "Invalid YouTube URL format.", "is_valid": False}
            
        match = re.search(r'(?:v=|youtu\.be/|embed/|v/)([\w-]{11})', video_url)
        video_url_id = match.group(1) if match else None
        
        return {"text": video_url, "is_valid": True, "video_id": video_url_id}
        
    except Exception as ex:
        return {"text": str(ex), "is_valid": False}

# --- n8n DATA ACCESS ---
# Access the chatInput from the incoming item
#chat_input = $input._items.first().get('chatInput', '')
#chat_input = _items[0].get('chatInput', '')
#chat_input = $input.first().json.chatInput

chat_input = "https://www.youtube.com/watch?v=8OoUzEAPADg"

# Run the validation logic
result = youtube_video_url_validator(chat_input)

# Return result in n8n's expected format
return [{"json": result}]