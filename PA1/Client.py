__author__ = 'anitalu'
import socket
import sys
import select
import time

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()

print 'Socket Created'
# Take input information to bind to the server
host = sys.argv[1];
port = int(sys.argv[2]);
#Give connection information to user
try:
    s.connect((host , port))
except:
    print 'Failed to connect'
    sys.exit()

print 'Socket Connected to ' + host

while 1:
    try:
        socket_list = [sys.stdin, s]

        # Select to determine the socket behavior
        s_read, s_write, s_error = select.select(socket_list , [], [])

        for sock in s_read:
            #In the case of server is sending message
            if sock == s:
                message = sock.recv(1024)
                if not message :
                    print '\nDisconnected'
                    sys.exit()
                else :
                    #print the received message
                    sys.stdout.write(message)
                    sys.stdout.flush()

            #user are sending a message
            else :
                message = sys.stdin.readline()
                s.send(message)
    #Handling control+C interrupting
    except KeyboardInterrupt:
        s.send('Keyboard interrupt by client') #Tell the server that the user typed control+C
        print 'Keyboard interrupt, exiting'
        sys.exit()

