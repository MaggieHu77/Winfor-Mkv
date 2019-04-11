# -*- coding:utf-8 -*-
# ! python3

from WindPy import w
from Mkv_constant import *
import pandas as pd
import re


class MkvSpec:
    field = "sectorconstituent"

    def __init__(self, spec, basic_indices, ics, ics_fv, ics_rank, mode="run", check_w=False):
        self._date = ""
        self._spec = spec.upper()
        self.basic_indices = basic_indices
        self.ics = ics
        self.ics_fv = ics_fv
        self.ics_rank = ics_rank
        self._codes = None
        self._fields = None
        self._spec_id = None
        self._names = None
        self.df_all = None
        self.df_filter = None
        self.pool_codes = None
        if mode == "test":
            self._flag = True
        else:
            self._flag = False
        if check_w:
            if not w.isconnected():
                w.start()
        self.check_spec_id()

    def gen_spec_param(self):
        """
        为w.wset函数提供输入参数字段
        要求两个参数:
        field固定为"sectorconstituent"
        options为"date"和"sctorid"以";"连接成的字符串
        :return: field, options
        """
        assert self._spec_id, "need to call check_spec_id() to get spec id in WindPy"
        opt = "date={};sectorid={}".format(self._date, self._spec_id)
        printt(f"{self.field};{opt}", self._flag)
        return self.field, opt

    def gen_fields_param(self, fields, parses):
        """
        为w.wss生成需要的输入参数字段，并检验该输入字段是否被系统支持
        需要参数为：

        codes:可以是list或者以","连接的字符串
        fields:可以是list或者以","连接的字符串，包含需要提取的基本面指标字段
        options:其他与指标相关的参数设定
        :param fields: list，包含用户输入的基本面指标字段
         :param parses: dict，用户输入基本面指标及对应条件关键词
        :return: fields, options
        """
        self.rpt_date = get_rpt_date(self._date)
        options = f"tradeDate={self._date};industryType=2;unit=1;currencyType=;rptDate={self.rpt_date}"
        fields_alias = []
        parses_ = dict()
        for ff in fields:
            alias_ = FIELDS_ALIAS_DICT.get(ff, 0)
            if alias_:
                fields_alias.append(alias_)
                parses_.update({alias_: parses[ff]})
            else:
                print(f"Warning: 参数basic_indices字段中{ff}不可用，已忽略")
        return fields_alias, parses_, options

    def fields_parse(self):
        """
        获得基本面筛选变量及其对应条件
        :return: a list-->基本面指标字段, a list-->每个元素为a tuple->(field, operator, number)
        eg. [(pe, ">=", 18), (roe, ">", 0.05)]
        """
        basic_indices = self.basic_indices.replace(" ", "")
        fields_ = [f.strip(" ") for f in basic_indices.split(";")]
        parses = {}
        fields = []
        for ff in fields_:
            res = re.search("([^>=<]*)([><=]*)([\d.]*)", ff)
            assert len(res.groups()) == 3, \
                f"fields parsing loss critical components in '{ff}', expect 3, get {len(res.groups())}"
            parses.update({res[1].lower(): (res[2], res[3])})
            fields.append(res[1].lower())
        printt(parses, flag=self._flag)
        return fields, parses

    def get_spec(self):
        res = w.wset(*self.gen_spec_param()).Data[1:]
        self._codes = res[0]
        self._names = res[1]
        return res

    def get_basic_fields(self):
        fields, parses = self.fields_parse()
        fields, parses, options = self.gen_fields_param(fields, parses)
        res = w.wss(self._codes, fields, options)
        columns = res.Fields
        content = dict(zip(columns, res.Data))
        self.df_all = pd.DataFrame(content, index=self._codes)
        filter_str = "&".join([f"(self.df_all.{ff.upper()} {parses[ff][0]} {parses[ff][1]})" for ff in fields])
        # 初步筛选
        exec(f'self.df_filter = self.df_all[{filter_str}]')
        return self.df_filter

    def industry_filter(self):
        # 取出对应二级行业数据
        # 确保行业内排序变量已被提取
        if self.ics_fv not in self.df_filter.columns:
            indus, ics_fv = w.wss(self.df_filter.index.tolist(), [self.ics, self.ics_fv],
                          f"tradeDate={self._date};industryType=2;unit=1;currencyType=;rptDate={self.rpt_date}").Data
            self.df_filter.loc[:, self.ics_fv.upper()] = ics_fv
        else:
            indus = w.wss(self.df_filter.index.tolist(), self.ics,
                          f"tradeDate={self._date};industryType=2").Data[0]
        self.df_filter.loc[:, "INDUSTRY"] = indus
        # 二级行业内进行分组
        self.df_filter_group = self.df_filter.groupby("INDUSTRY")
        self.pool_codes = []
        for _, tb in self.df_filter_group:
            if isinstance(self.ics_rank, int):
                ids = tb.sort_values(self.ics_fv.upper(),
                ascending=False).head(self.ics_rank).index.tolist()
            elif isinstance(self.ics_rank, list):
                rank_ = list(filter(lambda x: x <= tb.shape[0]-1, self.ics_rank))
                ids = tb.sort_values(self.ics_fv.upper(),
                                     ascending=False).iloc[rank_,].index.tolist()
            else:
                h, t = self.ics_rank
                if h < tb.shape[0]:
                    ids = tb.sort_values(self.ics_fv.upper(),
                                         ascending=False).iloc[h:min(t, tb.shape[0]),
                          ].index.tolist()
                else:
                    ids = []
            self.pool_codes.extend(ids)
        self.pool_codes = list(set(self.pool_codes))
        print(f"%本次更新获得{len(self.pool_codes)}只股票进入组合权重优化")
        return self.pool_codes

    def check_spec_id(self):
        if self._spec not in SET_ID_DICT.keys():
            self._spec_id = SET_ID_DICT.get(self._spec, SET_ID_DICT["A_SHARE"])
        else:
            self._spec_id = SET_ID_DICT.get(self._spec)
        printt(self._spec_id, self._flag)
        return self._spec_id

    def get_current_codes(self, trade_date):
        self.reset_date(trade_date)
        self.get_spec()
        self.get_basic_fields()
        return self.industry_filter()

    def reset_date(self, trade_date):
        self._date = trade_date

    @property
    def spec_id(self):
        return self._spec_id

    @property
    def global_codes(self):
        return self._codes

    @property
    def global_names(self):
        return self._names


def printt(content, flag=False):
    """
    use to control whether to print the processing information
    :param content: string to print
    :param flag: if True, print; else close print IO not in development process
    :return:
    """
    if flag:
        print(content)


# helper fuc:求特定交易日期可得财务报表（仅查找年报和半年报）最新报告期
# A股年报最晚披露时间4月底，因此从该年4月份末可读取上年年报
# 中报最晚披露时间8月底，因此从该年8月份末可读取本年度中报
def get_rpt_date(trade_date):
    yy, mm, _ = trade_date.split("-")
    yy = int(yy)
    mm = int(mm)
    if 4 <= mm < 8:
        # 年报披露范围内
        return f"{yy-1}-12-31"
    else:
        return f"{yy}-06-30"