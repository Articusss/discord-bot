import discord
from discord.ext import commands
import wavelink
from discord import app_commands
import os
from typing import cast
from dotenv import load_dotenv
from ui.ButtonMenu import ButtonMenu

load_dotenv()

class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #TODO maybe delete embed after playing finished?
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            # Handle edge cases...
            return

        original: wavelink.Playable | None = payload.original
        track: wavelink.Playable = payload.track

        embed: discord.Embed = discord.Embed(title="Now Playing")
        embed.description = f"**{track.title}** by `{track.author}`"

        if track.artwork:
            embed.set_image(url=track.artwork)

        if original and original.recommended:
            embed.description += f"\n\n`This track was recommended via {track.source}`"

        if track.album.name:
            embed.add_field(name="Album", value=track.album.name)

        await player.home.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            #Handle edge cases...
            return

        if player.queue.is_empty:
            #Disconnect
            await player.disconnect()

    async def on_wavelink_inactive_player(self, payload: wavelink.TrackStartEventPayload) -> None:
        player: wavelink.Player | None = payload.player
        if not player:
            return

        await player.disconnect()

    async def get_player(self, interaction: discord.Interaction) -> wavelink.Player | None:
        if not interaction.guild:
            interaction.response.send_message("You must use this command on a server!")
            return

        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player:
            await interaction.response.send_message("I am not playing anything in this server!")

        return player

    @app_commands.command(description="Adds a song to queue")
    @app_commands.choices(source=[
        app_commands.Choice(name="Youtube", value=str(wavelink.TrackSource.YouTube.value)),
        app_commands.Choice(name="Youtube Music", value=str(wavelink.TrackSource.YouTubeMusic.value)),
        app_commands.Choice(name="SoundCloud", value=str(wavelink.TrackSource.SoundCloud.value)),
    ])
    async def play(self, interaction: discord.Interaction, query:str, source: app_commands.Choice[str] = None) -> None:
        if not interaction.guild:
            return

        player: wavelink.Player
        player = cast(wavelink.Player, interaction.guild.voice_client)

        if not player:
            try:
                player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
            except AttributeError:
                await interaction.response.send_message("Please join a voice channel first!")
                return
            except discord.ClientException:
                await interaction.response.send_message("I was unable to join this voice channel. Please try again.")
                return

        player.autoplay = wavelink.AutoPlayMode.partial
        player.inactive_timeout = 60 #Inactive time to call inactive_player

        #Lock player to channel
        if not hasattr(player, "home"):
            player.home = interaction.channel
        elif player.home != interaction.channel:
            await interaction.response.send_message(f"You can only play songs in {player.home.mention}.")

        #This action can take a while, so defer
        await interaction.response.defer()
                
        #Search
        try:
            if source:
                tracks: wavelink.Search = await wavelink.Playable.search(query, source = wavelink.TrackSource(int(source.value)))
            else:
                tracks: wavelink.Search = await wavelink.Playable.search(query)
        except wavelink.LavalinkLoadException:
            await interaction.response.send_message("I was unable to process this request. Please try again later.")
            return
        
        if not tracks:
            await interaction.followup.send(content="Could not find tracks with that query.")
            return

        #Track is playlist
        if isinstance(tracks, wavelink.Playlist):
            added: int = await player.queue.put_wait(tracks)
            await interaction.followup.send(content=f"Added the playlist **`{tracks.name}`** ({added} songs) to the queue.")
        else:
            track: wavelink.Playable = tracks[0]
            await player.queue.put_wait(track)
            await interaction.followup.send(content=f"Added **`{track}`** to the queue")

        if not player.playing:
            await player.play(player.queue.get(), volume=100)

    @app_commands.command(description="Skips a song")
    async def skip(self, interaction: discord.Interaction) -> None:
        player : wavelink.Player = await self.get_player(interaction)

        if player:
            await player.skip(force=True)
            await interaction.response.send_message("Skipped the current song.")
    
    @app_commands.command(description="Stops playback")
    async def stop(self, interaction: discord.Interaction) -> None:
        player : wavelink.Player = await self.get_player(interaction)

        if player:
            await player.disconnect()
            await interaction.response.send_message("Stopped playback.")
    
    @app_commands.command(description="Resumes/Pauses a song")
    async def pause(self, interaction: discord.Interaction) -> None:
        player : wavelink.Player = await self.get_player(interaction)

        if player:
            await player.pause(not player.paused)
            await interaction.response.send_message(f"{"Paused" if player.paused else "Resumed"} the current song")
    
    @app_commands.command(description="Shows current queue")
    async def queue(self, interaction: discord.Interaction) -> None:
        player : wavelink.Player = await self.get_player(interaction)

        if player:
            page_size = 10
            queue = [player.current] + list(player.queue)
            pages = []
            for i in range(0, len(queue), page_size):
                text = '\n'.join([f"**{j if j != 0 else "🎵 Now playing:"}.** {queue[j].title} **{queue[j].author}**" for j in range(i, min(len(queue), i + page_size))])
                pages.append(discord.Embed(title="Queue", description=text))
            await interaction.response.send_message(embed=pages[0], view=ButtonMenu(pages, 600))

    @app_commands.command(description="Shuffles the current queue")
    async def shuffle(self, interaction: discord.Interaction) -> None:
        player : wavelink.Player = await self.get_player(interaction)

        if player:
            player.queue.shuffle()
            await interaction.response.send_message("Shuffled the current queue.")

    @app_commands.command(description="Applies nightcore filter to player")
    async def nightcore(self, interaction: discord.Interaction) -> None:
        player : wavelink.Player = await self.get_player(interaction)

        if player:
            filters: wavelink.Filters = player.filters
            filters.timescale.set(pitch=1.2, speed=1.2, rate=1)
            await player.set_filters(filters)
            await interaction.response.send_message("Filter applied successfully.")
    
    @app_commands.command(name="clearfilters", description="Clears all player filters")
    async def clear_filter(self, interaction: discord.Interaction) -> None:
        player : wavelink.Player = await self.get_player(interaction)
        
        if player:
            await player.set_filters()
            await interaction.response.send_message("Filters cleared successfully.")
    

async def setup(bot : commands.Bot):
    await bot.add_cog(Audio(bot),
                      guilds=[discord.Object(id = os.getenv("GUILD_ID"))])