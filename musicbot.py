import discord
import yt_dlp
import asyncio
import os
from discord import app_commands
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
        
    @commands.command(name="join")
    async def join(self, ctx):
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
            await ctx.send(f"Joined {ctx.author.voice.channel}")
        else:
            await ctx.send("You need to be in a voice channel bozo")
            
    @commands.command(name="play")
    async def play(self, ctx, url: str):
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
                title = info.get("title", "Unknown title")
                print(f"Audio URL: {audio_url}")
        except Exception as e:
            print(f"Error extracting audio URL: {e}")
            await ctx.send("Could not retrieve audio.")
            return

        # Play audio
        try:
            voice_client.play(discord.FFmpegOpusAudio(source=audio_url))
            await ctx.send(f"Now playing: {title}")
            print(f"Now playing: {title}")
        except Exception as e:
            print(f"Error in audio playback: {e}")
            await ctx.send("There was an error playing audio.")

            
    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Left the voice channel.")
            
client = commands.Bot(command_prefix="!", intents=intents)

load_dotenv()

async def main():
    await client.add_cog(MusicBot(client))
    await client.start(os.getenv("discordAPIKey"))
    
asyncio.run(main())