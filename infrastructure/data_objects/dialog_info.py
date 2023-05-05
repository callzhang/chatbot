'''
Author: zhiyong.liang zhiyong.liang@stardust.ai
Date: 2023-04-19 13:33:11
'''
from sqlalchemy import Column, BigInteger, String, TIMESTAMP, Boolean
from sqlalchemy.ext.declarative import declarative_base

from infrastructure.database.database import Database
from tools.datetime_util import DatetimeUtils
from tools.objects_util import Objects

Base = declarative_base()


class DialogInfo(Base):
    __tablename__ = 'dialog_info'

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='ID')
    user_id = Column(BigInteger, nullable=False, comment='用户 ID')
    dialog_name = Column(String(64), nullable=False, comment='对话名称')
    created_time = Column(TIMESTAMP, nullable=False,
                          server_default='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', comment='对话创建时间')
    delete_flag = Column(Boolean, nullable=False, default=False, comment='是否删除')

    def get_all_dialog_by_user_id(self,user_id:BigInteger):
        db = Database()
        dialog_list = db.query(DialogInfo, user_id=user_id).all()
        if dialog_list:
            return [dialog.dialog_name for dialog in dialog_list]
        else:
            return self.create_new_dialog(user_id,db)

    def create_new_dialog(user_id:BigInteger,db = None):
        if db is None:
            db = Database()
        dt = DatetimeUtils()
        formatted_now_time = dt.format(dt.now())
        new_dialog = DialogInfo(
                user_id=user_id,
                dialog_name=formatted_now_time.__str__,
                created_time=formatted_now_time
        )
        db.insert(new_dialog)
        
        return formatted_now_time.__str__.split(",")
    
    def clear_dialog(user_id: BigInteger, dialog_name:str):
        if Objects.check_params(user_id,dialog_name):
            db = Database()
            delete_dialog = DialogInfo(
                user_id=user_id,
                dialog_name=dialog_name
            )
            db.delete(delete_dialog)

    def update_dialog_name(user_id: BigInteger, dialog_name:str, new_dialog_name:str):
        if Objects.check_params(user_id,dialog_name,new_dialog_name):
            db = Database()
            db.update_one(
                DialogInfo,
                filter_dict={
                    "user_id":user_id,
                    "dialog_name":dialog_name
                },
                update_dict={
                    "dialog_name":new_dialog_name
                }
            )