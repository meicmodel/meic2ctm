import os
from functools import lru_cache
import numpy as np
import pandas as pd

from .config import config
from .factor import load_species_map, load_pm_factor, load_control_factor
from .mix import load_mix
from .projection import projection


@lru_cache(maxsize=128)
def load_asc(year, month, sector, meic_spec_name):
    asc_file = './input/MEIC/{}/{}_{}_{}_{}.asc'.format(year, year, str(month).zfill(2), sector, meic_spec_name)

    control_file_path = None
    if config.has_option('inventory', 'control_file'):
        control_file_path = config.get('inventory', 'control_file')

    pm_factor = None
    if 'PMcoarse' in asc_file:
        pm10 = np.loadtxt(asc_file.replace('PMcoarse', 'PM10'), skiprows=6, dtype=np.float32)
        if control_file_path is not None:
            control_factor = load_control_factor(control_file_path, sector, year, month, 'PM10')
            if control_factor is not None:
                pm10 *= control_factor
        pm25 = np.loadtxt(asc_file.replace('PMcoarse', 'PM25'), skiprows=6, dtype=np.float32)
        if control_file_path is not None:
            control_factor = load_control_factor(control_file_path, sector, year, month, 'PM25')
            if control_factor is not None:
                pm25 *= control_factor
        dat = pm10 - pm25
    elif not os.path.exists(asc_file):
        parts = asc_file.split('_')
        sector = parts[2]
        species = parts[3].split('.')[0]
        pm_factor = load_pm_factor(config.get('base', 'model'), sector, species)
        asc_file = asc_file.replace(species, 'PM25')
        dat = np.loadtxt(asc_file, skiprows=6, dtype=np.float32)
        if control_file_path is not None:
            control_factor = load_control_factor(control_file_path, sector, year, month, 'PM25')
            if control_factor is not None:
                dat *= control_factor
    else:
        dat = np.loadtxt(asc_file, skiprows=6, dtype=np.float32)
        if control_file_path is not None:
            if '_' in meic_spec_name:
                control_factor = load_control_factor(control_file_path, sector, year, month, 'VOC')
            else:
                control_factor = load_control_factor(control_file_path, sector, year, month, meic_spec_name)
            if control_factor is not None:
                dat *= control_factor
    dat = np.flipud(dat)
    if pm_factor is not None:
        dat *= pm_factor
    return dat


def calc_area(lat, mix_version='1'):
    resolution = 0.25 if mix_version == '1' else 0.1
    Re = 6371.392
    X = Re * np.cos(lat * (np.pi / 180)) * (np.pi / 180) * resolution
    Y = Re * (np.pi / 180) * resolution
    return X * Y


@lru_cache(maxsize=128)
def load_meic_dat_by_spec(year, month, spec):
    df_sr = load_species_map(config.get('base', 'model'))
    sectors = config.get('base', 'sectors').split(',')
    mix_year = config.get('inventory', 'mix_inventory_year')
    mix_ver = config.get('inventory', 'mix_inventory_version')

    dfm = df_sr[df_sr.model_spec == spec]
    dfms = dfm.to_dict(orient='records')
    result_by_sector = {}
    for sector in sectors:

        result = None
        for meic_spec in dfms:
            meic_spec_name = meic_spec.get('meic_spec')
            df_mix = np.ma.copy(load_mix(mix_year, month, sector, meic_spec_name, mix_ver))

            # 对于MIX数据 需要进行裁剪和投影转换
            if mix_ver == '1':
                latitudes = np.arange(-20.25, 90, 0.25)
            else:
                latitudes = np.arange(-14.95, 60.05, 0.1)

            # 对MIX数据进行投影转换
            area_array = calc_area(latitudes, mix_ver)
            df_mix /= np.expand_dims(area_array, 1)
            projected_data = projection(df_mix, mix_ver)

            df_meic = load_asc(year, month, sector, meic_spec_name)
            # 叠加MIX和MEIC排放
            projected_data += df_meic

            # 转换单位
            df = pd.read_csv(f"./factor/{config.get('base', 'model')}/species-convert.csv")
            # 将数据转换成键-值形式的map
            model_species_map = dict(zip(df['species'], df['unit_convert']))
            projected_data *= model_species_map[meic_spec.get('model_spec')]

            # 垂直分配
            df = pd.read_csv(f"./factor/{config.get('base', 'model')}/layer.csv")
            coefficients = df[df['sector'] == sector].iloc[0, 1:].values.astype(np.float32)
            projected_data = projected_data.reshape(1, *projected_data.shape) * coefficients.reshape(-1, 1, 1)

            # 物种分配权重
            projected_data *= meic_spec.get('weight')
            if result is None:
                result = projected_data
            else:
                result += projected_data

        result[result < 0] = 0
        result_by_sector[sector] = result

    return result_by_sector
