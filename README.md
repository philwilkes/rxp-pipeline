# rxp-pipeline

How we process registered .rxp data to allow us to process further. This process uses PDAL and requires installation of the Python bindings.

### File structure

File structure should be as below where `ScanPos001`, `ScanPos002`, ... `ScanPosXXX` are the raw date from the scanner and matrix are derived RiSCAN Pro. Anything in extraction is _temporary_ and could be deleted i.e. don't put anything in there that needs to be kept. `clouds` are the individually extracted trees, these can be either leaf-on or -off, conventaional naming is `<plot>_<year>_T<num>.ply` where `<num>` can be random or a tree tag (maybe need a different suffix to decipher this). `models` contain output from TreeQSM or treegraph, if there are both then put in separate directories.

```
20XX-XX-08.XXX.riproject
  ├── ScanPos001
  ├── ScanPos002
  ├── ScanPosXXX
  ├── matrix
  |   ├── ScanPos001.DAT
  |   ├── ScanPos002.DAT
  |   └── ScanPosXXX.DAT
  ├── extraction
  |   ├── rxp2ply
  |   |   └── <tiles created by rxp2ply.py
  |   ├── downsample
  |   |   └── <tiles created by downsample.py
  |   ├── fsct
  |   |   └── output from FSCT
  |   └── tile_index.dat
  ├── clouds
  |   └── <trees extracted with FSCT or other>
  └── models
      └── <QSMs from either TreeQSM or treegraph>
```
### Compiling PDAL with python bindings and .rxp support

_Before installing PDAL you could instead:_ `conda activate /home/ucfaptv/opt/miniconda/envs/pdal-python`

1.  Create a conda environment using `conda create -n pdal -c conda-forge gdal ninja cmake cxx-compiler laszip pdal python-pdal`
    
2.  Download the [PDAL current release](https://pdal.io/download.html#current-release-s) 

3.  Download the `rivlib-2_5_10-x86_64-linux-gcc9.zip` from the memebers area of the RIEGL website (make sure to get the gcc9 version). Unzip and add an environmental variable to point at the directory `export RiVLib_DIR=/path/to/rivlib-2_5_10-x86_64-linux-gcc9`

4.  Follow the [PDAL Unix Compilation](https://pdal.io/development/compilation/unix.html) notes. Before running cmake
    - edit line 63 of `cmake/options.cmake` to `"Choose if RiVLib support should be built" True)`
    - edit line 56 of `plugins/rxp/io/RxpReader.hpp` to `const bool DEFAULT_SYNC_TO_PPS = false;`

5. Copy `build/lib/libpdal_plugin_reader_rxp.so` to `/path/to/.conda/envs/pdal/lib/.`, this is required to open .rxp in Python.

### Processing data

`conda activate pdal`

Create a direcotry in the the `.riproject` directory called `extraction` using `mkdir`, navigate into it and create a directoty called `rxp2ply` and navigate into this.  

#### 1. rxp2ply.py 

Run `python rxp2ply.py --project /path/to/.riproject --length 10 --deviation 15 --odir . --verbose`

This will populate the `rxp2ply` directory with full resolution tiled data

#### 2. downsample.py

This downsamples the data to a uniform density

`mkdir ../downsample` and navigate to `cd ../downsample`

`python ~/opt/pdal/downsample.py -i ../rxp2ply/ --length .02 --verbose `

#### 3. tile_index.py

Navigate back to `extraction`

`python ~/opt/pdal/tile_index.py downsample` where `downsample` is the directory with downsampled tiles.

#### 4. Run FSCT

Instrcutions on this are [here](https://github.com/philwilkes/FSCT).
