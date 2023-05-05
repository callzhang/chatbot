'''
Author: zhiyong.liang zhiyong.liang@stardust.ai
Date: 2023-04-19 13:45:46
'''
from sqlalchemy import Column, BigInteger, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ConversationLog(Base):
    __tablename__ = 'conversation_log'

    id = Column(BigInteger(unsigned=True), primary_key=True, autoincrement=True, comment='ID')
    user_id = Column(BigInteger, nullable=False, comment='用户 ID')
    dialog_id = Column(BigInteger, nullable=False, comment='对话 ID')
    question = Column(Text, nullable=False, comment='问题内容')
    answer = Column(Text, nullable=False, comment='回答内容')
    occurrence_time = Column(TIMESTAMP, nullable=False,
                             server_default='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', comment='谈话时间')
