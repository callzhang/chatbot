'''
Author: zhiyong.liang zhiyong.liang@stardust.ai
Date: 2023-04-19 13:33:11
'''
from sqlalchemy import Column, BigInteger, TIMESTAMP, Integer, String
from sqlalchemy.orm import declarative_base

from infrastructure.database.database import Database

Base = declarative_base()


class UserInfo(Base):
    __tablename__ = 'user_info'

    id = Column(BigInteger, primary_key=True,
                autoincrement=True, comment='ID;系统内查询主键,并不对外暴漏')
    status = Column(Integer, nullable=False, comment='状态;-1：删除、0:冻结、1:启用')
    username = Column(String(200), comment='用户名')
    phone = Column(BigInteger, comment='手机号')
    salt = Column(String(32), comment='盐值')
    password = Column(String(255), comment='密码')
    email = Column(String(40), comment='邮箱')
    real_name = Column(String(32), nullable=False,
                       server_default='', comment='真实姓名')
    register_time = Column(TIMESTAMP, nullable=False,
                           server_default='CURRENT_TIMESTAMP', comment='注册时间')

    """
    根据real_name查询用户详情
    """

    def get_user_by_real_name(self, value):
        db = Database()
        return db.query_one(UserInfo, real_name=value)


if __name__ == '__main__':
    user_info = UserInfo()
    result = user_info.get_user_by_real_name('梁智勇')
    if result is not None:
        print(f"ID: {result.id}")
        print(f"用户名: {result.username}")
        print(f"手机号: {result.phone}")
        print(f"真实姓名: {result.real_name}")
