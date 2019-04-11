# -*- coding:utf-8 -*-
# ! python3


from WindPy import w
from Mkv_constant import *
from os import path
from openpyxl import load_workbook
from xlrd import open_workbook
from Mkv_spec import MkvSpec


class BTcodes:

    def __init__(self, input_mode):
        self.input_mode = input_mode
        self.codes = []
        self.target_index = None
        self.global_spec = None
        self.indices = None
        self.ics = None
        self.ics_fv = None
        self.ics_rank = None
        self.refresh_freq = None
        self.spec_obj = None
        if not w.isconnected():
            w.start()

    def set_codes_env(self, params):
        if self.input_mode == 3:
            self.codes.append(read_codes(params["code_file"]))
        elif self.input_mode == 1:
            self.target_index = params["target_index"]
        else:
            self.global_spec = params["global_spec"]
            self.indices = params["basic_indices"]
            self.ics = params["ics"]
            self.ics_fv = params["ics_fv"]
            self.ics_rank = params["ics_rank"]
            self.refresh_freq = int(params["refresh_freq"][0])
            self.spec_obj = MkvSpec(spec=self.global_spec,
                                    mode="run",
                                    basic_indices=self.indices,
                                    ics=self.ics,
                                    ics_fv=self.ics_fv,
                                    ics_rank=self.ics_rank)

    def get_current_codes(self, date, month_id):
        if self.input_mode == 3:
            return self.codes[-1]
        elif self.input_mode == 1:
            codes = w.wset("sectorconstituent",
                           f"date={date};windcode={self.target_index};field=wind_code").Data[0]
            self.codes.append(codes)
        else:
            if month_id % self.refresh_freq == 0:
                print("%更新股票筛选...")
                self.codes.append(self.spec_obj.get_current_codes(trade_date=date))
            else:
                self.codes.append(self.codes[-1])
        return self.codes[-1]


def read_codes(f):
    """
    从文件中读取股票列表
    :param f: 文件路径
    :return: list，包含股票字符串
    """
    b_name = path.basename(f)
    b_type = b_name.split(".")[-1]
    codes = []
    # if b_type == 'xls':
    #     # openpyxl不支持xls格式，先转化为xls
    #     e = wc.gencache.EnsureDispatch('Excel.Application')
    #     wb = e.Workbooks.Open(f)
    #     wb.SaveAs(f + 'x', FileFormat=51)
    #     wb.Close()
    #     e.Application.Quit()
    #     f = f + 'x'
    #     b_type = 'xlsx'
    if b_type == "txt":
        for code in open(f):
            code = code.strip("\n|;|,|/|")
            codes.append(code)
    elif b_type == "xlsx":
        wb = load_workbook(f)
        sheet = wb.active
        for code in list(sheet.columns)[0]:
            if code.value and "." in code.value:
                codes.append(code.value)
    elif b_type == 'xls':
        wb = open_workbook(f)
        sheet = wb.sheet_by_index(0)
        for code in sheet.col_values(0):
            if "." in code:
                codes.append(code)
    else:
        print(f"Error: 不支持的文件格式{b_type}")
    codes = list(set(codes))
    return codes

