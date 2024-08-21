import numpy as np
from functools import lru_cache

def calc_area(lat):
    Re = 6371.392
    X = Re * np.cos(lat * (np.pi / 180)) * (np.pi / 180) * 0.25
    Y = Re * (np.pi / 180) * 0.25
    return X * Y

@lru_cache(maxsize=5)
def calc_area_all():	
    # meic维度范围用来计算面积
    latitudes = np.arange(-20.25, 90, 0.25)
    area_array = calc_area(latitudes)
    return area_array
