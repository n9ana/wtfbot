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
    class channel():
        def __init__(self):
            self.is_playing = False
            self.is_paused = False
            self.music_queue = []
            self.vc = None
        

        
    def __init__(self, bot):
        self.bot = bot
        
        self.vc_list = {}
        self.YDL_OPTIONS = {'format': 'bestaudio/best'}
        # Debug use
        # self.YDL_OPTIONS = {'format': 'bestaudio/best',
        #                     'verbose': True}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                               'options': '-vn -filter:a "volume=0.25"'}

    def append_request(self, link, vc, channel: channel):
        try:
            with YoutubeDL(self.YDL_OPTIONS) as ydl:
                data = ydl.extract_info(link, download=False)
            title = data["title"]
        except Exception:
            return False
        channel.music_queue.append({'source':link,
                                'title':title,
                                'vc':vc})
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
        if self.vc_list.get(hash(voice_channel)) == None:
            self.vc_list[hash(voice_channel)] = self.channel()

        # perform yt search
        query = arg
        yt_url = ""
        if arg.startswith("https://"): 
            yt_url = query
        else:
            # Let user choose
            self.do_yt_search(ctx,query)

        vc_ch = self.vc_list[hash(voice_channel)]
        # append to list
        if not self.append_request(yt_url,voice_channel,vc_ch):
            await self.send_error(ctx,"Failed to add {yt_url}","")
            return
        msg = "***" + vc_ch.music_queue[-1]['title'] + "***" + " was added to the queue"
        await self.send_success(ctx,"Query success~",msg)
        if vc_ch.is_playing:
            return
            # play
        await self.play_music(ctx,vc_ch)
        
    async def play_music(self, ctx, channel:channel):
        if len(channel.music_queue) <= 0:
            channel.is_playing = False
            return
        channel.is_playing = True
        music = channel.music_queue[0]
        # join vc
        if channel.vc == None or not channel.vc.is_connected():
            channel.vc = await music['vc'].connect()
            if channel.vc == None: # Failed
                await self.send_error(ctx,"Failed to join vc","")
                return 
        else:
            await channel.vc.move_to(music['vc'])

        # Display play list
        await self.send_info(ctx,"Playlist",self.gen_playlist(channel))
        # Play music
        loop = asyncio.get_event_loop()
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            data = ydl.extract_info(music['source'], download=False)
        song = data['url']
        channel.music_queue.pop(0)
        await self.ui(ctx)
        channel.vc.play(discord.FFmpegOpusAudio(song, executable= "ffmpeg.exe", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_music(ctx,channel), self.bot.loop))

    def pause(self,vc_ch:channel):
        if not vc_ch.is_playing:
            return False
        vc_ch.is_playing = False
        vc_ch.is_paused = True
        vc_ch.vc.pause()
        return True

    def resume(self,vc_ch:channel):
        if not vc_ch.is_paused:
            return False
        vc_ch.is_playing = True
        vc_ch.is_paused = False
        vc_ch.vc.resume()
        return True
    
    async def next(self,interaction):
        vc_ch = self.vc_list[hash(interaction.user.voice.channel)]
        if vc_ch.vc != None and vc_ch.vc:
            vc_ch.vc.stop()
            #try to play next in the queue if it exists
            await self.play_music(interaction)

    async def skip(self,interaction):
        view = discord.ui.View(timeout = 30)
        vc_ch = self.vc_list[hash(interaction.user.voice.channel)]
        select_list = discord.ui.Select(
            placeholder = "Skip to ...", # the placeholder text that will be displayed if nothing is selected
            min_values = 1, # the minimum number of values that must be selected by the users
            max_values = 1, # the maximum number of values that can be selected by the users
            options = [ # the list of options from which users can choose, a required field
            ]
        )
        count = 1
        for it in vc_ch.music_queue:
            msg = str(count) +". " + it['title']
            count = count + 1
            select_list.append_option(discord.SelectOption(label=msg))
        select_list.callback = self.skip_selection_cb
        view.add_item(select_list)
        await interaction.channel.send("Select", view=view)

    # UI
    async def resume_button_cb(self, interaction: discord.Interaction):
        vc_ch = self.vc_list[hash(interaction.user.voice.channel)]
        if vc_ch.is_paused:
            self.resume(vc_ch)
            await interaction.response.edit_message(content = "Resumed")
        else:
            self.pause(vc_ch)
            await interaction.response.edit_message(content = "Paused")

    async def clear_button_cb(self, interaction: discord.Interaction):
        self.vc_list[hash(interaction.user.voice.channel)].music_queue = []
        await interaction.response.edit_message(content = "Playlist cleared")

    async def next_button_cb(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content = "Next song")
        await self.next(interaction)

    async def skip2_button_cb(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content = "Skip song")
        await self.skip(interaction)
    
    async def skip_selection_cb(self, interaction: discord.Interaction):
        msg = "Skipping to "+interaction.data['values'][0]
        await self.send_info(interaction.channel, msg,"")
        await interaction.response.autocomplete()
        
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
        skip2_button = discord.ui.Button(
            label = "Skip",
            style = discord.ButtonStyle.grey
        )
        clear_button = discord.ui.Button(
            label = "Clear",
            style = discord.ButtonStyle.red
        )
        
        resume_button.callback = self.resume_button_cb
        clear_button.callback = self.clear_button_cb
        next_button.callback = self.next_button_cb
        skip2_button.callback = self.skip2_button_cb
        view.add_item(resume_button)
        view.add_item(next_button)
        view.add_item(skip2_button)
        view.add_item(clear_button)
        await ctx.send("Control Panel", view=view)
    

    def gen_playlist(self, channel:channel):
        if len(channel.music_queue) <= 0:
            print("Unable to generate playlist, queue <= 0")
        play_list = "**1. __"+ channel.music_queue[0]['title'] + "__**"
        count = 2
        if len(channel.music_queue) > 1:
            for it in channel.music_queue[1:]:
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
