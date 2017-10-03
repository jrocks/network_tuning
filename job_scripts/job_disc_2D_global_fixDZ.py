import sys, os
sys.path.insert(0, '/data1/home/rocks/network_tuning/')
sys.path.insert(0, '/data1/home/rocks/network_tuning/python_src/')

import numpy as np
import numpy.random as rand
import numpy.linalg as la
import scipy as sp
import gzip
import cPickle as pickle
import itertools as it
import portalocker
import scipy.optimize as spo

import mech_network_solver as mns
import network as nw
import tuning_algs as talgs

def tune(NN, NTS, eta, irec, NDISC, Lp):

    # nw_label = "{}_distort_tri".format(NN)
    
    print 'NN', NN, 'NTS', NTS, 'eta', eta, 'irec', irec
    
    DIM = 2

#     length = int(np.sqrt(NN))

#     print "Length:", length
    
#     trinet = nw.create2DTriLattice(length, length, 1.0)

#     dist_net = nw.distortNetworkPos(trinet, sigma=0.1, seed=irec)
    
    # low_net = nw.lower_DZ(dist_net, 1.5, seed=irec, remove=True)
    # net = nw.lower_DZ(low_net, 1.0, seed=irec, remove=False)
    
    # net = nw.lower_DZ(dist_net, 1.0, seed=irec, remove=False, local=True)
    
    nw_label = "network_periodic_jammed/network_N{:05d}_Lp{:.2f}/network_irec{:04d}".format(NN, Lp, irec)
    
    with open("/data1/home/rocks/data/{:}.pkl".format(nw_label), 'rb') as pkl_file:

        nw_data = pickle.load(pkl_file)
        net2D = nw_data['network'] 
        
    net = nw.lower_DZ(net2D, 1.0, seed=irec, remove=False, local=True)
        
    NF = 1

    
    edgei = net.edgei
    edgej = net.edgej
    
    
    inodesi = [[] for t in range(NF)]
    inodesj = [[] for t in range(NF)]
    istrain_bonds = [[] for t in range(NF)]
    
    onodesi = [[] for t in range(NF)]
    onodesj = [[] for t in range(NF)]
    ostrain_bonds = [[] for t in range(NF)]
    
    edge_set = set()



##################################################
    
    
    edge = range(net.NE)
    
    rand.shuffle(edge)
    
    for i in range(NTS):
        b = edge.pop()
    
        onodesi[0].append(edgei[b])
        onodesj[0].append(edgej[b])
        ostrain_bonds[0].append(b)

######################################################

# ######################################################
#     gsize = int(np.ceil((NTS+1)**(1.0/DIM)))

#     print gsize



#     sites = list(rand.choice(np.arange(gsize**2), NTS+1, replace=False))

#     for i in range(NTS):

#         site = sites.pop()
#         si = site / gsize
#         sj = site % gsize

#         blist = nw.closestEdge(net, np.array([net.L[0] * si / gsize, net.L[1] * sj / gsize]))

#         for b in blist:
#             if b in edge_set:
#                 continue
#             else:
#                 edge_set.add(b)
#                 onodesi[0].append(edgei[b])
#                 onodesj[0].append(edgej[b])
#                 ostrain_bonds[0].append(b)
#                 break


# ####################################
    isvec = [[] for t in range(NF)]
    for t in range(NF):
        for (i, j) in zip(inodesi[t], inodesj[t]):
            posi = net.node_pos[DIM*i:DIM*i+DIM]
            posj = net.node_pos[DIM*j:DIM*j+DIM]
            bvec = posj - posi
            bvec -= np.round(bvec/net.L)*net.L
            isvec[t].extend(bvec) 

    istrain = [[] for t in range(NF)]
    istrain[0].append(1.0)


    osvec = [[] for t in range(NF)]
    ostrain = [[] for t in range(NF)]
    for t in range(NF):
        for (i, j) in zip(onodesi[t], onodesj[t]):
            posi = net.node_pos[DIM*i:DIM*i+DIM]
            posj = net.node_pos[DIM*j:DIM*j+DIM]
            bvec = posj - posi
            bvec -= np.round(bvec/net.L)*net.L
            osvec[t].extend(bvec) 

            # r = rand.randint(2)
            # ostrain[t].append((2*r-1) * eta)
            
            ostrain[t].append(eta)
            
            
#     theta = rand.random() * 2 * np.pi
    
#     Gamma = np.array([np.cos(2*theta), np.sin(2*theta), np.sin(2*theta), -np.cos(2*theta)])
    
    
    Gamma = np.array([1.0, 0.0, 0.0, 1.0])
    net.enableAffine()
    
    pert = []
    meas = []
    for t in range(NF):
        pert.append(talgs.Perturb())
        pert[t].setInputStrain(len(inodesi[t]), inodesi[t], inodesj[t], istrain_bonds[t], istrain[t], isvec[t])
        pert[t].setAffineStrain(True, Gamma)

        meas.append(talgs.Measure())
        meas[t].setOutputStrain(len(onodesi[t]), onodesi[t], onodesj[t], ostrain_bonds[t], osvec[t])

    obj_func = mns.CyIneqRatioChangeObjFunc(len(np.concatenate(ostrain)), net.NE, 
                                            np.zeros(len(np.concatenate(ostrain)), float), np.concatenate(ostrain))    

     
    K_disc = np.where(net.stretch_mod == 0, 0, 1)
    
    K_max = np.ones(net.NE, float) / net.eq_length
    

    tuner = talgs.TuneDiscLin(net, pert, meas, obj_func, K_max, K_disc, NDISC=NDISC, NCONVERGE=2, fix_NE=True)
    
    data = tuner.tune()

    data['network_label'] = nw_label
    data['Lp'] = Lp
    data['NN'] = net.NN
    data['NE'] = net.NE
    data['eta'] = eta
    data['irec'] = irec
    data['DZ_init'] = 2.0 * net.NE / net.NN - 2.0 * (DIM - 1.0 * DIM / net.NN)
    data['NTS'] = NTS
    data['NN_init'] = NN
    data['NDISC'] = NDISC
    
    data['istrain_nodesi'] = inodesi
    data['istrain_nodesj'] = inodesj
    data['istrain'] = istrain
    data['istrain_edges'] = istrain_bonds
    data['istrain_global'] = [Gamma]
    
    data['ostrain_nodesi'] = onodesi
    data['ostrain_nodesj'] = onodesj
    data['delta_ostrain_target'] = ostrain
    data['ostrain_edges'] = ostrain_bonds
    
    return data
    



job_list = []
    

# # NN_list = [16, 36, 64, 144, 256, 576]
# NN_list = [16, 36, 64, 100, 144, 196, 256, 400, 576, 784, 1024]
# NREC_list = np.arange(256)
# Lp_list = [-1.0]

# eta_list = {}
# for n in NN_list:
#     eta_list[n] = [1e-1]


# NTS_list = {16:2**np.arange(1, 5),
#            36:2**np.arange(2, 6),
#            64:2**np.arange(3, 6),
#            100:2**np.arange(3, 7),
#            144:2**np.arange(3, 7),
#            196:2**np.arange(4, 7),
#            256:2**np.arange(4, 8),
#            400:2**np.arange(5, 8),
#            576:2**np.arange(5, 8),
#            784:2**np.arange(6, 9),
#            1024:2**np.arange(6, 9),
#            1600:2**np.arange(0, 8),
#            2304:2**np.arange(0, 8),
#            3136:2**np.arange(0, 8),
#            4096:2**np.arange(0, 8)}

# NDIV = 3
# for NN in NN_list:
#     tmp1 = []
#     tmp2 = np.copy(NTS_list[NN])
#     for i in range(NDIV):
#         tmp1 = np.copy(tmp2)
#         tmp2 = []
#         for i in range(len(tmp1)-1):
#             tmp2.append(tmp1[i])
#             if tmp1[i+1] > tmp1[i] + 1:
#                 tmp2.append((tmp1[i+1] + tmp1[i]) / 2)
#         tmp2.append(tmp1[-1])
#     NTS_list[NN] = tmp2

# for NN in NN_list:
#     job_list.extend(list(it.product([NN], NREC_list, NTS_list[NN], eta_list[NN], Lp_list)))
    
# # ################################################          
    
         
# # 4^2 6^2 8^2 10^2 12^2 14^2 16^2 20^2 24^2 28^2 32^2 40^2 48^2 56^2 64^2
# # NN_list = [16, 36, 64, 144, 256, 576, 1024, 2304, 4096]
# NN_list = [16, 36, 64, 100, 144, 196, 256, 400, 576, 784, 1024]
# NREC_list = np.arange(32)
# Lp_list = [-1.0]

# eta_list = {}
# for n in NN_list:
#     eta_list[n] = [1e-1]


# NTS_list = {16:2**np.arange(0, 5),
#            36:2**np.arange(0, 6),
#            64:2**np.arange(0, 6),
#            100:2**np.arange(0, 7),
#            144:2**np.arange(0, 7),
#            196:2**np.arange(0, 7),
#            256:2**np.arange(0, 8),
#            400:2**np.arange(0, 8),
#            576:2**np.arange(0, 8),
#            784:2**np.arange(0, 9),
#            1024:2**np.arange(0, 9),
#            1600:2**np.arange(0, 8),
#            2304:2**np.arange(0, 8),
#            3136:2**np.arange(0, 8),
#            4096:2**np.arange(0, 8)}

# NDIV = 0
# for NN in NN_list:
#     tmp1 = []
#     tmp2 = np.copy(NTS_list[NN])
#     for i in range(NDIV):
#         tmp1 = np.copy(tmp2)
#         tmp2 = []
#         for i in range(len(tmp1)-1):
#             tmp2.append(tmp1[i])
#             if tmp1[i+1] > tmp1[i] + 1:
#                 tmp2.append((tmp1[i+1] + tmp1[i]) / 2)
#         tmp2.append(tmp1[-1])
#     NTS_list[NN] = tmp2

# for NN in NN_list:
#     job_list.extend(list(it.product([NN], NREC_list, NTS_list[NN], eta_list[NN], Lp_list)))
    

    
# NN_list = [8, 16, 32, 64, 128, 256, 512, 1024, 2048]
# NREC_list = np.arange(32)
# Lp_list = [-1.0]

# eta_list = {}
# for n in NN_list:
#     eta_list[n] = [1e-1]

    

# NTS_list = {8:2**np.arange(0, 5),
#            16:2**np.arange(1, 5),
#            32:2**np.arange(1, 5),
#            64:2**np.arange(2, 6),
#            128:2**np.arange(3, 7),
#            256:2**np.arange(4, 7),
#            512:2**np.arange(4, 8),
#            1024:2**np.arange(6, 9),
#            2048:2**np.arange(7, 10),
#            4096:2**np.arange(7, 10)}

# NDIV = 3
# for NN in NN_list:
#     tmp1 = []
#     tmp2 = np.copy(NTS_list[NN])
#     for i in range(NDIV):
#         tmp1 = np.copy(tmp2)
#         tmp2 = []
#         for i in range(len(tmp1)-1):
#             tmp2.append(tmp1[i])
#             if tmp1[i+1] > tmp1[i] + 1:
#                 tmp2.append((tmp1[i+1] + tmp1[i]) / 2)
#         tmp2.append(tmp1[-1])
#     NTS_list[NN] = tmp2

# for NN in NN_list:
#     job_list.extend(list(it.product([NN], NREC_list, NTS_list[NN], eta_list[NN], Lp_list)))
    

###################################################################
             
    
NN_list = [4096]
NREC_list = np.arange(32)
Lp_list = [-1.0]

eta_list = {}
for n in NN_list:
    eta_list[n] = [1e-1]

    

NTS_list = {8:2**np.arange(0, 5),
           16:2**np.arange(0, 5),
           32:2**np.arange(0, 5),
           64:2**np.arange(0, 6),
           128:2**np.arange(0, 7),
           256:2**np.arange(0, 7),
           512:2**np.arange(0, 8),
           1024:2**np.arange(0, 9),
           2048:2**np.arange(0, 10),
           4096:2**np.arange(7, 10)}

NDIV = 3
for NN in NN_list:
    tmp1 = []
    tmp2 = np.copy(NTS_list[NN])
    for i in range(NDIV):
        tmp1 = np.copy(tmp2)
        tmp2 = []
        for i in range(len(tmp1)-1):
            tmp2.append(tmp1[i])
            if tmp1[i+1] > tmp1[i] + 1:
                tmp2.append((tmp1[i+1] + tmp1[i]) / 2)
        tmp2.append(tmp1[-1])
    NTS_list[NN] = tmp2

for NN in NN_list:
    job_list.extend(list(it.product([NN], NREC_list, NTS_list[NN], eta_list[NN], Lp_list)))
    
    
# rand.shuffle(job_list)

    
N_jobs =  len(job_list)
print "Total Number of Jobs:", N_jobs

batch_tot = int(sys.argv[1])

print "Total Number of Batches", batch_tot

batch_size = int(np.ceil(1.0 * N_jobs / batch_tot))

print "Max Batch size:", batch_size

batch_num = int(sys.argv[2])

print "Batch Number:", batch_num

jobs = job_list[batch_size*batch_num: min(batch_size*(batch_num+1), N_jobs)]

print jobs

for (NN, irec, NTS, eta, Lp) in jobs:


    print NN, irec, NTS, eta, Lp

    DZ = 1.0e-1
    NDISC = 1

    directory = "/data1/home/rocks/data/sat_transition/tune_disc_2D_global_fixDZ_1/"

    fn = "N{:05d}_Lp{:.2f}_NTS{:06d}_eta{:.8f}_NDISC{:04d}_irec{:04d}.pkl".format(NN, Lp, NTS, eta, NDISC, irec)

    if os.path.exists(directory+"file_list.pkl"):
        with open(directory+"file_list.pkl", 'rb') as pkl_file:
            portalocker.lock(pkl_file, portalocker.LOCK_SH)
            if fn in pickle.load(pkl_file)['files']:
                print "File already exists"
                pkl_file.close()
                continue
            pkl_file.close()


    def cantor(k1, k2):
        return (k1 + k2) * (k1 + k2 + 1) / 2 + k2

    rand.seed(cantor(cantor(cantor(int(np.log2(NN)) % 100, NTS % 100), int(np.floor(100*np.abs(np.log10(np.abs(eta)))))  ), irec) % 4294967295)

    data = tune(NN, NTS, eta, irec, NDISC, Lp)

    print data

    with open(directory+fn, 'wb') as output:
        portalocker.lock(output, portalocker.LOCK_SH)
        pickler = pickle.Pickler(output, -1)

        pickler.dump(data)
