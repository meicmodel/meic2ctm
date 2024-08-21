import os
import argparse
import datetime

import netCDF4 as nc
import pandas as pd

from meic2ctm.factor import load_species_map, get_day_factor, get_hour_factor
from meic2ctm.config import config
from meic2ctm.meic import load_meic_dat_by_spec


def main(args):
    ts = datetime.datetime.strptime(f'{start}', '%Y-%m-%d')
    te = datetime.datetime.strptime(f'{end} 23:59:59', '%Y-%m-%d %H:%M:%S')

    df_spec = load_species_map(config.get('base', 'model'))

    model_specs = df_spec['model_spec'].drop_duplicates().to_list()

    df = pd.read_csv(f"./factor/{config.get('base', 'model')}/species-unit.csv")
    species_unit = dict(zip(df['var'], df['units']))

    cell_size = config.getfloat('projection', 'dx') / 1000 * config.getfloat('projection', 'dy') / 1000

    # 遍历每一天 每个小时一个文件
    while ts <= te:
        print(f'calc date: {ts.year}-{ts.month}-{ts.day}')
        oputs = ts

        for hour in range(0, 24):
            file = './output/' + ts.strftime('wrfchemi_d01_%Y-%m-%d') + "_" + str(hour).zfill(2) + "_00_00"
            if (os.path.exists(file)):
                os.remove(file)
            ncfile = nc.Dataset(file, 'a', format='NETCDF3_CLASSIC')

            # 创建 LAY、ROW、COL 维度
            layers = pd.read_csv(f"./factor/{config.get('base', 'model')}/layer.csv").columns

            ncfile.createDimension('Time', None)
            ncfile.createDimension("DateStrLen", 19);
            ncfile.createDimension('emissions_zdim', len(layers) - 1)

            ncfile.createDimension('south_north', config.getint('projection', 'ycells'))
            ncfile.createDimension('west_east', config.getint('projection', 'xcells'))

            ncfile.setncattr("TITLE", "EMISSIONS for WRF-Chem");
            ncfile.setncattr("MMINLU", "MODIFIED_IGBP_MODIS_NOAH");
            ncfile.setncattr("NUM_LAND_CAT", 20);

            # 创建新的变量，并指定维度
            for spec in model_specs:
                var = ncfile.createVariable("E_" + spec, 'f4', ('Time', 'emissions_zdim', 'south_north', 'west_east'))

                var.setncattr('description', 'EMISSIONS')
                var.setncattr('units', species_unit[spec])
                var.setncattr('coordinates', 'XLONG XLAT')
                var.setncattr('stagger', '')
                var.setncattr('MemoryOrder', 'XYZ')
                var.setncattr('FieldType', 104)

            var = ncfile.createVariable("Times", 'c', ('Time', 'DateStrLen'))
            var[0] = ts.strftime('%Y-%m-%d') + "_" + str(hour).zfill(2) + ":00:00"


            model_specs = df_spec['model_spec'].drop_duplicates().to_list()

            # 当有跨月的计算需求的时候重新计算meic数据
            if hour > 0:
                oputs = ts + datetime.timedelta(hours=hour)
            print('Processing hour {}'.format(oputs.hour))

            for spec in model_specs:
                hour_result = None

                meic_month_data = load_meic_dat_by_spec(oputs.year, oputs.month, spec)
                for sector in meic_month_data:
                    day_factor = get_day_factor(oputs.year, oputs.month, oputs.day, sector)
                    hour_factor = get_hour_factor(oputs.hour, sector)
                    if hour_result is None:
                        hour_result = meic_month_data[sector] * (day_factor * hour_factor)
                    else:
                        hour_result += meic_month_data[sector] * (day_factor * hour_factor)

                var = ncfile.variables["E_" + spec]
                var[0, :, :, :] = hour_result / cell_size

            ncfile.close()

        ts += datetime.timedelta(days=1)


# if __name__ == '__main__':

parser = argparse.ArgumentParser(description='split the nc to model ready nc.')
parser.add_argument('-s', '--start', help='change the start datetime', type=str, default=None)
parser.add_argument('-e', '--end', help='charnge the end datetime', type=str, default=None)

try:
    args = parser.parse_args()
except argparse.ArgumentError:
    print('Catching an argument Error!')

# cli 指定参数优先
start = args.start if args.start else config.get('time', 'start_date')
end = args.end if args.end else config.get('time', 'end_date')
main(args)
