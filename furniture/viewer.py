from websocket import create_connection

WEBSOCKET_PORT = 8008
WEBSOCKET_ADDR = f"ws://localhost:{WEBSOCKET_PORT}"

class PreviewConnection():
    def __init__(self):
        self.ws = None

    def __enter__(self):
        self.ws = create_connection(WEBSOCKET_ADDR)
        self.ws.send("CLEAR")
        return self

    def __exit__(self, type, value, traceback):
        self.ws.close()
    
    def send(self, content):
        self.ws.send(content)


def previewer():
    return PreviewConnection()


if __name__ == "__main__":
    from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket

    clients = []

    class SimpleChat(WebSocket):
        def handleMessage(self):
            for client in clients:
                if client != self:
                    # self.address[0]
                    client.sendMessage(self.data)

        def handleConnected(self):
            print(self.address, 'connected')
            clients.append(self)

        def handleClose(self):
            clients.remove(self)
            print(self.address, 'closed')


    server = SimpleWebSocketServer('', WEBSOCKET_PORT, SimpleChat)
    print(">>> Listening on", WEBSOCKET_PORT)
    server.serveforever()
