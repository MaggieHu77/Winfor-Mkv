# -*- coding:utf-8 -*-
# ! python3
import mosek
from Mkv_constant import *


def optimizer(param):
    """
    计算组合优化权重.

    :param param: dict，优化算法所需要的参数.

    :return: 包含现金持仓的各个资产权重.
    """
    with mosek.Env() as env:
        with env.Task() as task:
            inf = 0.0
            # 目标函数系数
            c = [r - param["cash_r"] for r in param["mu"]]
            # 控制变量约束
            if param["short"]:
                numvar = 2 * param["numvar"]
                numcon = NUMCON
                task.appendcons(numcon)
                task.appendvars(numvar)
                c = c + [-ci for ci in c]
                if param["up"] < DEFAULT_UP:
                    bkx = [mosek.boundkey.ra] * numvar
                    blx = [0.0] * numvar
                    bux = [param["up"]] * numvar
                else:
                    bkx = [mosek.boundkey.lo] * numvar
                    blx = [0.0] * numvar
                    bux = [inf] * numvar

                # 约束条件类型
                bkc = [mosek.boundkey.up, mosek.boundkey.up]
                blc = [inf, inf]
                buc = [1.0] + [param["vol"] ** 2 / 2]
                # 需要改线性约束条件的矩阵
                asub = [[0]] * numvar
                aval = [[1.0]] * numvar
                for j in range(numvar):
                    task.putcj(j, c[j])
                    task.putbound(mosek.accmode.var, j, bkx[j], blx[j], bux[j])
                    task.putacol(j, asub[j], aval[j])
                for i in range(numcon):
                    task.putbound(mosek.accmode.con, i, bkc[i], blc[i], buc[i])
                task.putqconk(1, param["qsubi"], param["qsubj"], param["qval"])
                task.putobjsense(mosek.objsense.maximize)
                task.optimize()
                solsta = task.getsolsta(mosek.soltype.itr)
                task.solutionsummary(mosek.streamtype.msg)
                xx = [0.] * numvar
                task.getxx(mosek.soltype.itr, xx)
                if solsta == mosek.solsta.optimal or solsta == mosek.solsta.near_optimal:
                    print("%获得最优解")
                    print(f"wi+:{xx[:int(numvar/2)]}")
                    print(f"wi-:{xx[int(numvar/2):]}")
                    w = list(map(lambda x, y: x-y, xx[:int(numvar/2)], xx[int(numvar/2):]))
                    wc = 1-sum([abs(wi) for wi in w])
                    w += [wc]
                    return w
                else:
                    print("%获取最优解失败")
                    return [0.] * (numvar/2 + 1)
            else:
                # 不包含现金
                numvar = param["numvar"]
                numcon = NUMCON
                task.appendcons(numcon)
                task.appendvars(numvar)
                if param["up"] < DEFAULT_UP:
                    bkx = [mosek.boundkey.ra] * numvar
                    blx = [0.0] * numvar
                    bux = [param["up"]] * numvar
                else:
                    bkx = [mosek.boundkey.lo] * numvar
                    blx = [0.0] * numvar
                    bux = [inf] * numvar

                # 约束条件类型
                bkc = [mosek.boundkey.up, mosek.boundkey.up]
                blc = [inf, inf]
                buc = [param["vol"] ** 2 / 2, 1.0]
                asub = [[1]] * numvar
                aval = [[1.0]] * numvar
                for j in range(numvar):
                    task.putcj(j, c[j])
                    task.putbound(mosek.accmode.var, j, bkx[j], blx[j], bux[j])
                    task.putacol(j, asub[j], aval[j])
                for i in range(numcon):
                    task.putbound(mosek.accmode.con, i, bkc[i], blc[i], buc[i])
                task.putqconk(0, param["qsubi"], param["qsubj"], param["qval"])
                task.putobjsense(mosek.objsense.maximize)
                task.optimize()
                solsta = task.getsolsta(mosek.soltype.itr)
                task.solutionsummary(mosek.streamtype.msg)
                xx = [0.] * numvar
                task.getxx(mosek.soltype.itr, xx)
                if solsta == mosek.solsta.optimal or solsta == mosek.solsta.near_optimal:
                    print("%获得最优解")
                    # print(f"-constrains violation in optimal:{pviolcon}")
                    return xx + [1 - sum(xx)]
                else:
                    print("%获取最优解失败")
                    return [0.] * (numvar + 1)




