# -*- coding:utf-8 -*-
# ! python3
from WindPy import w
from Mkv_constant import *
from datetime import datetime
import numpy as np
from scipy.sparse import lil_matrix
from nearPD import nearestPD
from time import sleep
import pandas as pd


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
        设定股票历史日(高频部分暂时支持小时)收益率
        :param rts:
        :return:
        """
        self.r = rts

    def input_time(self, time):
        """
        设定股票日收益率（高频支持小时）日期
        :param time:
        :return:
        """
        self.t = time


def create_stocks(codes, num_d, freq, end=datetime.now().strftime("%Y-%m-%d"), q=True):
    """
    提取样本收益率
    :param codes: 股票代码列表
    :param num_d: 数据日期长度
    :return:
    """
    stocks = []
    today = datetime.now().strftime("%Y-%m-%d")
    today_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not w.isconnected():
        w.start()
        sleep(3)
    if freq != "H":
        if q:
            fd = w.tdaysoffset(-(num_d - 1), today).Data[0][0]
            td = w.tdaysoffset(-1, today).Data[0][0]
            res11, res12 = w.wss(",".join(codes), STOCK_SEC).Data
            res2 = w.wsd(",".join(codes), "pct_chg", fd, td)
            res3 = w.wsq(",".join(codes), "rt_pct_chg").Data[0]
            for c in range(len(codes)):
                stocks.append(Stock(codes[c], res11[c], res12[c]))
                stocks[c].input_return(
                    [round(r / 100, 4) if not np.isnan(r) else 0.0 for r in res2.Data[c]])
                stocks[c].input_time([t.strftime("%Y-%m-%d") for t in res2.Times])
                res3[c] = round(res3[c], 4)
                stocks[c].r.append(res3[c])
                stocks[c].t.append(today)
        else:
            fd = w.tdaysoffset(-(num_d - 1), end).Data[0][0]
            td = end
            res = w.wss(",".join(codes), STOCK_SEC).Data
            res11, res12 = res
            # res11, res12 = w.wss(",".join(codes), STOCK_SEC).Data
            res2 = w.wsd(",".join(codes), "pct_chg", fd, td)
            for c in range(len(codes)):
                stocks.append(Stock(codes[c], res11[c], res12[c]))
                stocks[c].input_return(
                    [round(r / 100, 4) if not np.isnan(r) else 0.0 for r in res2.Data[c]])
                stocks[c].input_time([t.strftime("%Y-%m-%d") for t in res2.Times])
    # 小时回测要特殊处理
    else:
        if q:
            # 简化起见，最好使用4的整数倍作为估计均值和方差的窗口长度
            fd, td = get_nearest_hrange(now=today_now, num_h=num_d)
            # w.wsi函数左闭右开
            td = td[:-4] + "1" + td[-3:]
            res11, res12 = w.wss(",".join(codes), STOCK_SEC).Data
            res2 = w.wsi(",".join(codes), "pct_chg", fd, td, "barsize=60")
            res3 = w.wsq(",".join(codes), "rt_pct_chg").Data[0]
            for c in range(len(codes)):
                stocks.append(Stock(codes[c], res11[c], res12[c]))
                stocks[c].input_return(
                    [round(r / 100, 4) if not np.isnan(r) else 0.0 for r in res2.Data[c]])
                stocks[c].input_time([t.strftime("%Y-%m-%d %H:%M:%S") for t in res2.Times])
                res3[c] = round(res3[c], 4)
                stocks[c].r.append(res3[c])
                stocks[c].t.append(today)
        else:
            td = end
            fd, _ = get_nearest_hrange(now=td, num_h=num_d)

            # res11, res12 = w.wss(",".join(codes), STOCK_SEC).Data
            res2 = []
            # 期间可能出现停牌，导致数据缺失
            codes_ = []
            for cc in codes:
                res22 = w.wsi(cc, "pct_chg", fd, td, "barsize=60")
                if res22.ErrorCode != 0:
                    print(f"Warning: {cc}获取小时数据失败，时间{fd}-{td}")
                else:
                    codes_.append(cc)
                    res2.append(pd.DataFrame(res22.Data[0], columns=[cc], index=list(
                        map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"), res22.Times))))
                    # if len(res22.Data[0]) != num_d:
                    #     printt(cc)
            res = w.wss(",".join(codes_), STOCK_SEC).Data
            res11, res12 = res
            for c in range(len(codes_)):
                stocks.append(Stock(codes_[c], res11[c], res12[c]))
                try:
                    # stocks[c].input_return(
                        # [round(r / 100, 4) if not np.isnan(r) else 0.0 for r in res2[c]])
                    stocks[c].input_return(res2[c])
                except Exception as e:
                    print(e)
                    print(codes[c])
                stocks[c].input_time([t.strftime("%Y-%m-%d %H:%M:%S") for t in res22.Times])
    return stocks


def calc_params(stocks, short):
    """
    计算均值向量，协方差矩阵
    :param stocks:
    :return:
    """
    param = dict()
    param.update({"short": short})
    n = len(stocks)
    mtx_r = [s.r for s in stocks]
    mu = list(pd.DataFrame(mtx_r).mean(axis=1).values.round(4))

    # mtx_r.append([cash_r] * len(mtx_r[0]))
    cov = pd.DataFrame(mtx_r).T.cov().values
    # mtx_r = mtx_r.T.values

    if param["short"]:
        # # 如果不通过正定性检验，需要进行remedy
        cov1 = np.cov(np.concatenate((np.array(mtx_r), -np.array(mtx_r))))
        # 检验半正定性
        eig1 = np.linalg.eigvals(cov1)
        issd1 = bool(np.all(eig1 >= 0))
        print("风险资产扩展矩阵是否半正定?" + str(issd1))
        if not issd1:
            cov_pd = nearestPD(cov1)
        #     eigv, eigc = np.linalg.eig(cov)
        #     eigv = [v if v >= 0 else 0 for v in eigv]  # 如果有负的特征值，设为零
        #     cov = np.matmul(np.matmul(eigc, np.diag(eigv)), eigc.T)
        #     issdp = bool(np.all(np.linalg.eigvals(cov) >= 0))
        else:
            cov_pd = np.copy(cov1)
    else:
        eig = np.linalg.eigvals(cov)
        issd = bool(np.all(eig >= 0))
        print("风险资产矩阵是否半正定?" + str(issd))
        if not issd:
            cov_pd = nearestPD(cov)
        else:
            cov_pd = np.copy(cov)

    # cov_pd = nearestPD(cov)
    q = lil_matrix(cov_pd)
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


def get_nearest_hrange(now, num_h):
    dd, hh = now.split(" ")
    ft = max(filter(lambda x: x < hh, ["00"]+HOUR_BAR))
    if ft == "00":
        ft = HOUR_BAR[-1]
        dd_ = w.tdaysoffset(-1, dd).Data[0][0].strftime("%Y-%m-%d")
        idx_t = 0
    else:
        idx_t = HOUR_BAR.index(ft) + 1
        dd_ = dd
    days, idx_h = divmod(num_h-idx_t, 4)
    fh = HOUR_BAR[-idx_h]
    ddh = w.tdaysoffset(-days-int(idx_h > 0), dd).Data[0][0].strftime("%Y-%m-%d")
    return " ".join([ddh, fh]), " ".join([dd_, ft])
