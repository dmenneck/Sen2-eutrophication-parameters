import numpy as np
from numpy import inf
import os
import sys
import matplotlib.pyplot as plt
from datetime import datetime
from osgeo import gdal

from functions import array2raster, chla, turbidity, clipRaster, sd

np.errstate(invalid='ignore', divide='ignore')

gdal.UseExceptions()

shapePath, _input = None, None
shouldClip, statistics, plot = False, False, False
chla_rasters, turbidity_rasters, secchi_rasters,  dates = [], [], [], []
chla_means, turbidity_means, sd_means = [], [], []
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
    if "plot" in arg:
        plot = True

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
        date = f'{day}-{month}-{year}'
        dates.append(date)

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
        image = _input + f"\processed\_chla_{date}.tif"
        array2raster(os.listdir(joined_path)[0], image, chla_calc)

        # turbidity
        turbidity_calc = turbidity(bands_array[1], bands_array[2])
        turbidity_rasters.append(turbidity_calc)
        turbidity_calc[turbidity_calc == inf] = np.nan
        turbidity_means.append(np.nanmean(turbidity_calc))

        image = _input + f"\processed\_turbidity_{date}.tif"
        array2raster(os.listdir(joined_path)[0], image, turbidity_calc)

        # sd
        secchi_calc = sd(bands_array[0], bands_array[1])
        secchi_rasters.append(secchi_calc)
        secchi_calc[secchi_calc == inf] = np.nan
        sd_means.append(np.nanmean(secchi_calc))

        image = _input + f"\processed\_sd_{date}.tif"
        array2raster(os.listdir(joined_path)[0], image, secchi_calc)

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
            os.makedirs(_input + "\processed\statistics\chla")
            os.makedirs(_input + "\processed\statistics\sd")
            os.makedirs(_input + "\processed\statistics\/turbidity")

        print("Calculating statistics...", flush=True)

        # convert python list to np.array
        parameters = [np.array(chla_rasters), np.array(
            turbidity_rasters), np.array(secchi_rasters)]
        folder_names = ['chla', 'turbidity', 'sd']

        for i in range(len(parameters)):
            # mean
            image = _input + f"\processed\_mean.tif"
            array2raster(os.listdir(joined_path)[
                0], image, parameters[i].mean(axis=0))
            # std
            image = _input + f"\processed\_std.tif"
            array2raster(os.listdir(joined_path)[
                0], image, parameters[i].std(axis=0))
            # var
            image = _input + f"\processed\_var.tif"
            array2raster(os.listdir(joined_path)[
                0], image, parameters[i].var(axis=0))
            # min
            image = _input + f"\processed\_min.tif"
            array2raster(os.listdir(joined_path)[
                0], image, parameters[i].min(axis=0))
            # max
            image = _input + f"\processed\_max.tif"
            array2raster(os.listdir(joined_path)[
                0], image, parameters[i].max(axis=0))

            #  move into statistics folder
            files = ["_mean", "_std", "_var", "_min", "_max"]
            dir_names = os.listdir(_input + "\processed")

            for file in dir_names:
                for endings in files:
                    if endings in file:
                        # move a file by renaming it's path
                        os.rename(_input + "\processed\/" + file, _input +
                                  "\processed\statistics\/" + folder_names[i] + "/" + file)

    if plot:
        # Means are currently not sorted by date. Create dict from date and means list.
        chla_dict = dict(zip(dates, chla_means))
        turb_dict = dict(zip(dates, turbidity_means))
        sd_dict = dict(zip(dates, sd_means))
        # order dict by date
        chla_ordered = sorted(chla_dict.items(), key=lambda x: datetime.strptime(
            x[0], '%d-%m-%Y'), reverse=False)
        turb_ordered = sorted(turb_dict.items(), key=lambda x: datetime.strptime(
            x[0], '%d-%m-%Y'), reverse=False)
        sd_ordered = sorted(sd_dict.items(), key=lambda x: datetime.strptime(
            x[0], '%d-%m-%Y'), reverse=False)

        # list comprehension
        chla_ordered_list = [x[0] for x in chla_ordered]
        chla_means_ordered_list = [x[1] for x in chla_ordered]
        turb_ordered_list = [x[0] for x in turb_ordered]
        turb_means_ordered_list = [x[1] for x in turb_ordered]
        sd_ordered_list = [x[0] for x in sd_ordered]
        sd_means_ordered_list = [x[1] for x in sd_ordered]

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, True)
        plt.style.use("seaborn")

        ax1.plot(chla_ordered_list, chla_means_ordered_list, color="k",
                 marker="o", label="chla mean")
        ax2.plot(turb_ordered_list, turb_means_ordered_list, color="k",
                 marker="o", label="turbidity mean")
        ax3.plot(sd_ordered_list, sd_means_ordered_list, color="k",
                 marker="o", label="turbidity mean")

        ax1.set_ylabel("Mean chlorophyll-a")
        ax1.set_title("Water quality parameter mean values 2020")
        # ax1.legend()
        # ax1.grid(True)

        # ax2.set_xlabel("Dates")
        ax2.set_ylabel("Mean turbidity")
        # ax2.legend()
        # ax2.grid(True)

        # ax3.set_xlabel("Dates")
        ax3.set_ylabel("Mean secchi disk transparency")
        # ax3.legend()
        # ax3.grid(True)

        plt.show()

    print("Done", flush=True)
else:
    print("Invalid input. Please check your input parameters or refer to github for more informations.")
