import discord
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

FFMPEG_OPTIONS = {'options' : '-vn'}
YDL_OPTIONS = {
    "format" : "bestaudio/best",
    "noplaylist": True
}

class MusicBot(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.queue = []
        self.currentTrack = None
        self.currentTrackTitle = ""
        self.voiceChannel = ""
        self.timeoutSeconds = 300
        self.timeoutTask = None
        self.isLooping = False
        
    @commands.command(name="join")
    async def join(self, ctx) -> None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            self.voiceChannel = ctx.author.voice.channel
            await ctx.send(f"Joined {self.voiceChannel}")
        else:
            await ctx.send("You need to be in a voice channel bozo")
            
    @commands.command(name="play")
    async def play(self, ctx, url: str) -> None:
        if not ctx.voice_client:
            await self.join(ctx)
        
        voice_client = ctx.voice_client
        if voice_client is None:
            await ctx.send("Failed to connect to a voice channel.")
            return
            
        # Extract audio URL
        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "quiet": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                audio_url = info["url"]
                title = info["title"]
                print(f"Audio URL: {audio_url}")
        except Exception as e:
            print(f"Error extracting audio URL: {e}")
            await ctx.send("Could not retrieve audio.")
            return
        
        if self.queue or voice_client.is_playing():
            await ctx.send(f"Added {title} to the queue")
            
        self.queue.append((audio_url, title))
        
        if not voice_client.is_playing():
            await self.playNext(ctx)

    async def playNext(self, ctx) -> None:
        if self.queue:
            if not self.isLooping:
                url, title = self.queue.pop(0)
                
                try:
                    self.currentTrack = url
                    source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                    self.currentTrackTitle = title
                    ctx.voice_client.play(source, after=lambda _:self.client.loop.create_task(self.playNext(ctx)))
                    await ctx.send(f"Now playing **{title}**")
                except Exception as e:
                    print(f"Error in audio playback: {e}")
                    await ctx.send("There was an error playing audio")
            else:
                try:
                    source = await discord.FFmpegOpusAudio.from_probe(self.currentTrack, **FFMPEG_OPTIONS)
                    ctx.voice_client.play(source, after=lambda _:self.client.loop.create_task(self.playNext(ctx)))
                except Exception as e:
                    print(f"Error in audio playback: {e}")
                    await ctx.send("There was an error playing audio")
                
        elif not ctx.voice_client.is_playing():
            self.isLooping = False
            self.currentTrack = None
            self.currentTrackTitle = ""
            return
                    
    @commands.command(name="skip")
    async def skip(self, ctx) -> None:
        if ctx.voice_client and ctx.voice_client.is_playing():
            self.isLooping = False
            ctx.voice_client.stop()
            await ctx.send("Skipped")
            
    @commands.command(name="leave")
    async def leave(self, ctx) -> None:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue.clear()
            self.isLooping = False
            self.currentTrack = None
            self.currentTrackTitle = ""
            self.voiceChannel = ""
        else:
            await ctx.send("I'm not in a voice channel")
            return
            
    @commands.command(name="loop")
    async def loop(self, ctx) -> None:
        if ctx.voice_client.is_playing():
            if ctx.author.voice.channel != self.voiceChannel:
                await ctx.send("You aren't in the same channel bozo")
                return
            self.isLooping = not self.isLooping
            
            if self.isLooping:
                await ctx.send(f"Now looping **{self.currentTrackTitle}**")
            else:
                await ctx.send("Looping has been disabled.")
        else:
            await ctx.send("I am not playing anything right now.")
            return
        
    @commands.command(name="queue")
    async def showQueue(self, ctx) -> None:
        if self.queue:
            peekQueue = []
            for i, (_, title) in enumerate(self.queue):
                peekQueue.append(f"{i + 1}. **{title}**")
                await ctx.send("Current Queue:\n" + "\n".join(peekQueue))
        else:
            await ctx.send("The queue is empty")
            
client = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(os.getenv("discordAPIKey"))
    
asyncio.run(main())