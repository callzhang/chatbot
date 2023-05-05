from configparser import ConfigParser
from functools import wraps
from config.configparser import ConfigParser

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker


def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class Database:
    def __init__(self):
        # get db config info form config file
        connection_url = ConfigParser.get_mysql_config()
        self.engine = create_engine(connection_url)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def query(self, table, **kwargs):
        results = self.session.query(table).filter_by(**kwargs).all()
        return results

    def query_one(self, table, **kwargs):
        result = self.session.query(table).filter_by(**kwargs).one()
        self.session.close()
        return result

    def insert(self, record):
        self.session.add(record)
        self.session.commit()

    def update(self, table, id, **kwargs):
        self.session.query(table).filter_by(id=id).update(kwargs)
        self.session.commit()

    def delete(self, record):
        self.session.delete(record)
        self.session.commit()

    def get_instance(self):
        return self.session
