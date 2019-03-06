# -*- coding:utf-8 -*-
# ! python3

"""
定义参数和参量
"""

# 版本号
VERSION = "v0.3.1.190306_beta"
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
CONF_DICT = {"dir": ["code_file", "work_file"],
             "constraints": ["vol", "short", "max_weight", "cash_return"],
             "calculation": ["calc_time", "num_d", "start_time", "end_time"]}
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
# 优化问题限制条件个数
NUMCON = 2
