__author__ = 'anitalu'
import struct
import time
import threading
import sys
import os
import socket
import datetime

#This function does checksum job for the packet
def checksum(message):
    sum = 0
    for i in range(0, len(message), 2):
        if i < len(message) - 1:
            seg = ord(message[i]) + (ord(message[i+1]) << 8)
        elif i == len(message) - 1:
            seg = ord(message[i])
        sum = ((sum + seg) & 0xffff) + ((sum+seg) >> 16)
    return (~sum & 0xffff)
#######################################################################################################################

#This function closes the connections
def close_connection():
    print 'Connection closed'
    TCP.close()
    UDP.close()
#######################################################################################################################

#This function writes the received data into a file after the transmission has complete
def write_file(filename, data):
    try:
        File = open(filename,"wt")
    except:
        print 'File not found'
    File.write(data)
    File.close()
#######################################################################################################################

#This function sends ack to the sender
def sendack(source_port, dest_port, seq_num, ack_num, fin, sum, TCP):
    packet = struct.pack('HHIIII',source_port, dest_port, seq_num, ack_num, fin, sum)
    try:
        TCP.send(packet)
    except socket.error, msg:
        print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
#######################################################################################################################

#This function writes log information to logfile, or store it for directly display if asked by user
def writelogfile(logfile, indic, timestamp, source_port, dest_port, seq_num, ack_num, fin, sum):
    if indic == 'r':
        data = 'received: timestamp = ' + str(timestamp) +', source = '+ str(source_port) +', destination = '+ str(dest_port) +', seq_num = '+ str(seq_num) +', ack_num = '+ str(ack_num) +', fin = '+ str(fin) + ', sum = '+ str(sum) + '\n'
    else:
        data = 'sent: timestamp = ' + str(timestamp) +', source = '+ str(source_port) +', destination = '+ str(dest_port) +', seq_num = '+ str(seq_num) +', ack_num = '+ str(ack_num) +', fin = '+ str(fin) + ', sum = '+ str(sum) + '\n'
    if log_output == 0:
        logfile.write(data)
    else:
        print data
#######################################################################################################################

#GLOBAL VARIABLES
MAXSEGSIZE = 576    #max segment size
TIME_OUT = 0.5      #waiting time before connection close
FINISHED = 0        #indicate if the transmission has finished
SENDER_PORT = 0     #sender port number
SENDER_IP = 0       #sender IP address
log_output = 0      #indicate the display method of log information
#######################################################################################################################

if __name__=="__main__":
    #inputs check and allocation
    if len(sys.argv) != 6 :
        print 'Input parameters incorrect'
        sys.exit()

    [filename, listening_port, SENDER_IP, SENDER_PORT, log_filename] = sys.argv[1:]
    seq_expected = 0
    seq_received = []
    file_data = []
    buffer = {}
    fin_flag = 0

    if log_filename != 'stdout':
        try:
            logfile = open(log_filename,'wt')
        except:
            print 'unable to create file'
    else:
        logfile = 0
        log_output = 1

    #estblising connection
    UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listening_port = int(listening_port)
    SENDER_PORT = int(SENDER_PORT)
    UDP.bind(('', listening_port))

    TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        TCP.connect((SENDER_IP, SENDER_PORT))
    except:
        print 'Connect failed'
        sys.exit()
    TCP.send('a')

    #ack listening and response
    while (FINISHED == 0):
        received = UDP.recvfrom(1024)
        size_range = range(MAXSEGSIZE+1)
        size_range.reverse()
        for size in size_range:
            try:
                received_data = struct.unpack('!HHIIIHH%ds'%size, received[0])
                break
            except:
                pass
        [source_port, dest_port, seq_num, ack_num, fin, sum, oo, data] = received_data
        timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        writelogfile(logfile, 'r', timestamp, source_port, dest_port, seq_num, ack_num, fin, sum)
        data_sum = str(source_port) + str(dest_port) + str(seq_num) + str(ack_num) + str(fin) + str(data)
        source = listening_port
        dest = SENDER_PORT

        if fin == 0:
            if seq_num == seq_expected:#when receiving the wanted packet
                if checksum(data_sum) == sum:#if the packet has not been corrupted
                    file_data.append(data)
                    seq_expected = seq_expected + MAXSEGSIZE
                    sendack(source, dest, 0, seq_expected, 0, 0, TCP)
                    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    writelogfile(logfile, 's', timestamp, source, dest, 0, seq_expected, 0, 0)
                else:#if the packet has been corrupted
                    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                    sendack(source, dest, 0, seq_expected, 0, 0, TCP)
                    writelogfile(logfile, 's', timestamp, source, dest, 0, seq_expected, 0, 0)
            else:#when the received packet is not the wanted one:
                timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
                sendack(source, dest, 0, seq_expected, 0, 0, TCP)
                writelogfile(logfile, 's', timestamp, source, dest, 0, seq_expected, 0, 0)
        else:#if the transmission is finishing
            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            sendack(source, dest, 0, seq_expected, 1, 0, TCP)
            writelogfile(logfile, 's', timestamp, source, dest, 0, seq_expected, 0, 0)
            write_file(filename, ''.join(file_data))
            timer = threading.Timer(TIME_OUT, close_connection)
            timer.start()
            FINISHED = 1
            print 'Delivery completed successfully'









