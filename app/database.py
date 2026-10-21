from app.models import metadata_obj, Base, user_table, address_table
from sqlalchemy import create_engine, insert, select

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

#using table construct, CORE WAY
metadata_obj.create_all(engine)

# inserting with CORE way


stmt = insert(user_table).values(name='Ram', fullname='Ram Shrestha') # user_table is an instace of Table()
compiled_smt = stmt.compile()
print(compiled_smt.params) # the bound parameters 'Ram' and 'Ram Shrestha' will be printed
print(stmt)
with engine.begin() as conn:
    result = conn.execute(stmt)

print(insert(user_table)) # auto creates VALUES clause
# ouput: INSERT INTO user_account (id, name, fullname) VALUES (:id, :name, :fullname)


#inserting multiple values with a list of dicts, since insert() auto creates VALUES clause
#NOTE: only the first dictionary in the list determines what columns will be in the VALUES clause. The rest of the dictionaries are not scanned. 
result = insert(user_table),[
    {"name": "Shyam", "fullname": "Shyam Shrestha"},
    {"name": "Sita", "fullname": "Sita Shrestha"}
]
print(result)


# inserts only the “defaults” for a table without including any explicit values at all 
print(insert(user_table).values().compile(engine))
# output: INSERT INTO user_account DEFAULT VALUES


#insert...returning
insert_stmt = insert(address_table).returning(address_table.c.id, address_table.c.email_address)
print(insert_stmt)
# output: INSERT INTO address (id, user_id, email_address) VALUES (:id, :user_id, :email_address) RETURNING address.id, address.email_address


#insert...from select
# Bulk copying or deriving rows entirely inside the database is much faster than selecting rows into Python and inserting them back one by one
select_stmt = select(user_table.c.id, user_table.c.name + "@gmail.com") #concatenate the user_account.name with "@gmail.com"

# Insert into address, filling the columns user_id and email_address with the two values the SELECT produces, in that order.
ins_from_select = insert(address_table).from_select(["user_id", "email_address"], select_stmt)
print(ins_from_select.returning(address_table.c.user_id, address_table.c.email_address))




metadata_obj.drop_all(engine)



# ORM way
# Base.metadata.create_all(engine)
# Base.metadata.drop_all(engine)