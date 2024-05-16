import discord
from discord.ext import commands
import os
import logging
import wavelink
from dotenv import load_dotenv
import asyncio

load_dotenv()

class Bot(commands.Bot):
    def __init__(self) -> None:
        intents: discord.Intents = discord.Intents.default()
        intents.message_content = True

        discord.utils.setup_logging(level=logging.INFO)
        super().__init__(intents=intents, command_prefix="$", description="Bot muito democrático")

    async def setup_hook(self) -> None:
        nodes = [wavelink.Node(uri=os.getenv("LAVALINK_URI"), password=os.getenv("LAVALINK_PWD"))]

        # cache_capacity is EXPERIMENTAL. Turn it off by passing None
        await wavelink.Pool.connect(nodes=nodes, client=self, cache_capacity=100)

        #Load cogs
        await self.load_extension("cogs.audio")
        await bot.tree.sync(guild = discord.Object(id = os.getenv("GUILD_ID")))

    async def on_ready(self) -> None:
        logging.info("Logged in: %s | %s", self.user, self.user.id)

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload) -> None:
        logging.info("Wavelink Node connected: %r | Resumed: %s", payload.node, payload.resumed)

bot = Bot()

async def main() -> None:
    async with bot:
        await bot.start(os.getenv("API_KEY"))

asyncio.run(main())
