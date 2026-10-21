from app.models import Base, User, Address
from sqlalchemy import create_engine, select, insert
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
