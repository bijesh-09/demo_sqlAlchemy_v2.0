from sqlalchemy import ForeignKey, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession, create_async_engine
from typing import List
import datetime, asyncio

#AsyncAttrs is a mixin that adds an awaitable_attrs helper to every model. It’s there for lazy loading,
# an escape hatch for when you dont use selectinload or other loading strategies up front
class Base(AsyncAttrs, DeclarativeBase): 
    pass

class B(Base):
    __tablename__ = "b"

    id: Mapped[int] = mapped_column(primary_key=True)
    a_id: Mapped[int] = mapped_column(ForeignKey("a.id"))
    data: Mapped[str]

class A(Base):
    __tablename__ = "a"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str]
    create_date: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    bs: Mapped[List[B]] = relationship()

async def insert_objects(async_session: async_sessionmaker[AsyncSession]) -> None: # -> None annotates the fn returns nothing, its for developers and ignored by interpreter
    async with async_session() as session:
        async with session.begin() as conn:
            session.add_all(
                [
                    A( bs=[ B(data="b1"), B(data="b2") ], data="a1"), # the a_id of B will auto linked due to relationship() and the f_key constraint
                    A( bs=[], data="a2"),
                    A( bs=[ B(data="b3"), B(data="b4") ], data="a3")
                ]
            )

async def select_and_update_objects(async_session: async_sessionmaker[AsyncSession]) -> None: # the annotation "async_sessionmaker[AsyncSession]" means sessions this factory produces are AsyncSession objects
    async with async_session() as session:
        stmt = select(A).order_by(A.id).options(selectinload(A.bs)) #using selectinload strat to avoid lazy loading of A.bs relationship
        results =  await session.scalars(stmt)

        for a in results:
            print("a: ", a.data)
            print("created_at: ", a.create_date)
            for b in a.bs:
                print("b: ", b.data)
            print()

        # update
        # a1 = await session.scalars(select(A).order_by(A.id)).first() # note this wont work cuz session.scalars() is still a coroutine being awaited
        
        # # fix: use either of these:
        # a1 = (await session.scalars(select(A).order_by(A.id))).first()
        # OR
        result = await session.scalars(select(A).order_by(A.id))
        a1 = result.first()

        a1.data = "new a1"

        await session.commit()

        # access attribute subsequent to commit; this is what expire_on_commit=False allows
        print(a1.data)

        # alternatively, AsyncAttrs may be used to access any attribute as an awaitable for eager loading, since
        #   lazy loading requests implicit IO to db but its not allowed in asyncio, so we would need an awaitable.
        for b1 in await a1.awaitable_attrs.bs:
            print(f"{b1}, data: {b1.data}")

async def main() -> None:
    engine = create_async_engine("sqlite+aiosqlite://", echo=True) # empty // with sqlite means /:memmory: by default

    # async_sessionmaker: a factory for new AsyncSession objects.
    # expire_on_commit - don't expire objects after transaction commit
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with engine.begin() as conn:
        # metadata.create_all() is old fn so it only runs in synchronouse engine, hence .run_sync() makes it compatible with async
        await conn.run_sync(Base.metadata.create_all) # run_sync() expects fn reference not the fn call itself, if fn call passed then create_all() 
                                                            # will throw err since it expects synchronous engine

    await insert_objects(async_session)
    await select_and_update_objects(async_session)

    # for AsyncEngine created in function scope, close and
    # clean-up pooled connections
    await engine.dispose()

asyncio.run(main())


# VVI NOTE: Using AsyncSession with concurrent tasks

# The AsyncSession object is a mutable, stateful object which represents a single, stateful database transaction in progress.

# A session is not a connection pool or a toolbox. It’s one database transaction in progress, and it holds:
# - one database connection
# - a record of what’s been loaded, changed and flushed
# - the transaction’s state (begun, committed, rolled back)

# A database connection handles commands one after another, in order. If two tasks use the same session at once, their queries get interleaved 
#   on a single connection, and the session’s internal bookkeeping gets tangled between them. At best you get an error, and at worst you get wrong data.

# Preventing implicit io (lazy loading), some guidelines:

# when building new objects with a relationship, always pass the collection explicitly, like:
# A(bs=[], data="a2")
# cuz if u dont do so then bs wont be loaded and could cause error. being "not loaded" and being "empty" are different thing. being "empty" make sures its loaded but its currently has no item

# Make sure to use lazy raise, This makes any accidental lazy load fail immediately with a clear error,
# bs: Mapped[List[B]] = relationship(lazy="raise")

# use selectinload (eager loading stategy) for loading lazy attributes
