import discord
from discord.ext import commands
from discord.ui import Select, View

class HelpDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Automod", description="List of automod configuration commands."),
            discord.SelectOption(label="Fun Commands", description="List of fun commands"),
            discord.SelectOption(label="Games", description="List of available games."),
            discord.SelectOption(label="Image Manipulation", description="List of image manipulation commands."),
            discord.SelectOption(label="Level Commands", description="List of available level commands."),
            discord.SelectOption(label="Lunacy Commands", description="List of available Lunacy commands."),
            discord.SelectOption(label="Manager", description="List of available manager commands."),
            discord.SelectOption(label="Miscellaneous", description="List of miscellaneous commands"),
            discord.SelectOption(label="Moderation Commands", description="List of moderation commands"),
            discord.SelectOption(label="Music Commands", description="List of music commands"),
            discord.SelectOption(label="Welcomer", description="List of welcomer commands"),
            discord.SelectOption(label="Youtube Notification", description="List of youtube notification commands"),
        ]
        super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        embed = discord.Embed(title=f"Help - {category}", color=discord.Color.dark_purple())
        
        # Define embeds based on category
        if category == "Fun Commands":
            embed.add_field(name="**Fun Commands** (1/2)", value=(
                "`pet [@user1] [@user2]` - Pet one or two users and send a cute gif.\n"
                "`tape @user` - Tape a user and send a funny gif.\n"
                "`grab [@user1] [@user2]` - Grab one or two users and send a funny gif.\n"
                "`slap [@user1] [@user2]` - Slap someone (or two people) if you feel your hand is itchy. Harmless.\n"
                "`hug [@user1] [@user2]` - Hug someone (or two people). Simple as that.\n"
                "`roll [sides]` - Roll a dice with the specified number of sides (default is 6).\n"
                "`choose [option1] [option2] [...]` - Let the bot choose an option for you.\n"
                "`8ball [question]` - Consult the magic 8-ball to answer your question.\n"
            ), inline=False)

            embed.add_field(name="**Fun Commands** (2/2)", value=(
                "`coinflip` - Flip a coin. Useful when making a bet against someone.\n"
                "`urban [term]` - Search Urban Dictionary for a definition.\n"
                "`cat` - Measures how much you look like a cat. 🐱\n"
                "`kurin` - Measures how much \"hyperkuru\" you currently are.\n"
                "`messup` - Mess up the message above you or the message you are replying to.\n"
                "`match @user1 @user2` - Show matchmaking result between two users. Love love.\n"
                "`emojify <text>` - Convert text to emoji letters.\n"
                "`uwuify <text>` - Convert text to uwu speak with secret easter eggs.\n"
                "`memetemplates` - Show available meme templates.\n"
                "`meme [template ID] [text1] | [text2]` - Generate a meme with the specified template and text.\n"
            ), inline=False)


        elif category == "Moderation Commands":
            embed.add_field(name="**Moderation Commands** (1/2)", value=(
                "`kick [@mention/userID] [reason]` - Kick a user from the server.\n"
                "`ban [@mention/userID] [reason]` - Ban a user from the server.\n"
                "`unban [userID]` - Unban a user.\n"
                "`mute [@mention/userID] [duration] [reason]` - Mute a user for a specified duration.\n"
                "`unmute [@mention/userID]` - Unmute a user.\n"
                "`timeout [@mention/userID] [duration] [reason]` - Timeout a user for a specified duration.\n"
                "`remove_timeout [@mention/userID]` - Remove timeout from a user.\n"
            ), inline=False)
            embed.add_field(name="**Moderation Commands** (2/2)", value=(
                "`warn [@mention/userID] [reason]` - Issue a warning to a user.\n"
                "`warnings [@mention/userID]` - Display warnings for a user.\n"
                "`clear_warn [@mention/userID]` - Clear warnings for a user.\n"
                "`clear [number/all]` - Delete a number of messages or all possible messages.\n"
                "`createmuterole [role name]` - Create a mute role if it doesn't exist.\n"
                "`setmuterole @muterole` - Set the default mute role for moderation purposes.\n"
            ), inline=False)
        elif category == "Music Commands":
            embed.add_field(
                name="**Music Commands**",
                value=(
                    "`play (youtube/soundcloud) (query)` - Play music from specified platform.  \n"
                    "`pause` - Pause the currently playing song.\n"
                    "`resume` - Resume the paused song.\n"
                    "`stop` - Stop the player and clear the queue.\n"
                    "`skip` - Skip the currently playing song.\n"
                    "`queue` or `q` - Display the current song queue.\n"
                    "`volume [0-100]` - Adjust the volume of the player.\n"
                    "`shuffle` - Shuffle the current song queue.\n"
                    "`loop [song/queue/none]` - Toggle loop mode for the current song. Song mode will repeat current playing song, queue mode will repeat the whole queue, and none is nothing.\n"
                ),
                inline=False
            )
        elif category == "Miscellaneous":
            embed.add_field(
                name="Miscellaneous",
                value=(
                    "`ping` - Displays the bot's latency.\n"
                    "`stats` - Displays bot statistics.\n"
                    "`membercount` - Shows the number of members in the current server.\n"
                    "`whois [@user]` - Displays information about a user.\n"
                    "`avatar [@user]` - Fetches and displays your avatar or the mentioned user's avatar.\n"
                    "`guildinfo` - Shows information about the guild.\n"
                    "`info` - Displays information about the bot.\n"
                    "`servericon` - Shows the server icon in full resolution.\n"
                    '`poll "<question>" <option1> <option2>` - Creates a reaction poll with up to 10 options.\n'
                    "`remind <time> <reminder>` - Sets a reminder (e.g. 1h30m Check oven).\n"
                    "`roleinfo [@role]` - Displays detailed information about a role.\n"
                    "`channelinfo [#channel]` - Displays information about a channel.\n"
                    "`firstmessage` - Finds the first message in the current channel.\n\n"
                ),
                inline=False
            )

        elif category == "Games":
            embed.add_field(name="Game", value=(
                "`battle @user1 @user2` - Start a virtual battle between 2 \"hot tempered\" users.\n"
                "`hangman` - Play Hangman game.\n"
                "`rps [rock/paper/scissors]` - Play Rock Paper Scissors with bot.\n"
                "`numberguess` - Play Number Guessing game.\n"
                "`scramble` - Play Word Scramble game.\n"
                "`bet [red/black/number (range 0 - 36)]` - Play Roulette game.\n"
                "`memory` - Play Memory Game."
            ), inline=False)
        elif category == "Manager":
            embed.add_field(name="**Manager Commands (1/2)**", value=(
                "`addrole <@user> <@role>` - Assigns a role to a specified user.\n"
                "`removerole <@user> <@role>` - Removes a role from a specified user.\n"
                "`createrole <rolename> [hex color]` - Creates a new role with an optional color (hex code).\n"
                "`deleterole <@role>` - Deletes a specified role.\n"
                "`listroles` - Lists all roles in the server with the number of members in each.\n"
                "`createchannel <name> [type] [category]` - Creates a new channel of specified type (text/voice/stage) and optional category.\n"
                "`createcategory <name>` - Creates a new category with the specified name.\n"
                "`deletechannel <#channel>` - Deletes a specified channel.\n"
            ), inline=False)
            embed.add_field(name="**Manager Commands (2/2)**", value=(
                "`deletecategory <category name>` - Deletes a category with the specified name.\n"
                "`setchannelname <#channel> <new name>` - Changes the name of a specified channel.\n"
                "`setchannelcategory <#channel> <category name>` - Moves a channel to a different category.\n"
                "`listchannels` - Lists all channels in the server.\n"
                "`viewsettings` - View the current server settings (Administrator only).\n"
                "`setservername <new name>` - Changes the server's name.\n"
                "`setverificationlevel <level>` - Sets server verification level (0-4).\n"
                "`listbans` - Lists all banned users in the server.\n"
            ), inline=False)
        elif category == "Level Commands":
            embed.add_field(name="**Level Commands**", value=
                "`level @user_mention [optional]` - Check the level and XP of a user in the current guild.\n"
                "`setlevelchannel #channel_mention` - Set the channel where level-up messages will be sent.\n"
                "`restrictxpchannel #channel_mention` - Mark a channel as restricted/unrestricted from awarding XP.\n"
                "`restrictxpuser @user_mention` - Restrict/unrestrict a user from gaining XP in the server.\n"
                "`grantxp @user_mention [XP amount]` - Grants a specified amount of XP to a user.\n"
                "`resetxp [optional @user_mention] ` - Resets a user's XP and level to default values and removes any level roles.\n"
                "`toplevel` - Display the top users by XP in the current guild.\n"
                "`viewlevelroles` - View all the level-up roles set in the current guild.\n"
                "`setlevelrole [level] @role_mention` - Set a role to be given when a user reaches a specific level.\n"
                "`togglexpblock` - Mark a guild as restricted from awarding XP.\n"
                "`setxpamount [amount]` "
                , inline=False)
        elif category == "Image Manipulation":
            embed.add_field(name="**Image Manipulation Commands** (1/2)", value=(
                "`pixelate` - Pixelate the image.\n"
                "`distort` - Apply random distortions to the image.\n"
                "`rain` - Add a rain effect to the image.\n"
                "`spin` - Create a spinning animation of the image.\n"
                "`invert` - Invert the colors of the image.\n"
                "`grayscale` - Convert the image to grayscale.\n"
                "`blur [radius]` - Blur the image with an optional radius (default is 2.0).\n"
                "`warp` - Warp the image with a rotation effect.\n"
            ), inline=False)
            embed.add_field(name="**Image Manipulation Commands** (2/2)", value=(
                "`deepfry` - Deep-fry the image.\n"
                "`colorize <hex_color>` - Change the image color based on a hex code.\n"
                "`sharpen` - Sharpen the image.\n"
                "`emboss` - Apply an emboss effect to the image.\n"
                "`edge` - Detect edges in the image.\n"
                "`flip` - Flip the image vertically.\n"
                "`magic` - Apply a cursed effect to the image.\n"
            ), inline=False)
        elif category == "Welcomer":
            embed.add_field(name="Welcomer Commands", value=(
                "`configuremessages` - Guides the moderator through configuring welcome, goodbye, and new account messages.\n" 
                "`setgreetchannel #channel_name` - Set the welcoming channel.\n"
                "`setgoodbyechannel #channel_name` - Set the goodbye channel.\n"
            ), inline=False)
        elif category == "Youtube Notification":
            embed.add_field(name="Youtube Notification Commands", value=(
                "`notifychannel #channel_name` - Set the channel for receiving YouTube notifications.\n"
                
                "`trackchannel <url/channelID> [video count]` - Track a YouTube channel and receive notifications. "
                "Optional: specify video count (1-10, default 5).\n"
                
                "`settrackcount <url/channelID> <video count>` - Update the number of videos to track (1-10).\n"
                
                "`confignotimessage <url/channelID>` - Configure the custom notification message for a tracked YouTube channel.\n"
            ), inline=False)
        elif category == "Automod":
                embed.add_field(name="**Automod Configuration commands**", value=(
                    "`automod` - Show all available automod features.\n"
                    "`automod toggle <feature> on/off` - Toggle certain automod feature.\n"
                    "`automod all on/off` - Toggle all automod features.\n"
                ),
                inline=False
            )
                embed.add_field(name="**Threshold Configuration commands**", value=(
                    "`threshold` - Show and configure thresholds.\n"
                    "`threshold set <type> <value>` - Modify threshold.\n"
                ),
                inline=False
            )
                embed.add_field(name="**Other commands**", value=(
                    "`automodlog #channel_name` - Set the channel for AutoMod log.\n"
                    "`addfilterword` - Add a word to the word filter.\n"
                    "`removefilterword` - Remove a word from the word filter.\n"
                ),
                inline=False
            )
        elif category == "Lunacy Commands":
            embed.add_field(name="**Currency Commands**", value=(
                "`balance` - Check your Luna balance.\n"
                "`daily` - Collect your daily Luna with streak bonuses!\n"
                "`work` - Work to earn Luna.\n"
                "`gamble [amount]` - Bet your Luna on a coinflip!\n"
                "`trade @user [amount]` - Trade Luna with another user.\n"
                "`leaderboard` - Show the richest users.\n"
            ), inline=False)
            
            embed.add_field(name="**Shop & Inventory**", value=(
                "`shop` - View the Luna shop with regular and limited items.\n"
                "`buy [item_id] [quantity]` - Buy an item from the shop.\n"
                "`inventory` - View your inventory.\n"
            ), inline=False)
            
            embed.add_field(name="**Achievements**", value=(
                "`achievements` - View your achievements and progress.\n"
            ), inline=False)
        await interaction.response.edit_message(embed=embed)
        

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=30)
        self.help_message = None
        self.add_item(HelpDropdown())

    async def on_timeout(self):
        try:
            if self.help_message:
                await self.help_message.delete()
        except discord.NotFound:
            pass

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        """Displays the help message."""
        embed = discord.Embed(
            title="Help",
            description="Select a category from the dropdown. Command prefix: `&`",
            color=discord.Color.dark_purple()
        )

        view = HelpView()

        # Send the help message and get the message object
        help_message = await ctx.send(embed=embed, view=view)

        # Assign the message object to the view
        view.help_message = help_message


async def setup(bot):
    await bot.add_cog(Help(bot))
