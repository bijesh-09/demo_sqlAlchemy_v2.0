import asyncio

sem = asyncio.BoundedSemaphore(3)

#NOTE: plain asyncio.Semaphore() is buggy where we can call more release() than acquire(), this can increase the sem value more than its original value
        # but python allows it and this bug has its own usecase
            # If u want guarded usecase then use asyncio.BoundedSemaphore() which raises ValueError if release() makes semaphore counts past its original value

# HERE, these will increase sem from 3 to 5, if sem is instantiated from Semaphore(), but throws ValueError if its instantiated from BoundedSemaphore()
# sem.release()
# sem.release()

async def download(i):
    async with sem:
        print(f"start {i}")
        await asyncio.sleep(1)   # simulated network call
        print(f"done {i}")

async def main():
    await asyncio.gather(*(download(i) for i in range(5)))

asyncio.run(main())

#NOTE: using "async with" is safer since it pairs each acquire() with release(),if sem was instantiated from Semaphore() then release() being more than acquire is
    #    impossible unless we explicitly write release() in our code block and it work silently creating bug. but if sem was instantiated from Semaphore() then its 
            # even better since BoundedSemaphore()throws ValueError in such case.
    # "async with" also handles release if the task crashes mid execution, unlike in manual way where the crashed task could acquire sempahore forever.

# async with sem:
#     # work with shared resource

# // this is roughly equal to:

# await sem.acquire()
# try:
#     # work with shared resource
# finally:
#     sem.release()