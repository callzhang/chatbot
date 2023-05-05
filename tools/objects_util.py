'''
Author: zhiyong.liang zhiyong.liang@stardust.ai
Date: 2023-05-05 20:27:21
'''

class Objects:

    def check_params(*args):
        for arg in args:
            if arg is None or arg == '':
                return False
        return True