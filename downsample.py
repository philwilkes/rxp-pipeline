#!/usr/bin/env python

import pandas as pd
import os, glob
import multiprocessing
import argparse
import json
import pdal

def downsample(ply, args):
    
    if args.verbose:
        with args.Lock:
            print('downsampling:', ply)

    reader = {"type":"readers.ply",
              "filename":ply}
    
    downsample = {"type":"filters.voxelcenternearestneighbor",
                  "cell":f"{args.length}"}
    
    writer = {'type':'writers.ply',
              'storage_mode':'little endian',
              'filename':os.path.join(args.odir, os.path.split(ply)[1].replace('.ply', '.downsample.ply'))}
            
    cmd = json.dumps([reader, downsample, writer])
    pipeline = pdal.Pipeline(cmd)
    pipeline.execute()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--idir', type=str, help='directory where downsampled tiles are stored')
    parser.add_argument('-o','--odir', default='.', help='directory where downsampled tiles are stored')
    parser.add_argument('-l', '--length', type=float, default=.02, help='voxel edge length')
    parser.add_argument('--num-prcs', type=int, default=10, help='number of cores to use')
    parser.add_argument('--verbose', action='store_true', help='print something')
    args = parser.parse_args()
    
    m = multiprocessing.Manager()
    args.Lock = m.Lock()
    pool = multiprocessing.Pool(args.num_prcs)
    pool.starmap_async(downsample, [(ply, args) for ply in glob.glob(os.path.join(args.idir, '*.ply'))])
    pool.close()
    pool.join() 

