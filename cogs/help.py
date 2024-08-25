import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # ================= Help Categories =======================


    async def list(self, ctx, command=None):
        if command:
            return
        embed = discord.Embed(title="Help - Commands List", color=discord.Color.dark_purple())

        embed.add_field(name="Command Prefix: &", value=("Needed help, are ya?"))
        # Fun Commands
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
        embed.add_field(name="**Moderation Commands**", value=(
            "`&mute [userID] [reason]` - *Mute a user.*\n"
            "`&unmute [userID]` - *Unmute a user.*\n"
            "`&kick [userID]` - *Kick a user out.*\n"
            "`&ban [userID]` - *Ban a user.*\n"
            "`&muterole_create` - *Create mute role if not existed. This will override mute permissions and role to all categories and channels.*\n"
            "`&clear [all/number]` - *Delete messages.*\n"
        ), inline=False)
        embed.add_field(name="Music Commands", value=(
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
            "`&stream247 [deephouse/lofi/hardstyle]` - *Enters 24/7 mode and start streaming/playing defined genres.*\n"
            "`&stop247` - *Similar to how `stop` command works.*\n"
        ), inline=False)
        embed.add_field(name="Miscellaneous", value=(
            "`&usercount` - *Let you know how many members are in the current server.*\n"
        	"`&ticket` - Create a ticket to send a request for channel creation."), inline=False)
        await ctx.reply(embed=embed)

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
