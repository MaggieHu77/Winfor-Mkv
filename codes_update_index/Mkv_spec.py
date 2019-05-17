# -*- coding:utf-8 -*-
# ! python3

from WindPy import w
from Mkv_constant import *
import pandas as pd
import re


class MkvSpec:
    field = "sectorconstituent"

    def __init__(self, spec, basic_indices, ics_indices, ics, ics_fv, ics_rank, mode="run",
                 check_w=False):
        self._date = ""
        self._spec = spec
        self.basic_indices = basic_indices
        self.ics_indices = ics_indices
        self.ics = ics
        self.ics_fv = ics_fv
        self.ics_rank = ics_rank
        self._codes = []
        self._fields = None
        self._spec_id = []
        self._names = []
        self.df_all = None
        self.df_filter = None
        self.pool_codes = None
        self.print_obj = PrintOnce()
        if mode == "test":
            self._flag = True
        else:
            self._flag = False
        if check_w:
            if not w.isconnected():
                w.start()
        self.check_spec_id()

    def gen_spec_param(self, id):
        """
        为w.wset函数提供输入参数字段
        要求两个参数:
        field固定为"sectorconstituent"
        options为"date"和"sctorid"以";"连接成的字符串
        :param id: 需要获取股票成分的控件代码
        :return: field, options
        """
        opt = "date={};sectorid={};field=wind_code,sec_name".format(self._date, id)
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
        options = f"tradeDate={self._date};industryType=2;unit=1;days=-30;currencyType=;rptDate={self.rpt_date}"
        fields_alias = []
        parses_ = dict()
        for ff in fields:
            alias_ = FIELDS_ALIAS_DICT.get(ff, 0)
            if alias_:
                fields_alias.append(alias_)
                parses_.update({alias_: parses[ff]})
            else:
                self.print_obj(f"Warning: 参数basic_indices字段中{ff}不在程序默认字典内，推断是用户自选指标，请谨慎确认输入合法性")
                fields_alias.append(ff)
                parses_.update({ff: parses[ff]})
        return fields_alias, parses_, options

    def fields_parse(self, indices):
        """
        获得基本面筛选变量及其对应条件
        :return: a list-->基本面指标字段, a list-->每个元素为a tuple->(field, operator, number)
        eg. [(pe, ">=", 18), (roe, ">", 0.05)]
        """
        indices = indices.replace(" ", "")
        fields_ = [f.strip(" ") for f in indices.split(";")]
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
        # 由于回测期间公用一个spec object，需要在每次更新股票池的时候清空上一次的记录
        self._codes = []
        self._names = []
        assert self._spec_id, "need to call check_spec_id() to get spec id in WindPy"
        for id in self._spec_id:
            res = w.wset(*self.gen_spec_param(id)).Data
            self._codes.extend(res[0])
            self._names.extend(res[1])
        # 配对后去重
        res_ = dict(zip(self._codes, self._names))
        self._codes = list(res_.keys())
        self._names = list(res_.values())
        return res_

    def get_industry_df(self):
        ind = w.wss(self._codes, self.ics,
              f"tradeDate={self._date};industryType=2").Data[0]
        self.df_filter = pd.DataFrame(ind, index=self._codes, columns=["INDUSTRY"])

    def get_basic_fields(self, industry, _codes):
        fields, parses = self.fields_parse(self.ics_indices[industry.replace(" ", "")])
        fields, parses, options = self.gen_fields_param(fields, parses)
        if not _codes:
            return pd.DataFrame([])
        res = w.wss(_codes, fields, options)
        columns = res.Fields
        content = dict(zip(columns, res.Data))
        df_all = pd.DataFrame(content, index=_codes)
        filter_str = "&".join([f"({ff.upper()} {parses[ff][0]} {parses[ff][1]})" for ff in fields])
        # 初步筛选
        df_filter = df_all.query(filter_str)
        # exec(f'df_filter = df_all[{filter_str}]')
        return df_filter

    def get_basic_fields_v2(self, industry, _codes):
        fields, parses = self.fields_parse(self.ics_indices[industry.replace(" ", "")])
        fields, parses, options = self.gen_fields_param(fields, parses)
        df_filter = pd.DataFrame([], index=_codes)
        for ff in fields:
            if not _codes:
                return df_filter
            res = w.wss(_codes, ff, options)
            columns = res.Fields
            # content = dict(zip(columns, res.Data))
            df_filter[columns[0]] = res.Data[0]
            filter_str = f"({ff.upper()} {parses[ff][0]} {parses[ff][1]})"
            # 初步筛选
            df_filter = df_filter.query(filter_str)
            _codes = df_filter.index.tolist()
        # exec(f'df_filter = df_all[{filter_str}]')
        return df_filter

    def industry_filter(self):
        # 取出对应二级行业数据
        # 确保行业内排序变量已被提取
        # 二级行业内进行分组
        self.df_filter_group = self.df_filter.groupby("INDUSTRY")
        self.pool_codes = []
        for ii, tb in self.df_filter_group:
            icodes = tb.index.tolist()
            idf = self.get_basic_fields(industry=ii, _codes=icodes)

            print(f"{ii}:{idf.shape[0]}")
            if not idf.shape[0]:
                continue
            if self.ics_fv not in idf.columns:
                ics_fv = w.wss(idf.index.tolist(), [self.ics_fv],
                      f"tradeDate={self._date};"
                      f"industryType=2;unit=1;days=-30;currencyType=;rptDate={self.rpt_date}").Data[0]
                idf[self.ics_fv.upper()] = ics_fv
            if isinstance(self.ics_rank, int):
                ids = idf.sort_values(self.ics_fv.upper(),
                ascending=False).head(self.ics_rank).index.tolist()
            elif isinstance(self.ics_rank, list):
                rank_ = list(filter(lambda x: x <= idf.shape[0]-1, self.ics_rank))
                ids = idf.sort_values(self.ics_fv.upper(),
                                     ascending=False).iloc[rank_,].index.tolist()
            else:
                h, t = self.ics_rank
                if h < idf.shape[0]:
                    ids = idf.sort_values(self.ics_fv.upper(),
                                         ascending=False).iloc[h:min(t, idf.shape[0]),
                          ].index.tolist()
                else:
                    ids = []
            self.pool_codes.extend(ids)
        self.pool_codes = list(set(self.pool_codes))
        print(f"%本次更新获得{len(self.pool_codes)}只股票进入组合权重优化")
        return self.pool_codes

    def industry_filter_v2(self):
        # 取出对应二级行业数据
        # 确保行业内排序变量已被提取
        # 二级行业内进行分组
        self.df_filter_group = self.df_filter.groupby("INDUSTRY")
        self.pool_codes = []
        for ii, tb in self.df_filter_group:
            icodes = tb.index.tolist()
            idf = self.get_basic_fields_v2(industry=ii, _codes=icodes)
            # print("初步筛选后行业分布")
            print(f"{ii}:{idf.shape[0]}")
            if not idf.shape[0]:
                continue
            if self.ics_fv not in idf.columns:
                ics_fv = w.wss(idf.index.tolist(), [self.ics_fv],
                      f"tradeDate={self._date};"
                      f"industryType=2;unit=1;days=-30;currencyType=;rptDate={self.rpt_date}").Data[0]
                idf[self.ics_fv.upper()] = ics_fv
            if isinstance(self.ics_rank, int):
                ids = idf.sort_values(self.ics_fv.upper(),
                ascending=False).head(self.ics_rank).index.tolist()
            elif isinstance(self.ics_rank, list):
                rank_ = list(filter(lambda x: x <= idf.shape[0]-1, self.ics_rank))
                ids = idf.sort_values(self.ics_fv.upper(),
                                     ascending=False).iloc[rank_,].index.tolist()
            else:
                h, t = self.ics_rank
                if h < idf.shape[0]:
                    ids = idf.sort_values(self.ics_fv.upper(),
                                         ascending=False).iloc[h:min(t, idf.shape[0]),
                          ].index.tolist()
                else:
                    ids = []
            self.pool_codes.extend(ids)
        self.pool_codes = list(set(self.pool_codes))
        print(f"%本次更新获得{len(self.pool_codes)}只股票进入组合权重优化")
        return self.pool_codes


    def check_spec_id(self):
        for ss in self._spec:
            if ss.upper() in SET_ID_DICT.keys():
                self._spec_id.append(SET_ID_DICT[ss.upper()])
            elif ss[0] in ["1", "a"]:
                print(f"Warning: global_spec参数输入{ss.upper()}不在程序默认范围内，推断为用户自定义输入Wind对应版块代码；"
                      f"尝试获取板块成分")
            else:
                print(f"Warning: global_spec参数输入{ss.upper()}暂不支持，已忽略")
        if not self._spec_id:
            self._spec_id.append(SET_ID_DICT["A_SHARE"])
            print(f"Warning:global_spec参数输入未检测到支持的股票空间字段；应用默认参数'全部A股'；"
                  f"请检查您的输入或查询文档了解支持的股票空间字段，以获得正确结果。")
        # if self._spec not in SET_ID_DICT.keys():
        #     self._spec_id = SET_ID_DICT.get(self._spec, SET_ID_DICT["A_SHARE"])
        # else:
        #     self._spec_id = SET_ID_DICT.get(self._spec)
        printt(self._spec_id, self._flag)
        return self._spec_id

    def get_current_codes(self, trade_date):
        self.reset_date(trade_date)
        self.get_spec()
        self.get_industry_df()
        # return self.industry_filter()
        return self.industry_filter_v2()

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


class PrintOnce(object):
    global_counter = 0

    def __call__(self, msg):
        if self.global_counter == 0:
            print(msg)
            self.global_counter += 1

    def reset_counter(self):
        self.global_counter = 0