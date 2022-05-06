# rxp-pipeline

Methods used by UCL Geography to preprocess registered .rxp data to allow further processing. The pipeline uses PDAL and requires installation of the Python bindings.

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

1.  Create a conda environment using `conda create -n pdal -c conda-forge gdal ninja cmake cxx-compiler laszip pdal python-pdal pandas`
    
2.  Download the [PDAL current release](https://pdal.io/download.html#current-release-s).
    
    Example commands in linux:
    
    
        $ wget https://github.com/PDAL/PDAL/releases/download/2.3.0/PDAL-2.3.0-src.tar.gz
        $ tar -xf PDAL-2.3.0-src.tar.gz
        

3.  Download the `rivlib-2_5_10-x86_64-linux-gcc9.zip` from the memebers area of the RIEGL website (make sure to get the gcc9 version). Unzip and add an environmental variable to point at the directory `export RiVLib_DIR=/path/to/rivlib-2_5_10-x86_64-linux-gcc9`

4.  Before running cmake
    - edit line 63 of `cmake/options.cmake` to `"Choose if RiVLib support should be built" True)`
    - edit line 56 of `plugins/rxp/io/RxpReader.hpp` to `const bool DEFAULT_SYNC_TO_PPS = false;`

    Then, follow the [PDAL Unix Compilation](https://pdal.io/development/compilation/unix.html) notes to compile PDAL. Example commands in Linux:
       
        $ cd /path/to/PDAL-2.3.0-src
        $ mkdir build
        $ cd build
        $ cmake -G Ninja ..
        $ ninja
        $ ls bin/pdal
        bin/pdal
        
    Next, add the this bin path to the environmental variable $PATH `export PATH=/path/to/PDAL-2.3.0-src/build/bin:$PATH`

5. Copy `build/lib/libpdal_plugin_reader_rxp.so` to `/path/to/.conda/envs/pdal/lib/.`, this is required to open .rxp in Python.

### Processing data

`conda activate pdal`

Create a direcotry in the the `.riproject` directory called `extraction` using `mkdir`, navigate into it and create a directoty called `rxp2ply` and navigate into this.  

#### 0. Download the python scripts from github
`$ git clone https://github.com/philwilkes/rxp-pipeline.git`

#### 1. rxp2ply.py 

Navigate to `cd /path/to/xx.riporject/extraction/rxp2ply/`
Run `python /path/to/rxp-pipeline/rxp2ply.py --project ../../../xx.riproject --deviation 15 --odir . --verbose`

This will populate the `rxp2ply` directory with full resolution tiled data

#### 2. downsample.py

This downsamples the data to a uniform density

`mkdir ../downsample` and navigate to `cd ../downsample`

`python /path/to/rxp-pipeline/downsample.py -i ../rxp2ply/ --length .02 --verbose `

#### 3. tile_index.py

Navigate back to `extraction`

`python /path/to/rxp-pipeline/tile_index.py downsample` where `downsample` is the directory with downsampled tiles.

#### 4. Run FSCT

Instructions on this are [here](https://github.com/philwilkes/FSCT).
