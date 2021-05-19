import numpy as np
from numpy import inf
import os
import sys
from osgeo import gdal

from functions import array2raster, chla, turbidity, clipRaster, sd

np.errstate(invalid='ignore', divide='ignore')

gdal.UseExceptions()

shapePath, _input = None, None
shouldClip, statistics = False, False
chla_rasters, chla_means = [], []
amountOfScenes, currentScene = 0, 1

# number of arguments passed with script call
arguments = sys.argv

# loop over input arguments and find input and output
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

        # create folder for specific year and check if it already exists
        if not os.path.exists(_input + f'\processed\/{date}'):
            # create new folder
            os.makedirs(_input + f'\processed\/{date}')

        band_names = ['B02', 'B03', 'B04', 'B05',
                      'B06', 'B07', 'B11', 'B12', 'B8A']

        gdal_bands = []

        # open gdal bands
        for band in os.listdir(joined_path):
            if band[-11:-8] in band_names:
                temp = gdal.Open(band)
                gdal_bands.append(temp)

        bands_array = []

        # read gdal bands as array
        for band in gdal_bands:
            bands_array.append(band.ReadAsArray())

        if shouldClip:
            # clip raster
            for index, array in enumerate(gdal_bands):
                clipped = clipRaster(gdal_bands[index], shapePath)
                # overwrite band with clipped band
                bands_array[index] = clipped

        # chlorophyll a
        chla_calc = chla(bands_array[2], bands_array[3])
        # append to list for future statistical analysis
        chla_rasters.append(chla_calc)

        # replace inf with nan
        chla_calc[chla_calc == inf] = np.nan
        # check if inf is still in dataset
        # print(np.isinf(chla_calc).any())

        # add mean to list
        chla_means.append(np.nanmean(chla_calc))

        # create tif
        newImage = _input + f"\processed\_chla_{date}.tif"
        array2raster(os.listdir(joined_path)[0], newImage, chla_calc)

        # turbidity
        tt_calc = turbidity(bands_array[1], bands_array[2])
        newImage_2 = _input + f"\processed\_turbidity_{date}.tif"
        array2raster(os.listdir(joined_path)[0], newImage_2, tt_calc)

        # sd
        sd_calc = sd(bands_array[0], bands_array[1])
        newImage_2 = _input + f"\processed\_sd_{date}.tif"
        array2raster(os.listdir(joined_path)[0], newImage_2, sd_calc)

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

    print(chla_means)

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
