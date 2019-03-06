# -*- coding:utf-8 -*-
# ! python3


from WindPy import w


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

    def eval_returns(self, var="pct_chg"):
        stocks_str = ",".join(self._stocks)
        if not w.isconnected():
            w.start()
        if self._freq == "D":
            returns = w.wsd(stocks_str, var,
                            self._eval_seq[0],
                            self._eval_seq[-1],
                            "showblank=0").Data
        else:
            returns = w.wsd(stocks_str, var,
                            self._eval_seq[0],
                            self._eval_seq[-1],
                            "Period=%s;showblank=0" % self._freq).Data
        cash_days = {"M": 30,
                     "W": 7,
                     "D": 1}
        returns.append([self._cash_r * cash_days[self._freq]] * len(returns[0]))
        returns = list(zip(*returns))
        return returns