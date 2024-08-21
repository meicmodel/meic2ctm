import numpy as np
from pyproj import Transformer
from .config import config
from functools import lru_cache

idx = 0
idy = 0
dest_lat=np.zeros(0)
dest_lon=np.zeros(0)
@lru_cache(maxsize=2)
def projection_base(mix_version):
    if mix_version == '1':
        latitudes = np.arange(-20.25, 90, 0.25)
        longitudes = np.arange(40, 180, 0.25)
        resolution = 0.25
    else:
        latitudes = np.arange(-14.95, 60.05, 0.1)
        longitudes = np.arange(60.05, 154, 0.1)
        resolution = 0.1
    # 定义经纬度坐标系和Lambert投影坐标系
    wgs84 = "EPSG:4326"  # 经纬度坐标系

    lambert_params = config.get('projection', 'lambert_params')

    # 创建一个Transformer对象，用于从经纬度坐标系到Lambert投影坐标系的转换
    lambert_to_wgs84_transformer = Transformer.from_proj(lambert_params, wgs84)

    # 加载投屏配置数据
    xorig = config.getfloat('projection', 'xorig')
    yorig = config.getfloat('projection', 'yorig')  # 左下角纵坐标
    dx = config.getint('projection', 'dx')  # x方向长度（米）
    dy = config.getint('projection', 'dy')  # y方向长度（米）
    xcells = config.getint('projection', 'xcells')  # x方向网格数
    ycells = config.getint('projection', 'ycells')  # y方向网格数

    # 计算每个网格单元的中心位置在Lambert投影坐标系下的坐标
    lambert_xcoords = np.array([xorig + i * dx + dx / 2 for i in range(xcells)])
    lambert_ycoords = np.array([yorig + j * dy + dy / 2 for j in range(ycells)])

    # 将Lambert投影坐标系下的坐标转换为经纬度坐标系下的坐标
    dest_x = np.zeros((xcells, ycells), dtype=int)
    dest_y = np.zeros((xcells, ycells), dtype=int)

    global dest_lat
    dest_lat = np.zeros((xcells, ycells), dtype=float)
    global dest_lon
    dest_lon = np.zeros((xcells, ycells), dtype=float)

    global idx
    idx = 0
    global idy
    for x in lambert_xcoords:
        idy = 0
        for y in lambert_ycoords:
            lat, lon = lambert_to_wgs84_transformer.transform(x, y)
            dest_lat[idx, idy] = lat
            dest_lon[idx, idy] = lon
            dest_y[idx, idy] = np.floor((lat - latitudes[0]) / resolution).astype(int)
            dest_x[idx, idy] = np.floor((lon - longitudes[0]) / resolution).astype(int)
            idy += 1
        idx += 1

    return dest_x, dest_y, dx, dy


def projection(original_data, mix_version='1'):
    dest_x, dest_y, dx, dy = projection_base(mix_version)
    dest_data = original_data[dest_y, dest_x]
    dest_data = np.transpose(dest_data)
    dest_data *= (dx * dy / 1000 / 1000)
    return np.array(dest_data.data, dtype=np.float32)
