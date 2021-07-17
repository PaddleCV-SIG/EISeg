def check_gdal():
    try:
        import gdal
        return True
    except:
        try:
            from osgeo import gdal
            return True
        except ImportError:
            return False