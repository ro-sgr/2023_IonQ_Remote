teamname = 'InstaQu'
task = 'part 1'

import qiskit
from qiskit import quantum_info
from qiskit.execute_function import execute
from qiskit import BasicAer
import numpy as np
import pickle
import json
import os
import sys
from collections import Counter
from sklearn.metrics import mean_squared_error
from typing import Dict, List
import matplotlib.pyplot as plt

if len(sys.argv) > 1:
    data_path = sys.argv[1]
else:
    data_path = '.'

#define utility functions

def simulate(circuit: qiskit.QuantumCircuit) -> dict:
    """Simulate the circuit, give the state vector as the result."""
    backend = BasicAer.get_backend('statevector_simulator')
    job = execute(circuit, backend)
    result = job.result()
    state_vector = result.get_statevector()
    
    histogram = dict()
    for i in range(len(state_vector)):
        population = abs(state_vector[i]) ** 2
        if population > 1e-9:
            histogram[i] = population
    
    return histogram


def histogram_to_category(histogram):
    """This function takes a histogram representation of circuit execution results, and processes into labels as described in
    the problem description."""
    assert abs(sum(histogram.values())-1)<1e-8
    positive=0
    for key in histogram.keys():
        digits = bin(int(key))[2:].zfill(20)
        if digits[-1]=='0':
            positive+=histogram[key]
        
    return positive

def count_gates(circuit: qiskit.QuantumCircuit) -> Dict[int, int]:
    """Returns the number of gate operations with each number of qubits."""
    counter = Counter([len(gate[1]) for gate in circuit.data])
    #feel free to comment out the following two lines. But make sure you don't have k-qubit gates in your circuit
    #for k>2
    for i in range(2,20):
        assert counter[i]==0
        
    return counter


def image_mse(image1,image2):
    # Using sklearns mean squared error:
    # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_squared_error.html
    return mean_squared_error(255*image1,255*image2)

################################
#load the actual hackthon data (fashion-mnist)
images=np.load(data_path+'/images.npy')
labels=np.load(data_path+'/labels.npy')
################################

def test():
    n=len(images)
    mse=0
    gatecount=0

    for image in images:
        #encode image into circuit
        circuit,image_re=run_part1(image)
        image_re = np.asarray(image_re)

        #count the number of 2qubit gates used
        gatecount+=count_gates(circuit)[2]

        #calculate mse
        mse+=image_mse(image,image_re)

    #fidelity of reconstruction
    f=1-mse/n
    gatecount=gatecount/n

    #score for part1
    score_part1=f*(0.999**gatecount)
    
    #test part 2
    
    score=0
    gatecount=0
    n=len(images)

    for i in range(n):
        #run part 2
        circuit,label=run_part2(images[i])

        #count the gate used in the circuit for score calculation
        gatecount+=count_gates(circuit)[2]

        #check label
        if label==labels[i]:
            score+=1
    #score
    score=score/n
    gatecount=gatecount/n

    score_part2=score*(0.999**gatecount)
    
    print(score_part1, ",", score_part2 ",", data_path, sep="")


############################
#      YOUR CODE HERE      #
############################

def iterate_regions(image):
    '''
    Takes in the 2d array of pixel activations and returns the generate non-overlapping 2x2 image regions to pool over.
    (uses stride = 2)
    '''
    h, w = image.shape
    h_n = h // 2
    w_n = w // 2

    for i in range(h_n):
        for j in range(w_n):
            im_region = image[(i * 2):(i * 2 + 2), (j * 2):(j * 2 + 2)]
            yield im_region, i, j
            

def max_pool(in_):
    '''
    Performs a forward pass of the maxpool layer using the given input image and returns a 2d numpy array with dimensions 
    (h / 2, w / 2). This is possible on using a maxpool kernel with filter size = 2 and stride = 2. This will be implemented 
    with the help of iterate_regions function.
    '''
    last_input = in_

    h, w = in_.shape
    output = np.zeros((h // 2, w // 2))

    for im_region, i, j in iterate_regions(in_):
        output[i, j] = np.amax(im_region, axis=(0, 1))

    return output


def encode(image):
    image = max_pool(image) # dimension reduction
    q = qiskit.QuantumRegister(len(image))
    circuit = qiskit.QuantumCircuit(q)
    
    for y in range(len(image)):
        for x in range(len(image[y])):
            if image[y][x] != 0:
                circuit.rx(np.pi,y)
                
    return circuit


temp = dict()
for i in range(len(images)):
    image_temp = images[i]
    circuit_temp = encode(image_temp)
    histogram_temp = simulate(circuit_temp)
    temp[list(histogram_temp.keys())[0]] = image_temp

def image_dict(number):
    return temp[number]


def decode(histogram):
    for i in range(int(2**14)):
        if i in histogram.keys():
            image = image_dict(i)
            break
    return image

def run_part1(image):
    #encode image into a circuit
    circuit=encode(image)

    #simulate circuit
    histogram=simulate(circuit)

    #reconstruct the image
    image_re=decode(histogram)

    return circuit,image_re

def run_part2(image):
    # load the quantum classifier circuit
    classifier = q_classifier(image)
    
    #encode image into circuit
    circuit=encode(image)
    
    #append with classifier circuit
    nq1 = circuit.width()
    nq2 = classifier.width()
    nq = max(nq1, nq2)
    qc = qiskit.QuantumCircuit(nq)
    qc.append(circuit.to_instruction(), list(range(nq1)))
    qc.append(classifier.to_instruction(), list(range(nq2)))
    
    #simulate circuit
    histogram=simulate(qc)
        
    #convert histogram to category
    label=histogram_to_category(histogram)
    
    #thresholding the label, any way you want
    if label>0.5:
        label=1
    else:
        label=0
        
    return circuit,label

############################
#      END YOUR CODE       #
############################

test()
