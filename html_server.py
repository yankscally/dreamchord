import os
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PORT = 80
DEFAULT_PAGE = 'index.html'
WATCH_EXTENSIONS = ['.html', '.css', '.js']  # File extensions to watch for changes

class WebServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect root to default page
        if self.path == '/':
            self.path = '/' + DEFAULT_PAGE
        return SimpleHTTPRequestHandler.do_GET(self)

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server
        self.restart_needed = False
        self.last_modified = time.time()
    
    def on_modified(self, event):
        # Check if the modified file has one of the watched extensions
        if not event.is_directory:
            file_ext = os.path.splitext(event.src_path)[1].lower()
            if file_ext in WATCH_EXTENSIONS:
                # Avoid duplicate events (some systems trigger multiple events for a single change)
                current_time = time.time()
                if current_time - self.last_modified > 1:  # 1 second debounce
                    file_name = os.path.basename(event.src_path)
                    print(f"\n{file_name} has been modified. Reloading...")
                    self.last_modified = current_time
                    self.restart_needed = True

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, WebServerHandler)
    print(f"\nWeb server started on port {PORT}")
    print(f"You can access the site at: http://localhost:{PORT} or http://<your-local-ip>:{PORT}")
    print("To test on your phone, connect to the same WiFi network and enter your computer's IP address")
    print("Press Ctrl+C to stop the server")
    print(f"Watching for changes in files with extensions: {', '.join(WATCH_EXTENSIONS)}")
    
    # Start file watcher
    event_handler = FileChangeHandler(httpd)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()
    
    try:
        while True:
            httpd.handle_request()
            if event_handler.restart_needed:
                event_handler.restart_needed = False
                print("Server reloaded due to file changes")
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    # Check if watchdog is installed
    try:
        import watchdog
    except ImportError:
        print("The 'watchdog' package is required. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "watchdog"])
        print("Watchdog installed successfully!")
    
    # Start the server
    run_server()