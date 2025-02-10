import discord
from discord.ext import commands
import os, asyncio
import yaml
#import all of the cogs
from player import music_player

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

#remove the default help command so that we can write out own
bot.remove_command('help')

# Get bot token
dc_bot_token = ""
with open("params.yaml", "r") as stream:
    try:
        data = yaml.safe_load(stream)
        dc_bot_token = data["token"]
    except yaml.YAMLError as exc:
        print(exc)

# Start the bot
async def main():
    async with bot:
        await bot.add_cog(music_player(bot))
        # await bot.start("os.getenv['TOKEN']")
        await bot.start(dc_bot_token)
asyncio.run(main())