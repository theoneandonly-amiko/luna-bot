import os
import discord
from discord.ext import commands
from discord.ui import View, Button

class LogView(View):
    def __init__(self, log_lines, page_size=10):
        super().__init__(timeout=180)  # The view will timeout after 3 minutes
        self.log_lines = log_lines
        self.page_size = page_size
        self.current_page = 0
        self.pages = [log_lines[i:i + page_size] for i in range(0, len(log_lines), page_size)]

    async def update_message(self, interaction: discord.Interaction):
        if self.pages:
            description = "\n".join(self.pages[self.current_page])
        else:
            description = "No log entries available."
        embed = discord.Embed(
            title="Bot Log",
            description=description,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Page {self.current_page + 1} of {len(self.pages) if self.pages else 1}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='logs', help='Display the bot log with interactive navigation.')
    async def logs(self, ctx):
        # Define absolute path for the log file
        logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
        log_file = os.path.join(logs_dir, 'bot.log')
        if not os.path.exists(log_file):
            await ctx.send("Log file does not exist.")
            return
        
        # Read log content and create pages for pagination
        with open(log_file, "r", encoding="utf-8") as f:
            log_lines = f.read().splitlines()
        
        view = LogView(log_lines, page_size=10)
        if view.pages:
            description = "\n".join(view.pages[0])
        else:
            description = "No log entries available."
        
        embed = discord.Embed(
            title="Bot Log",
            description=description,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Page 1 of {len(view.pages) if view.pages else 1}")
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))
