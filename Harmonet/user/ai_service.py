# user/ai_service.py
from openai import OpenAI
from django.conf import settings

# Initialize OpenAI client
client = OpenAI(api_key=settings.OPENAI_API_KEY)


def get_music_recommendations(user):
    """
    Generate personalized music recommendations using OpenAI.
    Combines data from Spotify (if connected) and manual music preferences.
    
    Returns a dictionary with success status and recommendations or error message.
    """
    
    # Gather user's music data
    music_data = gather_user_music_data(user)
    
    # Check if user has any music data
    if not music_data['has_data']:
        return {
            'success': False,
            'message': 'Please connect Spotify or add your music preferences to get personalized recommendations!'
        }
    
    # Build the prompt
    prompt = build_recommendation_prompt(music_data)
    
    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {
                    "role": "system",
                    "content": """You are a music recommendation expert. Provide personalized, thoughtful recommendations.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

### **1. Artist Name**
- **Genre/Style:** [Genre]
- **Why you'd like them:** [2-3 sentences explaining the connection to their taste]
- **Songs to start with:**
  - "Song Title 1"
  - "Song Title 2"

---

### **2. Artist Name**
[same format]

Use this exact format for all 5 recommendations. Use ### for headers, ** for bold, and - for bullet points."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1200,
            temperature=0.7  
        )
        
        # Extract the recommendation text
        recommendations = response.choices[0].message.content
        
        return {
            'success': True,
            'recommendations': recommendations
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Error generating recommendations: {str(e)}'
        }


def gather_user_music_data(user):
    """
    Collect all available music data for a user.
    Returns a dictionary with user's music information.
    """
    
    data = {
        'has_data': False,
        'spotify_connected': False,
        'manual_artists': [],
        'manual_genres': [],
        'manual_tracks': []
    }
    
    # Get Spotify data (if available)
    # TODO: Add when Spotify integration is complete
    # token_info = request.session.get('spotify_token')
    # if token_info:
    #     data['spotify_connected'] = True
    #     data['has_data'] = True
    
    # Get manual music preferences
    try:
        from .models import MusicPreferences
        music_prefs = user.music_preferences
        data['manual_artists'] = music_prefs.get_artists_list()
        data['manual_genres'] = music_prefs.get_genres_list()
        data['manual_tracks'] = music_prefs.get_tracks_list()
        
        # Mark as having data if any preferences exist
        if data['manual_artists'] or data['manual_genres'] or data['manual_tracks']:
            data['has_data'] = True
            
    except:
        # User hasn't added preferences yet
        pass
    
    return data


def build_recommendation_prompt(music_data):

    
    prompt_parts = []
    
    prompt_parts.append("Based on this user's music taste, recommend 5 artists they would love:\n")
    
    # Add Spotify data if available
    if music_data.get('spotify_artists'):
        prompt_parts.append("\n**From Spotify:**")
        prompt_parts.append(", ".join(music_data['spotify_artists']))
    
    # Add manual preferences
    if music_data['manual_artists']:
        prompt_parts.append(f"\n**Favorite Artists:**")
        prompt_parts.append(", ".join(music_data['manual_artists']))
    
    if music_data['manual_genres']:
        prompt_parts.append(f"\n**Favorite Genres:**")
        prompt_parts.append(", ".join(music_data['manual_genres']))
    
    if music_data['manual_tracks']:
        prompt_parts.append(f"\n**Favorite Tracks:**")
        prompt_parts.append(", ".join(music_data['manual_tracks'][:5]))
    
    # Instructions
    prompt_parts.append("\n\nProvide 5 artist recommendations following the exact format specified in the system message.")
    
    return "\n".join(prompt_parts)