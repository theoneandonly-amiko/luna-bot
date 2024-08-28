import discord
from discord.ext import commands
from discord.ext.commands.help import HelpCommand
from discord.ui import View, Select


class HelpDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Fun Commands", description="List of fun commands"),
            discord.SelectOption(label="Moderation Commands", description="List of moderation commands"),
            discord.SelectOption(label="Music Commands", description="List of music commands"),
            discord.SelectOption(label="Miscellaneous", description="List of miscellaneous commands")
            discord.SelectOption(label="Games", description="List of available games.")
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        embed = discord.Embed(title=f"Help - {category}", color=discord.Color.dark_purple())

        if category == "Fun Commands":
            embed.add_field(name="**Fun Commands**", value=(
                "`&pet @user [@optionaluser]` - *Pet a user and send a cute gif.*\n"
                "`&grab @user [@optionaluser]` - *Grab a user and send a funny gif.*\n"
                "`&compliment @user` - *Send a compliment to a user. You can do this to yourself too, because why not?*\n"
                "`&battle @user1 @user2` - *Start a virtual battle between 2 \"hot tempered\" users.*\n"
                "`&roll` - *Roll a dice, of course.*\n"
                "`&choose [option1] [option2]` - *Choose an option for you.*\n"
                "`&8ball [question]` - *Consult the magic 8-ball to answer your question.*\n"
                "`&flip` - *Flip a coin. Useful when you making a bet against someone, hehe.*\n"
                "`&urban [term]` - *Be your 24/7 dictionary. Feel free to look for any terms you don\'t know.*\n"
                "`&cat` - *Measures how much you look like a cat. 🐱*\n"
                "`&kurin` - *Measures how much \"hyperkuru\" you currently are.*\n"
            ), inline=False)
        elif category == "Moderation Commands":
            embed.add_field(name="**Moderation Commands**", value=(
                "`&mute [userID] [reason]` - *Mute a user.*\n"
                "`&unmute [userID]` - *Unmute a user.*\n"
                "`&kick [userID]` - *Kick a user out.*\n"
                "`&ban [userID]` - *Ban a user.*\n"
                "`&muterole_create` - *Create mute role if not existed. This will override mute permissions and role to all categories and channels.*\n"
                "`&clear [all/number]` - *Delete messages.*\n"
            ), inline=False)
        elif category == "Music Commands":
            embed.add_field(name="Music Commands - Beta (yes)", value=(
                "`&play [Youtube Video URL or Search Query]` - *Join user connected voice channel and play music from given URL.*\n"
                "`&pause` - *This will pause the song.*\n"
                "`&resume` - *Continue playing the song.*\n"
                '`&stop` - *Clear the queue and disconnect from current voice channel.*\n'
                "`&queue` - *Display the current song queue.*\n"
                "`&skip` - *Skip the current song.*\n"
                "`&volume_up` - *Increase volume by 10%.*\n"
                "`&volume_down` - *Decrease volume by 10%.*\n"
                "`&clear_queue` - Clear the entire music queue.\n"
                "`&disconnect` - *Disconnect the bot from the voice channel.*\n"
                "`&24/7 [deephouse/lofi/hardstyle]` - *Enters 24/7 mode and start streaming/playing defined genres.*\n"
                "`&stop_24/7` - *Similar to how `stop` command works.*\n"
            ), inline=False)
        elif category == "Miscellaneous":
            embed.add_field(name="Miscellaneous", value=(
                "`&usercount` - *Let you know how many members are in the current server.*\n"
                "`&ticket` - *Create a ticket to send a request for channel creation.*\n"
                "`&help` - *Show this help message*"
            ), inline=False)
        elif category == "Games":
            embed.add_field(name="Game", value=(
                "`&hangman` - *Play Hangman game.*\n"
                "`&rps [rock/paper/scissors]` - *Play Rock Paper Scissors with bot.*\n"
                "`&numberguess` - *Play Number Guessing game.*\n"
                "`&scramble` - *Play Word Scramble game.*\n"
                "`&bet [red/black/number (range 0 - 36)]` - *Play Roulette game.*\n"
                "`&memory` - *Play Memory Game.*"
            ), inline=False)

        await interaction.response.edit_message(embed=embed)

class HelpView(View):
    def __init__(self, channel):
        self.channel = channel
        super().__init__(timeout=60)
        self.add_item(HelpDropdown())

    async def on_timeout(self):
        # Find the message and delete it after the timeout
        channel: discord.TextChannel = self.channel
        async for message in channel.history(limit=100):
            if message.author == channel.guild.me and message.embeds:
                await message.delete()
                break

class MyHelpCommand(HelpCommand):

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help - Select a Category", color=discord.Color.dark_purple())
        embed.description = "Use the dropdown menu to select a category for help."
        view = HelpView(self.get_destination())
        await self.get_destination().send(embed=embed, view=view)
    
    async def send_cog_help(self, cog):
        # sends information about a given category
        raise NotImplementedError
    
    async def send_command_help(self, command):
        # sends information about a given command
        raise NotImplementedError
    
class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = MyHelpCommand()
        bot.help_command.cog = self
        # Command to show developer features
        
    @commands.command(name='dev')
    async def dev(self, ctx):
        if ctx.author.id != self.bot.DEV_USER_ID:
            await ctx.send("You do not have permission to use this command.")
            return

        embed = discord.Embed(title="Developer Features", color=discord.Color.dark_purple())

        embed.add_field(name="Command Prefix: &", value=(
            "`blacklist [add/remove] [UserID]` - Add a user to blacklist, prevent them from executing the commands.\n"
            "`message [channel ID] [Write anything for the bot to send]` - A feature to communicate as the bot.\n"
            "`category create [Name]` - Create a category.\n"
            "`category delete [Category ID]` - Delete a category if the given ID is correct.\n"
            "`channel create [channel_name] [category_id] --private (optional argument) [user IDs]` - Create a channel, with options to make it private or not, adding users to a newly created private channel if given.\n"
            "`channel delete [channel ID]` - Delete a channel if the given ID is correct.\n"), inline=False)

        await ctx.send(embed=embed)

    # ================= Info Category ======================
    @commands.command(name='info')
    async def _help(self, ctx):
        embed = discord.Embed(title="**About me**", color=discord.Color.brand_green())
        embed.add_field(name="Short description", value=(
            "I\'m Luna, the bot serve with most basic purposes. Currently I\'m under development, but I\'ll be sure to not make you feel disappointed, hehe. ;)\n"
            "I was built from the migrations of Miko bot and Amiker bot, because of some inconvenient monitors and constant downtime from server side, with some more improvements and optimisations. If there\'s any new feature, feel free to suggest. Any cockroach I made? Catch them. 😁"
        ), inline=False)
        await ctx.send(embed=embed)



async def setup(bot):
    await bot.add_cog(Help(bot))
