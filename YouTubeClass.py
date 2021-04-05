import asyncio
import discord
from discord.ext import commands
import private_data
import youtube_dl


# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def send_song_info(data):
    pass # todo

class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['youtube'])
    async def yt(self, ctx, *, url):

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.data['webpage_url']))

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        if 0 <= volume <= 100:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send("Changed volume to {}%".format(volume))
        else:
            await ctx.send('Volume can only be from 0 to 100')

    @commands.command(aliases=['exit', 'leave'])
    async def disconnect(self, ctx):
        """Stops and disconnects the bot from voice"""
        if ctx.voice_client is not None:
            await ctx.send(f'OK I will leave {ctx.voice_client.channel}')
            await ctx.voice_client.disconnect()
        else:
            await ctx.send('I\'m already out of the voice channel')

    @commands.command(aliases=['enter', 'join'])
    async def connect(self, ctx):
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.send(f'Connected to {ctx.voice_client.channel}')
        else:
            await ctx.send(f'You are not in a voice channel')

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send('Song paused')
        else:
            await ctx.send('Song already paused')

    @commands.command(aliases=['play'])
    async def resume(self, ctx):
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send('Song resumed')
        else:
            await ctx.send('Song already playing')

   
    @yt.before_invoke
    async def ensure_connect(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
                await ctx.send(f'connected to {ctx.voice_client.channel}')
            else:
                await ctx.send("You are not connected to a voice channel.")
                #raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()
