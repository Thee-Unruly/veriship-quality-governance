from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import sys


class SPAHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve existing files normally
        path = self.translate_path(self.path)
        if os.path.exists(path) and not os.path.isdir(path):
            return SimpleHTTPRequestHandler.do_GET(self)

        # Otherwise serve index.html for SPA client-side routing
        self.path = '/index.html'
        return SimpleHTTPRequestHandler.do_GET(self)


def run(port: int = 8080, directory: str = '.'):
    os.chdir(directory)
    server = HTTPServer(('0.0.0.0', port), SPAHandler)
    print(f"Serving SPA from {os.path.abspath(directory)} on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    directory = sys.argv[2] if len(sys.argv) > 2 else '.'
    run(port=port, directory=directory)
