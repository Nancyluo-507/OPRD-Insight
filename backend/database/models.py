from sqlalchemy import Column, Integer, String, Text
from database.database import Base


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    title = Column(Text)
    abstract = Column(Text)
    authors = Column(Text)
    year = Column(Integer)

    # OpenAlex信息
    openalex_id = Column(String, unique=True)
    doi = Column(String)

    # 学科与关键词
    subjects = Column(Text)
    keywords = Column(Text)

    # 统计信息
    cited_by_count = Column(Integer)