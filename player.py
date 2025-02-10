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

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        self.FFMPEG_OPTIONS = {'options': '-vn'}

        self.vc = None
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)

    def append_yt_link(self, item):
        search = VideosSearch(item, limit=1)
        if search.result()["result"][0] == 0:
            return False
        else:
            self.music_queue.append({'source':search.result()["result"][0]["link"],
                                    'title':search.result()["result"][0]["title"],
                                    'thumbnail':search.result()["result"][0]["thumbnails"][0]["url"]})
        return True
    
    async def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            #get the first url
            m_url = self.music_queue[0][0]['source']

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
            song = data['url']
            self.vc.play(discord.FFmpegPCMAudio(song, executable= "ffmpeg.exe", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            self.is_playing = False

    @commands.command(name="play")
    async def play(self,ctx, arg):
        # add link
        if not self.append_yt_link(arg):
            await ctx.send("```Failed to add {arg}```")
            return
        await ctx.send("`" + self.music_queue[-1]['title'] + "` was added to the queue")

        # join vc
        if self.vc == None or not self.vc.is_connected():
            try:
                voice_channel = ctx.author.voice.channel
            except:
                await ctx.send("```You need to connect to a voice channel first!```")
                return 
            self.vc = await voice_channel.connect() # try join vc
            if self.vc == None: # Failed to join
                await ctx.send("```Could not connect to the voice channel```")
                return 
            
        ## not yet implement !!!!!!!!!!!!!!!!!!!!!!!!!
        if not self.is_playing:
            pass
        # else:
        # # play
        # data = self.ytdl.extract_info(m_url, download=False)
        # song = data['url']
        # self.vc.play(discord.FFmpegPCMAudio(song))
    
    
# url of the video 

  
# search = VideosSearch(url, limit=1)
# if not search:
#     print("Search Failed")
# else:
#     print(search.result()["result"][0]["title"])
#     print(search.result()["result"][0]["duration"])
#     print(search.result()["result"][0]["thumbnails"][0]["url"])
