from peewee import Model, SqliteDatabase

database = SqliteDatabase('db_meboss.db')


class BaseModel(Model):
    class Meta:
        database = database


from database.Customers import CustomersTable
from database.Products import ProductsTable
from database.Orders import OrdersTable
from database.Files import FileTable
# from database.Categories import CategoriesTable

CustomersTable.create_table()
ProductsTable.create_table()
OrdersTable.create_table()
FileTable.create_table()
FileTable.check_files()
# CategoriesTable.create_table()