import discord
from discord.ext import commands
from discord.ui import Select, View

class HelpDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Fun Commands", description="List of fun commands"),
            discord.SelectOption(label="Games", description="List of available games."),
            discord.SelectOption(label="Level Commands", description="List of available level commands."),
            discord.SelectOption(label="Manager", description="List of available manager commands."),
            discord.SelectOption(label="Miscellaneous", description="List of miscellaneous commands"),
            discord.SelectOption(label="Moderation Commands", description="List of moderation commands"),
            discord.SelectOption(label="Music Commands", description="List of music commands"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        embed = discord.Embed(title=f"Help - {category}", color=discord.Color.dark_purple())
        
        # Define embeds based on category
        if category == "Fun Commands":
            embed.add_field(name="**Fun Commands** (1/2)", value=(
                "`pet @user [@optionaluser]` - Pet a user and send a cute gif.\n"
                "`grab @user [@optionaluser]` - Grab a user and send a funny gif.\n"
                "`slap @user [@optionaluser]` - Slap someone if you feel your hand is itchy. Harmless.\n"
                "`hug @user [@optionaluser]` - Hug someone. Simple as that.\n"
                "`compliment @user` - Send a compliment to a user. You can do this to yourself too, because why not?\n"
                "`battle @user1 @user2` - Start a virtual battle between 2 \"hot tempered\" users.\n"
            ), inline=False)
            embed.add_field(name="**Fun Commands** (2/2)", value=(
                "`roll` - Roll a dice, of course.\n"
                "`choose [option1] [option2]` - Choose an option for you.\n"
                "`8ball [question]` - Consult the magic 8-ball to answer your question.\n"
                "`flip` - Flip a coin. Useful when making a bet against someone, hehe.\n"
                "`urban [term]` - Be your 24/7 dictionary. Feel free to look for any terms you don\'t know.\n"
                "`cat` - Measures how much you look like a cat. 🐱\n"
                "`kurin` - Measures how much \"hyperkuru\" you currently are.\n"
                "`messup` - Mess the message above you or the message you are replying to. Ehehe.\n"
                "`match @user1 @user2` - Show matchmaking result between 2 users. Love love.\n"
            ), inline=False)
        elif category == "Moderation Commands":
            embed.add_field(name="**Moderation Commands** (1/2)", value=(
                "`mute [userID] [reason]` - Mute a user.\n"
                "`unmute [userID]` - Unmute a user.\n"
                "`kick [userID]` - Kick a user out.\n"
                "`ban [userID]` - Ban a user.\n"
                "`create_mute_role` - Create mute role if not existed.\n"
            ), inline=False)
            embed.add_field(name="**Moderation Commands** (2/2)", value=(
                "`clear [all/number]` - Delete messages.\n"
                "`warn [userID]` - Warn a user.\n"
                "`warnings [userID]` - Display the number of warnings a user has.\n"
                "`clear_warn [userID]` - Clear warnings for a user.\n"
                "`setgreetchannel #channel_name` - Set mentioned channel as the welcoming channel.\n"
                "`setgoodbyechannel #channel_name` - Set the goodbye channel."
            ), inline=False)
        elif category == "Music Commands":
            embed.add_field(name="Music Commands", value=(
                "`play [Youtube Video URL or Search Query]` - Join user connected voice channel and play music from given URL or Query in Normal mode.\n"
                "`nightcore [Youtube Video URL or Search Query]` - Same as play command, but in Nightcore mode.\n"
                "`slowed [Youtube Video URL or Search Query]` - Same as play command, but in Slowed mode.\n"
                "`pause` - This will pause the song.\n"
                "`resume` - Continue playing the song.\n"
                '`stop` - Clear the queue and disconnect from current voice channel.\n'
                "`queue` - Display the current song queue.\n"
                "`toggle_effects [slowed/nightcore/normal]` - Switch between modes (specifically, queue). This only applies on the next queued song.\n"
                "`stream [genre]` - Enters 24/7 mode and start streaming/playing defined genres. Trigger command first to know all available genres.\n"
                "`stopstream` - Similar to how `stop` command works.\n"
            ), inline=False)
        elif category == "Miscellaneous":
            embed.add_field(name="Miscellaneous", value=(
                "`usercount` - Let you know how many members are in the current server.\n"
                "`help` - Show this help message\n"
                "`stats` - Show bot statistics\n"
                "`info` - Description about me.\n"
                "`whois @user` - Show information about an user in guild.\n"
                "`avatar @user` - Show user's avatar.\n"
                "`guildinfo` - Show current guild info."
            ), inline=False)
        elif category == "Games":
            embed.add_field(name="Game", value=(
                "`hangman` - Play Hangman game.\n"
                "`rps [rock/paper/scissors]` - Play Rock Paper Scissors with bot.\n"
                "`numberguess` - Play Number Guessing game.\n"
                "`scramble` - Play Word Scramble game.\n"
                "`bet [red/black/number (range 0 - 36)]` - Play Roulette game.\n"
                "`memory` - Play Memory Game."
            ), inline=False)
        elif category == "Manager":
            embed.add_field(name="**Manager Commands (1/2)**", value=(
                "`createrole [rolename] [hex color (optional)]` - Create role.\n"
                "`addrole @user @role` - Assigns a role to a specified user.\n"
                "`removerole @user @role` - Removes a role from a specified user.\n"
                "`deleterole @role` - Deletes a specified role.\n"
                "`listroles` - Lists all roles in the server with the number of members in each.\n"
                "`createchannel [name] [type] [category (optional)]` - Creates a new channel of specified type (text/voice/stage) and optional category.\n"
                "`createcategory [name]` - Creates a new category with the specified name.\n"
                "`deletechannel #channel` - Delete a specified channel\n"), inline=False)
            embed.add_field(name="**Manager Commands (2/2)**", value=(
                "`deletecategory [Category name]` - Deletes a category with the specified name.\n"
                "`setchannelname #channel [new name]` - Changes the name of a specified channel.\n"
                "`setchannelcategory #chanel [Category name]` - Moves a channel to a different category.\n"
                "`listchannels` - Lists all channels in the server.\n"
                "`viewsettings` - View server settings (Administrator only).\n"
                "`setservername [new name]` - Change the server's name.\n"
                "`setverificationlevel [0-4]` - Set server verification level (0-4).\n"
                "`listbans` - Lists all banned users in the server.\n"), inline=False)
        elif category == "Level Commands":
            embed.add_field(name="**Level Commands**", value=
                "`level` - Check the level and XP of a user in the current guild.\n"
                "`setlevelchannel #channel_mention` - Set the channel where level-up messages will be sent.\n"
                "`restrictxpchannel #channel_mention` - Mark a channel as restricted from awarding XP.\n"
                "`unrestrictxpchannel #channel_mention` - Remove a channel from the restricted XP list.\n"
                "`restrictxpuser @user_mention` - Restrict a user from gaining XP in the server.\n"
                "`grantxp @user_mention [XP amount]` - Grants a specified amount of XP to a user.\n"
                "`toplevel` - Display the top users by XP in the current guild.\n"
                "`viewlevelroles` - View all the level-up roles set in the current guild.\n"
                "`setlevelrole [level] @role_mention` - Set a role to be given when a user reaches a specific level.\n"
                "`togglexpblock` - Mark a guild as restricted from awarding XP.", inline=False)
        
        await interaction.response.edit_message(embed=embed)

class HelpView(View):
    def __init__(self, help_message):
        super().__init__(timeout=30)
        self.help_message = help_message
        self.add_item(HelpDropdown())
    
    async def on_timeout(self):
        try:
            await self.help_message.delete()
        except discord.NotFound:
            pass

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', help='Shows this help message')
    async def help(self, ctx):
        embed = discord.Embed(title="Help - Select a Category", color=discord.Color.dark_purple())
        embed.description = "Use the dropdown menu to select a category for help. Command prefix: `&`"
        help_message = await ctx.send(embed=embed, view=HelpView(None))
        
        # Pass the help_message to HelpView after sending it
        view = HelpView(help_message)
        await help_message.edit(view=view)


async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
