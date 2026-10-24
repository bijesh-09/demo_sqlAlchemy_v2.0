from app.models import Base, User, Address
from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import Session

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

Base.metadata.create_all(engine)

session = Session(engine)

u1 = User(name="bro")
print(u1.addresses) # prints []

a1 = Address(email_address="bro@gmail.com") # this will throw err at db ops since the "user_id" attribute of Address class is non nullable
u1.addresses.append(a1) #auto sync betwn u1 and a1 due to backpopulates parameter
a2 = Address(email_address="pro@gmail.com", user=u1) #explicitly passing "user" attribute

for addr in u1.addresses: 
    print(repr(addr)) 

# adds the a1 and a2 to the session auto since a1 and a2 has reln with u1
# this is called save-update cascade
session.add(u1) 
print(a1 in session)
print(a2 in session)

#since the a1 and a2 are f_key dependent upon u1, so session handles inserting of u1 before the a1 and a2
session.commit()

# since the u1, a1 and a2 are expired after commit, following line triggers fetch from db for u1 contents
print(u1)

#though the u1 was loaded, its relationship attribute isnt loaded, so following query triggers fetch for Address object in reln with u1 i.e. a1 and a2
#this is called lazy loading
print(u1.addresses)



# joining using relationships

# here when a relationship object is passed to .join() or .join_from() then, it tells two things at once:
#  the right side of the join is Address, and the ON clause is based on relationship's join condition(which is 
#   normally derived from the f_key constraint, i.e. user_account.id = address.user_id in this case)
print("joining using relationships: ", select(Address.email_address).select_from(User).join(User.addresses))
#output: SELECT addr.email_address FROM user_acc JOIN addr ON user_acc.id = addr.user_id

#join() and join_from() do not look at relationship() when they guess an ON clause until a relationship object is passed as arg
print("joining without using relationships: ", select(Address.email_address).join_from(User, Address))
# same output: SELECT addr.email_address FROM user_acc JOIN addr ON user_acc.id = addr.user_id

session.close()
Base.metadata.create_all(engine)