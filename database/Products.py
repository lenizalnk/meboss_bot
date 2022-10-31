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
    def select_products_by_n_and_cat(name, cat):
        return ProductsTable.select().where((ProductsTable.category_id == cat)
                                            & (ProductsTable.name.contains(name))).execute()
    @staticmethod
    def select_products_by_name(name):
        # return ProductsTable.select().where(ProductsTable.name ** name).execute()
        return ProductsTable.select().where(ProductsTable.name.contains(name)).execute()
        # return ProductsTable.select().where(ProductsTable.name.contains("name")).execute()