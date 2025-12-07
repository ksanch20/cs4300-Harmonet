import requests
import time
import logging
import ssl
import certifi

logger = logging.getLogger(__name__)

class SSLAdapter(requests.adapters.HTTPAdapter):
    """Custom SSL adapter to handle SSL connection issues"""
    def init_poolmanager(self, *args, **kwargs):
        from urllib3.util.ssl_ import create_urllib3_context
        context = create_urllib3_context()
        context.load_verify_locations(certifi.where())
        # Enable legacy renegotiation (fixes OpenSSL 3.0 issues)
        context.options |= 0x4  # SSL_OP_LEGACY_SERVER_CONNECT
        # Set reasonable security level
        try:
            context.set_ciphers('DEFAULT@SECLEVEL=1')
        except:
            pass
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class MusicBrainzAPI:
    BASE_URL = "https://musicbrainz.org/ws/2"
    COVERART_URL = "https://coverartarchive.org"
    
    def __init__(self):
        self.session = requests.Session()
        
        # Mount custom SSL adapter
        self.session.mount('https://', SSLAdapter())
        
        self.session.headers.update({
            'User-Agent': 'HarmoNet/1.0 ( ksanch20@gmail.com )',
            'Accept': 'application/json',
            'Connection': 'close'
        })
        self.last_request_time = 0
        self.rate_limit = 1.5
    
    def _rate_limit_wait(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit:
            time.sleep(self.rate_limit - time_since_last)
        self.last_request_time = time.time()
    
    def search_artists(self, query, limit=10):
        """Search for artists by name"""
        self._rate_limit_wait()
        
        try:
            logger.info(f"Searching MusicBrainz for: {query}")
            
            response = self.session.get(
                f"{self.BASE_URL}/artist/",
                params={
                    'query': query,
                    'limit': limit,
                    'fmt': 'json'
                },
                timeout=15
            )
            
            logger.info(f"Search response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            artists = []
            for artist in data.get('artists', []):
                artists.append({
                    'id': artist.get('id'),
                    'name': artist.get('name'),
                    'disambiguation': artist.get('disambiguation', ''),
                    'country': artist.get('country', ''),
                    'type': artist.get('type', ''),
                    'genres': self._extract_genres(artist),
                    'score': artist.get('score', 0)
                })
            
            logger.info(f"Found {len(artists)} artists")
            return artists
            
        except Exception as e:
            logger.error(f"Error searching artists: {e}", exc_info=True)
            return []
    
    def get_artist_details(self, artist_id):
        """Get detailed information about an artist"""
        self._rate_limit_wait()
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/artist/{artist_id}",
                params={
                    'inc': 'url-rels+genres+tags',
                    'fmt': 'json'
                },
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting artist details: {e}")
            return None
    
    def get_artist_image(self, artist_id):
        """Try to get artist image from Cover Art Archive"""
        try:
            response = self.session.get(
                f"{self.COVERART_URL}/release-group/{artist_id}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                if images:
                    return images[0].get('thumbnails', {}).get('small')
        except:
            pass
        return None
    
    def get_artist_albums(self, artist_id, limit=5):
        """Get artist's 5 most recent albums/releases sorted by date"""
        self._rate_limit_wait()
        
        try:
            logger.info(f"Fetching albums for artist ID: {artist_id}")
            
            response = self.session.get(
                f"{self.BASE_URL}/release-group/",
                params={
                    'artist': artist_id,
                    'type': 'album|ep',
                    'limit': 50,
                    'fmt': 'json'
                },
                timeout=15
            )
            
            logger.info(f"Album API response status: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            release_groups = data.get('release-groups', [])
            logger.info(f"Found {len(release_groups)} release groups from API")
            
            # Filter and collect albums with dates
            albums_with_dates = []
            seen_titles = set()
            
            for release_group in release_groups:
                title = release_group.get('title')
                release_date = release_group.get('first-release-date', '')
                
                # Skip if no title or duplicate or no date
                if not title or title in seen_titles or not release_date:
                    continue
                
                seen_titles.add(title)
                
                albums_with_dates.append({
                    'id': release_group.get('id'),
                    'title': title,
                    'type': release_group.get('primary-type', 'Album'),
                    'release_date': release_date,
                })
            
            # Sort by release date (most recent first)
            albums_with_dates.sort(key=lambda x: x['release_date'], reverse=True)
            
            # Get top N most recent
            recent_albums = albums_with_dates[:limit]
            
            if recent_albums:
                album_list = ', '.join([f"{a['title']} ({a['release_date'][:4]})" for a in recent_albums])
                logger.info(f"Top {len(recent_albums)} recent albums: {album_list}")
            
            # Fetch cover art for the most recent albums
            final_albums = []
            for album_data in recent_albums:
                logger.info(f"Fetching cover art for: {album_data['title']} ({album_data['release_date']})")
                # Don't let cover art failure stop the whole process
                try:
                    self._rate_limit_wait()
                    album_data['cover_art'] = self.get_album_cover_art(album_data['id']) or ''
                except Exception as e:
                    logger.warning(f"Failed to get cover art for {album_data['title']}: {e}")
                    album_data['cover_art'] = ''
                final_albums.append(album_data)
            
            logger.info(f"Returning {len(final_albums)} most recent albums")
            return final_albums
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting albums: {e.response.status_code if hasattr(e, 'response') else e}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting albums: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_artist_albums: {e}", exc_info=True)
            return []
    
    def get_album_cover_art(self, release_group_id):
        """Get cover art for a release group"""
        try:
            response = requests.get(
                f"{self.COVERART_URL}/release-group/{release_group_id}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                images = data.get('images', [])
                if images:
                    thumbnails = images[0].get('thumbnails', {})
                    return thumbnails.get('small') or thumbnails.get('250') or images[0].get('image')
        except Exception as e:
            logger.debug(f"No cover art found for {release_group_id}: {e}")
        return None
    
    def _extract_genres(self, artist_data):
        """Extract genre information from artist data"""
        genres = []
        
        if 'genres' in artist_data:
            genres.extend([g.get('name') for g in artist_data['genres']])
        
        if 'tags' in artist_data:
            genres.extend([t.get('name') for t in artist_data['tags'][:3]])
        
        return genres[:3]