from alchemy_v2.models import Base, User, Address
from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import Session, selectinload, joinedload, contains_eager

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

Base.metadata.create_all(engine)

session = Session(engine)

print("""NOTE: 
    the loader strategy applied in models.py or our db schema applies globally to that relationship.
    Eg: addresses: Mapped[List["Address"]] = relationship(back_populates="user", lazy="selectin")
    
    but In the query, with .options(), the loader applies to one statement only Other queries still use whatever the model default is, which is lazy loading unless you changed it.
    Eg: raiseload_result = session.scalars(select(User).options(selectinload(User.addresses)).order_by(User.id))
    """)

u1 = User(name="bro", fullname="broPro")
print(u1.addresses) # prints [] #NOTE: this will raise error now since we ve set raiseload in models.py

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

print("----------------------------------Inserting----------------------------------------------")
stmt = insert(User).returning(User.name, User.fullname)
session.execute(
    stmt,[
        {"name": "spongebob", "fullname": "Spngebob Squarepants"},
        {"name": "sandy", "fullname": "Sandy Cheeks"},
        {"name": "squidward", "fullname": "Squidward Tentacles"},
        {"name": "krabs", "fullname": "Eugene H. Krabs"},
    ]
)
select_stmt = select(User.id, User.fullname + "@gmail.com")
ins_stmt = insert(Address).from_select(["user_id", "email_address"], select_stmt).returning(Address.user_id, Address.email_address)
insert_result = session.execute(ins_stmt).all()
print("Address insert: ",insert_result)
print("------------------------------------------------------------------------------------------")


# loader strategies
print("----------------------------------Loder strategies----------------------------------------------")

# SELECT IN LOAD

# Say you load 6 users and then print each user’s addresses. With default lazy loading, SQLAlchemy runs one query for the users, 
#  then one more query per user the first time you touch addresses. That’s 7 queries. This is the N+1 problem.
# selectinload runs the users query, then runs one extra query that fetches the addresses for all users at once:

# Why it’s useful:
# -> Two queries total, no matter how many users there are.
# -> It doesn’t use JOIN, so parent rows aren’t duplicated the way they can be with joinedload.

# The trade-off
# The IN (...) list grows with the number of parents. For a few thousand users that’s usually fine, but it’s worth keeping in mind for very large result sets.

# to reload all the related data freshly by selectinload, and avoiding stale cache 
session.expire_all()

# Method 1 for selectinload
# select().options() is for providing extra instruction to alchemy on how to load related data(i.e. relationship obj)
# by providing selectinload for User.addresses relnship obj to .options(), we are instructing alchemy to use selectinload strat
print()
print("---selectinload---")
selectInLoad_result = session.scalars(select(User).options(selectinload(User.addresses)).order_by(User.id))
for user in selectInLoad_result:
    print(f"{user.name}, ({", ".join(a.email_address for a in user.addresses)})")
#VVI NOTE: here for user "bro" the "broPro@gmail.com" has been inserted to db, but the selectinload is loading only bro@gmail.com and pro@gmail.com but not broPro@gmail.com
#  cuz alchemy already loaded those two email and cached in Line 35, so selectinload didnt loaded addresses for user "bro" since it was already loaded previously
#   so do session.expire_all() just before this query in order to freshly reload the related data


# Method 2 for selectinload:
# For this to work this must be set in models.py:
    # addresses: Mapped[List["Address"]] = relationship(back_populates="user", lazy="selectin") # here the "lazy" must be set with "selectin"

# selectInLoad_result_from_models_py = session.scalars(select(User).order_by(User.id))
# for user in selectInLoad_result_from_models_py:
#     print(f"{user.name}, ({", ".join(a.email_address for a in user.addresses)})")



# JOINED LOAD (oldest eager load strategy)

# joinedload adds a JOIN to the same query so related data arrives in one statement.
# Best for many-to-one, where rows don’t multiply.
# For collections, rows multiply due to duplication of rows in join which may impact on performance
# The joined table is aliased, so your WHERE and ORDER BY can’t filter on it.

print()
print("---joinedload---")

# going for many-to-one way (addresses to user)
joinedload_result = session.scalars(select(Address)
                                    .options(joinedload(
                                        Address.user, innerjoin=True)) # left outer join is default, since all our addresses are linked with their user, so innerjoin is safe here
                                    .order_by(Address.id))
for addr in joinedload_result:
    print(f"{addr.email_address}, {addr.user.name}")
print()

# going for one-to-many way (user to addresses)
joinedload_result = session.scalars(select(User)
                                    .options(joinedload(User.addresses)) # no innerjoin=True cuz there maybe users which dont ve addresses yet
                                    .order_by(User.id) 
                                    ).unique() # alchemy requires .unique(), since if a user has multiple addresses, the user row in join will appear multiple  
                                                            #  times due to "per address row join" so, .unique() collapses those repeating user row into one and 
                                                            #   collects all its addresses into one user row
for user in joinedload_result:
    print(f"({", ".join(a.email_address for a in user.addresses)}), {user.name}")
print()

# HERE:, the WHERE clause wont work, and all addresses of all users would come in result instead of only the addresses with pro@gmail.com
#   cuz joinedload adds its own copy of the address table, named addr_1, and that copy is what fills user.addresses. The WHERE clause refers
#    to the plain addr table, which the join doesn’t use.
result = session.scalars( select(User)
                            .options(joinedload(User.addresses))
                            .where(Address.email_address == "pro@gmail.com")
                        ).unique().all()
print(result) 

# THE PROBLEM of duplication of tables in join made by joined_load can be solved by contains_eager:
result = session.scalars( select(Address)
                            .join(Address.user) # passing relationship obj her tells two things, right side of join is User table, and the ON clause condition
                            .where(Address.email_address == "pro@gmail.com") # our WHERE clause will work since contains_eager doesnt duplicate tables instead use the originaltables we explicitly joined 
                            .options(contains_eager(Address.user)) #the column/s (i.e. Address.user for now) from the join that we explicitly will be used by contains_eager, it'll fill Address.user
                            #NOTE: the same relationship object passed in .join() must be passed as it is to contains_eager() as it expects a relationship obj
                        ).first()
print(result) 

# RAISE LOAD

# Lazy loading runs SQL the first time you access an attribute like u1.addresses. In a loop over many users, that’s the N+1 problem, and it often happens without
#  us noticing. So, instead of silently running a query when you touch an attribute, the app raises an error, so you’re forced to decide up front how to load the data.

# raise_on_sql blocks lazy loading for a relationship attribute until you add a loader either selectinload/joinedload/contains_eager to the query

# to activate raiseload, in models.py do on both attributes:
    # addresses: Mapped[List["Address"]] = relationship(back_populates="user", lazy="raise_on_sql")
    # user: Mapped["User"] = relationship(back_populates="addresses", lazy="raise_on_sql")

# raiseload_result = session.scalars(select(User).order_by(User.id)) # throws: sqlalchemy.exc.InvalidRequestError: 'User.addresses' is not available due to lazy='raise_on_sql'
# raiseload_result = session.scalars(select(User).options(selectinload(User.addresses)).order_by(User.id))

# If a user’s addresses collection is already loaded in memory (from an earlier selectinload, joinedload, or a lazy load), reading it uses the stored list and emits no SQL. No error.


print("------------------------------------------------------------------------------------------------")


session.close()
Base.metadata.create_all(engine)