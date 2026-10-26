# Coroutines are a more generalized form of subroutines. Subroutines are entered at one point and exited at another point.
#  Coroutines can be entered, exited, and resumed at many different points. 

import asyncio, time

# async def main():
#     print('hello')
#     await asyncio.sleep(1)
#     print('world')

# asyncio.run(main()) 

# Calling an async def function doesn’t run its body. It returns a coroutine object that only executes when awaited or passed to the event loop.
# so running asyncio.run(main) wont run since asyncio.run() expects a coroutine obj not a function itself

# print(main()) # prints <coroutine object main at 0x7f7f1f6c9c00>

async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

# here main is a single task which is a plausible fn
async def main():
    print("sequential await")
    print(f"Started at {time.strftime('%X')}") # strftime means string format time, %X means current time as text
    await say_after(1, 'hello') # so main pauses for 1 sec until this is done
    await say_after(2, 'world') # so main pauses for 2 secs until this is done
    print(f"Finished at {time.strftime('%X')}") # so total of 3 secs delay after start time

asyncio.run(main()) # starts the event loop, An event loop is a loop that runs tasks and switches between them whenever one is waiting.

# In time.strftime()
# %Y year with century, e.g. 2026
# %m month, 10
# %d day, 24
# %H:%M:%S hour, minute, second, written out, e.g. 19:53:07
# %A weekday name, e.g. Saturday

# creating tasks that run concurrently
async def main():
    print("Using create_tasks")
    task1 = asyncio.create_task(
        say_after(1, "hello")
    )
    task2 = asyncio.create_task(
        say_after(2, "hello")
    )
    print(f"Started at {time.strftime('%X')}")
    await task1 # event loop switches to task2 when task1 awaits for 1 sec
    await task2 # by the time task1 ends, task2 also has completed its 1 sec, and 1 sec is left to be run
    print(f"Finished at {time.strftime('%X')}") # total of 2 secs time to run after start of time

asyncio.run(main())

# modern alternative to create tasks
async def main():
    print("Using TaskGroup class")
    async with asyncio.TaskGroup() as tg: # TaskGroup is a class
        task1 = tg.create_task(
            say_after(1, "hello")
        )
        task2 = tg.create_task(
            say_after(2, "world")
        )
        print(f"Started at {time.strftime('%X')}")
        # The await is implicit when the context manager exits(like a cleanup code).

    print(f"Finished at {time.strftime('%X')}")

asyncio.run(main())

# Python’s event loop only holds a weak reference to your task. If you don’t save the task in a variable,
# Python can delete it before it finishes, and your background work silently disappears. So:
# task = asyncio.create_task(say_hello(1))   # good: you kept a reference
# asyncio.create_task(say_hello(1))          # risky: nothing holds it

# It’s just a cleaner way to run several tasks and wait for all of them
# If any task fails, the others get cancelled and the error is raised, so nothing gets lost silently.

async def main():
    print("Using TaskGroup class again")
    print(f"Started at {time.strftime('%X')}")
    async with asyncio.TaskGroup() as tg: 
        for i in range(3):
            task = tg.create_task(say_after(i+1, f"hello{i+1}"))

    print(f"Finished at {time.strftime('%X')}")

asyncio.run(main())

# task cancellation
async def worker():
    try:
        print("running the worker...")
        await asyncio.sleep(4)
    except asyncio.CancelledError:
        print("Exception of CancelledError caught...")
        raise # this bare raise catches the error and re-raises the same exception. Without a re-raise, the except block would swallow it,
                #  and the exception would not propagate back to main so the task would look like it finished normally.
    finally:
        print("Cleaning up")

async def main():
    print("task cancellation")
    task = asyncio.create_task(worker())
    await asyncio.sleep(1) # the main awaits here, so event loop switches to 'task' which was created and scheduled just before but not run till now
    task.cancel() # by this time, sleep 1 sec has finished and main resumes, while the sleep(4) in worker has 3 sec left to finish and worker is still paused 
    # task.cancel doesnt cancels task immediately, it just marks the task is gonna receive CancellationError exception at next await line
    try:
        print("starting task...")
        await task # main pauses here and the CancellationError is passed to worker from here while the worker is paused for its 3 sec sleep to finish

    except asyncio.CancelledError: # the CancelledError exception propagates from worker back to the main in await of try block above, so except block runs now
        print("The task was cancelled")

asyncio.run(main())