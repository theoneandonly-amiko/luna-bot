from discord.ext import commands

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        return await self.bot.is_owner(ctx.author)
    
    @commands.command(hidden=True, description="pulls the repo")
    async def pull(self, ctx: commands.Context):
        """Pulls the current code from the repo"""

        embed = disnake.Embed(title="Git pull.", description="")
        git_commands = [["git", "stash"], ["git", "pull", "--ff-only"]]
        for git_command in git_commands:
            process = await asyncio.create_subprocess_exec(
                git_command[0],
                *git_command[1:],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            output, error = await process.communicate()
            embed.description += f'[{" ".join(git_command)!r} exited with return code {process.returncode}\n'
            if output:
                embed.description += f"**[stdout]**\n{output.decode()}\n"
            if error:
                embed.description += f"**[stderr]**\n{error.decode()}\n"
        await ctx.send(embed=embed)
    
    @commands.command(hidden=True)
    async def load(self, ctx: commands.Context, extension):
        embed = disnake.Embed()
        self.bot.load_extension(f"cogs.{extension}")
        embed.add_field(
            name="Load Extension", value=f"Loaded cog: ``{extension}`` successfully"
        )
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def unload(self, ctx: commands.Context, extension):
        self.bot.unload_extension(f"cogs.{extension}")
        embed = disnake.Embed()
        embed.add_field(
            name="Unload Extension", value=f"Unloaded cog: ``{extension}`` successfully"
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["r"], hidden=True)
    async def reload(self, ctx: commands.Context, extension=""):
        if not extension:
            for cog in tuple(self.bot.extensions):
                self.bot.reload_extension(cog)
            embed = disnake.Embed()
            embed.add_field(name="Reload Extension", value="Reloaded cogs successfully")
            await ctx.send(embed=embed)
        else:
            self.bot.reload_extension(f"cogs.{extension}")
            embed = disnake.Embed()
            embed.add_field(
                name="Reload Extension",
                value=f"Reloaded cog: ``{extension}`` successfully",
            )
            await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Staff(bot))