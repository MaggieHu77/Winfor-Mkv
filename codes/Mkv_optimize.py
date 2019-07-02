# -*- coding:utf-8 -*-
# ! python3
import mosek
from Mkv_constant import *


def optimizer(param):
    """
        计算组合优化权重.

        .. deprecated:: v0.6.3
           Use :func: `Mkv_optimize2.optimizer` instead.

        '' seealso:: modules :py:mod:`Mkv_optimize`.

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
                numcon = NUMCON + 2 * param["numvar"]
                task.appendcons(numcon)
                task.appendvars(numvar)
                c = c + [0.0] * param["numvar"]
                if param["up"] < DEFAULT_UP:
                    bkx = [mosek.boundkey.ra] * numvar
                    blx = [-param["up"]] * int(numvar/2) + [0.0] * int(numvar/2)
                    bux = [param["up"]] * numvar
                else:
                    bkx = [mosek.boundkey.fr] * int(numvar/2) + [mosek.boundkey.lo] * int(numvar/2)
                    blx = [inf] * int(numvar/2) + [0.0] * int(numvar/2)
                    bux = [inf] * numvar

                # 约束条件类型
                bkc = [mosek.boundkey.up] + [mosek.boundkey.lo] * numvar + [mosek.boundkey.up]
                blc = [inf, inf] + [0.0] * numvar
                buc = [1.0] + [inf] * numvar + [param["vol"] ** 2 / 2]
                # 需要改线性约束条件的矩阵
                asub = [[2*k+1, 2*k+2] for k in range(int(numvar/2))] + \
                       [[0, 2*k+1, 2*k+2] for k in range(int(numvar/2))]
                aval = [[1.0, -1.0]] * int(numvar/2) + [[1.0, 1.0, 1.0]] * int(numvar/2)
                for j in range(numvar):
                    task.putcj(j, c[j])
                    task.putbound(mosek.accmode.var, j, bkx[j], blx[j], bux[j])
                    task.putacol(j, asub[j], aval[j])
                for i in range(numcon):
                    task.putbound(mosek.accmode.con, i, bkc[i], blc[i], buc[i])
                task.putqconk(23, param["qsubi"], param["qsubj"], param["qval"])
                task.putobjsense(mosek.objsense.maximize)
                task.optimize()
                solsta = task.getsolsta(mosek.soltype.itr)
                task.solutionsummary(mosek.streamtype.msg)
                xx = [0.] * numvar
                task.getxx(mosek.soltype.itr, xx)
                if solsta == mosek.solsta.optimal or solsta == mosek.solsta.near_optimal:
                    print("%获得最优解")
                    print(f"wi:{xx[:int(numvar/2)]}")
                    print(f"ui:{xx[int(numvar/2):]}")
                    return xx[:int(numvar/2)] + [1 - sum(xx[int(numvar/2):])]
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




