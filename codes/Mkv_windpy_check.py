# -*- coding:utf-8 -*-
# ! python3


from WindPy import w
from time import sleep


class WindPyChecker:
    """
    check WindPy API's state and control the start setting
    """
    def __init__(self):
        self.start_flag = self._start_up()

    def _start_up(self):
        start_res = w.start()
        start_code = start_res.ErrorCode
        start_msg = start_res.Data[0]
        if start_code == 0:
            print("## WindPy 启动成功！")
            start_flag = True
        else:
            print("## WindPy 启动失败！")
            print("## 失败信息：%s, 错误代码：%s; 请检查量化接口权限。" % (start_msg, start_code))
            start_flag = False
        return start_flag

    def wait_for_wsi(self, execute=False, wait_sec=5):
        """
        当前版本WindPy w.wsi函数执行前需要在w.start()后冻结若干秒以保障网路连接。

        :param execute: bool, 是否执行sleep操作。
        :param wait_sec: int, sleep的秒数。
        """
        if execute:
            print("## 等待%d secs 以保证分钟数据正常提取..." % wait_sec)
            sleep(wait_sec)
