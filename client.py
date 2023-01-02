import socket
from colorama import Fore
import threading
import os

PORT = 9091  # server port
HOST = "localhost"  # server id
SEP = "<&sep&>"  # seperator for seperating data in a single send
BUFFER_SIZE = 1024
DOWNLOAD_FOLDER = "downloads/"


# creat folder if not exist 
if not os.path.exists(DOWNLOAD_FOLDER):
    os.mkdir(DOWNLOAD_FOLDER)


def resive_msg(soc: socket):
    while True:
        #get msg from server and process it
        msg = soc.recv(BUFFER_SIZE)
        if not msg:
            soc.close()
            break
        msg = msg.decode("utf-8").split(SEP)
        if msg[0] == "JOIN":
            # somebody joind the group chat
            msg = msg[1]
            print(Fore.YELLOW + msg)
            print(Fore.BLUE)
        elif msg[0] == "DISCONNET":
            # sombody left group chat
            msg = msg[1]
            print(Fore.RED + msg)
            print(Fore.BLUE)
        elif msg[0] == "ERROR":
            # error msg , didint acctually use it
            msg = msg[1]
            print(Fore.RED + msg)
            print(Fore.BLUE)
        elif msg[0] == "SENDINGFILE":
            # recive file from client
            file_name = msg[1]
            file_size = int(msg[2])
            with open(DOWNLOAD_FOLDER + file_name, "wb") as file:
                current_size = 0
                while current_size < file_size:
                    msg = soc.recv(BUFFER_SIZE)
                    file.write(msg)
                    current_size += len(msg)
            print(Fore.GREEN + f"recived file {file_name}")
            print(Fore.BLUE)
        else:
            # sombody sad something in chat
            print(Fore.GREEN + msg[0] + ": " + Fore.MAGENTA + msg[1])
            print(Fore.BLUE)


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
    soc.connect((HOST, PORT))
    msg = soc.recv(BUFFER_SIZE).decode("utf-8")
    if msg == "NICK":
        # send nickname
        nick = input("Enter Nickname:")
        soc.send(nick.encode("utf-8"))
        # handle reciving msg from server on another thread
        t = threading.Thread(target=resive_msg, args=(soc,))
        t.daemon = True
        t.start()
        while True:
            msg = input("")
            # exist if typed
            if msg == "exit()":
                soc.close()
                break
            # send file to server
            # handeld here
            elif msg.split(":")[0] == "sfile":
                file_path = msg.split(":")[1].replace('"', "").replace("'", "")
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                soc.send(f"SENDFILE{SEP}{file_name}{SEP}{file_size}".encode("utf-8"))
                with open(file_path, "rb") as file:
                    line = file.read(BUFFER_SIZE)
                    while line:
                        soc.send(line)
                        line = file.read(BUFFER_SIZE)
                print(Fore.GREEN + f"Sending file {file_name} done")
                continue
            # recive file from server handeled in resive_msg
            elif msg.split(":")[0] == "gfile":
                file_name = msg.split(":")[1]
                soc.send(f"REQUESTFILE{SEP}{file_name}".encode("utf-8"))
            else:
                # user typed a msg for chat
                soc.send(msg.encode("utf-8"))

    else:
        print("failed")
        soc.close()
