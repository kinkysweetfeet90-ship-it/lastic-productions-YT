import threading
import time
import webview
from app import app

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Wait a moment for Flask to be ready
    time.sleep(1.5)

    # Open native desktop window
    window = webview.create_window(
        title='Lastic Productions - Video Downloader',
        url='http://127.0.0.1:5000',
        width=900,
        height=780,
        min_size=(600, 600),
        resizable=True,
    )

    webview.start()
