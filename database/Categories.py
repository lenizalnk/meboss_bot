from database import BaseModel
from peewee import *


class CategoriesTable(BaseModel):
    category_id = PrimaryKeyField(null=False)
    name = TextField()
    sub_category = TextField()


    @staticmethod
    def get_Categories():
        return CategoriesTable.select().execute()