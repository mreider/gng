# -*- coding: utf-8 -*-

from sqlalchemy import ForeignKey
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Column
from sqlalchemy import Integer, String
from sqlalchemy.ext.declarative import declarative_base

'''
    SQLAlchemy-related classes and methods.
'''


class Database:
    """    """

    def __init__(self, database_path=None, debug_mode=False):
        self.database = database_path
        self.debug_mode = debug_mode
        self.start_engine()

    #         self.clear_all_tables()

    def start_engine(self):

        # CONNECT
        if not self.database:
            self.database = 'data.db'
        self.engine = create_engine('sqlite:///' + self.database, echo=False)
        self.connection = self.engine.connect()

        # Create Session for sqlalchemy ...
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        Base.metadata.create_all(self.engine)

    def clear_all_tables(self):

        for table in reversed(Base.metadata.sorted_tables):
            self.connection.execute(table.delete())
        self.session.commit()

    def connection_close(self):
        self.connection.close()

    def commit(self):
        self.session.commit()

    def get_product_details(self, slug):
        # print(slug)
        data = self.session.query(
            Product.id, Product.slug).filter(
            Product.name == slug).first()
        # print(data)
        return data

    def get_release_id(self, product_slug, version):
        # print(product_slug)
        # print(version)
        data = self.session.query(
            Release.id).filter(
            Release.product_slug == product_slug).filter(
            Release.version == version.strip()).first()
        # print(data)
        return data

    def get_file_details(self, release_id, file_name):
        # print(release_id)
        # print(file_name)
        data = self.session.query(
            ProductFile.id,
            ProductFile.release_id,
            ProductFile.filename,
            ProductFile.download_url,
            ProductFile.md5,
            ProductFile.release_date).filter(
            ProductFile.release_id == release_id).filter(
            ProductFile.filename == file_name).first()
        # print(data)
        return data

    def check_file_exists(self, file):
        return self.session.query(
            ProductFile.filename).filter(
            ProductFile.filename == file).first()


Base = declarative_base()


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    slug = Column(String)
    name = Column(String)


class Release(Base):
    __tablename__ = 'release'
    id = Column(Integer, primary_key=True)
    product_slug = Column(String, ForeignKey('product.slug'))
    version = Column(String)


class ProductFile(Base):
    __tablename__ = 'product_file'
    id = Column(Integer, primary_key=True)
    release_id = Column(Integer, ForeignKey('release.id'), primary_key=True)
    filename = Column(String)
    download_url = Column(String)
    md5 = Column(String)
    release_date = Column(String)
