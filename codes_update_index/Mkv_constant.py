# -*- coding:utf-8 -*-
# ! python3

"""
定义参数和参量
"""

# 版本号
VERSION = "v0.5.1.190330_beta"
# 一年内交易日
N = 245
# 历史交易日数据长度
T = 66
# 默认波动率 or 标准差
DEFAULT_VOL = 0.15
# 默认现金收益率
CASH_RETURN = 0.0
# 默认回测开始区间
DEFAULT_START_T = "2012-01"
# 默认回测结束区间
DEFAULT_END_T = "2017-12"
# 默认单股最大权重
DEFAULT_UP = float("inf")
# 重要参数字典
CONF_DICT = {"dir": ["target_index", "code_file", "work_file"],
             "constraints": ["mode", "vol", "short", "max_weight", "cash_return"],
             "calculation": ["calc_time", "num_d", "start_time", "end_time", "frequency"],
             "filter": ["global_spec", "basic_indices", "refresh_freq", "ics", "ics_fv", "ics_rank"]}
# configue参数配置文件名
CONF_NAME = "configParam_mkv.conf"
# 文件地址为空错误信息
FILE_EMPTY_MSG = "文件地址不能为空，请输入正确文件地址"
# 文件地址不正确错误信息
FILE_EXIST_MSG = "文件地址错误，请重新确认后输入【注意后缀名，支持.txt.xls.xlsx】:\n"
# 空头限制语句缺失警告
SHORT_MISS_WARNING = "空头限制为空或无效，为您选择默认设置：仅多头"
# 股票信息变量名
STOCK_SEC = "sec_name,exch_eng"
# 默认行业分类
DEFAULT_ICS = "industry_gics"
# 默认行业内排序参照变量：市值大小排序
DEFAULT_ICS_FV = "ev"
# 优化问题限制条件个数
# 默认二级行业内入选股票数
ICS_RANK = 4
NUMCON = 2
# 常见板块
SET_ID_DICT = {"A_SHARE": "a001010100000000",
               "SH": "a001010200000000",
               "SZ": "a001010300000000",
               "SZ_MAIN": "a001010500000000",
               "SZ_SME": "a001010400000000",
               "SZ_GE": "a001010r00000000"}
# 目前支持的行业分类标准代码
ICS_LIST = ["industry_gics", "industry_citic", "industry_sw", "industry_gx", "indexname_AMAC"]
# 目前支持检索的基本面字段
FIELDS_ALIAS_DICT = {"pe": "pe_ttm",
                     "ev": "ev",
                     "pb": "pb_lf",
                     "ps": "ps_ttm",
                     "pcf": "pcf_ncf_ttm",
                     "dicidendyield": "dividendyield2",
                     "roe": "roe_avg",
                     "est_netprofit": "west_netprofit_YOY",
                     "netprofit_cagr": "west_netprofit_CAGR",
                     "ocf2op": "operatecashflowtoop_ttm",
                     "debt_ratio": "debttoassets"}
