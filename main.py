import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import joblib
import math
import shutil
from osgeo import gdal, osr, ogr

from functions import array2raster, chla, turbidity, clipRaster, sd

np.errstate(invalid='ignore', divide='ignore')

gdal.UseExceptions()

shapePath = None
shouldClip = False
_input = None
statistics = False
chla_rasters = []
amountOfScenes, currentScene = 0, 1

# number of arguments passed with script call
arguments = sys.argv

# loop over input arguments and find input and output, skip first argument (main.py)
for arg in arguments[1:]:
    if "in=" in arg:
        _input = arg[3:]
    if "shape=" in arg:
        shouldClip = True
        shapePath = arg[6:]
    if "statistics" in arg:
        statistics = True


# check invalid input
if _input is None:
    print("Please enter input path to your data")


dir_names = os.listdir(_input)

for scenes in dir_names:
    if "S2A" in scenes:
        amountOfScenes = amountOfScenes + 1
    elif "S2B" in scenes:
        amountOfScenes = amountOfScenes + 1

# loop over bands
if _input is not None:
    print(f'Found {amountOfScenes} Sentinel-2 scenes', flush=True)

    # check if processed folder already exists
    if not os.path.exists(_input + "\processed"):
        # create new folder
        os.makedirs(_input + "\processed")

    for folder in dir_names:
        # skip if processed folder exists, otherwise loop would break
        if folder == "processed":
            continue

        if folder == "temp":
            continue

        print(f'{currentScene}/{amountOfScenes}', flush=True)

        # move to processed directory
        joined_path = os.path.join(_input, folder + "\GRANULE")

        joined_path = os.path.join(
            joined_path, os.listdir(joined_path)[0] + "\IMG_DATA\R20m")

        os.chdir(joined_path)

        # get date
        date = os.listdir(joined_path)[1][7:15]
        year = date[:4]
        month = date[4:6]
        day = date[6:8]
        date = f'{day}.{month}.{year}'

        # create folder for specific year
        # check if folder already exists
        if not os.path.exists(_input + f'\processed\/{date}'):
            # create new folder
            os.makedirs(_input + f'\processed\/{date}')

        for band in os.listdir(joined_path):
            if "B02" in band:
                B2 = gdal.Open(band)
            if "B03" in band:
                B3 = gdal.Open(band)
            if "B04" in band:
                B4 = gdal.Open(band)
            if "B05" in band:
                B5 = gdal.Open(band)
            if "B06" in band:
                B6 = gdal.Open(band)
            if "B07" in band:
                B7 = gdal.Open(band)
            if "B8A" in band:
                B8a = gdal.Open(band)
            if "B11" in band:
                B11 = gdal.Open(band)
            if "B12" in band:
                B12 = gdal.Open(band)

        # .astype(np.float) not needed -> same results
        B2_array = B2.ReadAsArray()
        B3_array = B3.ReadAsArray()
        B4_array = B4.ReadAsArray()
        B5_array = B5.ReadAsArray()
        B6_array = B6.ReadAsArray()
        B7_array = B7.ReadAsArray()
        B8a_array = B8a.ReadAsArray()
        B11_array = B11.ReadAsArray()
        B12_array = B12.ReadAsArray()

        # clip each raster with polygon
        if shouldClip:
            B2_array = clipRaster(B2, shapePath)
            B3_array = clipRaster(B3, shapePath)
            B4_array = clipRaster(B4, shapePath)
            B5_array = clipRaster(B5, shapePath)
            B6_array = clipRaster(B6, shapePath)
            B7_array = clipRaster(B7, shapePath)
            B8a_array = clipRaster(B8a, shapePath)
            B11_array = clipRaster(B11, shapePath)
            B12_array = clipRaster(B12, shapePath)

        # chlorophyll a
        chla_calc = chla(B4_array, B5_array)
        chla_rasters.append(chla_calc)
        newImage = _input + f"\processed\_chla_{date}.tif"
        array2raster(os.listdir(joined_path)[0], newImage, chla_calc)

        # turbidity
        tt_calc = turbidity(B3_array, B4_array)
        newImage_2 = _input + f"\processed\_turbidity_{date}.tif"
        array2raster(os.listdir(joined_path)[0], newImage_2, tt_calc)

        # turbidity
        sd_calc = sd(B2_array, B3_array)
        newImage_2 = _input + f"\processed\_sd_{date}.tif"
        array2raster(os.listdir(joined_path)[0], newImage_2, sd_calc)

        # mci
        # mci_calc = mci(B4_array, B5_array, B6_array)
        # newImage_2 = _input + f"\processed\_mci{date}.tif"
        # array2raster(os.listdir(joined_path)[0], newImage_2, mci_calc)

        #  move into specific folder
        files = ["_chla", "_turbidity", "_sd"]
        dir_names = os.listdir(_input + "\processed")

        for file in dir_names:
            for parameter in files:
                if parameter in file:
                    # move a file by renaming it's path
                    os.rename(_input + "\processed\/" + file, _input +
                              f'\processed\{date}\/{file}')

        currentScene = currentScene + 1

    print("Done creating water quality parameters", flush=True)

    # calculate statistics
    if statistics:
        print("Creating statistics folder...", flush=True)

        # check if statistics folder already exists
        if not os.path.exists(_input + "\processed\statistics"):
            # create new folder
            os.makedirs(_input + "\processed\statistics")

        print("Calculating statistics...", flush=True)

        np_array = np.array(chla_rasters)  # convert python list to np.array

        # mean
        newImage_2 = _input + f"\processed\_mean.tif"
        array2raster(os.listdir(joined_path)[
                     0], newImage_2, np_array.mean(axis=0))

        # std
        newImage_2 = _input + f"\processed\_std.tif"
        array2raster(os.listdir(joined_path)[
                     0], newImage_2, np_array.std(axis=0))

        # var
        newImage_2 = _input + f"\processed\_var.tif"
        array2raster(os.listdir(joined_path)[
                     0], newImage_2, np_array.var(axis=0))

        # min
        newImage_2 = _input + f"\processed\_min.tif"
        array2raster(os.listdir(joined_path)[
                     0], newImage_2, np_array.min(axis=0))

        # max
        newImage_2 = _input + f"\processed\_max.tif"
        array2raster(os.listdir(joined_path)[
                     0], newImage_2, np_array.max(axis=0))

        #  move into statistics folder
        files = ["_mean", "_std", "_var", "_min", "_max"]
        dir_names = os.listdir(_input + "\processed")

        for file in dir_names:
            for endings in files:
                if endings in file:
                    # move a file by renaming it's path
                    os.rename(_input + "\processed\/" + file, _input +
                              "\processed\statistics\/" + file)

    print("Done", flush=True)
else:
    print("Invalid input. Please check your input parameters or refer to github for more informations.")
