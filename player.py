import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import asyncio
# !!! pip install --force-reinstall 'httpx<0.28'

class music_player(commands.Cog):
    # @commands.Cog.listener()
    # async def on_interaction(self, interaction: discord.Interaction):
    #     print("1233")
    #     await interaction.respond(content="inin")

    def __init__(self, bot):
        self.bot = bot
    
        #all the music related stuff
        self.is_playing = False
        self.is_paused = False

        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        # Debug use
        # self.YDL_OPTIONS = {'format': 'bestaudio/best',
        #                     'verbose': True}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn -filter:a "volume=0.25"'}
        self.vc = None

    def append_request(self, link, channel):
        try:
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                data = ydl.extract_info(link, download=False)
            title = data["title"]
        except Exception:
            return False
        self.music_queue.append({'source':link,
                                'title':title,
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
            await self.send_error(ctx,"人？","Enter the voice channel first")
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
            await self.send_error(ctx,"Failed to add {yt_url}","")
            return
        msg = "***" + self.music_queue[-1]['title'] + "***" + " was added to the queue"
        await self.send_success(ctx,"Query success~",msg)
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
        # join vc
        if self.vc == None or not self.vc.is_connected():
            self.vc = await music['vc'].connect()
            if self.vc == None: # Failed
                await self.send_error(ctx,"Failed to join vc","")
                return 
        else:
            await self.vc.move_to(music['vc'])

        # Display play list
        await self.send_info(ctx,"Playlist",self.gen_playlist())

        # Play music
        loop = asyncio.get_event_loop()
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            data = ydl.extract_info(music['source'], download=False)
        song = data['url']
        self.music_queue.pop(0)
        await self.ui(ctx)
        self.vc.play(discord.FFmpegOpusAudio(song, executable= "ffmpeg.exe", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_music(ctx), self.bot.loop))

    def pause(self):
        if not self.is_playing:
            return False
        self.is_playing = False
        self.is_paused = True
        self.vc.pause()
        return True

    def resume(self):
        if not self.is_paused:
            return False
        self.is_playing = True
        self.is_paused = False
        self.vc.resume()
        return True
    
    async def next(self,ctx):
        if self.vc != None and self.vc:
            self.vc.stop()
            #try to play next in the queue if it exists
            await self.play_music(ctx)
    # UI
    async def resume_button_cb(self, interaction: discord.Interaction):
        if self.is_paused:
            self.resume()
            await interaction.response.edit_message(content = "Resumed")
        else:
            self.pause()
            await interaction.response.edit_message(content = "Paused")

    async def clear_button_cb(self, interaction: discord.Interaction):
        self.music_queue = []
        await interaction.response.edit_message(content = "Playlist cleared")

    async def next_button_cb(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content = "Next song")
        await self.next(interaction)

    async def ui(self,ctx):
        view = discord.ui.View(timeout = 600)
        resume_button = discord.ui.Button(
            label = "Resume/Pause",
            style = discord.ButtonStyle.blurple
        )
        next_button = discord.ui.Button(
            label = "Next",
            style = discord.ButtonStyle.blurple
        )
        clear_button = discord.ui.Button(
            label = "Clear",
            style = discord.ButtonStyle.red
        )
        
        resume_button.callback = self.resume_button_cb
        clear_button.callback = self.clear_button_cb
        next_button.callback = self.next_button_cb
        view.add_item(resume_button)
        view.add_item(next_button)
        view.add_item(clear_button)
        await ctx.send("Control Panel", view=view)
    

    def gen_playlist(self):
        if len(self.music_queue) <= 0:
            print("Unable to generate playlist, queue <= 0")
        play_list = "**1. __"+ self.music_queue[0]['title'] + "__**"
        count = 2
        if len(self.music_queue) > 1:
            for it in self.music_queue[1:]:
                play_list = play_list + str(count) + ". " + it['title'] + "\r\n"
                count = count + 1
        return play_list
    
    async def send_info(self, ctx, t, d):
        embed = discord.Embed(
            title = t,
            description = d,
            color = discord.Color.blue()
        )
        await ctx.send(embed = embed)

    async def send_error(self, ctx, t, d):
        embed = discord.Embed(
            title = t,
            description = d,
            color = discord.Color.red()
        )
        await ctx.send(embed = embed)

    async def send_success(self, ctx, t, d):
        embed = discord.Embed(
            title = t,
            description = d,
            color = discord.Color.green()
        )
        await ctx.send(embed = embed)
# search = VideosSearch(url, limit=1)
# if not search:
#     print("Search Failed")
# else:
#     print(search.result()["result"][0]["title"])
#     print(search.result()["result"][0]["duration"])
#     print(search.result()["result"][0]["thumbnails"][0]["url"])
