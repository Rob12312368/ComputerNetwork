import struct
import socket
def readtopo(fname):
    topo = {}
    ip_ports = {}
    with open(fname, 'r') as f:
        for line in f:
            tmp = line.strip().split(' ')
            tmp = list(map(lambda x:(x.split(',')[0], int(x.split(',')[1])), tmp))
            #tmp = [(i[0], int(i[1])) for i in tmp]
            #print(tmp[1:])
            topo[tmp[0]] = tmp[1:] # topo[tmp[0]] = tmp[1:] to make key with port
            ip_ports[tmp[0][0]] = tmp[0][1]
    return [topo, ip_ports]
def printdict(dic):
    for i, v in dic.items():
        print(i, v)
def buildfwtable(topo, cur_addr):
    # confirmed and tentative
    forward = {'conf':{}, 'tent':{}}
    forward['conf'][cur_addr] = [cur_addr, 0, None] # [dest, cost, nexthop]
    
    # put things into tentative
    for nei_addr in topo[cur_addr]:
        forward['tent'][nei_addr] = [nei_addr, 1, nei_addr]
    print(forward)
    #print('forward:',forward)
    while len(forward['tent']) > 0:
        nearest = min(forward['tent'].values(), key=lambda x:x[1])
        #print(nearest)
        nei_addr = nearest[0] # the new element added in to confirmed
        forward['conf'][nei_addr] = nearest
        forward['tent'].pop(nei_addr)
        print(forward)
        # update cost and next hop (there may be a shorter path)
        for i in forward['tent'].values():
            dest,cost,nexthop = i[0], i[1], i[2]
            #print([j[0] for j in topo[nei_ip]])
            if dest in topo[nei_addr]:
                if cost > nearest[1]+1:
                    i[1] = nearest[1] + 1
                    i[2] = nearest[2]

        # add more node into tentative
        for addr in topo[nei_addr]:
            if addr not in forward['conf'].keys() and addr not in forward['tent'].keys():
                print()
                forward['tent'][addr] = [addr, nearest[1]+1, forward['conf'][nei_addr][2]]

    # make it the specified format

    return forward['conf']

sample = struct.pack('!c4sI', 'L'.encode('utf-8'), 'asdf'.encode('utf-8'), socket.htonl(5))
sample2 = struct.pack('!B4s', 1, 'abcd'.encode('utf-8'))

#print(sample[0])
topo, ip_ports = readtopo('topology.txt')
print(topo)
printdict(buildfwtable(topo, ('127.0.1.1', 8000)))
a = struct.pack(f'!c4sHII{5}s','A'.encode(),socket.inet_aton('192.168.0.0'),socket.htons(8),socket.htonl(10),socket.htonl(10),'aaaaa'.encode())
#_,_,_,_,_,b = struct.unpack(f'!c4sHII{5}s',a[15:])
mylen = len(a[15:])
b = struct.unpack(f'!{mylen}s',a[15:])


a = 5
c = [a]
a = 10
print('C',c)


a = (1,2)

#print(socket.gethostbyname(socket.gethostname()))