from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import os
import threading
import yt_dlp
import datetime
import webbrowser
import subprocess
import json
import shutil
import re
import urllib.parse
import urllib.request
from threading import Timer

app = Flask(__name__)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)) if 'Flask app' not in os.getcwd() else os.path.dirname(os.getcwd())
VENV_SCRIPTS = os.path.join(PROJECT_ROOT, ".venv", "Scripts")
GALLERY_DL_PATH = os.path.join(VENV_SCRIPTS, "gallery-dl.exe")
YT_DLP_PATH = os.path.join(VENV_SCRIPTS, "yt-dlp.exe")

download_status = {
    'status': 'Ready',
    'progress': 0,
    'speed': 'N/A',
    'eta': 'N/A',
    'title': '',
    'error': None,
    'finished': False
}
download_lock = threading.Lock()

class YtdlpLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg):
        print(f"YTDLP ERROR: {msg}")
        with download_lock:
            download_status['error'] = msg

def progress_hook(d):
    if d['status'] == 'downloading':
        try:
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
            p = d.get('downloaded_bytes', 0) / total_bytes * 100
            with download_lock:
                download_status['progress'] = round(p, 1)
                download_status['speed'] = d.get('_speed_str', 'N/A')
                download_status['eta'] = d.get('_eta_str', 'N/A')
                download_status['status'] = f"Downloading: {download_status['progress']}%"
        except:
            pass
    elif d['status'] == 'finished':
        with download_lock:
            download_status['status'] = "Processing..."
            download_status['progress'] = 100

def detect_platform(url):
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'tiktok.com' in url_lower:
        return 'tiktok'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower or 'fb.com' in url_lower:
        return 'facebook'
    elif 'pinterest.com' in url_lower:
        return 'pinterest'
    elif 'reddit.com' in url_lower or 'redd.it' in url_lower:
        return 'reddit'
    elif 'linkedin.com' in url_lower:
        return 'linkedin'
    elif 'vimeo.com' in url_lower:
        return 'vimeo'
    elif 'dailymotion.com' in url_lower:
        return 'dailymotion'
    elif 'twitch.tv' in url_lower:
        return 'twitch'
    elif 't.co' in url_lower:
        return 'twitter'
    elif 'pornhub.com' in url_lower:
        return 'pornhub'
    return 'generic'

def is_playlist(url):
    url_lower = url.lower()
    return any(keyword in url_lower for keyword in ['playlist', 'list=', '/videos', '/channel/', '/c/', '/user/', '/@'])

def is_direct_media_url(url):
    url_lower = url.lower()
    # Remove query parameters for extension check
    url_without_query = url_lower.split('?')[0]
    return any(url_without_query.endswith(ext) for ext in ['.mp4', '.webm', '.m3u8', '.mov', '.mp3', '.m4a', '.wav', '.mkv', '.flv', '.avi', '.wmv'])

def get_platform_headers(platform):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    if platform in ('instagram', 'facebook'):
        headers['Referer'] = f'https://www.{platform}.com/'
        headers['Origin'] = f'https://www.{platform}.com/'
        headers['Sec-Fetch-Site'] = 'same-origin'
    elif platform == 'tiktok':
        headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
        headers['Referer'] = 'https://www.tiktok.com/'
    elif platform == 'twitter':
        headers['Authorization'] = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
        headers['Referer'] = 'https://www.twitter.com/'
    elif platform == 'youtube':
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
        headers['Accept-Language'] = 'en-US,en;q=0.9'
        headers['Sec-Fetch-Mode'] = 'navigate'
        headers['Sec-Fetch-Site'] = 'none'
    return headers

def get_extractor_args(platform, has_cookies=False):
    args = {}
    if platform == 'youtube':
        # Use multiple clients for better reliability
        args['youtube'] = {
            'player_client': ['android', 'ios', 'web'],
        }
    elif platform == 'twitter':
        args['twitter'] = {
            'include_quote': False,
            'include_card': True,
        }
    elif platform == 'instagram':
        args['instagram'] = {
            'check_host': False,
            'include_verified': False,
        }
    elif platform == 'tiktok':
        args['tiktok'] = {
            'app_version': '34.1.2',
            'manifest_app_version': '34.1.2',
        }
    return args

def build_ydl_opts(platform, extra_opts=None):
    has_cookies = os.path.exists(get_cookie_path())
    opts = {
        'quiet': True,
        'no_warnings': True,
        'logger': YtdlpLogger(),
        'http_headers': get_platform_headers(platform),
        'extractor_args': get_extractor_args(platform, has_cookies),
        'socket_timeout': 60,
        'retries': 15,
        'extractor_retries': 10,
        'fragment_retries': 15,
        'file_access_retries': 5,
        'retry_sleep_functions': {
            'http': lambda n: min(n * 3, 120),
            'fragment': lambda n: min(n * 3, 120),
            'file_access': lambda n: min(n * 2, 30)
        },
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'allow_unplayable_formats': True,
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'extractor_retries': 10,
    }
    if platform == 'youtube':
        opts['nocheckcertificate'] = True
        opts['ignoreerrors'] = 'download'
    cookie_path = get_cookie_path()
    if os.path.exists(cookie_path):
        opts['cookiefile'] = cookie_path
    if extra_opts:
        opts.update(extra_opts)
    return opts

def get_cookie_path():
    local = os.path.join(os.getcwd(), "cookies.txt")
    if os.path.exists(local):
        return local
    secret = "/etc/secrets/cookies.txt"
    if os.path.exists(secret):
        tmp = "/tmp/cookies_flask.txt"
        try:
            shutil.copy2(secret, tmp)
            return tmp
        except:
            return secret
    return local

def try_twitter_api(url):
    parsed = urllib.parse.urlparse(re.sub(r'\?.*$', '', url))
    api_url = "https://api.vxtwitter.com" + parsed.path
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            media = data.get('media_extended', [])
            for m in media:
                if m.get('type') == 'video' and 'url' in m:
                    return {
                        'title': data.get('text', 'Twitter Video'),
                        'thumbnail': m.get('thumbnail_url', ''),
                        'url': m['url']
                    }
            return {
                'title': data.get('text', 'Twitter Post'),
                'thumbnail': data.get('user', {}).get('profile_image_url', '') if not media else media[0].get('thumbnail_url', ''),
                'url': url
            }
    except Exception as e:
        print(f"Twitter API bypass failed: {e}")
        return None

def try_instagram_api(url):
    try:
        clean = re.sub(r'\?.*$', '', url)
        api_url = clean.rstrip('/') + '/?__a=1&__d=1'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'X-IG-App-ID': '936619743392459',
            'Referer': 'https://www.instagram.com/',
        }
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            items = data.get('graphql', {}).get('shortcode_media', {})
            if not items:
                items = data.get('items', [{}])[0] if data.get('items') else {}
            title = items.get('edge_media_to_caption', {}).get('edges', [{}])[0].get('node', {}).get('text', 'Instagram Post')
            thumb = items.get('display_url', '')
            return {'title': title[:80], 'thumbnail': thumb, 'url': url}
    except Exception as e:
        print(f"Instagram API bypass failed: {e}")
        return None

def fix_url(url):
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Clean up URL
    url = url.replace(' ', '%20')
    url = url.replace('m.facebook.com', 'www.facebook.com')
    url = url.replace('mobile.twitter.com', 'twitter.com')
    
    return url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    raw_url = request.json.get('url')
    if not raw_url:
        return jsonify({'error': 'No URL provided'}), 400

    url = fix_url(raw_url)
    platform = detect_platform(url)
    playlist_detected = is_playlist(url)
    print(f"Platform detected: {platform}, Playlist: {playlist_detected}")

    if platform == 'twitter':
        result = try_twitter_api(url)
        if result and result.get('url', '').endswith('.mp4'):
            return jsonify({
                'title': result['title'],
                'thumbnail': result['thumbnail'],
                'qualities': ['Best', 'Audio Only'],
                'fixed_url': result['url']
            })

    if platform == 'instagram':
        result = try_instagram_api(url)
        if result:
            ydl_opts = build_ydl_opts('instagram')
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    ig_formats = info.get('formats') or []
                    valid_qualities = set()
                    for f in ig_formats:
                        if f and f.get('vcodec') != 'none':
                            height = f.get('height')
                            if height: valid_qualities.add(f"{height}p")
                    sorted_q = sorted(valid_qualities, key=lambda x: int(x.replace('p', '')), reverse=True)
                    sorted_q.insert(0, 'Best')
                    ig_formats2 = info.get('formats') or []
                    if not any('video' in str(f.get('vcodec', '')) for f in ig_formats2 if f and f.get('vcodec')):
                        sorted_q = ['Best', 'Audio Only']
                    return jsonify({
                        'title': result['title'],
                        'thumbnail': result['thumbnail'],
                        'qualities': sorted_q,
                        'fixed_url': url
                    })
            except Exception as e:
                print(f"Instagram yt-dlp analyze failed: {e}")
                return jsonify({
                    'title': result['title'],
                    'thumbnail': result['thumbnail'],
                    'qualities': ['Best', 'Audio Only'],
                    'fixed_url': url
                })

    ydl_opts = build_ydl_opts(platform)
    info = None
    try:
        print(f"Analyzing URL with yt-dlp: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError("No info returned")
    except Exception as e:
        print(f"Primary extraction failed: {e}")
        err_str = str(e)
        info = None
        # Only retry if it's not the internal unpack error, or if we haven't retried yet
        if "not enough values to unpack" not in err_str:
            try:
                fallback_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 60,
                    'retries': 5,
                    'nocheckcertificate': True,
                    'ignoreerrors': True,
                }
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as ge:
                print(f"Fallback extraction failed: {ge}")
                info = None

    # Last-resort retry for YouTube using IOS client which is more stable
    if not info and platform == 'youtube':
        try:
            ios_opts = {
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 60,
                'retries': 5,
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios'],
                    }
                },
            }
            with yt_dlp.YoutubeDL(ios_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e2:
            print(f"iOS retry failed: {e2}")
            info = None
    
    if info:
        print(f"Success: {info.get('title', 'Unknown')}")

        # Check if it's a playlist
        if info.get('_type') == 'playlist' or info.get('entries'):
            entries = info.get('entries', [])
            playlist_title = info.get('title', 'Playlist')
            return jsonify({
                'title': playlist_title,
                'thumbnail': info.get('thumbnail', ''),
                'qualities': ['Best', 'Audio Only'],
                'fixed_url': url,
                'is_playlist': True,
                'video_count': len(entries) if entries else info.get('playlist_count', 0)
            })

        formats = info.get('formats') or []
        valid_qualities = set()
        has_video = False
        for f in formats:
            if f and f.get('vcodec') and f['vcodec'] != 'none':
                has_video = True
                height = f.get('height')
                if height: valid_qualities.add(f"{height}p")

        sorted_qualities = sorted(valid_qualities, key=lambda x: int(x.replace('p', '')), reverse=True)
        sorted_qualities.insert(0, 'Best')
        if not has_video:
            sorted_qualities = ['Best', 'Audio Only']
        else:
            sorted_qualities.append('Audio Only')

        return jsonify({
            'title': info.get('title', 'Unknown'),
            'thumbnail': info.get('thumbnail', ''),
            'qualities': sorted_qualities,
            'fixed_url': url
        })

    # If we reach here, all extraction attempts failed
    # For generic/unknown platforms, still allow download attempt
    if platform == 'generic' or is_direct_media_url(url):
        return jsonify({
            'title': 'Media from ' + url.split('/')[2] if len(url.split('/')) > 2 else 'Unknown Media',
            'thumbnail': '',
            'qualities': ['Best', 'Audio Only'],
            'fixed_url': url
        })
    
    # For known platforms that failed, show specific errors
    err_msg = "Could not extract video information from this URL. The site may not be supported or the video may be private."
    if platform == 'instagram':
        return jsonify({'error': f"Instagram: Make sure the link is a public post/video URL. Private accounts require login cookies."}), 500
    elif platform == 'twitter':
        return jsonify({'error': f"Twitter/X: Could not extract video. Ensure the tweet has a video and is public."}), 500
    elif platform == 'tiktok':
        return jsonify({'error': f"TikTok: Could not extract video. Try a different TikTok link format."}), 500
    elif platform == 'facebook':
        return jsonify({'error': f"Facebook: This video may be private or require login. Try a public reel/page URL."}), 500
    elif platform == 'youtube':
        return jsonify({'error': f"YouTube: This video may be restricted or unavailable. Try updating yt-dlp or use a different video."}), 500
    elif platform == 'pornhub':
        return jsonify({'error': f"PornHub: Could not extract video. The video may be private or removed."}), 500
    
    return jsonify({'error': err_msg}), 500

@app.route('/search', methods=['POST'])
def search_videos():
    query = request.json.get('query')
    platform = request.json.get('platform', 'youtube')
    max_results = request.json.get('max_results', 12)

    if not query or not query.strip():
        return jsonify({'error': 'No search query provided'}), 400

    search_query = f"ytsearch{max_results}:{query.strip()}"
    ydl_opts = build_ydl_opts(platform, {
        'extract_flat': True,
        'skip_download': True,
    })

    try:
        print(f"Searching: {search_query}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            entries = info.get('entries', [])
            results = []
            for entry in entries:
                if not entry:
                    continue
                result = {
                    'title': entry.get('title', 'Unknown'),
                    'url': f"https://www.youtube.com/watch?v={entry.get('id')}" if entry.get('id') and not entry.get('url') else entry.get('url', ''),
                    'thumbnail': entry.get('thumbnail', ''),
                    'channel': entry.get('channel', entry.get('uploader', 'Unknown')),
                    'duration': entry.get('duration', 0),
                    'views': entry.get('view_count', 0),
                    'id': entry.get('id', ''),
                }
                results.append(result)

            print(f"Search returned {len(results)} results")
            return jsonify({'results': results, 'query': query.strip()})

    except Exception as e:
        print(f"Search failed: {str(e)}")
        return jsonify({'error': f"Search failed: {str(e)[:150]}"}), 500


@app.route('/download', methods=['POST'])
def download():
    data = request.json
    raw_url = data.get('url')
    quality = data.get('quality')
    audio_format = data.get('audio_format', 'mp3')
    bitrate = data.get('bitrate', '320')
    download_subs = data.get('download_subs', False)
    sub_langs = data.get('sub_langs', 'en')

    if not raw_url:
        return jsonify({'error': 'No URL provided'}), 400

    url = fix_url(raw_url)
    platform = detect_platform(url)

    twitter_result = None
    if platform == 'twitter':
        twitter_result = try_twitter_api(url)
        if twitter_result and twitter_result.get('url', '').endswith('.mp4'):
            url = twitter_result['url']

    download_status.update({
        'status': 'Initializing...',
        'progress': 0,
        'finished': False,
        'error': None
    })

    thread = threading.Thread(target=run_download, args=(url, quality, audio_format, bitrate, platform, download_subs, sub_langs))
    thread.start()
    return jsonify({'message': 'Download started'})

def run_download(url, quality, audio_format, bitrate, platform='unknown', download_subs=False, sub_langs='en'):
    local_download_dir = os.path.join(os.getcwd(), "downloads")
    if not os.path.exists(local_download_dir):
        os.makedirs(local_download_dir)

    # Check if it's a playlist and create subdirectory
    playlist_detected = is_playlist(url)
    if playlist_detected:
        playlist_dir = os.path.join(local_download_dir, "playlist_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        if not os.path.exists(playlist_dir):
            os.makedirs(playlist_dir)
        outtmpl = os.path.join(playlist_dir, '%(playlist_index)s - %(title)s.%(ext)s')
    else:
        outtmpl = os.path.join(local_download_dir, '%(title)s.%(ext)s')

    ydl_opts = build_ydl_opts(platform, {
        'progress_hooks': [progress_hook],
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
    })

    if playlist_detected:
        ydl_opts['ignoreerrors'] = True
        ydl_opts['download_archive'] = os.path.join(local_download_dir, 'downloaded.txt')

    # Add subtitle download if requested
    if download_subs:
        ydl_opts['writesubtitles'] = True
        ydl_opts['subtitleslangs'] = [sub_langs]
        ydl_opts['writeautomaticsub'] = True

    if quality == 'Audio Only':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': audio_format,
            'preferredquality': bitrate
        }]
    elif quality == 'Best':
        # For generic platforms, use more flexible format selection
        if platform == 'generic':
            ydl_opts['format'] = 'best/best'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
    else:
        height = quality.replace('p', '').strip()
        # Validate height is a number before using it in format spec
        if height.isdigit() and int(height) > 0:
            ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best'
        else:
            ydl_opts['format'] = 'bestvideo+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise ValueError("yt-dlp did not return video information. The video may be unavailable, private, or blocked.")

            # Find the actual downloaded file in the downloads directory
            local_download_dir = os.path.join(os.getcwd(), "downloads")
            final_filename = None

            # Method 1: Check requested_downloads from yt-dlp
            if 'requested_downloads' in info and info['requested_downloads']:
                final_filename = info['requested_downloads'][0].get('filepath')

            # Method 2: If not found, scan the downloads directory for the most recent COMPLETED file
            if not final_filename or not os.path.exists(final_filename):
                if os.path.exists(local_download_dir):
                    files = [os.path.join(local_download_dir, f) for f in os.listdir(local_download_dir)]
                    files = [f for f in files if os.path.isfile(f) and not f.endswith('.part')]
                    if files:
                        final_filename = max(files, key=os.path.getmtime)

            # Method 3: Fallback to prepare_filename
            if not final_filename:
                final_filename = ydl.prepare_filename(info)
                if quality == 'Audio Only' and not final_filename.endswith(f".{audio_format}"):
                    base, _ = os.path.splitext(final_filename)
                    final_filename = f"{base}.{audio_format}"

            download_status['title'] = info.get('title', 'Video')
            download_status['file_path'] = final_filename
            download_status['status'] = "Completed"
            download_status['finished'] = True
    except Exception as e:
        download_status['error'] = str(e)
        download_status['status'] = "Error"

@app.route('/status')
def status():
    return jsonify(download_status)

@app.route('/get_file')
def get_file():
    path = download_status.get('file_path')
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True)

    if path:
        base, _ = os.path.splitext(path)
        for ext in ['.mp3', '.m4a', '.mp4', '.mkv', '.webm']:
            alt_path = base + ext
            if os.path.exists(alt_path):
                return send_file(alt_path, as_attachment=True)

    return "File not found. Try downloading again.", 404

@app.route('/profile/analyze', methods=['POST'])
def profile_analyze():
    profile_url = request.json.get('url')
    if not profile_url:
        return jsonify({'error': 'No URL provided'}), 400

    if not os.path.exists(GALLERY_DL_PATH):
        return jsonify({'error': 'gallery-dl not installed. Use single link mode instead.'}), 501

    try:
        cmd = [GALLERY_DL_PATH, "--get-urls", "--range", "1-12", profile_url]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(timeout=30)

        urls = [line.strip() for line in stdout.split('\n') if line.strip() and line.startswith('http')]

        items = []
        for url in urls:
            if url == profile_url or url.endswith('/timeline') or url.endswith('/status'):
                continue
            type_media = 'image'
            if any(ext in url.lower() for ext in ['.mp4', '.mkv', '.mov', '.webm']):
                type_media = 'video'
            items.append({
                'url': url,
                'thumbnail': url if type_media == 'image' else '/static/video_icon.png',
                'type': type_media
            })

        return jsonify({'items': items})
    except Exception as e:
        return jsonify({'error': f"Failed to list profile media: {str(e)}"}), 500

@app.route('/profile/download', methods=['POST'])
def profile_download():
    profile_url = request.json.get('url')
    if not profile_url:
        return jsonify({'error': 'No URL provided'}), 400

    if not os.path.exists(GALLERY_DL_PATH):
        return jsonify({'error': 'gallery-dl not installed. Use single link mode instead.'}), 501

    download_status.update({
        'status': 'Initializing Profile Download...',
        'progress': 0,
        'finished': False,
        'error': None
    })

    thread = threading.Thread(target=run_profile_download, args=(profile_url,))
    thread.start()
    return jsonify({'message': 'Bulk download started'})

def run_profile_download(url):
    local_download_dir = os.path.join(os.getcwd(), "downloads", "profile_extract_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    if not os.path.exists(local_download_dir):
        os.makedirs(local_download_dir)

    try:
        download_status['status'] = "Downloading Profile Media..."
        cmd = [GALLERY_DL_PATH, "-d", local_download_dir, "--range", "1-50", url]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        count = 0
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                count += 1
                prog = min(95, count * 5)
                download_status['progress'] = prog
                download_status['status'] = f"Downloading: Item {count}"

        zip_path = os.path.join(os.getcwd(), "downloads", "profile_bundle.zip")
        if os.path.exists(zip_path): os.remove(zip_path)

        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', local_download_dir)

        download_status['file_path'] = zip_path
        download_status['title'] = "Profile Media Bundle"
        download_status['progress'] = 100
        download_status['status'] = "Completed"
        download_status['finished'] = True

    except Exception as e:
        download_status['error'] = str(e)
        download_status['status'] = "Error"

if __name__ == '__main__':
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()

    print(f"\n* Lastic Productions Flask Server Ready!")
    print(f"* Local Address: http://127.0.0.1:5001")
    print(f"* Network Address: http://{ip}:5001 (Open this on your phone!)\n")

    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5001")

    Timer(1.5, open_browser).start()

    app.run(host='0.0.0.0', port=5001, debug=False)
