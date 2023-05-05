'''
Author: zhiyong.liang zhiyong.liang@stardust.ai
Date: 2023-05-05 19:02:15
'''
import datetime

class DatetimeUtils:

    @staticmethod
    def now():
        return datetime.datetime.now()

    @staticmethod
    def format(date, format="%Y-%m-%d %H:%M:%S"):
        return date.strftime(format)