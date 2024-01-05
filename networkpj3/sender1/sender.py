# python3 sender.py -p <port> -g <requester port> -r <rate> -q <seq_no> -l <length>

import socket
import struct
import sys
import time
import datetime
import argparse

def printmessage(type, requet_add, myseqnum, payloadlen, payload):
    if type == 'D':
        print('DATA Packet')
    else:
        print('END Packet')
    curtime = datetime.datetime.now()
    print('{0:<17}{1}'.format('send time:', curtime))
    print('{0:<17}{1}'.format('requester addr:', (requet_add[0] +':'+str(requet_add[1]))))
    print('{0:<17}{1}'.format('sequence:', myseqnum))
    print('{0:<17}{1}'.format('length:', payloadlen))
    print('{0:<17}{1}'.format('payload:', payload))
    print()

def waitforack(seq_packet, seq_timeout, seq_count, in_packet, addresstogo):
    global retransmit
    global transmit
    if in_packet != None:
        prior, source_addr, source_port, dest_addr, dest_port, inner_pack_size, packet_type, seq_num, window_size = struct.unpack(f'!B4sH4sHIcII',in_packet[:26])
        seq_num = socket.ntohl(seq_num)
        #print('seq_num:', seq_num)
        if packet_type.decode() == 'A':
            #print('ACK!!!')
            if seq_num in seq_packet:
                seq_packet.pop(seq_num)
                seq_timeout.pop(seq_num)
                seq_count.pop(seq_num)
    seq_timeout_copy = seq_timeout.copy()
    for s,t in seq_timeout_copy.items():
        # time out!
        curtime = time.time()
        #print('curtime and expire time:', curtime, t)
        if curtime > t:
            #print('TIME OUT!!!')
            if seq_count[s] > 4:
                # resend more than 5 times
                print(f"gave up on packet {s}")
                #print("giva up on", seq_packet[s])
                seq_packet.pop(s)
                seq_timeout.pop(s)
                seq_count.pop(s)
            else:
                # resend
                #print('RESEND!!!')
                prior, source_addr, source_port, dest_addr, dest_port, inner_pack_size, packet_type, seq_num, window_size = struct.unpack(f'!B4sH4sHIcII',seq_packet[s][:26])
                #print(socket.ntohs(source_port))
                #print(seq_packet[s])
                #print('wrong address:', (socket.inet_ntoa(source_addr),socket.ntohs(source_port)))
                receive_sock.sendto(seq_packet[s], addresstogo)
                retransmit += 1
                transmit += 1
                seq_timeout[s] = curtime + paradict['timeout'] / 1000
                seq_count[s] += 1
                #print(seq_count)




        

    
# get parameter
parser = argparse.ArgumentParser()
parser.add_argument('-p')
parser.add_argument('-g')
parser.add_argument('-r')
parser.add_argument('-q')
parser.add_argument('-l')
parser.add_argument('-f')
parser.add_argument('-e')
parser.add_argument('-i')
parser.add_argument('-t')
args = parser.parse_args()

paradict = {}
try:
    paradict['receive_port'] = int(args.p) # sender port
    paradict['response_port'] = int(args.g) # requester port
    paradict['send_rate'] = int(args.r)
    paradict['seq_num'] = int(args.q)
    paradict['packet_len'] = int(args.l)
    paradict['emulator_port'] = int(args.e)
    paradict['priority'] = int(args.i)
    paradict['timeout'] = int(args.t)
except:
    print('One of the parameters is not interger!')
    sys.exit(0)
paradict['emulator_name'] = args.f
# binding
receive_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#print(socket.gethostbyname(socket.gethostname()),paradict['receive_port'])
receive_sock.bind((socket.gethostbyname(socket.gethostname()),paradict['receive_port']))
#response_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# listen (waiting for the requester)
lastindex = 0
#myseqnum = paradict['seq_num']
# changed
retransmit = 0
transmit = 0
myseqnum = 1
in_packet, requet_add = receive_sock.recvfrom(1024)
addresstogo = requet_add
#print("from where", requet_add)
prior, source_addr, source_port, dest_addr, dest_port, inner_pack_size, packet_type, seq_num, window_size = struct.unpack('!B4sH4sHIcII',in_packet[:26])
receive_sock.setblocking(False)
window_size = socket.ntohl(window_size)
window_size_backup = window_size
seq_packet = {}
seq_timeout = {}
seq_count = {} # resend count
filename = struct.unpack(f'{len(in_packet[26:])}s',in_packet[26:])
if packet_type.decode('utf-8') == 'R':
    with open(filename[0].decode(), 'r') as file: 
        data = file.read()
        while lastindex + paradict['packet_len'] <= len(data) or seq_packet:
            try:
                in_packet, requet_add = receive_sock.recvfrom(1024)
                #print(in_packet)
                waitforack(seq_packet, seq_timeout, seq_count, in_packet, addresstogo)
            except socket.error:
                waitforack(seq_packet, seq_timeout, seq_count, None, addresstogo)
            if len(seq_packet) == 0:
                if lastindex + paradict['packet_len'] > len(data):
                    break
                window_size = window_size_backup
            if window_size > 0 and lastindex + paradict['packet_len'] <= len(data):
                payload = data[lastindex:lastindex + paradict['packet_len']]
                #printmessage('D',requet_add, myseqnum, len(payload), payload[0:4])
                #print(round(time.time() * 1000), requet_add, myseqnum, payload[0:4])
                payload = payload.encode()
                packet = struct.pack(f'!cII{len(payload)}s', 'D'.encode(), socket.htonl(myseqnum), socket.htonl(paradict['packet_len']), payload)
                packet = struct.pack(f'!B4sH4sHI',paradict['priority'],socket.inet_aton(socket.gethostbyname(socket.gethostname())),socket.htons(paradict['receive_port']),socket.inet_aton((requet_add[0])),socket.htons(paradict['response_port']), socket.htonl(len(packet))) + packet
                #packet = struct.pack(f'!B4sH4sHI',1,socket.inet_aton(socket.gethostbyname(socket.gethostname())),socket.htons(paradict['requester_port']),socket.inet_aton(socket.gethostbyname(i[1])),socket.htons(int(i[2])),socket.htonl(len(packet))) + packet
                receive_sock.sendto(packet, addresstogo)
                transmit += 1
                
                seq_packet[myseqnum] = packet
                seq_timeout[myseqnum] = time.time() + paradict['timeout'] / 1000
                seq_count[myseqnum] = 0
                #print(window_size)
                #print(seq_packet)
                #print(seq_timeout)
                #print(seq_count)
                #print('--------------')
                # changed
                #myseqnum += paradict['packet_len']
                myseqnum += 1
                lastindex += paradict['packet_len']
                window_size -= 1
                time.sleep(1 / paradict['send_rate'])
        #print(lastindex,len(data))
        while lastindex < len(data) or seq_packet:
            try:
                in_packet, requet_add = receive_sock.recvfrom(1024)
                waitforack(seq_packet, seq_timeout, seq_count, in_packet, addresstogo)
            except socket.error:
                waitforack(seq_packet, seq_timeout, seq_count, None, addresstogo)
            if len(seq_packet) == 0:
                if lastindex > len(data):
                    break
                window_size = window_size_backup
            if window_size > 0 and lastindex < len(data):
                payload = data[lastindex:]
                #printmessage('D',requet_add, myseqnum, len(payload), payload[0:4])
                payload = payload.encode()
                packet = struct.pack(f'!cII{len(payload)}s', 'D'.encode(), socket.htonl(myseqnum), socket.htonl(len(data[lastindex:])), payload)
                packet = struct.pack(f'!B4sH4sHI',paradict['priority'],socket.inet_aton(socket.gethostbyname(socket.gethostname())),socket.htons(paradict['receive_port']),socket.inet_aton((requet_add[0])),socket.htons(paradict['response_port']), socket.htonl(len(packet))) + packet
                receive_sock.sendto(packet, addresstogo)
                transmit += 1
                seq_packet[myseqnum] = packet
                seq_timeout[myseqnum] = time.time() + paradict['timeout'] / 1000
                seq_count[myseqnum] = 0
                # changed
                #myseqnum += len(data[lastindex:])
                myseqnum += 1
                lastindex += paradict['packet_len']
                window_size -= 1
                time.sleep(1 / paradict['send_rate'])
        #print('SENDINg E Packet')
        packet = struct.pack('!cIIc', 'E'.encode(), socket.htonl(myseqnum), socket.htonl(0), 'E'.encode())
        packet = struct.pack(f'!B4sH4sHI',paradict['priority'],socket.inet_aton(socket.gethostbyname(socket.gethostname())),socket.htons(paradict['receive_port']),socket.inet_aton((requet_add[0])),socket.htons(paradict['response_port']), socket.htonl(len(packet))) + packet
        #printmessage('E',requet_add, myseqnum, 0, '')
        receive_sock.sendto(packet, addresstogo)
        print('Loss rate: ', retransmit/transmit)
                
                
