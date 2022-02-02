import os
import sys
import glob
import multiprocessing
import json
import argparse

from tqdm import tqdm
import pandas as pd
import numpy as np

import ply_io
import pdal

def tile_index(riproject):

    tile_index = pd.DataFrame(columns=['tile', 'x', 'y'])
    F = glob.glob(os.path.join(riproject, '*.ply')) + glob.glob(os.path.join(riproject, '*.pcd'))


    for i, ply in tqdm(enumerate(F), total=len(F)):
        T = int(os.path.split(ply)[1].split('.')[0])
        reader = {"type":f"readers{os.path.splitext(ply)[1]}",
                  "filename":ply}
        stats =  {"type":"filters.stats",
                  "dimensions":"X,Y"}
        JSON = json.dumps([reader, stats])
        pipeline = pdal.Pipeline(JSON)
        pipeline.execute()
        JSON = json.loads(pipeline.metadata)
        X = JSON['metadata']['filters.stats']['statistic'][0]['average']
        Y = JSON['metadata']['filters.stats']['statistic'][1]['average']
        tile_index.loc[i, :] = [T, X, Y]   

    tile_index.to_csv('tile_index.dat', index=False, header=False, sep=' ')

if __name__ == '__main__':
    tile_index(sys.argv[1])
