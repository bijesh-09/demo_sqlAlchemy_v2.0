from sqlalchemy import MetaData, Table, Column, String
from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

meta = MetaData()

t1 = Table("t1", meta, Column("name", String(50), primary_key=True))

async def async_main() -> None:
    engine = create_async_engine("sqlite+aiosqlite://", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(meta.drop_all)
        await conn.run_sync(meta.create_all)

        await conn.execute(t1.insert(),[
            {"name": "some name 1"}, 
            {"name": "some name 2"}
        ])

    async with engine.connect() as conn:
        result = await conn.execute(t1.select().where(t1.c.name == "some name 1"))

        print(result.fetchall())

    # for AsyncEngine created in function scope, close and clean-up pooled connections
    await engine.dispose()

asyncio.run(async_main())