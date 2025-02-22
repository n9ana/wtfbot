import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio
# !!! pip install --force-reinstall 'httpx<0.28'

class music_player(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
        #all the music related stuff
        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        self.FFMPEG_OPTIONS = {'options': '-vn'}

        self.vc = None

    def append_request(self, link, channel):
        search = VideosSearch(link, limit=1)
        if search.result()["result"][0] == 0:
            return False
        else:
            self.music_queue.append({'source':search.result()["result"][0]["link"],
                                    'title':search.result()["result"][0]["title"],
                                    'vc': channel})
        return True
    
    def do_yt_search(self, ctx, arg):
        search = VideosSearch(arg, limit=5)
        if search.result()["result"][0] == 0:
            return ""
        else: # !!! Not implement
            # do search and wait user select
            return ""
        
    @commands.command(name="play")
    async def play(self,ctx, arg):
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send("```人？```")
            return
        
        query = arg
        yt_url = ""
        
        # perform yt search
        if arg.startswith("https://"): 
            yt_url = query
        else:
            # Let user choose
            self.do_yt_search(ctx,query)
        # append to list
        if not self.append_request(yt_url,voice_channel):
            await ctx.send("```Failed to add {yt_url}```")
            return
        await ctx.send("```" + self.music_queue[-1]['title'] + " was added to the queue```")
        if self.is_playing:
            return
            # play
        await self.play_music(ctx)
    
    async def play_music(self, ctx):
        if len(self.music_queue) <= 0:
            self.is_playing = False
            return
        self.is_playing = True
        music = self.music_queue[0]
        self.music_queue.pop(0)
        # join vc
        if self.vc == None or not self.vc.is_connected():
            self.vc = await music['vc'].connect()
            if self.vc == None: # Failed
                await ctx.send("```Failed to join vc```")
                return 
        else:
            await self.vc.move_to(music['vc'])
        loop = asyncio.get_event_loop()
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            data = ydl.extract_info(music['source'], download=False)
        song = data['url']
        play_list = "Playing: -------- " + music['title'] + " --------\r\n"
        count = 2
        for it in self.music_queue:
            play_list = play_list + str(count) + ". " + it['title'] + "\r\n"
            count = count + 1
        await ctx.send("```~Playlist~ \r\n" + play_list + "```")
        self.vc.play(discord.FFmpegPCMAudio(song, executable= "ffmpeg.exe", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_music(ctx), self.bot.loop))
  
# search = VideosSearch(url, limit=1)
# if not search:
#     print("Search Failed")
# else:
#     print(search.result()["result"][0]["title"])
#     print(search.result()["result"][0]["duration"])
#     print(search.result()["result"][0]["thumbnails"][0]["url"])
