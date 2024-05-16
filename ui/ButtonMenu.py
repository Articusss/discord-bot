from discord.ui import View
from discord import ui
import discord
from typing import Optional, List

class ButtonMenu(View):
    def __init__(self, pages:list, timeout:float, user:Optional[discord.Member]=None) -> None:
        super().__init__(timeout=timeout)
        self.curr_page = 0
        self.pages = pages
        self.user = user
        self.len = len(self.pages) - 1

        self.children[0].disabled = True
        self.children[1].disabled = False if len != 0 else True
    
    async def update(self, page:int):
        self.curr_page = page
        if len == 0: #Only one page, disable buttons
            self.children[0].disabled = True
        elif page == 0:
            self.children[0].disabled = True
            self.children[1].disabled = False
        elif page == self.len:
            self.children[0].disabled = False
            self.children[1].disabled = True
        else:
            for i in self.children: i.disabled = False
    
    async def getPage(self, page):
        "Return (string, embed, files)"
        if isinstance(page, str):
            return page, [], []
        if isinstance(page, discord.Embed):
            return None, [page], []
        if isinstance(page, discord.File):
            return None, [], [page]
        if isinstance(page, List):
            if all([isinstance(x, discord.Embed) for x in page]): 
                return None, page, []
            if all([isinstance(x, discord.File) for x in page]): 
                return None, [], page
            raise TypeError("Can't have alternative files and embeds on same page array.")

        raise TypeError("Pages are not of type string, embed, file or list of embeds/files")

    async def showPage(self, page:int, interaction:discord.Interaction):
        await self.update(page)
        content, embeds, files = await self.getPage(self.pages[page])

        await interaction.response.edit_message(
            content=content,
            embeds=embeds,
            attachments=files or [],
            view=self
        )
    
    @ui.button(emoji='⬅️', style=discord.ButtonStyle.red)
    async def prev_page(self, interaction: discord.Interaction, button):
        await self.showPage(self.curr_page - 1, interaction)
    
    @ui.button(emoji='➡️', style=discord.ButtonStyle.red)
    async def next_page(self, interaction: discord.Interaction, button):
        await self.showPage(self.curr_page + 1, interaction)    