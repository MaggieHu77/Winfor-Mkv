# -*- coding:utf-8 -*-
# ! python3


from WindPy import w
from time import sleep
import numpy as np
from tqdm import tqdm
import pandas as pd
# from Mkv_constant import *


"""
评估回测期间的收益率表现
"""
class MkvEval(object):
    """用于计算和处理回测模式下各个区间收益情况."""
    def __init__(self, eval_seq, freq, stocks, cash_r, rebalance_h=None):
        """
        初始化函数.

        :param eval_seq: list,回测时间内各周期末日期.
        :param freq: 回测频率.
        :param stocks: eval_seq中每个日期对应持仓股票代码.
        :param cash_r: float,年化现金收益率.
        :param rebalance_h: int,如果回测频率为”H",需要给出该参数.
        """
        self._eval_seq = eval_seq
        self._freq = freq
        self._rebalance_h = rebalance_h
        self._stocks = stocks
        self._cash_r = cash_r

    @property
    def eval_seq(self):
        """
        回测期间内持仓期末时点.
        """
        return self._eval_seq

    @property
    def freq(self):
        """回测频率."""
        return self._freq

    @property
    def stocks(self):
        """股票代码列表."""
        return self._stocks

    @property
    def cash_r(self):
        """年化现金收益率."""
        return self._cash_r

    @property
    def rebalance_h(self):
        """小时级别调仓周期."""
        return self._rebalance_h

    def eval_returns(self, var="pct_chg", get_t_seq=False):
        """
        在各时间段内持仓股票品种不变的情形下，应用该函数获取每个时点上每只股票对应频率的变量值.

        :param var: str,wind变量名，一般是区间收益率.
        :param get_t_seq: bool,是否返回时间序列字符串.

        :return: 变量集合，日期list.
        """
        if not w.isconnected():
            w.start()
        if self._freq == "D":
            res = w.wsd(self._stocks, var,
                            self._eval_seq[0],
                            self._eval_seq[-1],
                            "showblank=0")
            returns = res.Data
        elif self._freq == "H":
            # 这部分函数有错误，暂时不用，改用eval_retrns12替代
            # w.wsi的时间是左开右闭
            eval_end = self._eval_seq[-1]
            eval_end = eval_end[:-4] + "1" + eval_end[-3:]
            res = w.wsi(self._stocks, var, self._eval_seq[0], eval_end, "BarSize=60;showblank=0")
            returns = res.Data
        else:
            res = w.wsd(self._stocks, var,
                            self._eval_seq[0],
                            self._eval_seq[-1],
                            "Period=%s;showblank=0" % self._freq)
            returns = res.Data
        cash_days = {"M": 30,
                     "W": 7,
                     "D": 1,
                     "H": float(1/24)}
        returns.append([self._cash_r * cash_days[self._freq]] * len(returns[0]))
        returns = list(zip(*returns))
        if get_t_seq:
            if self._freq != "H":
                returns = returns, list(map(lambda x: x.strftime("%Y-%m-%d"), res.Times))
            else:
                returns = returns, list(map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"), res.Times))
        return returns

    def eval_returns12(self, codes, eval_date, var="pct_chg", eval_interval_start=None,
                       include_head=False):
        """
        返回特定评估日，所有股票的区间收益率.

        :param codes: list, stock codes.
        :param eval_date: str, 评估日当日， fmt='%Y-%m-%d'或'%Y-%m-%d H:M:S'.
        :param var: str或者list, 需要提取的变量，一般是收益率.
        :param eval_interval_start: str，区间开始日期，fmt='%Y-%m-%d'，只有_freq=H时有效,
        :param skip: 一次评估基础K线长度，特别用于_freq=H.
        :param include_head: 数据开始是否包括左侧区间点.
        :return: list or DataFrame，股票变量对象.
        """
        if not w.isconnected():
            w.start()
            sleep(3)
        if self._freq == "D":
            return_ = w.wsd(codes, var, eval_date, eval_date,"showblank=0").Data[0]
        elif self._freq == "H":
            # w.wsi的时间是左开右闭
            eval_end = eval_date[:-4]+"1"+eval_date[-3:]
            return_ = []
            tq_bar = tqdm(codes)
            tq_bar.set_description(f"eval_returns {eval_date}", refresh=True)
            for ss in tq_bar:
                res = w.wsi(ss, var, eval_interval_start, eval_end, "BarSize=60;showblank=0")
                if res.ErrorCode != 0:
                    return_.append(0.0)
                else:
                    rt_seq = res.Data[0]
                    if not include_head:
                        rt_seq.pop(0)
                    rt_cum = np.prod(np.array(rt_seq)+1)-1
                    return_.append(float(rt_cum))
            # res = w.wsi(codes, var, eval_interval_start, eval_end, "BarSize=60;showblank=0")
            # return_ = res.Data[1]

        else:
            return_ = w.wsd(codes, var, eval_date, eval_date,
                            "Period=%s;showblank=0" % self._freq).Data[0]
        cash_days = {"M": 30,
                     "W": 7,
                     "D": 1,
                     "H": float(1 / 24)}
        return_.append(self._cash_r * cash_days[self._freq])
        return return_

    def eval_returns_drange(self, codes, eval_begin, eval_end, var="pct_chg", get_t_seq=False):
        """
        获取"D"频率下，指定开始和结束日期内每个K线指定股票变量值.

        :param codes: list,股票代码.
        :param eval_begin: str, 开始日期.
        :param eval_end: str, 结束日期.
        :param var: str, wind变量名.
        :param get_t_seq: bool, 是否返回区间内日期.

        :return: list or DataFrame, list; 变量对象,日期.
        """
        if not w.isconnected():
            w.start()
            sleep(3)
        assert self._freq == "D", "ParameterError: method eval_returns_drange仅支持D为频率"
        res = w.wsd(codes, var, eval_begin, eval_end, "showblank=0")
        returns = res.Data
        cash_days = {"M": 30,
                     "W": 7,
                     "D": 1}
        returns.append([self._cash_r * cash_days[self._freq]] * len(returns[0]))
        returns = list(zip(*returns))
        if get_t_seq:
            returns = returns, list(map(lambda x: x.strftime("%Y-%m-%d"), res.Times))
        return returns

    def eval_returns_hrange(self, codes, eval_begin, eval_end, skip, var="pct_chg",
                            get_t_seq=False):
        """
        获取"H"频率下，指定开始和结束日期内每个K线指定股票变量值.

        :param codes: list, 股票代码.
        :param eval_begin: str, 开始时间.
        :param eval_end: str, 结束时间.
        :param skip: int, 区间内K线数量.
        :param var: str, 变量名.
        :param get_t_seq: bool, 是否返回时间list.

        :return: list or DataFrame, list; 变量对象,日期.
        """
        if not w.isconnected():
            w.start()
            sleep(3)
        assert self._freq == "H", "ParameterError: method eval_returns_hrange仅支持H为频率"
        eval_end = eval_end[:-4] + "1" + eval_end[-3:]
        eval_begin = eval_begin[:-4] + "1" + eval_begin[-3:]
        returns = []
        eval_t_seq = list(map(lambda t: t.strftime("%Y-%m-%d %H:%M:%S"), w.wsi("000001.SH", var,
                                                                       eval_begin, eval_end,
                             "BarSize=60;showblank=0").Times))
        assert skip == len(eval_t_seq), "TimeIndexError: 预测区间长度与实际获取长度不一致"
        # tqdm_obj = tqdm(codes)
        for ss in codes:
            # tqdm_obj.set_description(desc=f"eval hourly return: {ss}", refresh=False)
            res = w.wsi(ss, var, eval_begin, eval_end, "BarSize=60;showblank=0")
            if res.ErrorCode != 0:

                returns.append(pd.Series([0.0]*skip, index=eval_t_seq, name=ss))
            else:
                returns.append(pd.Series(res.Data[0], index=list(map(lambda t: t.strftime(
                    "%Y-%m-%d %H:%M:%S"), res.Times)), name=ss))
        cash_days = {"M": 30,
                     "W": 7,
                     "D": 1,
                     "H": float(1/24)}
        returns = pd.concat(returns, axis=1).replace(np.nan, 0.0)
        returns.loc[:, "cash"] = self._cash_r * cash_days[self._freq]
        returns = returns.values.tolist()
        if get_t_seq:
            returns = returns, eval_t_seq
        return returns