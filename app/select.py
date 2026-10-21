from app.models import metadata_obj, Base, user_table, address_table, User, Address
from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import Session

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

#select with CORE way
metadata_obj.create_all(engine)


#select returns an list of rows where rows are namedtuples, so once that obj is iterated it will exhaust
with engine.begin() as conn:    
    stmt = select(user_table).where(user_table.c.name == "spongebob")
    print(stmt)
    for row in conn.execute(stmt):
        print(row)


# prerequisite for "multiple columns can be specified by:" line below
# x = ["name", "fullname"]      # [ ] on its own, in a value position -> LIST
# x = ("name", "fullname")      # parentheses + commas -> TUPLE
# x = "name", "fullname"        # commas alone -> TUPLE (same as above)

# d["name", "fullname"]         # [ ] directly after an object -> INDEXING,
#                               # and the contents are a tuple
# d[["name", "fullname"]]       # indexing, whose contents are a real list
# [ ] after an object means “index into it”, and the brackets are not a list.
# [ ] standing alone as a value means “build a list”.

# multiple columns can be specified by:
print(select(user_table.c["name", "fullname"]))

#when only the tablename is selected, all colns are selected like select * from ...
print(select(user_table))
# OR when orm used
# print(select(User))


metadata_obj.drop_all(engine)


print()
print("------------------------------------------------------------------")
print()

#orm way
Base.metadata.create_all(engine)


with Session(engine) as session:
    session_stmt = select(User).where(User.name == "spongebob")
    print(session_stmt)
    for row in session.execute(session_stmt):
        print(row)




#usefulness of scalars: scalars() takes the first element of each result row (i.e. 0th idx item of each named tuple returned)

# Example
# user_account
# id | name       | fullname
# 1  | spongebob  | Spongebob Squarepants
# 2  | sandy      | Sandy Cheeks

# # A) execute + first -> Row containing the User
# a = session.execute(select(User)).first()
# print(a)         # (User(id=1, ...),)
# print(a[0].name) # spongebob     <- need [0]

# # B) scalars + first -> the User itself
# b = session.scalars(select(User)).first()
# print(b)         # User(id=1, ...)
# print(b.name)    # spongebob     <- direct

# # C) execute + all -> list of Rows
# c = session.execute(select(User)).all()
# print(c)         # [(User(id=1,...),), (User(id=2,...),)]
# print(c[1][0].name)   # sandy

# # D) scalars + all -> list of Users
# d = session.scalars(select(User)).all()
# print(d)         # [User(id=1,...), User(id=2,...)]
# print(d[1].name) # sandy

with Session(engine) as session:
    stmt = insert(User).returning(User.name, User.fullname)
    result = session.execute(
        stmt,[
            {"name": "spongebob", "fullname": "Spngebob Squarepants"},
            {"name": "sandy", "fullname": "Sandy Cheeks"},
        ]
    )
    print("result = ", result.all())
    user = session.scalars(select(User)).first()
    print("user: ", user.name, user.fullname)
    #this is equivalent to:
    # row = session.execute(select(User)).first()
    # print("row: ", row[0].name, row[0].fullname)
    #but the session.execute way can cause err cuz row[0] throws err if the row is None, while scalars handle it gracefully and just returns None back as it is

    result = session.execute(select(User.name, User.fullname)).all()
    print("all result: ", result)
    print("all rows: ")
    for row in result:
        print(row)


    select_stmt = select(User.id, User.fullname + "@gmail.com")
    ins_stmt = insert(Address).from_select(["user_id", "email_address"], select_stmt).returning(Address.user_id, Address.email_address)
    insert_result = session.execute(ins_stmt).all()
    print("Address insert: ",insert_result)

    print("inserting extra user: ")
    session.execute(insert(User).values(name="ExtraUser", fullname="extraFullname"))

    final_stmt = select(User.name, Address).where(User.id == Address.user_id)
    print("final stmt: ", final_stmt)
    final_result = session.execute(final_stmt).all()
    print("final_result: ", final_result)


Base.metadata.create_all(engine)
