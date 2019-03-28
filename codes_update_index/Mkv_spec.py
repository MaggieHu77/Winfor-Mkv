# -*- coding:utf-8 -*-
# ! python3

from WindPy import w
from Mkv_constant import *
import pandas as pd
import re



class MkvSpec:
    field = "sectorconstituent"

    def __init__(self, spec, mode="run", check_w=False):
        self._date = ""
        self._spec = spec.upper()
        self._codes = None
        self._fields = None
        self._spec_id = None
        self._names = None
        if mode == "test":
            self._flag = True
        else:
            self._flag = False
        if check_w:
            if not w.isconnected():
                w.start()

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

    def gen_fields_param(self, fields):
        """
        为w.wss生成需要的输入参数字段，并检验该输入字段是否被系统支持
        需要参数为：

        codes:可以是list或者以","连接的字符串
        fields:可以是list或者以","连接的字符串，包含需要提取的基本面指标字段
        options:其他与指标相关的参数设定
        :param fields: list，包含用户输入的基本面指标字段
        :return: fields, options
        """
        rpt_date = get_rpt_date(self._date)
        options = f"tradeDate={self._date};industryType=2;unit=1;currencyType=;rptDate={rpt_date}"
        fields_alias = []



    def fields_parse(self, basic_indices):
        """
        获得基本面筛选变量及其对应条件
        :param basic_indices: 包含所有基本面指标和对应筛选条件的字符串，不同指标之间用;分隔
        :return: a list-->基本面指标字段, a list-->每个元素为a tuple->(field, operator, number)
        eg. [(pe, ">=", 18), (roe, ">", 0.05)]
        """
        basic_indices = basic_indices.replace(" ", "")
        fields_ = [f.strip(" ") for f in basic_indices.split(";")]
        parses = []
        fields = []
        for ff in fields_:
            res = re.search("([^>=<]*)([><=]*)([\d.]*)", ff)
            assert len(res.groups()) == 3, \
                f"fields parsing loss critical components in '{ff}', expect 3, get {len(res.groups())}"
            parses.append((res[1], res[2], res[3]))
            fields.append(res[1].lower())
        printt(parses, flag=self._flag)
        return fields, parses

    def get_spec(self):
        res = w.wset(*self.gen_spec_param()).Data[1:]
        self._codes = res[0]
        return res

    def get_spec_df(self):
        self._codes, self._names = self.get_spec()
        df = pd.DataFrame([self._codes, self._names], columns=["codes", "names"])
        return df

    def get_basic_fields(self, basic_indices):
        fields, parses = self.fields_parse(basic_indices)
        self.gen_fields_param(fields)
        res = w.wss(self._codes, fields, )

    def check_spec_id(self):
        if self._spec not in SET_ID_DICT.keys():
            self._spec_id = SET_ID_DICT.get(self._spec, SET_ID_DICT["A_SHARE"])
        else:
            self._spec_id = SET_ID_DICT.get(self._spec)
        printt(self._spec_id, self._flag)
        return self._spec_id

    def get_current_codes(self, trade_date):
        self.reset_date(trade_date)
        pass

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