from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List

# defining schemas using table constructs
metadata_obj = MetaData()

user_table = Table(
    "user_account",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(30)), #name with max length 30
    Column("fullname", String)    
)

address_table = Table(
    "address",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("user_id", ForeignKey("user_account.id"), nullable=False),
    Column("email_address", String, nullable=False),
)

# print(user_table.c) # .c is shorthand for columns
# print(user_table.c.keys())
# print(repr(user_table.c.name)) # repr() is a built-in Python function that returns the “developer-facing” string for an object
# print(repr(user_table.c.id))
# print(repr(user_table.primary_key))


# defining schemas using ORM mapped classes

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_acc"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]

    addresses: Mapped[List["Address"]] = relationship(back_populates="user")

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})" # !r means call repr() eg: self.id!r means repr(self.id)

class Address(Base):
    __tablename__ = "addr"
    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id: Mapped[int]  = mapped_column(ForeignKey("user_acc.id"))

    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self):
        return f"Address(id={self.id!r}, email_address={self.email_address!r}, user_id={self.user_id!r}, user={self.user!r})" 


# without using Mapped type annotations

# class User(Base):
#     __tablename__ = "user_acc"
#     id = mapped_column(Integer, primary_key=True)
#     name = mapped_column(String(30))
#     fullname = mapped_column(String)

#     addresses = relationship("Address", back_populates="user")

# class Address(Base):
#     __tablename__ = "addr"
#     id= mapped_column(Integer, primary_key=True)
#     email_address = mapped_column(String)
#     user_id = mapped_column(ForeignKey("user_acc.id"))

#     user = relationship("User", back_populates="addresses")
