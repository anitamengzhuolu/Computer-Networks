__author__ = 'anitalu'
import socket
import sys
import time
import threading
import os
from thread import *

#This function reads in the username and password information
def readfile():
    diction = open("user_pass.txt")
    rows = diction.readlines()
    for row in rows:
        row = row.split(' ')
        dic_usernames.append(row[0])
        USERNAME[row[0]] = []
        dic_passwords.append(row[1])
##############################################################

def

def filetransfer(conn, username, comamnd_parameter):
    [filename, remote_IP, remote_port, ack_port_num, log_filename, window_size] = comamnd_parameter
    fileinfo = os.stat(filename)
    file_sending = []

    try:
        file = open(filename,"r")
    except:
        print 'File not found'
    for index in range(1,fileinfo.st_size/MAXSEGSIZE+2):
        packet = file.read(MAXSEGSIZE)
        file_sending.append(packet)
    file.close()

    pack(remote_port, )




#This function realise the "whoelse" command, if no one is online, will send "Not Found"
def whoelse(conn, username):
    flag = 0
    conn.sendall('The currently online users are:\n')
    for user in login_usernames.keys():
        if not user == username:
            if login_usernames[user][2] == 1:
                conn.sendall(user)
                if login_usernames[user][4] != 0:
                    conn.sendall('   <' + login_usernames[user][4] + '>' + '\n')
                else:
                    conn.sendall('\n')
                flag = 1
    if flag == 0:
        conn.sendall('(Not found)\n')
#########################################################################################

#This function realise the "whoelse" command, if no one has been online for the giving period, will send "Not Found"
def wholast(conn, timelast, username):
    flag = 0
    conn.sendall('The users that are online in the last ' + str(timelast) + ' minutes are:\n')
    for user in login_usernames.keys():
        if not user == username:
            offline_time = time.time() - login_usernames[user][1]
            if offline_time <= timelast*60 or login_usernames[user][2] == 1:
                conn.sendall(user)
                if login_usernames[user][4] != 0:
                    conn.sendall('   <' + login_usernames[user][4] + '>' + '\n')
                else:
                    conn.sendall('\n')
                flag = 1
    if flag == 0:
        conn.sendall('(Not found)\n')
######################################################################################################################

#This function broadcast message to all users, if the user is not online, the system will wait until the user logging in to show him/her the message
#The system will also indicate the user that this is a broadcast message
def broadcastmessage(conn, username, message):
    for user in login_usernames.keys():
        if login_usernames[user][2] == 1 and user != username:
            login_usernames[user][3].send('\n' + username +': ' + message + ' <broadcast message>' + '\nCommand:')
    for user in dic_usernames:
        if user not in login_usernames.keys():
            USERNAME[user].append(str('\n' + username +': ' + message + ' <broadcast message>'))
#####################################################################################################################################################

#This function will broadcast message to a selected range of users, if not online, the system will wait until they log in
#If the user input involved a typo, the system will alert the user
def broadcastuser(conn, receiver_list, message, username):
    for user in receiver_list:
        if user in login_usernames.keys() and login_usernames[user][2] == 1:
            if user != username:
                login_usernames[user][3].send('\n' + username +': ' + message + '\nCommand:')
            else:
                login_usernames[user][3].send('\n' + username +': ' + message)
        elif user not in dic_usernames:
            conn.sendall('(Input includes a typo on receiver names: ' + user + ', not delivered)\n')
        else:
            conn.sendall('(Receiver ' + user + ' is currently offline, message will be delivered when they log in next time)\n')
            USERNAME[user].append(str('\n' + username +': ' + message))
##########################################################################################################################

#This function send private message to user, if user not online, the system will wait until the user login to send the message
#The system will also indicate this is a private message.
#If the sender typed a wrong name, the system will alert the user
def pmessage(conn, receiver, message, username):
    if receiver in login_usernames.keys() and login_usernames[receiver][2] == 1:
        if receiver != username:
            login_usernames[receiver][3].send('\n' + username +': ' + message + ' <private message>' + '\nCommand:')
        else:
            login_usernames[receiver][3].send('\n' + username +': ' + message + ' <private message>')
    elif receiver not in dic_usernames:
        conn.sendall('(Input includes a typo on receiver names: ' + receiver + ', not delivered)\n')
    else:
        conn.sendall('(Receiver ' + receiver + ' is currently offline, message will be delivered when they log in next time)\n')
        USERNAME[receiver].append(str('\n' + username +': ' + message + ' <private message>'))
###############################################################################################################################

#This function let user to input a personal introduction, when other user run command "whoelse" or "wholast", they will be able to see
#both the username and corresponding personal introduction
def personalintro(conn, username):
    conn.sendall('Please enter your personal introduction:\n')
    intro = conn.recv(1024)
    if intro == 'Keyboard interrupt by client':
        checkclientstatus(conn, username, addr)
    intro = intro.strip()
    login_usernames[username][4] = intro
#######################################################################################################################################

#User will go through this function to logout, it handles parameters related to logout as well
def logout(conn, username, addr):
    #Logging out time
    login_usernames[username][1] = time.time()
    #Online flag set back to 0
    login_usernames[username][2] = 0
    logoff(username, conn, addr)
###############################################################################################

#This function enabled the system to time out a user
def timeout(conn, username, addr):
    conn.sendall('(You are time out)\n')
    logout(conn, username, addr)
####################################################

#This function handles keyboard interruption from the client side, it will stop the system from poping error message and also mark the user as logged out
def checkclientstatus(conn, username, addr):
    if username == 0:
        print 'Disconnected with ' + addr[0] + ':' + str(addr[1])
        conn.close()
    else:
        logout(conn, username, addr)
##########################################################################################################################################################

#This function is for logging in, it will indicate the user to login and handle incorrect inputs
def login(conn, addr):
    #Username input
    while 1:
        conn.sendall('\nUsername:')
        username = conn.recv(1024)
        if username == 'Keyboard interrupt by client':
            checkclientstatus(conn, 0, addr)
            return 0
        else:
            username = username.strip()
        if username in dic_usernames:
            break
        else:
            conn.sendall('Username incorrect, please check.')
    count=0
    #Passwpord input
    while 1:
        if username in blocked_usernames.keys():
            if addr[0] == blocked_usernames[username][1]:
                blockedtime = time.time() - blocked_usernames[username][0]
                if blockedtime > BLOCK_TIME:
                    blocked_usernames.pop(username)
                else:
                    conn.sendall('Im sorry, you are currently blocked, and you need to wait for another ' + str(BLOCK_TIME - blockedtime) + ' seconds')
                    logoff(username, conn, addr)
                    return 0
        elif username in login_usernames and login_usernames[username][2] == 1:
            conn.sendall('You are already logged in')
            logoff(username, conn, addr)
            return 0

        conn.sendall('\nPassword:')
        password = conn.recv(1024)
        if password == 'Keyboard interrupt by client':
            checkclientstatus(conn, 0, addr)
            return 0
        else:
            password = password.strip()

        if password in dic_passwords and dic_usernames.index(username) == dic_passwords.index(password):
            conn.sendall('Login successful, Welcome to simple chat server!')
            #Record logging in time, leave space for loggingout time, set online flag to 1
            login_usernames[username]=[time.time(), 0, 1, conn, 0]
            if len(USERNAME[username]) > 0:
                conn.sendall('\nYour offline messages:')
                for offlinemessage in USERNAME[username]:
                    conn.sendall(offlinemessage)
                USERNAME[username] = []
            return username
        else:
            count = count + 1
            if count == LOGIN_TIMES:
                blocked_usernames[username] = [time.time(), addr[0]]
                conn.sendall('Im sorry, you are currently blocked, and you need to wait for ' + str(BLOCK_TIME) + ' seconds')
                count = 0
                logoff(username, conn, addr)
                return 0
            else:
                conn.sendall('Password incorrect, Please try again, if you fail ' + str(LOGIN_TIMES - count) + ' more times you will be blocked for a while')
#####################################################################################################################################################################

#This function will close the socket and break connection with the user
def logoff(username, conn, addr):
    conn.sendall('\nLogging off')
    print 'Disconnected with ' + addr[0] + ':' + str(addr[1])
    conn.close()
########################################################################

#This function is for handling connections, using threads, it also handles user inputs, including respond to commands and handle incorrect inputs
def clientthread(conn, addr):
    username = login(conn, addr)
    #Running commands
    if username:
        while login_usernames and login_usernames[username][2] == 1:
            conn.sendall('\nCommand:')
            timer = threading.Timer(TIME_OUT, timeout, (conn, username, addr))
            timer.start()
            command = conn.recv(1024)
            if command == 'Keyboard interrupt by client':
                checkclientstatus(conn, username, addr)
                break
            if login_usernames[username][2] == 0:
                break
            timer.cancel()
            command = command.strip()
            command_command = command.split(' ')[0]
            comamnd_parameter = command.split(' ')[1:]
            if not command_command in COMMANDS_LIST:
                conn.sendall('\nCommand invalid.')
            else:
                if command_command == 'whoelse':
                    whoelse(conn, username)
                if command_command == 'wholast':
                    if not len(comamnd_parameter) == 1:
                        conn.sendall('\nCommand invalid.')
                    elif int(comamnd_parameter[0]) > 60 or int(comamnd_parameter[0]) < 0:
                        conn.sendall('\nViewing time should be within 0-60 mins.')
                    else:
                        wholast(conn, comamnd_parameter[0], username)
                if command_command == 'broadcast':
                    if comamnd_parameter[0] == 'message':
                        if not len(comamnd_parameter) > 1:
                            conn.sendall('\nCommand invalid.')
                        else:
                            message = ' '.join(comamnd_parameter[1:])
                            broadcastmessage(conn, username, message)
                    elif comamnd_parameter[0] == 'user':
                        if not len(comamnd_parameter) > 1 or not 'message' in comamnd_parameter:
                            conn.sendall('\nCommand invalid.')
                        else:
                            index_message = comamnd_parameter.index('message')
                            receiver_list = comamnd_parameter[1:index_message]
                            message = ' '.join(comamnd_parameter[index_message+1:])
                            broadcastuser(conn, receiver_list, message, username)
                    else:
                        conn.sendall('\nCommand invalid.')
                if command_command == 'message':
                    if not len(comamnd_parameter) > 1:
                            conn.sendall('\nCommand invalid.')
                    else:
                        receiver = comamnd_parameter[0]
                        message = ' '.join(comamnd_parameter[1:])
                        pmessage(conn, receiver, message, username)
                if command_command == 'personalintro':
                    personalintro(conn, username)
                if  command_command == 'filetransfer':
                    filetransfer(conn, username, comamnd_parameter)
                if command_command == 'logout':
                    logout(conn, username, addr)
#################################################################################################################################################

if __name__=="__main__":

    HOST = ''   #All available interfaces
    PORT = int(sys.argv[1])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'Socket created successfully'

    #Bind socket
    try:
        s.bind((HOST, PORT))
    except socket.error , msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
    print 'Socket bind successfully'
    #Start listening on socket
    s.listen(100)
    print 'All is well, listening'

    #GLOBAL VARIABLES
    blocked_usernames = {}    #The list which stores all the blocked users
    login_usernames = {}    #Store usernames who logged in
    BLOCK_TIME = 60    #Block time, currently at 60 seconds
    LOGIN_TIMES = 3    #Number of consecutive failures, now at 3
    COMMANDS_LIST = ['whoelse', 'wholast', 'broadcast', 'message', 'logout', 'personalintro']    #The list of commands
    TIME_OUT = 30*60    #User time out time, currently at half an hour
    USERNAME = {}    #A list stores usernames
    dic_usernames=[]    #Readed in usernames
    dic_passwords=[]    #Readed in passwords
    MAXSEGSIZE=576

    readfile()

    #now keep talking with the client
    while 1:
        try:
            #wait to accept a connection - blocking call
            conn, addr = s.accept()
            print 'Connected with ' + addr[0] + ':' + str(addr[1])
            #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
            start_new_thread(clientthread ,(conn, addr))
        except KeyboardInterrupt:
            print 'Keyboard interrupt, exiting'
            sys.exit()

