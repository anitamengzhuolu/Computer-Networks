__author__ = 'anitalu'

import socket
import sys
import select
import time
from thread import *
from threading import Timer
import json
import datetime

# This function constructs the routing table of the client
def routing_table(name):
    data = {}
    data['sender'] = SELF_NAME
    data['type'] = 'UPDATE'
    for node in NETWORK.keys():
        if NETWORK[node]['link'] == name and NETWORK[node]['link'] != node:
            data[node] = float('inf')       #Poisoned Reverse
        else:
            data[node] = NETWORK[node]['cost']
    return data
##############################################################################

# This is the function printing routing table to user
def show_rt():
    print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + ' Distance vector list is:'
    for node in NETWORK.keys():
        data = 'Destination = ' + node + ', Cost = ' + str(NETWORK[node]['cost']) + ', Link = (' + NETWORK[node]['link'] + ')'
        print data
##############################################################################

# This function broadcast the routing table to all of the user's neighbor
def broadcast(RESEND_FLAG):
    global resend_timer,FLAG
    while(1):
        if FLAG == 0:
            FLAG = 2
            for node in NEIGHBOR_LIST.keys():
                if NEIGHBOR_LIST[node]['cost'] != float("inf"):
                    rt = routing_table(node)
                    UDP_write.sendto(json.dumps(rt), (NEIGHBOR_LIST[node]['IP'], int(NEIGHBOR_LIST[node]['port'])))

            resend_timer.cancel()
            resend_timer = Timer(TIMEOUT, broadcast, (1,))
            resend_timer.daemon = True
            resend_timer.start()
            FLAG = 0
            break
##############################################################################

# This function kills a long not updating neighbor, and all edges connecting to it
def kill_neighbor(name):
    global FLAG
    while(1):
        if FLAG == 0:
            FLAG = 2
            NEIGHBOR_LIST.pop(name, None)
            #print 'killed '+name
            for node in NETWORK.keys():
                if NETWORK[node]['link'] == name:
                    NETWORK[node]['cost'] = float("inf")
            FLAG = 0
            break
    broadcast(0)
##############################################################################

# This function sends a linkdown message
def send_linkdown(name):
    data = {}
    data['sender'] = SELF_NAME
    data['type'] = 'LINKDOWN'
    UDP_write.sendto(json.dumps(data), (NEIGHBOR_LIST[name]['IP'], int(NEIGHBOR_LIST[name]['port'])))
##############################################################################

# This function sends a linkup message
def send_linkup(name):
    data = {}
    data['sender'] = SELF_NAME
    data['type'] = 'LINKUP'
    UDP_write.sendto(json.dumps(data), (NEIGHBOR_LIST[name]['IP'], int(NEIGHBOR_LIST[name]['port'])))
##############################################################################

# This function sends a build edge message
def send_build(name, weight):
    data = {}
    data['sender'] = SELF_NAME
    data['type'] = 'BUILD'
    data['weight'] = weight
    UDP_write.sendto(json.dumps(data), (NEIGHBOR_LIST[name]['IP'], int(NEIGHBOR_LIST[name]['port'])))
##############################################################################

# This function linkdown an edge, as user request
def linkdown(name):
    DOWN_EDGE[name] = NEIGHBOR_LIST[name]['cost']
    NEIGHBOR_LIST.pop(name, None)
    TIMER_LIST[name].cancel()
    for node in NETWORK.keys():
        if NETWORK[node]['link'] == name:
            NETWORK[node]['cost'] = float("inf")
            for neighbor in NEIGHBOR_LIST.keys():
                if node in NEIGHBOR_LIST[neighbor]['DV'].keys():
                    if NETWORK[node]['cost'] > NEIGHBOR_LIST[neighbor]['cost'] + NEIGHBOR_LIST[neighbor]['DV'][node]:
                        NETWORK[node]['cost'] = NEIGHBOR_LIST[neighbor]['cost'] + NEIGHBOR_LIST[neighbor]['DV'][node]
                        NETWORK[node]['link'] = neighbor
##############################################################################

# This function responds to user's input command
def command_check(command):
    global FLAG
    name = command.split(' ')[1:]
    command = command.split(' ')[0]
    if command == 'LINKDOWN':
        FLAG = 2
        if len(name) != 2:
            print 'Command invalid.'
        else:
            name = ' '.join(name)
            if name in NEIGHBOR_LIST.keys():
                send_linkdown(name)
                linkdown(name)
            else:
                print 'Command invalid.'
        FLAG = 0
        broadcast(0)

    elif command == 'LINKUP':
        FLAG = 2
        if len(name) != 2:
            print 'Command invalid.'
        else:
            name = ' '.join(name)
            if name in DOWN_EDGE.keys():
                value = DOWN_EDGE.pop(name, None)
                [name_IP, name_port] = name.split(' ')
                NEIGHBOR_LIST[name] = {}
                NEIGHBOR_LIST[name]['cost'] = value
                NEIGHBOR_LIST[name]['IP'] = name_IP
                NEIGHBOR_LIST[name]['DV'] = {}
                NEIGHBOR_LIST[name]['port'] = name_port
                TIMER_LIST[name] = Timer(3*TIMEOUT, kill_neighbor, (name,))
                TIMER_LIST[name].daemon = True
                TIMER_LIST[name].start()
                if value < NETWORK[name]['cost']:
                    NETWORK[name]['cost'] = value
                    NETWORK[name]['link'] = name
                send_linkup(name)
            else:
                print 'Command invalid.'
        FLAG = 0
        broadcast(0)
    elif command == 'SHOWRT':
        show_rt()
    elif command == 'CLOSE':
        print 'Bye'
        sys.exit()
    elif command == 'TRAN':
        broadcast(0)
    elif command == 'TIMER':
        for t in TIMER_LIST.keys():
            print t
    elif command == 'NEIGHBOR':
        for node in NEIGHBOR_LIST.keys():
            print node + '(' + str(NEIGHBOR_LIST[node]['cost']) + ')'
    elif command == 'BUILDEDGE':
        FLAG = 2
        if len(name) != 3:
            print 'Command invalid.'
        else:
            weight = float(name[2])
            name = name[0:2]
            name = ' '.join(name)
            if name in NETWORK.keys() and name not in NEIGHBOR_LIST.keys():
                [name_IP, name_port] = name.split(' ')
                NEIGHBOR_LIST[name] = {}
                NEIGHBOR_LIST[name]['cost'] = weight
                NEIGHBOR_LIST[name]['IP'] = name_IP
                NEIGHBOR_LIST[name]['DV'] = {}
                NEIGHBOR_LIST[name]['port'] = name_port
                TIMER_LIST[name] = Timer(3*TIMEOUT, kill_neighbor, (name,))
                TIMER_LIST[name].daemon = True
                TIMER_LIST[name].start()
                if weight < NETWORK[name]['cost']:
                    NETWORK[name]['cost'] = weight
                    NETWORK[name]['link'] = name
                send_build(name, weight)
            else:
                print 'Command invalid.'
        FLAG = 0
        broadcast(0)

    else:
        print 'Command invalid.'
##############################################################################

# This function updates the routing table after receiving messages
def update_network(data_dict):
    global FLAG
    if data_dict['type'] == 'UPDATE':
        sender = data_dict.pop("sender", None)
        FLAG = 2
        data_dict.pop("type", None)
        if sender not in NEIGHBOR_LIST.keys():
            TIMER_LIST[sender] = Timer(3*TIMEOUT, kill_neighbor, (sender,))
            TIMER_LIST[sender].daemon = True
            TIMER_LIST[sender].start()

            NEIGHBOR_LIST[sender] = {}
            sender_data = sender.split(' ')
            NEIGHBOR_LIST[sender]['IP'] = sender_data[0]
            NEIGHBOR_LIST[sender]['port'] = sender_data[1]
            NEIGHBOR_LIST[sender]['cost'] = data_dict[SELF_NAME]
            NEIGHBOR_LIST[sender]['DV'] = {}
            NETWORK[sender] = {}
            NETWORK[sender]['cost'] = data_dict[SELF_NAME]
            NETWORK[sender]['link'] = sender
            FLAG = 1
        else:
            TIMER_LIST[sender].cancel()
            TIMER_LIST[sender] = Timer(3*TIMEOUT, kill_neighbor, (sender,))
            TIMER_LIST[sender].daemon = True
            TIMER_LIST[sender].start()
            if NETWORK[sender]['cost'] > NEIGHBOR_LIST[sender]['cost']:
                NETWORK[sender]['cost'] = NEIGHBOR_LIST[sender]['cost']
                NETWORK[sender]['link'] = sender
                FLAG = 1
            if NEIGHBOR_LIST[sender]['cost'] == float("inf"):
                NEIGHBOR_LIST[sender]['cost'] = data_dict[SELF_NAME]

        for node in data_dict.keys():
            NEIGHBOR_LIST[sender]['DV'][node] = data_dict[node]

        for node in data_dict.keys():
            if node != SELF_NAME:
                if node not in NETWORK.keys():
                    NETWORK[node] = {}
                    if node in NEIGHBOR_LIST.keys():
                        NETWORK[node]['cost'] = data_dict[node]
                        FLAG = 1
                    else:
                        NETWORK[node]['cost'] = data_dict[node] + NETWORK[sender]['cost']
                        FLAG = 1
                    NETWORK[node]['link'] = sender
                else:
                    if NETWORK[node]['link'] != sender:
                        if data_dict[node] + NETWORK[sender]['cost'] < NETWORK[node]['cost']:
                            NETWORK[node]['cost'] = data_dict[node] + NETWORK[sender]['cost']
                            NETWORK[node]['link'] = sender
                            FLAG = 1
                    else:
                        pre = NETWORK[node]['cost']
                        NETWORK[node]['cost'] = data_dict[node] + NETWORK[sender]['cost']
                        NETWORK[node]['link'] = sender
                        if NETWORK[node]['cost'] != pre:
                            FLAG = 1
        if FLAG == 1:
            FLAG = 0
            broadcast(0)
        else:
            FLAG = 0
    elif data_dict['type'] == 'LINKDOWN':
        FLAG = 2
        data_dict.pop("type", None)
        sender = data_dict.pop("sender", None)
        TIMER_LIST[sender].cancel()
        value = NEIGHBOR_LIST[sender]['cost']
        NEIGHBOR_LIST.pop(sender, None)
        DOWN_EDGE[sender] = value
        for node in NETWORK.keys():
            if NETWORK[node]['link'] == sender:
                NETWORK[node]['cost'] = float("inf")
            for neighbor in NEIGHBOR_LIST.keys():
                if node in NEIGHBOR_LIST[neighbor]['DV'].keys():
                    if NETWORK[node]['cost'] > NEIGHBOR_LIST[neighbor]['cost'] + NEIGHBOR_LIST[neighbor]['DV'][node]:
                        NETWORK[node]['cost'] = NEIGHBOR_LIST[neighbor]['cost'] + NEIGHBOR_LIST[neighbor]['DV'][node]
                        NETWORK[node]['link'] = neighbor
        FLAG = 0
        broadcast(0)


    elif data_dict['type'] == 'LINKUP':
        FLAG = 2
        data_dict.pop("type", None)
        sender = data_dict.pop("sender", None)
        TIMER_LIST[sender] = Timer(3*TIMEOUT, kill_neighbor, (sender,))
        TIMER_LIST[sender].daemon = True
        TIMER_LIST[sender].start()
        [sender_IP, sender_port] = sender.split(' ')
        NEIGHBOR_LIST[sender] = {}
        NEIGHBOR_LIST[sender]['cost'] = DOWN_EDGE[sender]
        DOWN_EDGE.pop(sender, None)
        NEIGHBOR_LIST[sender]['IP'] = sender_IP
        NEIGHBOR_LIST[sender]['port'] = sender_port
        NEIGHBOR_LIST[sender]['DV'] = {}
        if NEIGHBOR_LIST[sender]['cost']  < NETWORK[sender]['cost']:
            NETWORK[sender]['cost'] = NEIGHBOR_LIST[sender]['cost']
            NETWORK[sender]['link'] = sender
        FLAG = 0
        broadcast(0)

    elif data_dict['type'] == 'BUILD':
        FLAG = 2
        data_dict.pop("type", None)
        sender = data_dict.pop("sender", None)
        TIMER_LIST[sender] = Timer(3*TIMEOUT, kill_neighbor, (sender,))
        TIMER_LIST[sender].daemon = True
        TIMER_LIST[sender].start()
        [sender_IP, sender_port] = sender.split(' ')
        NEIGHBOR_LIST[sender] = {}
        NEIGHBOR_LIST[sender]['cost'] = data_dict['weight']
        NEIGHBOR_LIST[sender]['IP'] = sender_IP
        NEIGHBOR_LIST[sender]['port'] = sender_port
        NEIGHBOR_LIST[sender]['DV'] = {}
        if NEIGHBOR_LIST[sender]['cost']  < NETWORK[sender]['cost']:
            NETWORK[sender]['cost'] = NEIGHBOR_LIST[sender]['cost']
            NETWORK[sender]['link'] = sender
        FLAG = 0
        broadcast(0)
##############################################################################

# Global variables
EDGE = {}
SELF_NAME = ''
NETWORK = {}
DOWN_EDGE = {}
FLAG = 0
resend_FLAG = 0
TIMER_LIST = {}
##############################################################################

if __name__ == '__main__':
    NEIGHBOR_LIST = {}
    PORT = sys.argv[1]
    TIMEOUT = float(sys.argv[2])
    neighbor_arg = sys.argv[3:]
    SELF_NAME = socket.gethostbyname(socket.gethostname()) +' '+ PORT
    if len(neighbor_arg) %3 != 0:
        print "Input parameters incorrect"
        sys.exit()
    i=0
    while(i < len(neighbor_arg)-1):
        name = neighbor_arg[i]+' '+neighbor_arg[i+1]
        NEIGHBOR_LIST[name] = {}
        NEIGHBOR_LIST[name]['IP'] = neighbor_arg[i]
        NEIGHBOR_LIST[name]['port'] = int(neighbor_arg[i+1])
        NEIGHBOR_LIST[name]['cost'] = float(neighbor_arg[i+2])
        NEIGHBOR_LIST[name]['DV'] = {}

        NETWORK[neighbor_arg[i] +' '+ neighbor_arg[i+1]] = {}
        NETWORK[neighbor_arg[i] +' '+ neighbor_arg[i+1]]['cost'] = float(neighbor_arg[i+2])
        NETWORK[neighbor_arg[i] +' '+ neighbor_arg[i+1]]['link'] = neighbor_arg[i] +' '+ neighbor_arg[i+1]
        TIMER_LIST[name] = Timer(3*TIMEOUT, kill_neighbor, (name,))
        TIMER_LIST[name].daemon = True
        TIMER_LIST[name].start()
        i = i+3

    UDP_read = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = int(PORT)
    UDP_read.bind(('', port))

    UDP_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    resend_timer = Timer(TIMEOUT, broadcast, (1,))
    resend_timer.daemon = True
    resend_timer.start()
    broadcast(1)
    resend_FLAG = 1

    while 1:
        try:
            socket_list = [sys.stdin, UDP_read]

            # Select to determine the socket behavior
            UDP_read_read, UDP_read_write, UDP_read_error = select.select(socket_list , [], [])

            for sock in UDP_read_read:
                #In the case of client receive an update
                if sock == UDP_read:
                    data = sock.recv(4096)
                    loaded = json.loads(data)
                    update_network(loaded)

                #user are sending a command
                else :
                    command = sys.stdin.readline()
                    command = command.strip()
                    command_check(command)

        #Handling control+C interrupting
        except KeyboardInterrupt:
            print 'Bye'
            sys.exit()