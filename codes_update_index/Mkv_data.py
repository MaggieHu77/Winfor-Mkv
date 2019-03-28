# -*- coding:utf-8 -*-
# ! python3
from WindPy import w
from Mkv_constant import *
from datetime import datetime
import numpy as np
from scipy.sparse import lil_matrix
from nearPD import nearestPD


class Stock:
    def __init__(self, code, name, mkt):
        """
        设定股票基本信息
        :param code: 股票WIND代码
        :param name: 股票名称
        :param mkt: 股票上市交易的交易所
        """
        self.code = code
        self.name = name
        self.mkt = mkt
        self.r = []
        self.t = []

    def input_return(self, rts):
        """
        设定股票历史日收益率
        :param rts:
        :return:
        """
        self.r = rts

    def input_time(self, time):
        """
        设定股票日收益率日期
        :param time:
        :return:
        """
        self.t = time


def create_stocks(codes, num_d, end=datetime.now().strftime("%Y-%m-%d"), q=True):
    """
    提取样本收益率
    :param codes: 股票代码列表
    :param num_d: 数据日期长度
    :return:
    """
    stocks = []
    today = datetime.now().strftime("%Y-%m-%d")
    if not w.isconnected():
        w.start()
    if q:
        fd = w.tdaysoffset(-(num_d - 1), today).Data[0][0]
        td = w.tdaysoffset(-1, today).Data[0][0]
        res11, res12 = w.wss(",".join(codes), STOCK_SEC).Data
        res2 = w.wsd(",".join(codes), "pct_chg", fd, td)
        res3 = w.wsq(",".join(codes), "rt_pct_chg").Data[0]
        for c in range(len(codes)):
            stocks.append(Stock(codes[c], res11[c], res12[c]))
            stocks[c].input_return([round(r / 100, 4) if not np.isnan(r) else 0.0 for r in res2.Data[c]])
            stocks[c].input_time([t.strftime("%Y-%m-%d") for t in res2.Times])
            res3[c] = round(res3[c], 4)
            stocks[c].r.append(res3[c])
            stocks[c].t.append(today)
    else:
        fd = w.tdaysoffset(-(num_d - 1), end).Data[0][0]
        td = end
        res11, res12 = w.wss(",".join(codes), STOCK_SEC).Data
        res2 = w.wsd(",".join(codes), "pct_chg", fd, td)
        for c in range(len(codes)):
            stocks.append(Stock(codes[c], res11[c], res12[c]))
            stocks[c].input_return([round(r / 100, 4) if not np.isnan(r) else 0.0 for r in res2.Data[c]])
            stocks[c].input_time([t.strftime("%Y-%m-%d") for t in res2.Times])
    return stocks


def calc_params(stocks, cash_r):
    """
    计算均值向量，协方差矩阵
    :param stocks:
    :return:
    """
    param = dict()
    n = len(stocks)
    mtx_r = [s.r for s in stocks]
    mu = list(np.mean(mtx_r, axis=1).round(4))
    # mtx_r.append([cash_r] * len(mtx_r[0]))
    cov = np.cov(mtx_r)
    # 检验半正定性
    eig = np.linalg.eigvals(cov)
    issd = bool(np.all(eig >= 0))
    print("风险资产矩阵是否半正定?" + str(issd))

    # # 如果不通过正定性检验，需要进行remedy
    if not issd:
        cov_pd = nearestPD(cov)
    #     eigv, eigc = np.linalg.eig(cov)
    #     eigv = [v if v >= 0 else 0 for v in eigv]  # 如果有负的特征值，设为零
    #     cov = np.matmul(np.matmul(eigc, np.diag(eigv)), eigc.T)
    #     issdp = bool(np.all(np.linalg.eigvals(cov) >= 0))
    else:
        cov_pd = np.copy(cov)
    cov1 = np.zeros((2 * len(stocks), 2 * len(stocks)))
    cov1[:len(stocks), :len(stocks)] = cov_pd
    eig1 = np.linalg.eigvals(cov1)
    issd1 = bool(np.all(eig1 >= 0))
    print("扩展矩阵是否半正定?" + str(issd1))
    # cov_pd = nearestPD(cov)
    q = lil_matrix(cov1)
    q_data = q.data
    q_rows = q.rows
    qsubi = []
    qsubj = []
    qval = []
    for i in range(len(q_rows)):
        for j in range(len(q_rows[i])):
            if q_rows[i][j] <= i:
                qsubi.append(i)
                qsubj.append(q_rows[i][j])
                qval.append(q_data[i][j])
    param.update({"numvar": n, "mu": mu, "qsubi": qsubi, "qsubj": qsubj, "qval": qval})
    cov_init = np.zeros((cov.shape[0]+1, cov.shape[1]+1))
    cov_init[:cov.shape[0], :cov.shape[1]] = cov
    param.update({'cov': cov_init})
    return param