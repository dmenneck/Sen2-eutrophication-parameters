from osgeo import gdal, osr, ogr
import numpy as np


def mci(B4, B5, B6):
    return B5 - 1.005 * (B4 + ((B6 - B4) * (0.705 - 0.665) / (0.740 - 0.665)))


def chla(B4, B5):
    # return (1/B4 - 1/B5) * B6
    return 127.63 * (B5 / B4) - 99.2


def turbidity(B3, B4):
    return ((B4 - B3) / (B4 + B3))


def sd(B2, B3):  # in meters
    return 4.7134 * (B2 / B3)**2.5569


def clipRaster(band, shape):
    band_clip = gdal.Warp(
        "_.tif", band, cutlineDSName=shape, dstNodata = 0)

    band_clip = band_clip.ReadAsArray().astype(np.float)

    return band_clip # delete zeros


def array2raster(originalImage, newImage, array):
    # lese originales S2 als GDAL Datensatz ein
    raster = gdal.Open(originalImage)
    # Abrufen der Transformationskoeffizienten und speichern als Tuple
    geotransform = raster.GetGeoTransform()
    # Abrufen der X min Koordinate (obere linke Bildecke)
    originX = geotransform[0]
    # Abrufen der Y max Koordinate (obere linke Bildecke)
    originY = geotransform[3]
    # Abrufen der Pixel-"Weite"
    pixelWidth = geotransform[1]
    # Abrufen der Pixel-"Höhe"
    pixelHeight = geotransform[5]
    # Abrufen der Spaltenanzahl
    cols = raster.RasterXSize
    # Abrufen der Zeilenanzahl
    rows = raster.RasterYSize

    # GDAL Treiber für GeoTIFFs
    driver = gdal.GetDriverByName('Gtiff')
    # Erzeugt einen neuen Datensatz mit spezifizierten Eigenschaften
    outRaster = driver.Create(newImage, cols, rows, 1, gdal.GDT_Float32)
    # Weist dem erzeugten Datensatz, basierend auf den Eigenschaften des originalen S2s, eine Projektion zu
    outRaster.SetGeoTransform(
        (originX, pixelWidth, 0, originY, 0, pixelHeight))
    # Band-Objekt für einen Datensatz abrufen
    outband = outRaster.GetRasterBand(1)
    # Schreibe NumPy Array in GDAL Band
    outband.WriteArray(array)
    # Aufruf des Objekts für das Koordinatenreferenzsystem
    outRasterSRS = osr.SpatialReference()
    # Setze OGRSpatialReference basierend auf einer well-known-text Koordinatenreferenzsystem Definition
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    # Setze die Projektion für den Datensatz
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    # Leere den Zwischenspeicher
    outband.FlushCache()
