try:
    from osgeo import gdal, ogr, osr
except ImportError:
    import gdal
    import ogr
    import osr


def save_shp(shp_path, geocode_list):
    # 支持中文路径
    gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES")
    # 属性表字段支持中文
    gdal.SetConfigOption("SHAPE_ENCODING", "UTF-8")
    # 注册驱动
    ogr.RegisterAll()
    # 创建shp数据
    strDriverName = "ESRI Shapefile"
    oDriver = ogr.GetDriverByName(strDriverName)
    if oDriver == None:
        return "驱动不可用：" + strDriverName
    # 创建数据源
    oDS = oDriver.CreateDataSource(shp_path)
    if oDS == None:
        return "创建文件失败：" + shp_path
    # 创建一个多边形图层，指定坐标系为WGS84
    papszLCO = []
    geosrs = osr.SpatialReference()
    geosrs.SetWellKnownGeogCS("WGS84")
    # 线：ogr_type = ogr.wkbLineString
    # 点：ogr_type = ogr.wkbPoint
    ogr_type = ogr.wkbPoint
    # 面的类型为Polygon，线的类型为Polyline，点的类型为Point
    oLayer = oDS.CreateLayer("Polygon", geosrs, ogr_type, papszLCO)
    if oLayer == None:
        return "图层创建失败！"
    # 创建属性表
    # 创建id字段
    oId = ogr.FieldDefn("id", ogr.OFTInteger)
    oLayer.CreateField(oId, 1)
    # 创建address、title、level字段
    oAddress = ogr.FieldDefn("class", ogr.OFTString)
    oLayer.CreateField(oAddress, 1)
    oDefn = oLayer.GetLayerDefn()
    # 创建要素
    # 数据集
    for index, f in enumerate(geocode_list):
        oFeaturePolygon = ogr.Feature(oDefn)
        oFeaturePolygon.SetField("id", index)
        oFeaturePolygon.SetField("class", f['class'])
        geomPolygon = ogr.CreateGeometryFromWkt(f['point'])
        oFeaturePolygon.SetGeometry(geomPolygon)
        oLayer.CreateFeature(oFeaturePolygon)
    # 创建完成后，关闭进程
    oDS.Destroy()
    return "数据集创建完成！"


if __name__ == "__main__":
    pass