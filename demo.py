from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ':memory:' means in-memory db, 
# pysqlite is a default python's built in sqlite3 driver, 
# echo=True means show all logs of engine
# engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)
# FORMAT: sqlite+pysqlite:// [empty host] / demo.db
# eg: sqlite+pysqlite:///home/user/demo.db from 3rd / is abs path
# eg: sqlite+pysqlite:///demo.db from 3rd / its relative path

engine = create_engine("sqlite+pysqlite:///:memory:", echo=True)

#default behavior, tx rollback on engine.connect()
with engine.connect() as conn: 

    #by using 'with' as context manager which also runs the cleanup code, it simply does
    # try:
    #     result = conn.execute(text("select 'hello world'"))
    #         print(result.all())
    # finally: 
    #     conn.close() --> cleanup code

    result = conn.execute(text("select 'hello world'"))
    print(result.all())

#commit as u go
#engine.connect allows us to commit as much as we want, where each commit marks end of an tx, so we can ve multiple tx run 
with engine.connect() as conn: 
    conn.execute(text("create table some_table (x int, y int)"))
    conn.execute(text("insert into some_table (x,y) values (:x, :y)"),
                    [{"x": 1, "y": 2}, {"x": 2, "y": 4}]) #this is called parameterizing
        
    conn.commit() #commits the tx

    result = conn.execute(text("select * from some_table"))
    for row in result:
        print(f"x: {row.x}, y: {row.y}")

#begin once
#engine.begin runs whole thing as single tx and autocommits on successful tx, else rollback, 
# so u cannot commit manually else it will conflict
with engine.begin() as conn: 
    conn.execute(text("insert into some_table (x,y) values (:x, :y)"),
                 [{"x": 3, "y": 6}, {"x": 9, "y": 12}])

    # here result returned by conn.execute() is a one-shot stream, so its exhausted once u iterate over it
    result = conn.execute(text("select * from some_table"))

    # here 'result' returns table rows of db as rows objects
    # each rows are a namedtuple, eg:
    from collections import namedtuple
    mypoint = namedtuple('Point', ["p","q","r"])
    s = mypoint(11, 22, r=20)
    print(s[0] + s[1] + s[2]) #indexing works cuz its tuple
    print(s.p + s.q + s.r) #attributing works
    a,b,c = s #unpack like a regular tuple
    print(a,b,c)
    print(s) # prints mypoint(11,22,10)
    # print(p["x"] + p["y"]) #this wont work since tuple isnt a dict


    #ways to access the result
    #note: only the first for loop will run since it will exhaust the 'result' one shot stream object

    # tuple assignment
    for x, y in result:
        print(f"x: {x}, y: {y}")

    #integer index
    for row in result:
        print(f"x: {row[0]}, y: {row[1]}")
     
    #attribute name
    for row in result:
        print(f"x: {row.x}, y: {row.y}")

    # Mapping access
    # the dict method access wont work since row isnt a dict, to convert it into dict do: 
    # either result.mappings() 
    for row in result.mappings():
        print(f"x: {row["x"]}, y: {row["y"]}") 
    # OR DO:
    for row in result:
        print(f"x: {row._mapping["x"]}, y: {row._mapping["y"]}") 
    
with engine.connect() as conn:

    # the text() accepts the :y parameter, and the actual value is passed as dict or list of dicts in 2nd arg of conn.execute()
    # parameterizing prevents SQL injection since the sqlalchemy handles it properly

    # sending single parameter , 2nd arg as single dict
    result = conn.execute(text("select x, y from some_table where y > :y"), {"y": 2})
    for row in result:
        print(f"x: {row.x}, y: {row.y}")

    # sending single parameter , 2nd arg as list of dicts
    conn.execute(
        text("INSERT INTO some_table (x, y) VALUES (:x, :y)"),
        [{"x": 11, "y": 12}, {"x": 13, "y": 14}]
        #note following will either throw err or dont return the affected rows back at all:
        # text("INSERT INTO some_table (x, y) VALUES (:x, :y) returning x, y"),
                # [{"x": 11, "y": 12}, {"x": 13, "y": 14}],
        #this is cuz, the driver doesnt returns affected the rows back just by writing 'returning x, y'
        # inside text() with parameterization , though it should have, cuz the driver or db just doesnt support it
        # so use insert() or insert.returning() to get rows back reliably. this will be discussed later on 
    )
    conn.commit()


# Session is very similar to the conn, but session gives more ability, and its built on 
# top of conn as conn is the actual core thats doing the job internally

# The Session doesn’t actually hold onto the Connection object after it ends the transaction. 
# It gets a new Connection from the Engine the next time it needs to execute SQL against the database.

with Session(engine) as session:
    stmt = text("select x,y from some_table where y > :y order by x, y")
    result = session.execute(stmt, {"y": 6})
    for row in result:
        print(f"x: {row.x}, y: {row.y}") 

with Session(engine) as session:
    result = session.execute(
        text("UPDATE some_table SET y=:y WHERE x=:x"),
        [{"x": 9, "y": 11}, {"x": 13, "y": 15}],
    )
    session.commit()