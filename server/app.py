import os
import sys
import platform
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import threading

import json
import shutil

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

import paths
import database
import bot
import scheduler

load_dotenv(os.path.join(paths.BASE_DIR, '.env'))

app = Flask(__name__, static_folder=paths.FRONTEND_DIR, static_url_path='')


@app.after_request
def add_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    # Prevent browser from caching HTML pages so new builds are always loaded
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


BASE_DIR = paths.BASE_DIR
FRONTEND_DIR = paths.FRONTEND_DIR
UPLOAD_DIR = paths.UPLOAD_DIR
LOG_DIR = paths.LOG_DIR
LOG_FILE = paths.LOG_FILE
DATA_DIR = paths.DATA_DIR

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024   # 5 MB


# --- Logging setup ---
def setup_logging():
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)


setup_logging()
logger = logging.getLogger(__name__)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Frontend (SPA) ---

@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.errorhandler(404)
def fallback(e):
    """Serve index.html for SPA client-side routing."""
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if os.path.isfile(index_path):
        return send_from_directory(FRONTEND_DIR, 'index.html')
    return jsonify({'error': 'Frontend not built. Run: cd ui && npm run build'}), 404


# --- API endpoints ---

@app.route('/api/posts', methods=['POST'])
def api_create_post():
    text = request.form.get('text', '').strip()
    scheduled_at = request.form.get('scheduled_at', '').strip()
    status = request.form.get('status', 'draft').strip()

    # Dynamic character limit based on X Premium status
    char_limit = 280
    profile_path = os.path.join(DATA_DIR, 'profile_info.json')
    if os.path.isfile(profile_path):
        try:
            with open(profile_path, 'r', encoding='utf-8') as pf:
                pinfo = json.load(pf)
            if pinfo.get('is_verified'):
                char_limit = 25000
        except Exception:
            pass
    if len(text) > char_limit:
        return jsonify({'error': f'Text exceeds {char_limit} characters'}), 400

    image_path = ''
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            if not allowed_file(file.filename):
                return jsonify({'error': 'Format not supported (use png, jpg, jpeg, gif, webp)'}), 400
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            if size > MAX_IMAGE_SIZE:
                return jsonify({'error': f'File too large (max {MAX_IMAGE_SIZE // 1024 // 1024}MB)'}), 400
            filename = secure_filename(file.filename)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = ts + filename
            filepath = os.path.join(UPLOAD_DIR, filename)
            file.save(filepath)
            image_path = filepath

    if not text and not image_path:
        return jsonify({'error': 'Post must have text or an image'}), 400

    if status == 'scheduled' and not scheduled_at:
        return jsonify({'error': 'Scheduled posts need a date/time'}), 400

    post_id = database.create_post(
        text=text,
        image_path=image_path,
        scheduled_at=scheduled_at or None,
        status=status
    )
    logger.info(f"Post #{post_id} created (status={status})")
    return jsonify({'id': post_id, 'status': status}), 201


@app.route('/api/posts', methods=['GET'])
def api_list_posts():
    status = request.args.get('status')
    if status:
        posts = database.get_posts_by_status(status)
    else:
        posts = database.get_all_posts()
    return jsonify(posts)


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def api_get_post(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    return jsonify(post)


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def api_update_post(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    data = request.get_json() if request.is_json else request.form.to_dict()
    text = data.get('text', post['text'])
    scheduled_at = data.get('scheduled_at', post['scheduled_at'])
    status = data.get('status', post['status'])

    database.update_post(post_id, text=text, scheduled_at=scheduled_at, status=status)
    logger.info(f"Post #{post_id} updated")
    return jsonify({'id': post_id, 'updated': True})


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def api_delete_post(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Delete uploaded media file from disk
    image_path = post.get('image_path', '')
    if image_path and os.path.isfile(image_path):
        try:
            os.remove(image_path)
            logger.info(f"Media file deleted: {image_path}")
        except OSError as e:
            logger.warning(f"Could not delete media file: {e}")

    database.delete_post(post_id)
    logger.info(f"Post #{post_id} deleted")
    return jsonify({'deleted': True})


@app.route('/api/posts/<int:post_id>/post-now', methods=['POST'])
def api_post_now(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    database.update_post_status(post_id, 'posting')
    result = bot.post_to_x(text=post.get('text', ''), image_path=post.get('image_path', ''))

    if result.get('success'):
        tweet_url = result.get('tweet_url', '')
        database.update_post(post_id, status='posted', posted_at=datetime.now().isoformat(), tweet_url=tweet_url)
        logger.info(f"Post #{post_id} published immediately (tweet_url={tweet_url})")
        return jsonify({'success': True, 'tweet_url': tweet_url})
    else:
        error = result.get('error', 'Unknown error')
        database.update_post_status(post_id, 'error', error_message=error)
        logger.error(f"Post #{post_id} failed: {error}")
        return jsonify({'success': False, 'error': error}), 500


@app.route('/api/posts/<int:post_id>/schedule-now', methods=['POST'])
def api_schedule_now(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    scheduled_at = post.get('scheduled_at')
    if not scheduled_at:
        return jsonify({'error': 'Post has no scheduled date'}), 400

    database.update_post_status(post_id, 'scheduling')
    result = bot.post_to_x(
        text=post.get('text', ''),
        image_path=post.get('image_path', ''),
        scheduled_at=scheduled_at,
    )

    if result.get('success'):
        database.update_post_status(post_id, 'scheduled_on_x')
        logger.info(f"Post #{post_id} scheduled on X for {scheduled_at}")
        return jsonify({'success': True})
    else:
        error = result.get('error', 'Unknown error')
        database.update_post_status(post_id, 'error', error_message=error)
        logger.error(f"Post #{post_id} scheduling failed: {error}")
        return jsonify({'success': False, 'error': error}), 500


@app.route('/api/posts/<int:post_id>/retry', methods=['POST'])
def api_retry_post(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    database.update_post(post_id, status='posting', error_message='', retries_count=0)
    result = bot.post_to_x(text=post.get('text', ''), image_path=post.get('image_path', ''))

    if result.get('success'):
        tweet_url = result.get('tweet_url', '')
        database.update_post(post_id, status='posted', posted_at=datetime.now().isoformat(), tweet_url=tweet_url)
        logger.info(f"Post #{post_id} retry successful (tweet_url={tweet_url})")
        return jsonify({'success': True, 'tweet_url': tweet_url})
    else:
        error = result.get('error', 'Unknown error')
        database.update_post_status(post_id, 'error', error_message=error)
        logger.error(f"Post #{post_id} retry failed: {error}")
        return jsonify({'success': False, 'error': error}), 500


@app.route('/api/posts/<int:post_id>/delete-from-x', methods=['POST'])
def api_delete_from_x(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    tweet_url = post.get('tweet_url', '')
    if not tweet_url:
        return jsonify({'error': 'No tweet URL stored for this post'}), 400

    result = bot.delete_tweet(tweet_url)

    if result.get('success'):
        # Delete uploaded media file from disk
        image_path = post.get('image_path', '')
        if image_path and os.path.isfile(image_path):
            try:
                os.remove(image_path)
                logger.info(f"Media file deleted: {image_path}")
            except OSError as e:
                logger.warning(f"Could not delete media file: {e}")

        # Delete the post from database
        database.delete_post(post_id)
        logger.info(f"Post #{post_id} deleted from X and database (was {tweet_url})")
        return jsonify({'success': True, 'already_deleted': result.get('already_deleted', False)})
    else:
        error = result.get('error', 'Unknown error')
        logger.error(f"Post #{post_id} delete from X failed: {error}")
        return jsonify({'success': False, 'error': error}), 500


@app.route('/api/posts/<int:post_id>/delete-scheduled-from-x', methods=['POST'])
def api_delete_scheduled_from_x(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    if post.get('status') != 'scheduled_on_x':
        return jsonify({'error': 'Post is not scheduled on X'}), 400

    post_text = post.get('text', '')
    if not post_text or not post_text.strip():
        return jsonify({'error': 'Post has no text, cannot match on X'}), 400

    result = bot.delete_scheduled_tweet(post_text)

    if result.get('success'):
        # Delete uploaded media file from disk
        image_path = post.get('image_path', '')
        if image_path and os.path.isfile(image_path):
            try:
                os.remove(image_path)
                logger.info(f"Media file deleted: {image_path}")
            except OSError as e:
                logger.warning(f"Could not delete media file: {e}")

        # Delete the post from database
        database.delete_post(post_id)
        logger.info(f"Post #{post_id} scheduled tweet deleted from X and database")
        return jsonify({'success': True})
    else:
        error = result.get('error', 'Unknown error')
        logger.error(f"Post #{post_id} delete scheduled from X failed: {error}")
        return jsonify({'success': False, 'error': error}), 500


@app.route('/api/posts/<int:post_id>/remove-media', methods=['POST'])
def api_remove_media(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    image_path = post.get('image_path', '')
    if image_path and os.path.isfile(image_path):
        try:
            os.remove(image_path)
            logger.info(f"Media file deleted: {image_path}")
        except OSError as e:
            logger.warning(f"Could not delete media file: {e}")

    database.update_post(post_id, image_path='')
    logger.info(f"Post #{post_id} media removed")
    return jsonify({'success': True})


@app.route('/api/posts/<int:post_id>/duplicate', methods=['POST'])
def api_duplicate_post(post_id):
    post = database.get_post(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    # Copy the media file so each post owns its own copy
    new_image_path = ''
    image_path = post.get('image_path', '')
    if image_path and os.path.isfile(image_path):
        ext = os.path.splitext(image_path)[1]
        ts = datetime.now().strftime('%Y%m%d_%H%M%S_')
        new_filename = ts + 'copy' + ext
        new_image_path = os.path.join(UPLOAD_DIR, new_filename)
        shutil.copy2(image_path, new_image_path)

    new_id = database.create_post(
        text=post['text'],
        image_path=new_image_path,
        status='draft'
    )
    logger.info(f"Post #{post_id} duplicated as #{new_id}")
    return jsonify({'id': new_id}), 201


ENV_KEYS = [
    'X_USERNAME',
    'X_PASSWORD',
    'CHROME_PROFILE_DIR',
    'CHROME_PATH',
    'HEADLESS',
    'CHECK_INTERVAL_SECONDS',
    'MAX_RETRIES',
]


@app.route('/api/settings/preferences', methods=['GET'])
def api_get_preferences():
    prefs_path = os.path.join(DATA_DIR, 'preferences.json')
    prefs = {}
    if os.path.isfile(prefs_path):
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
        except Exception:
            pass
    return jsonify(prefs)


@app.route('/api/settings/preferences', methods=['POST'])
def api_save_preferences():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400
    prefs_path = os.path.join(DATA_DIR, 'preferences.json')
    # Merge with existing
    prefs = {}
    if os.path.isfile(prefs_path):
        try:
            with open(prefs_path, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
        except Exception:
            pass
    prefs.update(data)
    with open(prefs_path, 'w', encoding='utf-8') as f:
        json.dump(prefs, f)
    return jsonify({'success': True})


@app.route('/api/settings/env', methods=['GET'])
def api_get_env():
    env_path = os.path.join(BASE_DIR, '.env')
    values = {}
    if os.path.isfile(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, _, val = line.partition('=')
                    key = key.strip()
                    val = val.strip()
                    if key in ENV_KEYS:
                        if key == 'X_PASSWORD':
                            values[key] = '********' if val else ''
                        else:
                            values[key] = val
    for k in ENV_KEYS:
        if k not in values:
            # Defaults
            if k == 'CHECK_INTERVAL_SECONDS':
                values[k] = '15'
            elif k == 'MAX_RETRIES':
                values[k] = '1'
            else:
                values[k] = ''
    return jsonify(values)


@app.route('/api/settings/env', methods=['POST'])
def api_save_env():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    env_path = os.path.join(BASE_DIR, '.env')

    # Read existing values to preserve password if masked
    existing = {}
    if os.path.isfile(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, _, val = line.partition('=')
                    existing[key.strip()] = val.strip()

    lines = []
    for key in ENV_KEYS:
        val = data.get(key, '')
        # Keep existing password if the user didn't change it
        if key == 'X_PASSWORD' and val == '********':
            val = existing.get('X_PASSWORD', '')
        # Apply defaults if empty
        if not val:
            if key == 'CHECK_INTERVAL_SECONDS':
                val = '15'
            elif key == 'MAX_RETRIES':
                val = '1'
        lines.append(f'{key}={val}')

    with open(env_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    # Reload dotenv
    load_dotenv(override=True)

    # Restart browser so it picks up new settings (headless, chrome path, etc.)
    bot.restart_browser()

    logger.info("Environment settings updated")
    return jsonify({'success': True})


@app.route('/api/settings/test-connection', methods=['GET'])
def api_test_connection():
    result = bot.test_connection()
    return jsonify(result)


@app.route('/api/settings/connect-google', methods=['POST'])
def api_connect_google():
    """Open Chrome via Playwright on Google login page for manual authentication."""
    result = bot.open_google_login()
    return jsonify(result)


@app.route('/api/settings/check-google', methods=['GET'])
def api_check_google():
    """Check if a Google account is connected in the Chrome profile."""
    result = bot.check_google_connected()
    return jsonify(result)


@app.route('/api/profile/fetch', methods=['POST'])
def api_fetch_profile():
    result = bot.fetch_profile()
    if result.get('success'):
        followers_count = result.get('followers_count', 0)
        following_count = result.get('following_count', 0)
        # Save profile info to a JSON file for quick access
        info = {
            'display_name': result.get('display_name', ''),
            'username': result.get('username', ''),
            'is_verified': result.get('is_verified', False),
            'verified_type': result.get('verified_type', ''),
            'followers_count': followers_count,
            'following_count': following_count,
            'bio': result.get('bio', ''),
            'join_date': result.get('join_date', ''),
        }
        info_path = os.path.join(DATA_DIR, 'profile_info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f)
        # Save snapshot to followers history
        database.add_follower_snapshot(followers_count, following_count, username=info.get('username', ''))
    return jsonify(result)


@app.route('/api/profile', methods=['GET'])
def api_get_profile():
    info_path = os.path.join(DATA_DIR, 'profile_info.json')
    pic_path = os.path.join(DATA_DIR, 'profile_picture.jpg')
    has_picture = os.path.isfile(pic_path)
    info = {}
    if os.path.isfile(info_path):
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
    return jsonify({
        'display_name': info.get('display_name', os.getenv('X_USERNAME', '')),
        'username': info.get('username', os.getenv('X_USERNAME', '')),
        'has_picture': has_picture,
        'is_verified': info.get('is_verified', False),
        'verified_type': info.get('verified_type', ''),
        'followers_count': info.get('followers_count', 0),
        'following_count': info.get('following_count', 0),
        'bio': info.get('bio', ''),
        'join_date': info.get('join_date', ''),
    })


@app.route('/api/profile/stats', methods=['GET'])
def api_profile_stats():
    info_path = os.path.join(DATA_DIR, 'profile_info.json')
    info = {}
    if os.path.isfile(info_path):
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
    history = database.get_follower_history(username=info.get('username'))
    return jsonify({
        'profile': {
            'display_name': info.get('display_name', os.getenv('X_USERNAME', '')),
            'username': info.get('username', os.getenv('X_USERNAME', '')),
            'is_verified': info.get('is_verified', False),
            'verified_type': info.get('verified_type', ''),
            'followers_count': info.get('followers_count', 0),
            'following_count': info.get('following_count', 0),
            'bio': info.get('bio', ''),
            'join_date': info.get('join_date', ''),
        },
        'history': history,
    })


@app.route('/api/profile/picture')
def api_profile_picture():
    pic_path = os.path.join(DATA_DIR, 'profile_picture.jpg')
    if os.path.isfile(pic_path):
        return send_from_directory(DATA_DIR, 'profile_picture.jpg')
    return '', 404


@app.route('/api/logs', methods=['GET'])
def api_get_logs():
    try:
        if not os.path.isfile(LOG_FILE):
            return jsonify({'logs': ''})
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Return last 200 lines
        content = ''.join(lines[-200:])
        return jsonify({'logs': content})
    except Exception as e:
        return jsonify({'logs': f'Error reading logs: {e}'}), 500


# Global reference to pywebview window (set in __main__)
_webview_window = None


@app.route('/api/browse/folder', methods=['POST'])
def api_browse_folder():
    """Open a folder selection dialog."""
    global _webview_window
    if _webview_window is None:
        return jsonify({'path': None, 'error': 'No window available'})
    try:
        import webview
        result = _webview_window.create_file_dialog(webview.FOLDER_DIALOG)
        if result and len(result) > 0:
            return jsonify({'path': result[0]})
        return jsonify({'path': None})
    except Exception as e:
        return jsonify({'path': None, 'error': str(e)})


@app.route('/api/browse/file', methods=['POST'])
def api_browse_file():
    """Open a file selection dialog."""
    global _webview_window
    if _webview_window is None:
        return jsonify({'path': None, 'error': 'No window available'})
    try:
        import webview
        result = _webview_window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=('Executable Files (*.exe)', 'All Files (*.*)')
        )
        if result and len(result) > 0:
            return jsonify({'path': result[0]})
        return jsonify({'path': None})
    except Exception as e:
        return jsonify({'path': None, 'error': str(e)})


@app.route('/api/detect-chrome', methods=['GET'])
def api_detect_chrome():
    """Auto-detect Chrome paths on the system."""
    import platform
    system = platform.system()

    chrome_path = None
    profile_dir = None

    if system == 'Windows':
        # Chrome executable paths to check
        chrome_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'Application', 'chrome.exe'),
        ]
        for path in chrome_paths:
            if os.path.isfile(path):
                chrome_path = path
                break

        # Chrome profile directory
        local_app_data = os.environ.get('LOCALAPPDATA', '')
        if local_app_data:
            profile = os.path.join(local_app_data, 'Google', 'Chrome', 'User Data', 'Default')
            if os.path.isdir(profile):
                profile_dir = profile

    elif system == 'Darwin':  # macOS
        chrome_paths = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            os.path.expanduser('~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
        ]
        for path in chrome_paths:
            if os.path.isfile(path):
                chrome_path = path
                break

        profile = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default')
        if os.path.isdir(profile):
            profile_dir = profile

    elif system == 'Linux':
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
        ]
        for path in chrome_paths:
            if os.path.isfile(path):
                chrome_path = path
                break

        profile = os.path.expanduser('~/.config/google-chrome/Default')
        if os.path.isdir(profile):
            profile_dir = profile
        else:
            profile = os.path.expanduser('~/.config/chromium/Default')
            if os.path.isdir(profile):
                profile_dir = profile

    return jsonify({
        'chrome_path': chrome_path,
        'profile_dir': profile_dir,
        'detected': chrome_path is not None or profile_dir is not None
    })


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


# --- Start ---

if __name__ == '__main__':
    import webbrowser

    database.init_db()
    scheduler.start()
    logger.info("X Post Management starting...")

    # Try to use pywebview if available, otherwise fall back to browser
    try:
        import webview

        # Run Flask in a daemon thread so it stops when the window closes
        flask_thread = threading.Thread(
            target=lambda: app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False),
            daemon=True,
        )
        flask_thread.start()

        # Open a native window pointing at the Flask server
        window = webview.create_window('X Post Management', 'http://127.0.0.1:5000', width=1200, height=800)
        _webview_window = window  # Store reference for file dialogs
        gui_backend = 'edgechromium' if platform.system() == 'Windows' else None
        webview.start(gui=gui_backend)

        # Cleanup after window close
        logger.info("Window closed, shutting down...")
        scheduler.stop()
        bot.close()

    except Exception as e:
        # Fallback: run Flask directly and open browser
        logger.warning(f"pywebview not available ({e}), running in browser mode")
        print("\n" + "="*50)
        print("  X Post Management - Development Mode")
        print("  Open http://127.0.0.1:5000 in your browser")
        print("  Press Ctrl+C to stop")
        print("="*50 + "\n")
        webbrowser.open('http://127.0.0.1:5000')
        try:
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        except KeyboardInterrupt:
            pass
        finally:
            scheduler.stop()
            bot.close()
