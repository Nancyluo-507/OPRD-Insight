from database.database import engine
from database.models import Base

print("开始创建数据库...")

# 创建所有数据表
Base.metadata.create_all(bind=engine)

print("数据库创建完成！")