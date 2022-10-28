from database import BaseModel
from peewee import *


class ProductsTable(BaseModel):
    products_id = PrimaryKeyField(null=False)
    name = TextField()
    color = TextField()
    price = IntegerField()
    available = IntegerField()
    old_price = IntegerField()
    category_id = TextField()
    sub_category = TextField()
    piority = IntegerField()
    description = TextField()
    set = TextField()

    @staticmethod
    def get_all():
        return ProductsTable.select().execute()

    @staticmethod
    def select_products_by_category(id):
        return ProductsTable.select().where(ProductsTable.category_id == id).execute()

    @staticmethod
    def get_products_by_categoryprice(id):
        return ProductsTable.select().where(ProductsTable.category_id == id and ProductsTable.price > 0).execute()
