from osgeo import gdal, osr
import numpy as np


def chla(B4, B5):
    return 127.63 * (B5 / B4) - 99.2


def turbidity(B3, B4):
    return ((B4 - B3) / (B4 + B3))


def sd(B2, B3):  # in meters
    return 4.7134 * (B2 / B3)**2.5569


def clipRaster(band, shape):
    band_clip = gdal.Warp(
        "_.tif", band, cutlineDSName=shape, dstNodata=0)

    band_clip = band_clip.ReadAsArray().astype(np.float)

    return band_clip


def array2raster(originalImage, newImage, array):
    raster = gdal.Open(originalImage)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = raster.RasterXSize
    rows = raster.RasterYSize

    driver = gdal.GetDriverByName('Gtiff')
    outRaster = driver.Create(newImage, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform(
        (originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()
