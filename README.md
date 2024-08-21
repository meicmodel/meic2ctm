# MEIC2CTM

## MEIC清单动态处理模式

## 使用前准备

### 程序准备

程序运行依赖Python 3 运行环境及相关依赖库。如使用pip进行依赖管理，可以使用pip install -r requirements.txt 命令安装相关依赖。

### 数据准备

#### 排放数据

程序运行依赖于中国大陆地区MEIC清单和亚洲地区MIX排放清单。

* MEIC清单：请根据实际需求，在[中国污染物排放]([http://](http://meicmodel.org.cn/?page_id=560)) 模块下载<font color="red">**兰伯特投影**</font>后的分部门逐月排放数据，并根据实际模型需求，选择输出VOC化学机制。
* MIX清单：支持MIX和MIX v2清单数据。可根据实际需求在[共享清单](http://meicmodel.org.cn/?page_id=1770)模块下载。

#### 分配方案

系统在factor目录内置了默认的时间、空间和物种分配方案，可根据实际需要对系数进行调整。

##### 日分配

day.csv 描述了从周一到周日，各部门的变化曲线。

##### 小时分配

hour.csv 描述了从0时到23时，各部门的变化曲线。

##### 垂直分配

layer.csv 描述了各部门在各个高度层的分配权重。注：此文件需要和配置文件中layers的长度匹配。

##### 物种分配
species-unit.csv 描述了各个物种在模型中的单位。

species-map.csv 描述了各个物种在清单数据和模型中的映射关系。

species-convert.csv 描述了各个物种从排放量向排放强度的转换关系。

pm25factor.csv 描述了PM2.5向颗粒物组分的转换关系。

### 配置文件

程序运行的具体配置从config.ini中读取，可以生成2020年7月1日-2020年7月2日的排放结果。
具体每一列的含义请参见配置文件注释，常见可能需要修改的参数包括：

base

```config
output_path：排放输出路径
```

inventory

```config
mix_inventory_year：MIX清单年份
contorl_file: 可选参数，调控系数路径，具体写法请见调控系数部分。
```

time

```config
start_date：模式开始日期
end_date：模式结束日期
one_file_hours：单个文件小时数
```

projection(此部分配置需和MEIC数据投影一致)
```config
lambert_params：投影参数设置，遵循PROJ.4语法
xorig：左下角横坐标
yorig：左下角纵坐标
dx：x方向长度（米）
dy：y方向长度（米）
xcells：x方向网格数
ycells：y方向网格数
```

## 调控系数

系统支持在分省、逐月、分部门为各物种增加调控系数。调控系数需要准备成一份csv文件（逗号分隔文件）。样例及具体每一列的含义如下：

| category | province | year | month | species | factor |
|----------|----------|------|-------|---------|--------|
| power    | 51       | 2018 | 12    | SO2     | 0.6    |

| 列名       | 含义   | 参数                                                                                                                |
|----------|------|-------------------------------------------------------------------------------------------------------------------|
| category | 部门   | power industry transportation residential agriculture                                                             |
| province | 省份   | 2位省级行政区划代码，如北京 11 天津 12 河北省 13，详见： [2022年中华人民共和国县以上行政区划代码](https://www.mca.gov.cn/mzsj/xzqh/2022/202201xzqh.html) |
| year     | 年份   | MEIC清单年份                                                                                                          |
| month    | 月份   | 1-12                                                                                                              |
| species  | 物种   | SO2 NOx CO VOC NH3 PM10 PM25 BC OC                                                                                |
| factor   | 系数   | ≥0                                                                                                                |

## 程序执行

### CMAQ
使用python cmaq.py命令调用程序。程序执行完成后，自动退出。程序会在config文件指定的output目录下，以EM_China_d01_YYYYMMdd.nc的格式，从开始日期到结束日期，每天生成一个文件。

### WrfChem
使用python wrchem.py命令调用程序。程序执行完成后，自动退出。程序会在config文件指定的output目录下，以wrfchemi_d01_YYYY-MM-dd_HH_00_00的格式，从开始日期到结束日期，每小时生成一个文件。

## 联系方式
软件的使用问题或相关建议，请联系meic@tsinghua.edu.cn。

## 贡献者
| 贡献者 | 单位   | 贡献内容   |
|-----|------|--------|
| 张强  | 清华大学 | 系统框架设计 |
| 刘晓东 | 清华大学 | 代码实现   |


## 版权信息

本软件由清华大学MEIC团队开发，并开源。

本软件遵循 GNU 通用公共许可证 (GPL)，您可以自由地使用、修改和分发该软件，但必须遵守 GPL 的条款。
