'''
Author: zhiyong.liang zhiyong.liang@stardust.ai
Date: 2023-04-19 13:33:11
'''
from sqlalchemy import Column, BigInteger, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class DialogInfo(Base):
    __tablename__ = 'dialog_info'

    id = Column(BigInteger, primary_key=True, comment='ID')
    user_id = Column(BigInteger, nullable=False, comment='用户 ID')
    dialog_name = Column(String(64), nullable=False, comment='对话名称')
    created_time = Column(TIMESTAMP, nullable=False,
                          server_default='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', comment='对话创建时间')

    def create_new_dialog():
        pass