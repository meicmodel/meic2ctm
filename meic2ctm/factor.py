import datetime
import calendar
import pandas as pd
from functools import lru_cache
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

from meic2ctm import projection


@lru_cache(maxsize=10)
def load_species_map(basedir):
    """
    加载物种映射配置文件，返回一个包含'sector', 'species'和'spec'三列的DataFrame。
    
    Args:
        无参数。
    
    Returns:
        pd.DataFrame: 
    
    """
    # 加载物种映射配置
    df = pd.read_csv(f'./factor/{basedir}/species-map.csv')
    dff = df.melt(id_vars=['Var'], var_name='meic_spec', value_name='weight')
    dff.dropna(subset=["weight"], inplace=True)
    dff = dff.rename(columns={'Var': 'model_spec'})

    return dff


@lru_cache(maxsize=1024)
def calc_day_factor(year, month):
    df = pd.read_csv('./factor/day.csv')
    # print(df)
    dfc = df.melt(id_vars=['sector'], var_name='weekday', value_name='factor')
    dfc['weekday'] = dfc['weekday'].astype(int)
    dfc.loc[:, 'weekday'] = dfc['weekday'] - 1
    # print(dfc)

    dfd = pd.DataFrame()
    # 需要解决跨日/月的问题

    delta = datetime.timedelta(days=1)
    init_days_weekday, month_last_day = calendar.monthrange(year, month)

    tss = datetime.date(year, month, 1)
    tes = datetime.date(year, month, month_last_day)
    while tss <= tes:
        d = pd.DataFrame.from_records(
            [{'year': tss.year, 'month': tss.month, 'day': tss.day, 'weekday': tss.weekday()}])
        dft = dfc.join(d.set_index(['weekday']), on=['weekday'], how='inner')
        if dfd.empty:
            dfd = dft
        else:
            dfd = pd.concat([dfd, dft], ignore_index=True)
        tss += delta

    dfs = dfd.groupby(['sector', 'year', 'month']).agg({'factor': 'sum'})
    dfs.rename(columns={'factor': 'day_factor_sum'}, inplace=True)

    dfs = dfd.join(dfs, on=['sector', 'year', 'month'], how='left')
    dfs.loc[:, 'day_factor'] = dfs['factor'] / dfs['day_factor_sum']
    return dfs[['sector', 'year', 'month', 'day', 'day_factor']]


@lru_cache(maxsize=1024)
def get_day_factor(year, month, day, sector):
    df = calc_day_factor(year, month)
    df = df[(df.sector == sector) & (df.month == month) & (df.day == day)]
    re = df.to_dict(orient='records')
    return re[0]['day_factor']


@lru_cache(maxsize=1024)
def load_hour_factor():
    """
    加载小时分配因子格式转换
    
    Args:
        无
    
    Returns:
        DataFrame: 包含小时、行业、小时因子的DataFrame
    
    """
    df = pd.read_csv('./factor/hour.csv')
    # print(df)
    dfc = df.melt(id_vars=['sector'], var_name='hour', value_name='hour_factor')
    dfc['hour'] = dfc['hour'].astype(int)

    dfc = dfc[dfc.sector != 'biogenic']

    return dfc[['hour', 'sector', 'hour_factor']]


@lru_cache(maxsize=1024)
def get_hour_factor(hour, sector):
    df = load_hour_factor()
    df = df[(df.sector == sector) & (df.hour == hour)]
    re = df.to_dict(orient='records')
    return re[0]['hour_factor']


@lru_cache(maxsize=10)
def load_species_convert():
    '''
        加载物种转换系数
    '''
    df = pd.read_csv('./factor/species-convert.csv')  # 假设CSV文件中没有列名
    # 将数据转换成键-值形式的map
    model_species_map = dict(zip(df['species'], df['unit_convert']))
    return model_species_map


lru_cache(maxsize=10)


def load_layer_weight(sector):
    df = pd.read_csv('./factor/layer.csv')  # 假设CSV文件中没有列名
    coefficients = df[df['sector'] == sector].iloc[0, 1:].values
    return coefficients


@lru_cache(maxsize=1024)
def load_pm_factor(basedir, sector, parameter):
    file_path = f"./factor/{basedir}/pm25factor.csv"

    # 读取CSV文件
    df = pd.read_csv(file_path)
    # 获取对应的系数
    coefficient = df.loc[df['Sector'] == sector, parameter].values[0] / 100
    return coefficient


@lru_cache(maxsize=128)
def load_control_factor(control_file_path, sector, year, month, species):
    df = pd.read_csv(control_file_path)
    filtered_df = df[(df['sector'] == sector) &
                     (df['year'] == year) &
                     (df['month'] == month) &
                     (df['species'] == species)]
    if filtered_df.empty:
        return None
    else:
        grid = np.ones((projection.idy, projection.idx))
        for i in range(projection.idx):
            for j in range(projection.idy):
                lat = projection.dest_lat[i][j]
                lon = projection.dest_lon[i][j]
                adcode = get_province_from_shapefile(lon, lat)
                if adcode is not None:
                    for index, row in filtered_df.iterrows():
                        if row['adcode'] == adcode:
                            grid[j, i] = row['factor']
        grid = np.flipud(grid)
        return grid


gdf = gpd.read_file("factor/shp/province.shp")


@lru_cache(maxsize=36000)
def get_province_from_shapefile(lon, lat):
    point = Point(lon, lat)
    for _, row in gdf.iterrows():
        if row['geometry'].contains(point):
            return int(row['pr_adcode'][:2])
    return None
