from alchemy_v2.models import Base, User, Address
from sqlalchemy import create_engine, select, insert, and_, or_, func, desc 
from sqlalchemy.orm import Session

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

Base.metadata.create_all(engine)



session = Session(
    bind=engine,
    # expire_on_commit=False # its used typically in Async applications, where implicit database I/O on attribute access can be problematic.
)

stmt = insert(User).returning(User.name, User.fullname)
result = session.execute(
    stmt,[
        {"name": "spongebob", "fullname": "Spngebob Squarepants"},
        {"name": "sandy", "fullname": "Sandy Cheeks"},
    ]
)
print("result = ", result.all())

#these objects are currently in "transient" state since they are not associated with any db yet
squidward = User(name="squidward", fullname="Squidward Tentacles")
krabs = User(name="ehkrabs", fullname="Eugene H. Krabs")
print(squidward.id, krabs.id) # prints None None, since these objects are in transient state and our db's auto increment hasnt assigned id to them

session.add(squidward)
session.add(krabs)
print(session.new) # shows pending or transient objects
session.flush()
#NOTE: when the objects are inserted, each obj are inserted as one row at a time to db as it has to retrieve the id given by db's auto-increment, this can hamper performance in bulky tx 

# prints the ids, cuz now these objects are in "persistent" state as they got flushed to db
print(squidward.id, krabs.id) 

some_squidward = session.get(User, 1) # p_key of object is tied with session, so session.get returns the object with that p_key if already loaded in memory, if not it fetched from db
print(some_squidward.id, some_squidward.name, some_squidward.fullname)



# where clause for multiple conditions:
print("------------------------------WHERE----------------------------")
multiple_where = session.scalars(select(Address.email_address)
                                 .where(User.name == "squidward")
                                 .where(Address.user_id == User.id)).first()
#the query defaults to AND operation for condns in multiple .where():
# SELECT addr.email_address FROM addr, user_acc 
# WHERE user_acc.name = ? AND addr.user_id = user_acc.id
print("multiple conditions in where clause: ", multiple_where)

# and_() or_() in .where()  
print(select(Address.email_address).where(
    and_(
        or_(User.name == "sandy", User.name == "squidward"),
        Address.user_id == User.id
    )
))
#output:
# SELECT addr.email_address FROM addr, user_acc 
# WHERE (user_acc.name = :name_1 OR user_acc.name = :name_2) AND addr.user_id = user_acc.id

print(
    select(Address.email_address).where(
        or_(
            User.name == "squidward",
            and_(Address.user_id == User.id, User.name == "sandy"),
        )
    )
)
# ouput: NOTICE HERE, how there is no bracket betwn the AND operands cuz AND has higher operator precedence than OR in sql
# SELECT addr.email_address FROM addr, user_acc 
# WHERE user_acc.name = :name_1 OR addr.user_id = user_acc.id AND user_acc.name = :name_2

print("--------------------------------------------------------------")


#joins
print("------------------------------JOINS----------------------------")

result_join = session.execute(select(User.name, Address.email_address)).all()
print("select from multiple tables(cartesian product): ", result_join) #SELECT user_acc.name, addr.email_address FROM user_acc, addr

# .join_from() specifies both left and right hand side of join
#SELECT user_acc.name, addr.email_address FROM user_acc JOIN addr ON user_acc.id = addr.user_id
result_join = session.execute(select(User.name, Address.email_address).join_from(User, Address)).all()
print(".join_from() both LHS and RHS: ", result_join) 

#NOTE: the "ON user_acc.id = addr.user_id" is auto done since our addr.user_id refs to user_acc.id

# .join_from() specifies only the right hand side of join, while LHS is inferred
#SELECT user_acc.name, addr.email_address FROM user_acc JOIN addr ON user_acc.id = addr.user_id
result_join = session.execute(select(User.name, Address.email_address).join(Address)).all()
print(".join(), only RHS, LHS inferred: ", result_join)

# UP TO HERE, sqlalchemy was auto inferring the tables and ON clause, but some cases are where we want to explicitly 
# join ourselves, and where alchemy cant infer witth its guess, eg:

result_join = session.execute(select(Address.email_address).select_from(User).join(Address)).all()
print(".select_from() eg: ", result_join)

result_join = session.scalars(select(func.count("*")).select_from(User)).all()
print(".select_from() for aggregation fns: ", result_join)

#UP TO HERE, alchemy auto inferred the ON clause, but we ve to explicitly give the condns for ON clause when there is no
#  f_key constraint or multiple f_key constraints

print("explicit on clause with .join(): ", select(Address.email_address).select_from(User).join(
    Address, User.id == Address.user_id
))

print("explicit on clause with .join_from(): ", select(Address.email_address).join_from(
    User, Address, User.id == Address.user_id
))

#outer and full joins
print("outer join: ", select(Address.email_address).select_from(User).join(
    Address, isouter=True # the isOuter defaults to LEFT OUTER JOIN
))
print("full join: ", select(Address.email_address).select_from(User).join(
    Address, full=True 
))
print("--------------------------------------------------------------")



#order by, group_by, having
print("------------------------------order by, group_by, having----------------------------")

print("order_by: ", select(User).order_by(
    User.name, 
    User.fullname.desc() # here User.fullname is Tie Breaker, and it'll be used only when the User.name happens to be same
    # the desc() sorts in descending order, while the .asc() is the default
))
result_groupBy = session.execute(
    select(User.name, func.count(Address.id).label("address_count"))
                           .join(Address)
                           .group_by(User.name)
                           .having(func.count(Address.id) > 1)
).all()
print("users with more than one address: ", result_groupBy)

# ordering and grouping by label
print(
    select(Address.user_id, func.count(Address.id).label("num_addresses")) # here in SELECT clause, there are two expns that we can refer to: Address.user_id and num_addresses
    .join(User, User.id == Address.id)
    .group_by(  "user_id") # referring to Address.user_id 
    .order_by("user_id", desc("num_addresses")) # referring to Address.user_id and num_addresses
)

print("--------------------------------------------------------------")


session.commit()


#Update in orm
sandy = session.scalars(select(User).filter_by(name="sandy")).first()
print(sandy.fullname) # prints "Sandy Cheeks"

sandy.fullname = "Sandy Squirrel" #changing the fullname, now sandy obj is in dirty state
print(sandy in session.dirty) #prints True

session.flush() #now the dirty sandy obj's fullname is auto updated in db

sandy_fullname = session.scalars(select(User.fullname).where(User.id == 2)).first()
print(sandy_fullname) # prints "Sandy Squirrel" since its already got updated in db


# Delete in orm
squidward_del = session.get(User, 3)
session.delete(squidward_del) # the delete doesnt happen until the session is flushed
print("squidward_del: ", squidward_del.fullname) # since session isnt flushed, the squidward_del obj still exists
print(squidward_del in session.deleted) # prints True

# since we are trying to fetch the user thats supposed to be deleted, session auto flushes and the DELETE will run prior before 
# this SELECT. NOTE: the SELECT fro "addr" table runs prior to DELETE automatically as CASCADE since its user_id refs to User.id
deleted_squidward = session.scalars(select(User).where(User.id == 3 )).first() 
print("deleted_squidward: ", deleted_squidward) # prints None since the user is already deleted
print(squidward_del in session) # prints False
#NOTE: all these changes wont be saved permanently until committed, this all is happening in a tx

# so if "autoflush" is enabled, whenever u try to run new query and if a row obj is dirty or marked deleted previously, then
# the corressponding update or delete queries are run automatically prior to our new query

session.rollback() # discards all the current changes in tx
# NOTE: every objects in the tx expires when the tx is either rolled back or committed

# HERE: the sandy obj is expired due to rollback, so the select query for sandy is auto emitted to load sandy obj with values
print(sandy.fullname) # prints "Sandy Cheeks" which was previously modified as "Sandy Squirrel"


session.close()
# NOTE: every objects in the tx becomes detached object when the session is closed

# this will cause detachedInstanceErr if it was an expired obj, but since we reloaded the sandy obj right after 
# rollback just above, so the values of sandy is in python's mem hence no query is needed to reload so no
# detachedInstanceErr appears, but now this sandy has become a ghost obj rn 
print(sandy.fullname) # here the sandy is a detached object

# Try to avoid using objects in their detached state, if possible. 
# but if u wanna still use it anyway, then u can re-establish the session by:
# session.add(sandy)
# print(sandy.fullname)

# For cases where detached objects are necessary, typically the immediate display of just-committed objects for a web
# application where the Session is closed before the view is rendered, set the Session.expire_on_commit flag to False.

# when expire_on_commit=False, the detached objects wont expire at all, so The loaded value remains accessible because it wasn't expired by the commit.
# Important: This works for already-loaded attributes. Unloaded relationships or expired attributes can still require database access,
#  and detached objects cannot lazy-load those attributes.


Base.metadata.drop_all(engine)
