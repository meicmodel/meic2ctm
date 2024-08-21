import os
from functools import lru_cache

import numpy as np
import netCDF4 as nc

from meic2ctm.config import config
from meic2ctm.factor import load_pm_factor

sector_mapping = {
    'power': 'POWER',
    'transportation': 'TRANSPORT',
    'residential': 'RESIDENTIAL',
    'industry': 'INDUSTRY',
    'agriculture': 'AGRICULTURE'
}


@lru_cache(maxsize=128)
def load_mix(year, month, sector, species, version):
    if version == '1':
        return load_mix_v1(year, month, sector, species)
    else:
        return load_mix_v2(year, month, sector, species)


def load_mix_v1(year, month, sector, species):
    nc_path = f'./input/MIX/MIX_V1/MIX_{year}/MICS_Asia_{species}_{year}_0.25x0.25.nc'
    pm_factor = None

    mask_china = np.loadtxt('./factor/mask_china.csv', delimiter=",", dtype=np.int8)

    if 'PMcoarse' in nc_path:
        pm10 = nc.Dataset(nc_path.replace('PMcoarse', 'PM10'), 'r')
        pm25 = nc.Dataset(nc_path.replace('PMcoarse', 'PM25'), 'r')
        if "PM10_" + sector_mapping.get(sector) in pm10.variables:
            variable_data = pm10.variables["PM10_" + sector_mapping.get(sector)][month - 1]
            variable_data -= pm25.variables["PM2.5_" + sector_mapping.get(sector)][month - 1]
            result = variable_data * mask_china
        else:
            result = np.zeros((441, 560))

    elif not os.path.exists(nc_path):
        pm_factor = load_pm_factor(config.get('base', 'model'), sector, species)
        nc_path = nc_path.replace(species, 'PM25')
        nc_file = nc.Dataset(nc_path, 'r')

        if "PM2.5_" + sector_mapping.get(sector) in nc_file.variables:
            variable_data = nc_file.variables["PM2.5_" + sector_mapping.get(sector)][month - 1]
            result = variable_data * mask_china
        else:
            result = np.zeros((441, 560))

    else:
        nc_file = nc.Dataset(nc_path, 'r')

        if species == 'PM25':
            species = 'PM2.5'

        if species + "_" + sector_mapping.get(sector) in nc_file.variables:
            variable_data = nc_file.variables[species + "_" + sector_mapping.get(sector)][month - 1]
            result = variable_data * mask_china
        else:
            result = np.zeros((441, 560))

    if pm_factor:
        result *= pm_factor
    return result


def load_mix_v2(year, month, sector, spec):
    nc_path = f'./input/MIX/MIX_V2/{year}/MIXv2.3_{spec}_{year}_monthly_0.1deg.nc'

    pm_factor = None
    sector_title = sector.title()
    var_name = f'{spec}_{sector_title}'

    mask_china = np.loadtxt('./factor/mask_mix_v2_china.csv', delimiter=",", dtype=np.int8)

    if 'PMcoarse' in nc_path:
        pm10 = nc.Dataset(nc_path.replace('PMcoarse', 'PM10'), 'r')
        pm25 = nc.Dataset(nc_path.replace('PMcoarse', 'PM25'), 'r')
        if f"PM10_{sector_title}" in pm10.variables:
            variable_data = pm10.variables[f"PM10_{sector_title}"][month - 1]
            variable_data -= pm25.variables[f"PM25_{sector_title}"][month - 1]
            result = variable_data * mask_china
        else:
            result = np.zeros((750, 940))

    elif not os.path.exists(nc_path):
        pm_factor = load_pm_factor(config.get('base', 'model'), sector, spec)
        nc_path = nc_path.replace(spec, 'PM25')
        nc_file = nc.Dataset(nc_path, 'r')

        if f"PM25_{sector_title}" in nc_file.variables:
            variable_data = nc_file.variables[f"PM25_{sector_title}"][month - 1]
            result = variable_data * mask_china
        else:
            result = np.zeros((750, 940))

    else:
        nc_file = nc.Dataset(nc_path, 'r')
        if var_name in nc_file.variables:
            variable_data = nc_file.variables[var_name][month - 1]
            result = variable_data * mask_china
        else:
            result = np.zeros((750, 940))

    if pm_factor:
        result *= pm_factor
    return result
