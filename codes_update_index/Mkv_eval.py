# -*- coding:utf-8 -*-
# ! python3


from WindPy import w
from time import sleep
import numpy as np
# from Mkv_constant import *


class MkvEval(object):
    """用于计算和处理回测模式下各个区间收益情况"""
    def __init__(self, eval_seq, freq, stocks, cash_r):
        self._eval_seq = eval_seq
        self._freq = freq
        self._stocks = stocks
        self._cash_r = cash_r

    @property
    def eval_seq(self):
        return self._eval_seq

    @property
    def freq(self):
        return self._freq

    @property
    def stocks(self):
        return self._stocks

    @property
    def cash_r(self):
        return self._cash_r

    def eval_returns(self, var="pct_chg", get_t_seq=False):
        if not w.isconnected():
            w.start()
            sleep(3)
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

    def eval_returns12(self, codes, eval_date, var="pct_chg"):
        if not w.isconnected():
            w.start()
            sleep(3)
        if self._freq == "D":
            return_ = w.wsd(codes, var, eval_date, eval_date,"showblank=0").Data[0]
        elif self._freq == "H":
            # w.wsi的时间是左开右闭
            eval_end = eval_date
            eval_end = eval_end[:-4]+"1"+eval_end[-3:]
            return_ = []
            for ss in codes:
                res = w.wsi(ss, var, eval_date, eval_end, "BarSize=60;showblank=0")
                if res.ErrorCode != 0:
                    return_.append(0.0)
                else:
                    return_.extend(res.Data[0])
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