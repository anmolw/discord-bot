import asyncio
import bot
import config

try:
    import uvloop
except ImportError:
    print("Using default asyncio event loop")
else:
    print("Using uvloop")
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

if __name__ == "__main__":
    bot_instance = bot.Aimbot()
    bot.setup(bot_instance)
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot_instance.start(config.bot_token))
    except KeyboardInterrupt:
        print("Received keyboard interrupt, terminating")
        loop.run_until_complete(bot_instance.close())
    finally:
        loop.close()
