import pyedflib
import os
import numpy as np
import glob

root_data_dir = '/home/mdani31/akata-shared/datasets/USDet'

#read all .edf files in the directory and print annotations
search_dir = root_data_dir + '/**/*.edf'
for file in glob.glob(search_dir, recursive=True):
    print(file)
    f = pyedflib.EdfReader(file)
    ann = f.readAnnotations()
    print(ann)
    f._close()