import os
import glob
import multiprocessing
import json
import argparse

import pandas as pd
import numpy as np

import ply_io
import pdal

def tile_data(scan_pos, args):

#    try:    
        base, scan = os.path.split(scan_pos)
        try:
            if args.test:
                print(os.path.join(base, scan, '??????_??????.mon.rxp'))
                rxp = glob.glob(os.path.join(base, scan, '??????_??????.mon.rxp'))[0]
            else:
                rxp = glob.glob(os.path.join(base, scan, '??????_??????.rxp'))[0]
        except:
            if args.verbose: print(f"!!! Can't find {os.path.join(base, scan, '??????_??????.rxp')} !!!")
            return
        sp = int(scan.replace(args.prefix, '').replace('.SCNPOS', ''))
    
        if args.verbose:
            with args.Lock:
                print('rxp -> xyz:', rxp)
    
        fn_matrix = glob.glob(os.path.join(base, 'matrix', f'{scan.replace(".SCNPOS", "")}.*'))[0]
        matrix = np.loadtxt(fn_matrix)
        st_matrix = ' '.join(matrix.flatten().astype(str))
    
        # pdal commands as dictionaries
        read_in = {"type":"readers.rxp",
                   "filename": rxp,
                   "sync_to_pps": "false",
                   "reflectance_as_intensity": "false"}
    
        dev_filter = {"type":"filters.range", 
                      "limits":"Deviation[0:{}]".format(args.deviation)}
    
        refl_filter = {"type":"filters.range", 
                      "limits":"Reflectance[{}:{}]".format(*args.reflectance)}
    
        transform = {"type":"filters.transformation",
                     "matrix":st_matrix}
    
        tile = {"type":"filters.splitter",
                "length":f"{args.tile}",
                "origin_x":"0",
                "origin_y":"0"}

        # link commmands and pass to pdal
        cmds = [read_in, dev_filter, refl_filter, transform, tile]
        JSON = json.dumps(cmds)
        pipeline = pdal.Pipeline(JSON)
        pipeline.execute()
    
        # iterate over tiled arrays
        for arr in pipeline.arrays:
    
            arr = pd.DataFrame(arr)
            arr.columns = ['x', 'y', 'z', 'InternalTime', 'ReturnNumber', 'NumberOfReturns',
                           'amp', 'refl', 'EchoRange', 'dev', 'BackgroundRadiation', 
                           'IsPpsLocked', 'EdgeOfFlightLine']
            arr.loc[:, 'sp'] = sp
            arr = arr[['x', 'y', 'z', 'refl', 'dev', 'ReturnNumber', 'NumberOfReturns', 'sp']] # save only relevant fields
    
            # remove points outside bbox
            arr = arr.loc[(arr.x.between(args.bbox[0], args.bbox[1])) & 
                          (arr.y.between(args.bbox[2], args.bbox[3]))]
            if len(arr) == 0: continue
    
            # identify tile number
            X, Y = (arr[['x', 'y']].min() // args.tile * args.tile).astype(int)
            tile = args.tiles.loc[(args.tiles.x == X) & (args.tiles.y == Y)] 
    
            # save to xyz file
            with args.Lock:
                with open(os.path.join(args.odir, f'{args.plot_code}{tile.tile.item():03}.xyz'), 'ab') as fh: 
                    fh.write(arr.to_records(index=False).tobytes()) 
#    except:
#        print('!!!!', scan_pos, '!!!!') 
    
def xyz2ply(xyz_path, args):

    if args.verbose:
        with args.Lock:
            print('xyz -> ply:', xyz_path)
    
    open_file = open(xyz_path, encoding='ISO-8859-1')
    tmp = pd.DataFrame(np.fromfile(open_file, dtype='float64,float64,float64,float32,float32,uint8,uint8,int64'))
    tmp.columns = ['x', 'y', 'z', 'refl', 'dev', 'ReturnNumber', 'NumberOfReturns', 'sp']
    ply_io.write_ply(xyz_path.replace('.xyz', '.ply'), tmp)
    os.unlink(xyz_path)
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--project', '-p', required=True, type=str, help='path to point cloud')
    parser.add_argument('--plot-code', type=str, default='', help='plot suffix')
    parser.add_argument('--odir', type=str, default='.', help='output directory')
    parser.add_argument('--deviation', type=float, default=15, help='deviation filter')
    parser.add_argument('--reflectance', type=float, nargs=2, default=[-999, 999], help='reflectance filter')
    parser.add_argument('--tile', type=float, default=10, help='length of tile')
    parser.add_argument('--num-prcs', type=int, default=10, help='number of cores to use')
    parser.add_argument('--prefix', type=str, default='ScanPos', help='file name prefix, deafult:ScanPos')
    parser.add_argument('--bbox', type=int, nargs=4, default=[], help='file name prefix, deafult:ScanPos')
    parser.add_argument('--pos', default=[], nargs='*', help='process using specific scan positions')
    parser.add_argument('--test', action='store_true', help='test using the .mon.rxp')
    parser.add_argument('--verbose', action='store_true', help='print something')

    args = parser.parse_args()

    args.matrix_dir = os.path.join(args.project, 'matrix')
    if not os.path.isdir(args.matrix_dir): raise Exception(f'no such directory: {args.matrix_dir}')
    args.ScanPos = sorted(glob.glob(os.path.join(args.project, f'{args.prefix}*')))
    if args.plot_code != '': args.plot_code += '_'

    # generate bounding box from matrix
    M = glob.glob(os.path.join(args.matrix_dir, f'{args.prefix}*.*'))
    matrix_arr = np.zeros((len(M), 3))
    for i, m in enumerate(M):
        matrix_arr[i, :] = np.loadtxt(m)[:3, 3]

    # bbox [xmin, xmax, ymin, ymax]
    if len(args.bbox) == 0:
        args.bbox = np.array([matrix_arr.min(axis=0)[:2] - args.tile,
                              matrix_arr.max(axis=0)[:2] + (args.tile * 2)]).T.flatten() // args.tile * args.tile
    if args.verbose: print('bounding box:', args.bbox)

    # create tile db
    X, Y = np.meshgrid(np.arange(args.bbox[0], args.bbox[1] + args.tile, args.tile),
                       np.arange(args.bbox[2], args.bbox[3] + args.tile, args.tile))
    args.tiles = pd.DataFrame(data=np.vstack([X.flatten(), Y.flatten()]).T.astype(int), columns=['x', 'y'])
    #args.tiles.loc[:, 'tile'] = [os.path.abspath(os.path.join(args.rxp2ply_dir, f'{t:03}.ply')) for t in range(len(args.tiles))]
    #args.tiles.loc[:, 'tile'] = [f'{n:03}' for n in range(len(args.tiles))]
    args.tiles.loc[:, 'tile'] = range(len(args.tiles))

    if len(args.pos) > 0:
        if args.verbose: print('processing only:', args.pos)
        args.ScanPos = [os.path.join(args.project, p) for p in args.pos]

    # read in and tile scans
    Pool = multiprocessing.Pool(args.num_prcs)
    m = multiprocessing.Manager()
    args.Lock = m.Lock()
    Pool.starmap(tile_data, [(sp, args) for sp in np.sort(args.ScanPos)])

    # write to ply - reusing Pool
    xyz = glob.glob(os.path.join(args.odir, '*.xyz'))
    Pool.starmap_async(xyz2ply, [(xyz, args) for xyz in np.sort(xyz)])
    Pool.close()
    Pool.join()

    # write tile index
    #args.tiles[['tile', 'x', 'y']].to_csv(os.path.join(args.odir, 'tile_index.dat'), 
    #                                      sep=' ', index=False, header=False)
