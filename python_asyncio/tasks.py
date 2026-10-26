import asyncio, time
import datetime as dt

# running tasks concurrently using taskgroup, its stricter and modern alternative
#NOTE: the TaskGroup cancels all other remaining tasks if any one of the task raises an exception
# async def fail():
#     await asyncio.sleep(1)
#     raise ValueError("boom")

# async def slow():
#     await asyncio.sleep(5)
#     print("never printed")

# async def main():
#     async with asyncio.TaskGroup() as tg:
#         try:
#             tg.create_task(fail())
#             tg.create_task(slow())
#         except* ValueError as eg: # the except* is is used because the ExceptionGroup bundles all of the errors raised in TaskGroup into one object
#             print("Caught: ", eg.exceptions)

# asyncio.run(main())


async def display_date():
    loop = asyncio.get_running_loop() # returns the event loop thats running this coroutine
    end_time = loop.time() + 5.0 # loop.time() is the monotonous clock of the event loop
    while True:
        print(dt.datetime.now())
        if (loop.time() + 1.0) >= end_time:
            break
        await asyncio.sleep(1)

asyncio.run(display_date())

# running tasks concurrently using .gather(), its old way and less stricter
# it doesnt cancel all other remaining tasks if any one of the task raises an exception
# it returns a list of the results returned by all the tasks
async def factorial(name, number):
    f = 1
    for i in range(2, number + 1):
        print(f"Task {name}: Compute factorial({number}), currently i={i}...")
        await asyncio.sleep(1)
        f *= i
    print(f"Task {name}: factorial({number}) = {f}")
    return f

async def main():
    # Schedule three calls *concurrently*:
    L = await asyncio.gather( # return_exceptions are false by default, but if its true, gather() returns the results and the exceptions as well 
        factorial("A", 2),
        factorial("B", 3),
        factorial("C", 4),
    )
    print(L)

asyncio.run(main())

#timeouts
#NOTE: A timeout works by cancelling the task. Your code must not swallow CancelledError silently, or the timeout won’t stop it.x``

async def long_running_task():
    await asyncio.sleep(10) # longrunningtask is paused here, as soon as timeouts, eventloop resumes this task and raises CancelledError which propagates from here to the main()
    print("long_running_task finished!")


async def main():
    #NOTE: this is wrong since the TImeoutError raised by timeout() wont be catched by the except block cuz timeout() is not in try block here 
    # async with asyncio.timeout(10):
    #     try:
    #         await long_running_task()
    #     except TimeoutError:   # never triggers here
    #         ...

    try:
        async with asyncio.timeout(3): # timeout() is a context manager and it tells event loop to cancel the task if that task crosses the time limit
            await long_running_task() # the timeout() catches the CancelledError and then raises TimeoutError
    except TimeoutError:
        print("The long operation timed out, but we've handled it.")

asyncio.run(main())


async def main():
    try: 
        async with asyncio.timeout(None) as cm: # unlimited timeout for now
            new_deadline = asyncio.get_running_loop().time() + 3
            cm.reschedule(new_deadline) # reschedule(when) takes clock value as arg not a time delay
            await long_running_task()
    except TimeoutError:
        pass

    if cm.expired(): # expired() returns True if the task in cm timed out
        print("Looks like we haven't finished on time.")

asyncio.run(main())


async def main():
    try: 
        deadline = asyncio.get_running_loop().time() + 3
        async with asyncio.timeout_at(deadline): # timeout(delay) takes time delay as arg while timeout_at(when) takes clock value or absolute deadline as arg 
            await long_running_task()
    except TimeoutError:
        pass

asyncio.run(main())

# running in threads:
def blocking_io():
    print(f"start blocking_io at {time.strftime('%X')}")
    # Note that time.sleep() can be replaced with any blocking
    # IO-bound operation, such as file operations.
    time.sleep(1) # this is a blocking operation which blocks its whole thread unti its done
    print(f"blocking_io complete at {time.strftime('%X')}")

async def main():
    print(f"started main at {time.strftime('%X')}")

    await asyncio.gather(
        asyncio.to_thread(blocking_io), # to_thread() sends blockingio() to another thread since it would block the event loop if it was on same current thread
        # NOTE: to_thread() returns a coroutine that wraps the blocking fn, but the blocking fn itself is as it is its not a coroutine
        # VVI NOTE: if the blocking fn has timeout and if it timedout then the fn doesnt stop until its done or returns something, its just that when
        #  timeout event loop gives up on waiting blocking fn
        asyncio.sleep(1))

    print(f"finished main at {time.strftime('%X')}")

asyncio.run(main())


def blocking_io():
    print(f"start blocking_io at {time.strftime('%X')}")
    count = 0
    for i in range(1000000000+1):
        count = count + 1
    print(f"blocking_io complete at {time.strftime('%X')}")

async def main():
    print(f"started main at {time.strftime('%X')}")

    try: 
        async with asyncio.timeout(1):
            await asyncio.to_thread(blocking_io)
    except TimeoutError:
        print("Blockingio timeout, but its still running in worker thread, its only that event loop has given up waiting on it.")

    print(f"finished main at {time.strftime('%X')}")


asyncio.run(main())