from database import BaseModel
from peewee import *


class CustomersTable(BaseModel):
    customer_id = PrimaryKeyField(null=False)
    name = TextField()
    telegram_id = IntegerField(unique=True)
    phone = TextField()
    email = TextField()
    address = TextField()


    @staticmethod
    def add_customer(name, telegram_id, phone, email, address):
        return CustomersTable.create(name=name, telegram_id=telegram_id, phone=phone, email=email, address=address)

    @staticmethod
    def get_customer_by_id(id):
        return CustomersTable.get(customer_id=id)

    # @staticmethod
    # def delete_user_by_telegram_id(telegram_id):
    #     CustomersTable.delete().where(CustomersTable.telegram_id == telegram_id).execute()

    def print_customer(self):
        print(self.user_id, self.name, self.telegram_id)

    # def change_telegram_id(self, new_telegram_id):
    #     self.update(telegram_id=new_telegram_id).execute()

    # @staticmethod
    # def change_telegram_id_by_customer_id(user_id, new_telegram_id):
    #     CustomersTable.update(telegram_id=new_telegram_id).where(CustomersTable.user_id == user_id).execute()
