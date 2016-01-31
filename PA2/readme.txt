a. A brief introduction

This project implements a simplified TCP-like transport layer protocol. My implementation provides a stable, in order and relatively efficiency file transmission even over an unreliable network, using a hybrid of Go-Back-N and Selective Repeat(more concept from GBN are implemented). It contains 2 python files (sender.py and receiver.py) and a sample file (harry_potter_2.txt) for testing, which contains Harry Potter and the Chamber of Secrets. When invoking, the sender file will transmit selected file to the receiver in pipelined fashion, and record the log information for both sender and receiver. During transmission, the sending progress will be continuously updated and printed on sender’s terminal showing the current progress in a percentage value. 

In sender.py, the program will firstly build a TCP connection(for ACK listening) and a UDP connection (for data delivery). After that it sends the first window of packets, with window size decided by user’s input. In the mean time, a son thread will be listing to the ACK received, and give response based on the ACK number. Time out is also implemented here to avoid packet loss and corruption. The program will keep as many timer as the window size, each using an individual thread. They retransmits the corresponding packet with the timed out sequence number upon time out. After all ACKs has been received, the sender will send a fin to the receiver to close the connection. 

In receiver.py, after connections establishment, the receiver will listen to the packets from sender, and respond it with the corresponding ACK number. The receiver will give the next expected sequence number if the received data is correct and has the right sequence number, and will ask the sender to transmit the current expecting packet again otherwise. When received a fin, the receiver will write the received file and close the connections.

b. Usage scenarios

A typical text case for the project using the proxy provided are listed below :

Firstly in proxy side call: ./newudpl -i127.0.0.1:* -o127.0.0.1:20000 -p5000:6000 -L7 -B5 -O9

Then in sender side call: python sender.py harry_potter_2.txt 127.0.0.1 5000 20001 logfile_sender.txt 10

After that, in receiver side call: python receiver.py received_file.txt 20000 127.0.0.1 20001 logfile_receiver.txt

Then we will see the transmission has begun. a percentage value will be showing and updating on sender’s terminal, like this:

******Sending Progress******
             57%

After the number reached 100%, which indicates the transmission is completed, the sender’s terminal will display:

Delivery completed successfully
Total bytes sent (and securely received by receiver) = 491904
Segments sent (and securely received by receiver) = 855
Segments retransmitted = 3634

And the receiver’s terminal will display:

Delivery completed successfully
Connection closed

In the receiver side the new received file can be found, as well as a log file, some of the lines from the receiver log file are:

received: timestamp = 2015-11-07 23:09:31, source = 20001, destination = 5000, seq_num = 0, ack_num = 0, fin = 0, sum = 31421
sent: timestamp = 2015-11-07 23:09:31, source = 20000, destination = 20001, seq_num = 0, ack_num = 576, fin = 0, sum = 0
received: timestamp = 2015-11-07 23:09:31, source = 20257, destination = 5000, seq_num = 576, ack_num = 0, fin = 0, sum = 28718
sent: timestamp = 2015-11-07 23:09:31, source = 20000, destination = 20001, seq_num = 0, ack_num = 576, fin = 0, sum = 0

Some of the lines from the sender log file are:
received: timestamp = 2015-11-07 23:09:32, source = 20000, destination = 20001, seq_num = 0, ack_num = 1728, fin = 0, sum = 0, RTT = 0.00518350720406
received: timestamp = 2015-11-07 23:09:32, source = 20000, destination = 20001, seq_num = 0, ack_num = 1728, fin = 0, sum = 0, RTT = 0.00518350720406
sent: timestamp = 2015-11-07 23:09:32, source = 20001, destination = 5000, seq_num = 1728, ack_num = 0, fin = 0, sum = 46978, RTT = 0.00518350720406

c. TCP segment structure used

	1. TCP segment structure used for data (20 bytes + 576 bytes), although the acknowledgement number is not useful in this implementation. 
	
	—————————————————————————————————————————————————————
	|Source port# (2 Bytes) | Destination port# (2 Bytes)|
	—————————————————————————————————————————————————————
	|             Sequence number# (4 Byte)              |
	—————————————————————————————————————————————————————
	|           Acknowledgment number# (4 Byte)          |
	—————————————————————————————————————————————————————
	|               	FIN (4 Byte)                  |
	—————————————————————————————————————————————————————
	|  Checksum value(2 Bytes) |    Unused (2 Bytes)     |
	—————————————————————————————————————————————————————
	|                                                    |
	|                  Data (576 Bytes)                  |
	|                                                    |
	|                                                    |
	—————————————————————————————————————————————————————
	
	2. TCP segment structure used for ACK (20 bytes), although the sequence number and checksum value is not useful in this implementation.
	
	—————————————————————————————————————————————————————
	|Source port# (2 Bytes) | Destination port# (2 Bytes)|
	—————————————————————————————————————————————————————
	|             Sequence number# (4 Byte)              |
	—————————————————————————————————————————————————————
	|           Acknowledgment number (4 Byte)           |
	—————————————————————————————————————————————————————
	|               	FIN (4 Byte)                  |
	—————————————————————————————————————————————————————
	|                Checksum value(4 Bytes)             |
	—————————————————————————————————————————————————————

d. The states typically visited by a sender and receiver

	1. The states typically visited by a sender
	
	(1). sender listening state: In this state the sender waits for ACKs, when received an ACK larger than the base of the current window, this means this ACK indicate the sender can now transmit more packets. It will now move base and transmit more packets (those newly included by window), and stay in state (1).
	When the received ACK number is equal to the current base, this means a duplicate ACK has been received. The duplicate time for that particular sequence number will increase by 1, and when the duplicate time for the sequence number reached 3, the sender will go to state (2).
	When the received ACK number is less then the current base, it will be ignored because this packet has already been securely delivered.
	When the received ACK number indicates all the packets has been securely delivered, it will go to state (3)
	When received a packet with FIN=1, the sender will go to state (4)
	When any packets has time outed, state (5) is reached.
	
	(2). TCP fast retransmit state: In this state, the packet with 3 duplicate ACKs will be retransmitted, and its timer will be restarted. After this the sender will go back to state (1)

	(3). Ready to finish state: In this state, the sender will know all of the packets has been securely delivered (by checking the ACK number), and it will send a packet with FIN=1, and go back to state (1)

	(4). Closing state: The sender will print all the statistics and exit the system.

	(5). Time out state: In this state, sender retransmit the time outed packet and reset its timer, and go back to state (1).

	2. The states typically visited by a receiver

	(1). receiver listening state: In this state the receiver waits for packets. When a packet arrived, it firstly checks the sequence number, if it is the expecting one, it conducts checksum. If successful, receiver will update the expecting sequence number and send ACK for the new expecting sequence number and stay in state (1).
	If packet has correct sequence number but checksum failed, receiver will send ACK with current expecting sequence number and stay in state (1).
	if the packet has wrong sequence number, receiver will send ACK with current expecting sequence number and stay in state (1).
	If the packet has FIN=1, go to state (2)

	(2). Finishing state: In this state, receiver write the received data to a file, and close connection. 

e. The loss recovery mechanism

When a packet is loss, it can be recovered by time out or TCP fast retransmission. So the lost packet will be retransmitted. 

f. Details on development environment

This project was developed in a MAC os with Python 2.7.10, and also tested in python 2.6.9. This may not work in Windows.

g. unusual about my implementation

This implementation applied TCP fast retransmit to improve efficiency. It also displays the current sending progress on sender’s terminal, which enhanced user experience. 

To avoid too long time out value, the sample RTT will be calculated only for packets which successfully reached the receiver without corruption in their first transmission (packets with no retransmission), so if the network environment is so unstable that no packet has been received in their first try, the estimated RTT may appeared to be not changing. 

Thanks for reading!

Mengzhuo Lu

2015.11