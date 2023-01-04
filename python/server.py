import socket
import threading
import pathlib
import os

BASEDIR = pathlib.Path(__file__).parent

PORT = 9091
HOST = "localhost"
SEP = "<&sep&>"  # seperator for seperating data in a single send
UPLOAD_FOLDER = BASEDIR / "uploads"
BUFFER_SIZE = 1024
# creat folder if not exist
if not UPLOAD_FOLDER.exists():
    UPLOAD_FOLDER.mkdir()
clients = []  # lsit of clients sockets
threads = []  # list of threads


def disconnect(soc: socket, nick: str):
    # disconnect the client
    clients.remove((soc, nick))
    soc.close()
    broadcast(f"DISCONNET{SEP}{nick} disconnected from the server")  #
    print(f"{nick} disconnected from the server")


def handl_client(soc: socket, nick: str):
    while True:
        msg = soc.recv(BUFFER_SIZE).decode("utf-8")
        if not msg:
            disconnect(soc, nick)
            break
        # check to see what did clinet send, a command or jsut a msg
        if msg.split(SEP)[0] == "SENDFILE":
            # recivefile from client
            file_name = msg.split(SEP)[1]
            file_size = int(msg.split(SEP)[2])
            with open(UPLOAD_FOLDER / f"{nick}_{file_name}", "wb") as file:
                current_size = 0
                while current_size < file_size:
                    msg = soc.recv(BUFFER_SIZE)
                    file.write(msg)
                    current_size += len(msg)
            broadcast(f"{nick} send file {SEP} {nick}_{file_name}", nick)
            continue
        elif msg.split(SEP)[0] == "REQUESTFILE":
            # send file to client from server
            file_name = msg.split(SEP)[1]
            if os.path.exists(UPLOAD_FOLDER / file_name):
                file_size = os.path.getsize(UPLOAD_FOLDER / file_name)
                soc.send(f"SENDINGFILE{SEP}{file_name}{SEP}{file_size}".encode("utf-8"))
                with open(UPLOAD_FOLDER / file_name, "rb") as file:
                    line = file.read(BUFFER_SIZE)
                    while line:
                        soc.send(line)
                        line = file.read(BUFFER_SIZE)
            else:
                soc.send(f"ERROR{SEP}File dose not exist")
        else:
            broadcast(f"{nick} sad{SEP}{msg}")


def broadcast(msg: str, nick=None):
    # send msg to all clients exept the one with nick if set
    for soc, n in clients:
        if nick is not None and nick == n:
            continue
        try:
            soc.send(msg.encode("utf-8"))
        except Exception as ex:
            disconnect(soc, "ANONYMOUSE")


def auth_client(soc: socket):
    # get nick from client
    soc.send("NICK".encode("utf-8"))
    nick = soc.recv(BUFFER_SIZE).decode("utf-8")
    print(f"Client with nick {nick} connected")
    clients.append((soc, nick))
    broadcast(f"JOIN{SEP}{nick} connected to the server")  # sep only for ez
    handl_client(soc, nick=nick)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gs:
    gs.bind((HOST, PORT))

    gs.listen(10)  # listen for up to 10 clients
    print(f"Server is listening of port {PORT}")

    while True:  # loop for accepting clients
        con, addr = gs.accept()  # get new socket and ip address of connected client
        print(f"client {addr} connected")
        # creat new thread so we can handel multi client
        t = threading.Thread(target=auth_client, args=(con,))
        threads.append(t)
        t.start()
