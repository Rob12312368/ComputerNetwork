
# ('1.0.0.0', '1'): [('2.0.0.0', '2'), ('3.0.0.0', '3')]
def readtopo(fname):
    topo = {}
    with open(fname, 'r') as f:
        for line in f:
            tmp = line.strip().split(' ')
            print(tmp)
            tmp = list(map(lambda x:tuple(x.split(',')), tmp))
            topo[tmp[0][0]] = tmp[1:] # topo[tmp[0]] = tmp[1:] to make key with port
    return topo


    

        


topo = readtopo('topology.txt')
print(topo)