__author__ = 'anitalu'
import struct
import time
import threading
import sys
import os
import socket
from thread import *
import datetime

#This function reads the input file and cut it into segments, with each segment size is 576 bytes besides the last segment, which size is whatever
#left in the file
def readfile(filename):
    file_sending = []
    num=0
    try:
        file = open(filename,"r")
    except:
        print 'File not found'
    fileinfo = os.stat(filename)
    for index in range(0,fileinfo.st_size/MAXSEGSIZE):
        packet = file.read(MAXSEGSIZE)
        file_sending.append(packet)
        num = num + 1
    packet = file.read(fileinfo.st_size%MAXSEGSIZE)
    file_sending.append(packet)
    num = num + 1
    file.close()
    return [file_sending, num]
#######################################################################################################################

#This function does checksum work for the packet
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

#This function pack the input information to a packet and send it to the receiver, as well as write the packet's header into logfile
def send(source_port, dest_port, seq_num, ack_num, fin, sum, data):
    inside = str(source_port) + str(dest_port) + str(seq_num) +str(ack_num) + str(fin) + str(data)
    sum = checksum(inside)
    packet = struct.pack('!HHIIIHH%ds'%len(data),source_port, dest_port, seq_num, ack_num, fin, sum, 0, data)
    writelogfile(logfile, 's', datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), estimated_RTT, source_port, dest_port, seq_num, ack_num, fin, sum)
    try:
        UDP.sendto(packet, (RECEIVER_IP, RECEIVER_PORT))                             # Timer start time
    except socket.error, msg:
        print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
#######################################################################################################################

#This packet estimate RTT and adjust TIME_OUT value accordingly
def estimate(t_sent ,t_received):
    global estimated_RTT, dev_RTT, TIME_OUT, window_size
    sample_RTT = t_received - t_sent
    estimated_RTT = (1-0.125) * estimated_RTT + 0.125 * sample_RTT
    dev_RTT = (1-0.25) * dev_RTT + 0.25 * abs(sample_RTT - estimated_RTT)
    TIME_OUT = estimated_RTT + 4 * dev_RTT
    return estimated_RTT, TIME_OUT
#######################################################################################################################

#This function is called when time out happens, and retransmits the timed out packet, as well as setting a new timer for it
def timeout(pack_num):
    global retransmit, TIME_OUT, resent
    if FINISHED < 2:
        if pack_num<base:
            sys.exit()
        seq_num = pack_num * MAXSEGSIZE
        if (pack_num) not in resent:
            resent.append(pack_num)
        send(ack_port_num, remote_port, seq_num, 0, 0, 0, file_sending[pack_num])
        timer[pack_num%window_size] = (threading.Timer(TIME_OUT, timeout, (pack_num,)))
        timer[pack_num%window_size].start()
        retransmit = retransmit + 1
        sys.exit()
#######################################################################################################################

#This function writes the packet's header into a logfile, or stores the log information and display it after transmission, as user requires
def writelogfile(logfile, indic, timestamp, RTT, source, destination, seq_num, ack_num, fin, sum):
    global logdata
    if indic == 'r':
        data = 'received: timestamp = '+str(timestamp) +', source = '+ str(source) +', destination = '+ str(destination) +', seq_num = '+ str(seq_num) +', ack_num = '+ str(ack_num) +', fin = '+ str(fin) + ', sum = '+ str(sum) + ', RTT = ' + str(RTT) + '\n'
    else:
        data = 'sent: timestamp = '+str(timestamp) +', source = '+ str(source) +', destination = '+ str(destination) +', seq_num = '+ str(seq_num) +', ack_num = '+ str(ack_num) +', fin = '+ str(fin) + ', sum = '+ str(sum) + ', RTT = ' + str(RTT) + '\n'
    if log_output == 0:
        logfile.write(data)
    else:
        logdata = logdata + data
#######################################################################################################################

#This function lies in a separate thread; listens to acks and give corresponding reaction
def ack_listen(conn, addr, logfile):
    global ack_num, estimated_RTT, TIME_OUT, base, timer, FINISHED, retransmit
    global duplicate,resent
    while(FINISHED != 2):
        ack = conn.recv(20)
        ack_data = struct.unpack('HHIIII', ack)
        fin = ack_data[4]
        writelogfile(logfile, 'r', datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'), estimated_RTT, ack_data[0], ack_data[1], ack_data[2], ack_data[3], ack_data[4], ack_data[5])
        if fin !=1:
            ack_num = ack_data[3]
            if ack_num == num_pack*MAXSEGSIZE:
                FINISHED = 1
            if FINISHED == 0:
                if (ack_num/MAXSEGSIZE)>base:
                    last_base = base
                    base = ack_num/MAXSEGSIZE
                    t_received[ack_num/MAXSEGSIZE -1] = time.time()
                    if (ack_num/MAXSEGSIZE -1) not in resent:
                        estimated_RTT, TIME_OUT = estimate(t_sent[ack_num/MAXSEGSIZE-1] ,t_received[ack_num/MAXSEGSIZE-1])
                    if FINISHED == 0:
                        end = base + window_size
                    else:
                        end = num_pack
                    for pack_num in range(last_base + window_size, end):
                        if pack_num < num_pack:
                            seq_num = pack_num * MAXSEGSIZE
                            timer[pack_num%window_size].cancel()
                            send(ack_port_num, remote_port, seq_num, 0, 0, 0, file_sending[pack_num])
                            t_sent[pack_num] = time.time()
                            timer[pack_num%window_size] = (threading.Timer(TIME_OUT, timeout, (pack_num,)))
                            timer[pack_num%window_size].start()
                        else:
                            break
                elif (ack_num/MAXSEGSIZE)==base:
                    duplicate[ack_num/MAXSEGSIZE] = duplicate[ack_num/MAXSEGSIZE] +1
                    if duplicate[ack_num/MAXSEGSIZE] == 3:
                        if (ack_num/MAXSEGSIZE) not in resent:
                            resent.append(ack_num/MAXSEGSIZE)
                        retransmit = retransmit + 1
                        timer[(ack_num/MAXSEGSIZE)%window_size].cancel()
                        send(ack_port_num, remote_port, ack_num, 0, 0, 0, file_sending[ack_num/MAXSEGSIZE])
                        timer[(ack_num/MAXSEGSIZE)%window_size] = (threading.Timer(TIME_OUT, timeout, (ack_num/MAXSEGSIZE,)))
                        timer[(ack_num/MAXSEGSIZE)%window_size].start()
                            #t_sent[ack_num/MAXSEGSIZE] = time.time()
                        duplicate[ack_num/MAXSEGSIZE] = 0

        else:
            FINISHED = 2
#######################################################################################################################

#GLOBAL VARIABLES
MAXSEGSIZE=576          #max segment size
RECEIVER_IP = 0         #receiver's IP address
RECEIVER_PORT = 0       #receiver's port number
FINISHED = 0            #flag to indicate if the transmission has finished
ack_expected = 0        #expecting ack number
base = 0                #base number for the current window
remote_port = 0         #receiver's port number
ack_port_num = 0        #port number for ack listening
file_sending = []       #list of packets waiting to be sent
TIME_OUT = 0.1          #initial time out value
t_sent = {}             #Records the sent time of each packets, to calculate sample RTT
t_received = {}         #Records the receive time of each package, to calculate sample RTT
estimated_RTT = 0.005   #initial estimate RTT value
dev_RTT = 0.05          #parameter used to calculate the estimated RTT
ack_num = 0             #ack number
window_size = 0         #window size for pipelining
timer = []              #timer list, with a size equals to window_size, keeps a timer for each packet in current window
retransmit = 0          #calculate the total retransmission time
duplicate = {}          #indicate how many times the packet has been transmitted before, used for TCP fast retransmit
resent = []             #indicate if the packet has been transmitted before, avoiding inaccurately calculate RTT, causing too long TIMEOUT
log_output = 0          #flag for the method of outputting log information
logdata = ''            #storing log data if user required log information being printed directly
#######################################################################################################################

if __name__=="__main__":

    #Input information check and allocation
    if len(sys.argv)!=6 and len(sys.argv)!=7:
        print 'Input parameters incorrect'
        sys.exit()
    elif len(sys.argv) == 7:
        [filename, remote_IP, remote_port, ack_port_num, log_filename, window_size] = sys.argv[1:]
    elif len(sys.argv) == 6:
        [filename, remote_IP, remote_port, ack_port_num, log_filename] = sys.argv[1:]
        window_size = 1
    window_size = int(window_size)
    remote_port = int(remote_port)
    ack_port_num = int(ack_port_num)
    RECEIVER_IP = remote_IP
    RECEIVER_PORT = remote_port

    #Distinguish the log information outputting method
    if log_filename != 'stdout':
        try:
            logfile = open(log_filename,'wt')
        except:
            print 'unable to create file'
    else:
        logfile = 0
        log_output = 1

    #partiting files and record the total number of segments
    [file_sending, num_pack] = readfile(filename)

    #creating TCP and UDP connection for acks and datas respectively
    UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    HOST = ''
    TCP.bind((HOST, ack_port_num))
    TCP.listen(10)
    conn, addr=TCP.accept()
    conn.recv(1024)

    #starting a new thread for ack listening
    start_new_thread(ack_listen ,(conn, addr, logfile))

    #initialise values
    for p in range(0,num_pack):
        duplicate[p] = 0

    #sending the first window
    for pack_num in range(base, window_size):
        if pack_num < num_pack:
            seq_num = pack_num * MAXSEGSIZE
            send(ack_port_num, remote_port, seq_num, 0, 0, 0, file_sending[pack_num])
            t_sent[pack_num] = time.time()
            timer.append(threading.Timer(TIME_OUT, timeout, (pack_num,)))
            timer[pack_num%window_size].start()
        else:
            break

    print '******Sending Progress******'

    #Monitoring the sending progress
    while(FINISHED != 2):#When the transmission is not finished
        if FINISHED == 1:#if all the packets has be securely sent, send fin to the receiver to indicate the completion of job
            send(ack_port_num, remote_port, 0, 0, 1, 0, '0')
            timer_fin = threading._Timer(TIME_OUT, send, (ack_port_num, remote_port, 0, 0, 1, 0, '0'))
            timer_fin.start()
        #when sending in progress, display the current sending progress percentage to sender's terminal
        sys.stdout.write('\r'+'             '+str(int(100*round((ack_num/MAXSEGSIZE)/float(num_pack),2)))+'%')
        sys.stdout.flush()

        if FINISHED == 2:#when sending finished:
            timer_fin.cancel()
            print '\n',
            print 'Delivery completed successfully'
            print 'Total bytes sent (and securely received by receiver) = ' + str(ack_num-MAXSEGSIZE)
            print 'Segments sent (and securely received by receiver) = ' + str(num_pack)
            print 'Segments retransmitted = ' + str(retransmit)
            if log_output == 1:
                print 'log information:'
                print logdata
            sys.exit()


