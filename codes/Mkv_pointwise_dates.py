# -*- coding:utf-8 -*-
# ! python3


from WindPy import w
from Mkv_constant import *
from dateutil.relativedelta import relativedelta
from datetime import datetime
from time import sleep


class BTdate(object):
    """处理回测时间点序列相关"""
    def __init__(self, start, end, freq, calendar, rebalance_h=None):
        """
        初始化函数.

        :param start: str, 回测开始时点，fmt="%Y-%m-%d".
        :param end: str, 回测结束时点，fmt="%Y-%m-%d".
        :param freq: str, 回测频率，"D", "W", "M", "H".
        :param rebalance_h: int, 适用于"H"频率下，调仓间隔K线个数.
        """
        self._start = start
        self._end = end
        self._freq = freq
        self._calendar = calendar
        self._rebalance_h = rebalance_h

    @property
    def start(self):
        """
        回测开始时间.
        """
        return self._start

    @property
    def end(self):
        """
        回测结束时间.
        """
        return self._end

    @property
    def calendar(self):
        """
        回测结束时间.
        """
        return self._calendar

    @property
    def freq(self):
        """
        回测频率.
        """
        return self._freq

    @property
    def rebalance_h(self):
        """
        特别针对"H"为基本K线，持仓K线数.
        """
        return self._rebalance_h

    def get_backtest_dates(self):
        """返回对应回测频率的重新回测日期"""
        seq_dict = {
            "M": lambda x: self.get_seq_m(*x),
            "W": lambda x: self.get_seq_w(*x),
            "D": lambda x: self.get_seq_d(*x),
            "H": lambda x: self.get_seq_h(*x)
        }
        return seq_dict[self._freq]((self._start, self._end))

    def get_eval_dates(self, ref_seq):
        """
        返回对应回测频率的rebalance后持仓收益评估日期.

        :param ref_seq: list,确定调仓日期list，由get_seq_*函数返回值.

        :return: list, 评估持仓.
        """
        seq_dict = {
            "M": lambda x: self._eval_seq_m(x),
            "W": lambda x: self._eval_seq_w(x),
            "D": lambda x: self._eval_seq_d(x),
            "H": lambda x: self._eval_seq_h(x)
        }
        return seq_dict[self._freq](ref_seq)

    def get_backtest_first_date(self, num_d):
        """
        返回第一次回测所需要提取数据的最早日期.

        .. deprecated:: v.6.0.3
           Use :func:`Mkv_data2.get_nearest_hrange` instead.

        :param num_d: 估计组合收益率统计量所需K线个数.

        :return: str, 开始时间.
        """
        if not w.isconnected():
            w.start()
            sleep(3)
        first = w.tdaysoffset(-(num_d - 1), self._start, f"TradingCalendar={self.calendar}").Data[0][0].strftime("%Y-%m-%d")
        return first

    def get_seq_m(self, start, end):
        """
        根据开始时间和结束时间，返回频率为“M"的回测任务确定新仓位时间list.

        :param start: str, 开始时间.
        :param end: str, 结束时间.

        :return: list, 计算下期仓位各时点list。
                """
        if not w.isconnected():
            w.start()
            sleep(3)
        # 将时间后推一个月
        end = (datetime.strptime(end, "%Y-%m-%d") + relativedelta(months=1)).strftime("%Y-%m-%d")
        # seq = w.tdays(start, end, f"Period=M;TradingCalendar={self.calendar}").Data[0]
        # 转换为使用工作日
        seq = w.tdays(start, end, "Period=M;Days=Weekdays").Data[0]
        seq = [(seq[ii].strftime("%Y-%m-%d"), ii) for ii in range(len(seq))]
        return seq[:-1]

    def get_seq_w(self, start, end):
        """
        根据开始时间和结束时间，返回频率为“W"的回测任务确定新仓位时间list.

        :param start: str, 开始时间.
        :param end: str, 结束时间.

        :return: list, 计算下期仓位各时点list。
        """
        if not w.isconnected():
            w.start()
            sleep(3)
        # wind的w.tdays函数准确性较差，需要严格检验
        # seq = w.tdays(start, end, f"Period=W;TradingCalendar={self.calendar}").Data[0]
        # 转换为工作日
        seq = w.tdays(start, end, "Period=W;Days=Weekdays").Data[0]
        if seq[-1].weekday() != 4:
            seq.pop()
        seq = [dd.strftime("%Y-%m-%d") for dd in seq]
        month = []
        seq_ = []
        for ss in seq:
            if ss[0:7] not in month:
                # 只有在新月份出现时才可能出现更新
                month.append(ss[0:7])
                seq_.append((ss, len(month)-1))
            else:
                seq_.append((ss, 0.5))
        return seq_

    def get_seq_d(self, start, end):
        """
        根据开始时间和结束时间，返回频率为“D"的回测任务确定新仓位时间list.

        :param start: str, 开始时间.
        :param end: str, 结束时间.

        :return: list, 计算下期仓位各时点list。
        """
        if not w.isconnected():
            w.start()
            sleep(3)
        # 日频级别暂时不变更为工作日日历，对于假期造成的不交易，当天仓位无法变更
        seq = w.tdays(start, end, f"TradingCalendar={self.calendar}").Data[0]
        seq = [dd.strftime("%Y-%m-%d") for dd in seq]
        month = []
        seq_ = []
        for ss in seq:
            if ss[0:7] not in month:
                # 只有在新月份出现时才可能出现更新
                month.append(ss[0:7])
                seq_.append((ss, len(month) - 1))
            else:
                seq_.append((ss, 0.5))
        return seq_

    def get_seq_h(self, start, end):
        """
        根据开始时间和结束时间，返回频率为“H"的回测任务确定新仓位时间list.

        :param start: str, 开始时间.
        :param end: str, 结束时间.

        :return: list, 计算下期仓位各时点list。
        """
        if not w.isconnected():
            w.start()
            sleep(3)
        seq = w.tdays(start, end, f"TradingCalendar={self.calendar}").Data[0]
        seq = [dd.strftime("%Y-%m-%d ") for dd in seq]
        seqq = []
        hh = HOUR_BAR
        for d in seq:
            seqq.extend([d+h for h in hh])
        # 为了使持仓周期尽量在同天
        # debug: 不能直接用start向前推，因为start当天可能不是交易日，应当用seq[0]
        dd_ahead = w.tdaysoffset(-1, seq[0], f"TradingCalendar={self.calendar}").Data[0][
            0].strftime(
            "%Y-%m-%d 14:00:00")
        seqq = [dd_ahead] + seqq
        seq = self._skip_extract(seq=seqq, skip=self.rebalance_h)
        month = []
        seq_ = []
        for ss in seq:
            if ss[0:7] not in month:
                # 只有在新月份出现时才可能出现更新
                month.append(ss[0:7])
                seq_.append((ss, len(month) - 1))
            else:
                seq_.append((ss, 0.5))
        return seq_

    def _eval_seq_h(self, seq_h):
        if not w.isconnected():
            w.start()
            sleep(3)
        seq = seq_h.copy()
        seq.pop(0)
        last = seq[-1]
        next_ = self._get_next_hourly_eval_time_stamp(last_t=last, skip=self.rebalance_h)
        seq.append(next_)
        return seq

    def _eval_seq_d(self, seq_d):
        if not w.isconnected():
            w.start()
            sleep(3)
        seq = seq_d.copy()
        seq.pop(0)
        last = seq[-1]
        next_ = w.tdaysoffset(1, last, f"TradingCalendar={self.calendar}").Data[0][0].strftime(
            "%Y-%m-%d")
        seq.append(next_)
        return seq

    def _eval_seq_w(self, seq_w):
        if not w.isconnected():
            w.start()
            sleep(3)
        seq = seq_w.copy()
        seq.pop(0)
        last = seq[-1]
        tail = (datetime(*map(int, last.split("-"))) +
                relativedelta(months=1)).strftime("%Y-%m-%d")
        # next_ = w.tdays(last, tail, f"Period=W;TradingCalendar={self.calendar}").Data[0][
        #     1].strftime("%Y-%m-%d")
        # 转变为工作日
        # NOTE：之所以取序列的第二个时间，是因为last本身是周五，在序列中会被包含进去，tail是向后一个月的日期，序列第二个日期就是last的下一个周五
        next_ = w.tdays(last, tail, "Period=W;Days=Weekdays").Data[0][
            1].strftime("%Y-%m-%d")
        seq.append(next_)
        return seq

    def _eval_seq_m(self, seq_m):
        if not w.isconnected():
            w.start()
            sleep(3)
        seq = seq_m.copy()
        seq.pop(0)
        last = seq[-1]
        tail = (datetime(*map(int, last.split("-")[:2]), 1) +
                relativedelta(months=2)).strftime("%Y-%m-%d")
        # next_ = w.tdays(last, tail, "Period=M", f"TradingCalendar={self.calendar}").Data[0][1].strftime("%Y-%m-%d")
        # 转变为工作日
        next_ = w.tdays(last, tail, "Period=M;Days=Weekdays").Data[0][
            1].strftime("%Y-%m-%d")
        seq.append(next_)
        return seq

    @staticmethod
    def _skip_extract(seq, skip, include_head=True):
        """
        helper func,用于间隔提取数据list后，返回新list.

        :param seq: list,原完整序列.
        :param skip: int,间隔元素数.

        :return: list,提取后的数据.
        """
        new_seq = []
        assert isinstance(skip, int), \
            "ParameterError: 'skip' supposed to be a non-negative integer"
        len_seq = len(seq)
        if skip == 0:
            if include_head:
                seq.pop(0)
            return seq
        max_ = len_seq // skip
        for mm in range(max_+1):
            new_seq.append(seq[mm*skip])
        assert len(new_seq) == max_ + 1, \
            "Debug: the length of outcome may not be correct"
        if not include_head:
            new_seq.pop(0)
        return new_seq

    def _get_next_hourly_eval_time_stamp(self, last_t, skip):
        """
        helper func,用于从最后一个调仓时间点，推得最后一个评估持仓收益的eval时间点.

        :param last_t: str,最后一期调仓时间点，fmt="%Y-%m-%d H:M:S".
        :param skip: int,回测间隔小时K线个数.

        :return: str, 最后一期评估持仓收益率的字符串.
        """
        bar_nums = len(HOUR_BAR)
        dd, hh = last_t.split(" ")
        hh_idx = HOUR_BAR.index(hh)
        dd_plus, hh_idx_new = divmod(skip + hh_idx, bar_nums)
        if dd_plus == 0:
            dd_new = dd
        else:
            if not w.isconnected():
                w.start()
            dd_new = w.tdaysoffset(dd_plus, dd, f"TradingCalendar={self.calendar}").Data[0][0].strftime("%Y-%m-%d")
        last_eval = " ".join([dd_new, HOUR_BAR[hh_idx_new]])
        return last_eval
