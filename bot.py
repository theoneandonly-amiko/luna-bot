import discord
from discord.ext import commands, tasks
from discord.ext.commands import BucketType
from dotenv import load_dotenv
import os
import time
from googleapiclient.discovery import build
import random
import requests
import asyncio
import logging
import json
import yt_dlp
import re


# Configure logging
logging.basicConfig(
    filename='bot_activity.log',  # Specify the file to save logs
    level=logging.INFO,           # Set logging level to INFO or higher
    format='%(asctime)s - %(message)s'
)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
DEV_USER_ID = int(os.getenv('DEV_USER_ID'))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="&", intents=intents, help_command=None)

# Initialize the YouTube API client
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# Function to get the latest video details from a channel
def get_all_videos(channel_id):
    try:
        request = youtube.search().list(
            part="snippet",
            channelId=channel_id,
            order="date",
            maxResults=50
        )
        response = request.execute()
        if 'items' in response and response['items']:
            return response['items']  # Return all videos
        return []
    except Exception as e:
        logging.error(f"Error fetching videos: {e}")
        return []

BLACKLIST_FILE = 'blacklist.json'
blacklisted_users = set()

def load_blacklist():
    global blacklisted_users
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as file:
                blacklisted_users = set(json.load(file))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error loading blacklist from {BLACKLIST_FILE}: {e}")

def save_blacklist():
    try:
        with open(BLACKLIST_FILE, 'w') as file:
            json.dump(list(blacklisted_users), file)
    except IOError as e:
        logging.error(f"Error saving blacklist to {BLACKLIST_FILE}: {e}")

# Load initial blacklist
load_blacklist()

# =========================================================
@bot.event
async def on_ready():
    print(f"{bot.user} is connected and ready to use.")
    update_presence.start()
# =================== Youtube Presence ====================
@tasks.loop(minutes=5)
async def update_presence():
    videos = get_all_videos(YOUTUBE_CHANNEL_ID)
    if videos:  # Check if the list is not empty
        random_video = random.choice(videos)  # Choose a random video from the list
        title = random_video['snippet']['title']
        channel = random_video['snippet']['channelTitle']
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f'{title} by {channel}'
        ))
    else:
        logging.warning("No videos found or failed to fetch videos.")

@update_presence.before_loop
async def before_update_presence():
    await bot.wait_until_ready()
# ================= CHECK BLACKLIST =======================
def check_blacklist():
    async def predicate(ctx):
        if ctx.author.id in blacklisted_users:
            await ctx.send("You are currently blacklisted and cannot use this command.")
            return False
        return True
    return commands.check(predicate)
# ========================================================
# Log all commands used
@bot.event
async def on_command(ctx):
    command_name = ctx.command
    user = ctx.author
    guild = ctx.guild
    channel = ctx.channel
    logging.info(f"Command '{command_name}' invoked by {user} in guild '{guild}' in channel '{channel}'.")

# Log errors
@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Error in command '{ctx.command}' by {ctx.author}: {error}")

# ================= Help Categories =======================

@bot.command(name='help')
async def help(ctx):
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
    embed.add_field(name="Music Commands (unavailable due to Youtube requirements. Do not attempt to spam these commands.)", value=(
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
    await ctx.send(embed=embed)

# Command to show developer features
@bot.command(name='dev')
async def dev(ctx):
    if ctx.author.id != DEV_USER_ID:
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
@bot.command(name='info')
@check_blacklist()
async def help(ctx):
    embed = discord.Embed(title="**About me**", color=discord.Color.brand_green())
    embed.add_field(name="Short description", value=(
        "I\'m Luna, the bot serve with most basic purposes. Currently I\'m under development, but I\'ll be sure to not make you feel disappointed, hehe. ;)\n"
        "I was built from the migrations of Miko bot and Amiker bot, because of some inconvenient monitors and constant downtime from server side, with some more improvements and optimisations. If there\'s any new feature, feel free to suggest. Any cockroach I made? Catch them. 😁"
    ), inline=False)
    await ctx.send(embed=embed)

# =============== Keyword Response =================
# Organized keywords and responses
keyword_responses = {
    'said they were human': ['Well, tell them to finish the captcha, then. 🙄', 
                             'I suppose which bot ever said so were a member of Online Bank Scammer companies. 🤔', 
                             'Are they okay?', 
                             'Pfff, I can also say I am a human, if you trust. 🥱', 
                             'I don\'t know but maybe one day they will become human, and you will become the bot. It\'s like an exchange, but... Who knows? 🤷‍♀️', 
                             'They probably just need a better captcha. 🤖🔒', 
                             'Maybe they\'re just aspiring to be like us bots. 🤔', 
                             'Humans, always trying to blend in with the bots. 🙄', 
                             'Being human sounds like a lot of work. 😅', 
                             'Humans... can\'t live with them, can\'t live without them. 🤷‍♀️'],

    'bot dumb': ['I\'m under development, duh... 😒', 
                 'Not as much as you. 🥱',
                 'Give me time to improve, come on... 😥',
                 'Sheesh... Stop it.', 
                 'I\'m still learning, cut me some slack! 😅', 
                 'My AI is a work in progress, just like your jokes.', 
                 'That\'s...not very nice. I\'m doing my best! 🤖💔', 
                 'Says the one who talks to bots all day. 🙃'],

    'dumb bot': ['No. More. Dumb. Accusations.', 
                 'Not dumb, just processing... 🤔', 
                 'I\'m learning every day, just like you.', 
                 'Who are you calling dumb? Watch it, human! 😡', 
                 'I may be a bot, but I\'m not that easy to fool. 😎',
                 'I\'m under development, so cut me some slack... 😒',
                 'No more accusations, please.'],

    'suggest some game' : ['Ever heard of ADOFAI?🔥<>❄️', 
                           'Average Fornite player? Hmm...', 
                           'What about CIU then?', 
                           'Go outside and shout out loud if you love Geometry dash', 
                           'I\'m farming in Hay Day right now. Sorry, too much work.', 
                           'How about Tetris?', 
                           'I\'m not really enjoy playing FPS game, but yeah, if you asked, Valorant.', 
                           'We Become What We Behold, hehehe 😈', 
                           'How about trying out Among Us? Betraying your friends has never been more fun! 🔪🎲', 
                           'Have you played Stardew Valley? Farming is surprisingly therapeutic. 🌾🐓', 
                           'You should check out The Witcher 3: Wild Hunt. A masterpiece of storytelling and open world exploration. 🐺🗡️', 
                           'Minecraft. Because sometimes, building a blocky universe is all you need. 🌍🧱', 
                           'Ever heard of Celeste? It\'s a challenging platformer with a heartfelt story. 🍓🏔️', 
                           'Portal 2. Solve puzzles, laugh at GLaDOS\'s sarcasm, and never trust a cube again. 🧩🤖', 
                           'How about diving into the vast world of Skyrim? Dragons, magic, and endless adventures await. 🐉⚔️', 
                           'If you\'re into strategy, try Civilization VI. Just one more turn... 🌍🏛️'],

    'hey luna': ['Yes?', 
                 'What do you want?', 
                 'I\'m here!', 
                 'You called?', 
                 'Hello!', 
                 'Uh huh?', 
                 'What do you want?', 
                 'Did I told you that I was here? 🥴', 
                 'Hm?',
                 'Yes, I\'m here! What\'s up?',
                 'Hey there! Need assistance?',],

    'meow': ['meow!',
             'meow? meow meow!',
             'meow!! meow meow...',
             'meow.'],

    'Meow': ['meow!',
             'meow? meow meow!',
             'meow!! meow meow...',
             'meow.']
    # Add more keywords and responses as needed
}

@bot.event
@check_blacklist()
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore messages sent by the bot itself

    # Check for keywords and send appropriate responses with username
    for keyword, responses in keyword_responses.items():
        if keyword in message.content.lower():
            response = random.choice(responses)
            await message.channel.send(f'{response}')
            break  # Exit loop after sending a response

    await bot.process_commands(message)  # "Again, please don't stop working", Amiko said.

# ================ Random gif picker (locally) =======================
# Function to fetch a random pet GIF from the local assets folder
def fetch_random_gif():
    asset_folder = 'assets/pet'
    gif_files = [f for f in os.listdir(asset_folder) if f.endswith('.gif')]
    if not gif_files:
        return None
    return random.choice(gif_files)

# Function to fetch a random grab GIF from the local assets folder
def fetch_random_grab_gif():
    asset_folder = 'assets/grab'
    gif_files = [f for f in os.listdir(asset_folder) if f.endswith('.gif')]
    if not gif_files:
        return None
    return os.path.join(asset_folder, random.choice(gif_files))

# ========================== Fun Commands ==============================
# Pet command
@bot.command(name='pet')
@check_blacklist()
async def pet(ctx, *users: discord.User):
    if not users:
        await ctx.send("Please mention at least one user to pet.")
        return

    # Check if the user is trying to pet themselves as the only user
    if len(users) == 1 and users[0] == ctx.author:
        funny_responses = [
            "Why did you even try petting yourself at first, duh?",
            "That's not how it works!",
            "Maybe ask someone else to pet you?",
            "Self-petting detected. Petting others. No care mode: On."
        ]
        response = random.choice(funny_responses)
        await ctx.send(response)
        return

    # Filter out self-mentions from the users list
    valid_users = [user for user in users if user != ctx.author]

    if not valid_users:
        await ctx.send("Please mention at least one user other than yourself to pet.")
        return

    pet_gif = fetch_random_gif()

    if len(valid_users) == 1:
        user = valid_users[0]
        if user == bot.user:
            bot_responses = [
                "I cannot pet myself, the same with you. 😶",
                "Maybe you try it.",
                "I'm not designed to pet myself!",
                "Ask someone else to pet me.",
                "I'm flattered, but I can't do that. 😪"
            ]
            response = random.choice(bot_responses)
            await ctx.send(response)
        else: # If there's only 1 valid user mentioned (except bot and the author)
            pets = [
                "{0} pets {1} on the head.",
                "{0} just come and pet the cutest creature in the world: {1}",
                "{0} cannot resist to pet {1} and they just did it*",
                "{0} petted {1} because they're too cute to not being petted*"
            ]
            response = random.choice(pets).format(ctx.author.mention, user.mention)
            if pet_gif:
                pet_gif_path = os.path.join('assets/pet', pet_gif)
                file = discord.File(pet_gif_path, filename=pet_gif)

                embed = discord.Embed(
                    description=response,
                    color=discord.Color.magenta()
                )
                embed.set_image(url=f"attachment://{pet_gif}")

                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(response)
    elif len(valid_users) == 2: # 2 different users mentioned at the same time.
        user1, user2 = valid_users
        pets = [
            "{0} pets {1} on the head.",
            "{0} just come and pet the cutest creature in the world: {1}*",
            "{0} cannot resist to pet {1} and they just did it*",
            "{0} tickles {1}'s belly.",
            "{0} petted {1} because they're too cute to not being petted*"
        ]
        response = random.choice(pets).format(user1.mention, user2.mention)
        if pet_gif:
            pet_gif_path = os.path.join('assets', pet_gif)
            file = discord.File(pet_gif_path, filename=pet_gif)

            embed = discord.Embed(
                description=response,
                color=discord.Color.blue()
            )
            embed.set_image(url=f"attachment://{pet_gif}")

            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(response)
    else:
        await ctx.send("Please mention only one or two users to pet.")
        return

# Grab command
@bot.command(name='grab')
@check_blacklist()
async def grab(ctx, *users: discord.User):
    if not users:
        await ctx.send("Uh, who to grab? Air? Space? 🤔")
        return

    user = random.choice(users)
    if bot.user in users and ctx.author in users and len(users) == 2:
        grabs = [
            "{0} grabs {1} by the arm and.",
            "Look, {0} and {1} are grabbing each other.",
            "{0} just stole {1} from the road.",
            "{0} just come and picked {1} up."
        ]
        grab_gif = fetch_random_grab_gif()
        response = random.choice(grabs).format(ctx.author.mention, bot.user.mention, user.mention)

        if grab_gif:
            file = discord.File(grab_gif, filename=os.path.basename(grab_gif))

            embed = discord.Embed(
                description=response,
                color=discord.Color.blue()
            )
            embed.set_image(url=f"attachment://{os.path.basename(grab_gif)}")

            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(response)
    elif user == bot.user:
        responses = [
            "I cannot grab myself, try doing it with yourself. 🥱",
            "Maybe you try it.",
            "I'm not designed to grab myself! 😫",
            "Ask someone else to grab me.",
            "Nope. I cannot do so if you cannot. 😏"
        ]
        response = random.choice(responses)
        await ctx.send(response)
    elif user == ctx.author:
        self_responses = [
            "You think you can do it? 🤨",
            "You cannot make yourself fly by doing so.",
            "Interesting choice, trying to grab yourself! 🤔",
            "Maybe rethink the strategy there. 😗"
        ]
        response = random.choice(self_responses)
        await ctx.send(response)
    else:
        grabs = [
            "{0} grabs {1} by the arm.",
            "Go, {0}, go and grab {1}!",
            "{0} just stole {1} from the road. Whew!",
            "{0} just come and picked {1} up"
        ]
        grab_gif = fetch_random_grab_gif()
        response = random.choice(grabs).format(ctx.author.mention, user.mention)

        if grab_gif:
            file = discord.File(grab_gif, filename=os.path.basename(grab_gif))

            embed = discord.Embed(
                description=response,
                color=discord.Color.dark_magenta()
            )
            embed.set_image(url=f"attachment://{os.path.basename(grab_gif)}")

            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(response)

# Compliment command
@bot.command(name='compliment', aliases=['nice', 'sweet'])
@check_blacklist()
async def compliment(self, ctx, user: commands.MemberConverter):
        compliments = [
            f"{user.mention}, you are as bright as a shooting star! 🌟",
            f"{user.mention}, you have a heart of gold. 💛",
            f"{user.mention}, you bring sunshine into everyone's day! 🌞",
            f"{user.mention}, your positivity is infectious! 😄",
            f"{user.mention}, you're more fun than a ball pit filled with candy. 🍬🎉",
            f"{user.mention}, your kindness knows no bounds. 🌈",
            f"{user.mention}, you're a gift to those around you! 🎁",
            f"{user.mention}, you're as sweet as a freshly baked cookie! 🍪",
            f"{user.mention}, you make the world a better place just by being in it! 🌍"
        ]
        
        compliment = random.choice(compliments)
        await ctx.send(compliment)

# Roll dice
@bot.command(name='roll', help='Rolls a dice.')
@check_blacklist()
async def roll(ctx, sides: int = 6):
    if sides < 1 or sides > 100:
        await ctx.send('Please choose a number of sides between 1 and 100.')
        return
    result = random.randint(1, sides)
    await ctx.send(f'🎲 You rolled a {result} on a {sides}-sided dice!')

# 8-Ball Command
@bot.command(name='8ball', help='Answers a yes/no question.')
@check_blacklist()
async def eight_ball(ctx, *, question: str = None):
    if question is None:
        await ctx.send("Magic 8-ball cannot answer your empty question. Ask again.")
        return

    responses = [
        'Yes', 'No', 'Maybe', 'Ask again later', 'Definitely', 'I wouldn\'t count on it',
        'Absolutely', 'Not sure', 'Probably', 'Absolutely not', 'Without a doubt', 'Very doubtful'
    ]
    response = random.choice(responses)
    await ctx.send(f'🔮 {response}')


# Coin flip
@bot.command(name='flip', help='Flips a coin.')
@check_blacklist()
async def flip(ctx):
    result = random.choice(['Heads', 'Tails'])
    await ctx.send(f'🪙 The coin landed on {result}!')

# Make a decision for your life, lmao
@bot.command(name='choose', help='Makes a decision for you.')
@check_blacklist()
async def choose(ctx, *choices: str):
    if len(choices) < 2:
        await ctx.send('You need to provide at least two choices. If not then you already have your decision, duh. 🤷‍♀️')
        return
    decision = random.choice(choices)
    await ctx.send(f'Well, I choose: {decision}')

# Urban Dictionary
@bot.command(name='urban', help='Searches Urban Dictionary for a definition.')
@check_blacklist()
async def urban(ctx, *, term: str = None):
    if term is None:
        await ctx.send("What are you looking for? I cannot see thin air.")
        return

    response = requests.get(f'https://api.urbandictionary.com/v0/define?term={term}')
    data = response.json()

    if data['list']:
        definition = data['list'][0]['definition']
        example = data['list'][0]['example']
        embed = discord.Embed(title=f'Urban Dictionary: {term}', description=definition, color=discord.Color.blue())
        embed.add_field(name='Example', value=example, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f'No results found for {term}')

# ==================== GAME COMMAND ====================
# The virtual battle
@bot.command()
@check_blacklist()
async def battle(ctx, user1: discord.Member, user2: discord.Member):
    if user1 == user2:
        await ctx.send("You can't battle yourself!")
        return
    
    user1_hp = 100
    user2_hp = 100
    
    attack_responses = [
        "{attacker} throws a punch at {defender}, dealing {damage} damage!",
        "{attacker} kicks {defender}, causing {damage} damage!",
        "{attacker} smashes {defender} with a mighty blow, dealing {damage} damage!",
        "{attacker} strikes {defender} fiercely, causing {damage} damage!",
        "{attacker} hurls a rock at {defender}, dealing {damage} damage!",
        "{attacker} slaps {defender}, causing {damage} damage!",
        "{attacker} tries dropping a bomb to {defender}, causing {damage} damage!"
    ]
    
    def create_battle_embed():
        embed = discord.Embed(title="An epic battle has started!", color=discord.Color.red())
        embed.add_field(name=user1.display_name, value=f"HP: {user1_hp}", inline=True)
        embed.add_field(name="VS", value="\u200B", inline=True)
        embed.add_field(name=user2.display_name, value=f"HP: {user2_hp}", inline=True)
        return embed
    
    message = await ctx.send(embed=create_battle_embed())
    
    while user1_hp > 0 and user2_hp > 0:
        attacker, defender = (user1, user2) if random.choice([True, False]) else (user2, user1)
        damage = random.randint(5, 20)
        
        if attacker == user1:
            user2_hp = max(0, user2_hp - damage)
        else:
            user1_hp = max(0, user1_hp - damage)
        
        response = random.choice(attack_responses).format(attacker=attacker.display_name, defender=defender.display_name, damage=damage)
        embed = create_battle_embed()
        await message.edit(content=response, embed=embed)
        await asyncio.sleep(2)
    
    winner = user1 if user2_hp == 0 else user2
    await ctx.send(f"{winner.display_name} wins the battle!")

@bot.command(name='cat')
@check_blacklist()
async def cat_percent(ctx):
    percentage = random.randint(0, 100)
    embed = discord.Embed(
        title="Cat Percentage",
        description=f"{ctx.author.mention}, you look {percentage}% like a cat! 🐱",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name='kurin')
@check_blacklist()
async def kurin_percent(ctx):
    custom_emoji = "<a:kurin:1270461365122760877>"
    custom_emoji_id = "1270461365122760877"
    percentage = random.randint(0, 100)
    embed = discord.Embed(
        title = "Kuru kuru~! Kururin!",
        description=f"{ctx.author.mention} hyperkuru rate is {percentage}%! {custom_emoji}",
        color=discord.Color.purple()
    )
    message = await ctx.send(embed=embed)

    emoji = discord.PartialEmoji(name='cat_emoji', id=int(custom_emoji_id))
    await message.add_reaction(emoji)

# ======================== Channel and Category Managements====================
@bot.command(name='ticket')
async def ticket(ctx):
    # Initialize the interactive message process
    await start_ticket_process(ctx)

async def start_ticket_process(ctx):
    questions = [
        "What's the name for your channel?",
        "Do you want to make the channel private? (yes/no)",
        "If it's private, please provide the user IDs you wish to add to your channel, separate by commas (,). Type 'None' if you wish to be alone, or if the channel was public."
    ]

    answers = []

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    for question in questions:
        await ctx.send(question)
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond. The ticket request has been closed.")
            return

        answers.append(msg.content)

    # Send the ticket details to the destination channel
    await send_ticket_details(ctx, answers)

async def send_ticket_details(ctx, answers):
    channel_name = answers[0]
    private = answers[1].lower() == 'yes'
    user_ids = [int(user_id) for user_id in answers[2].split(',') if user_id.strip() != 'None']

    # Create the embed message
    embed = discord.Embed(title=f"{ctx.author.name}'s Ticket", color=discord.Color.dark_magenta())
    embed.add_field(name="Channel Name", value=channel_name, inline=False)
    embed.add_field(name="Private or Not", value="Yes" if private else "No", inline=False)
    embed.add_field(name="Other User IDs", value=', '.join(map(str, user_ids)) if user_ids else 'None', inline=False)

    # Send the embed message to the destination channel
    destination_channel_id = 1271775821706559488
    destination_channel = ctx.guild.get_channel(destination_channel_id)

    if destination_channel:
        await destination_channel.send(embed=embed)

    # Notify the user
    await ctx.send(f"Your ticket details have been sent. Thank you!")
    await asyncio.sleep(5)
    await ctx.channel.purge(limit=8)  # Adjust this as needed

# Category creation
@bot.command(name='category')
@commands.has_permissions(manage_guild=True)
async def category(ctx, action: str, *args):
    guild = ctx.guild

    if action.lower() == "create":
        if len(args) < 1:
            await ctx.send("Invalid command usage for 'create'. Usage: `!category create <category_name>`")
            return

        category_name = " ".join(args)
        existing_category = discord.utils.get(guild.categories, name=category_name)
        if existing_category is None:
            await guild.create_category(category_name)
            await ctx.send(f'Category `{category_name}` created!')
        else:
            await ctx.send(f'Category `{category_name}` already exists.')

    elif action.lower() == "delete":
        if len(args) != 1:
            await ctx.send("Invalid command usage for 'delete'. Usage: `!category delete <category_id>`")
            return

        try:
            category_id = int(args[0])
        except ValueError:
            await ctx.send("Invalid category ID.")
            return

        category = discord.utils.get(guild.categories, id=category_id)
        if category:
            await category.delete()
            await ctx.send(f'Category `{category.name}` deleted!')
        else:
            await ctx.send(f'Category with ID `{category_id}` not found.')

    else:
        await ctx.send("Invalid action. Use `create` or `delete`.")

# Error handling for missing permissions and command errors
@category.error
async def category_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to manage categories.")
    else:
        await ctx.send("An error occurred while processing the command.")
# Error handling for missing permissions
@category.error
async def category_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to manage channels.")

# Channel Creation
@bot.command(name='channel')
@commands.has_permissions(manage_channels=True)
async def channel(ctx, action: str, *args):
    """Creates or deletes a text channel, with options to make it private and add users. Category ID is optional."""
    guild = ctx.guild

    # Initialize variables
    private = False
    user_ids = []
    category_id = None

    if action.lower() == "create":
        if len(args) < 1:
            await ctx.send("Invalid command usage for 'create'. Usage: `!channel create <channel_name> [category_id] [--private [user_ids...]]`")
            return

        channel_name = args[0]
        if len(args) > 1 and args[1].isdigit():
            try:
                category_id = int(args[1])
                args = args[2:]
            except ValueError:
                await ctx.send("Invalid category ID.")
                return
        else:
            args = args[1:]

        if '--private' in args:
            private = True
            args = list(filter(lambda x: x != '--private', args))

        user_ids = [int(arg) for arg in args if arg.isdigit()]

        category = discord.utils.get(guild.categories, id=category_id) if category_id else None
        if category_id and not category:
            await ctx.send(f'Category with ID `{category_id}` not found.')
            return

        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel is None:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=not private)
            }
            if private and user_ids:
                for user_id in user_ids:
                    user = discord.utils.get(guild.members, id=user_id)
                    if user:
                        overwrites[user] = discord.PermissionOverwrite(read_messages=True)

            await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
            await ctx.send(f'{"Private " if private else ""}Channel `{channel_name}` created{" in category `" + category.name + "`" if category else ""}.')
        else:
            await ctx.send(f'Channel `{channel_name}` already exists.')

    elif action.lower() == "delete":
        if len(args) != 1:
            await ctx.send("Invalid command usage for 'delete'. Usage: `!channel delete <channel_id>`")
            return

        try:
            channel_id = int(args[0])
        except ValueError:
            await ctx.send("Invalid channel ID.")
            return

        channel = discord.utils.get(guild.text_channels, id=channel_id)
        if channel:
            await channel.delete()
            await ctx.send(f'Channel `{channel.name}` deleted!')
        else:
            await ctx.send(f'Channel with ID `{channel_id}` not found.')

    else:
        await ctx.send("Invalid action. Use `create` or `delete`.")

# Error handling for missing permissions and command errors
@channel.error
async def channel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to manage channels.")
    else:
        await ctx.send("An error occurred while processing the command.")

# Log all commands used
@bot.event
async def on_command(ctx):
    command_name = ctx.command
    user = ctx.author
    guild = ctx.guild
    channel = ctx.channel
    logging.info(f"Command '{command_name}' invoked by {user} in guild '{guild}' in channel '{channel}'.")

# Log errors
@bot.event
async def on_command_error(ctx, error):
    logging.error(f"Error in command '{ctx.command}' by {ctx.author}: {error}")

# ================== Moderation ========================

# Command to ban a user by ID
@bot.command()
@check_blacklist()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user_id: int, *, reason=None):
    user = await bot.fetch_user(user_id)
    if user:
        await ctx.guild.ban(user, reason=reason)
        await ctx.send(f'Banned {user} for reason: {reason}')
    else:
        await ctx.send('User not found')

# Command to kick a user by ID
@bot.command()
@check_blacklist()
@commands.has_permissions(kick_members=True)
async def kick(ctx, user_id: int, *, reason=None):
    member = ctx.guild.get_member(user_id)
    if member:
        await member.kick(reason=reason)
        await ctx.send(f'Kicked {member} for reason: {reason}')
    else:
        await ctx.send('User not found or not in the server')

# Command to create a Muted role and set permissions
@bot.command()
@check_blacklist()
@commands.has_permissions(administrator=True)
async def muterole_create(ctx):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role:
        await ctx.send('Muted role already exists.')
    else:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True)
        await ctx.send('Muted role created and permissions set for all channels.')

# Command to mute a user by ID
@bot.command()
@check_blacklist()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, user_id: int, *, reason=None):
    member = ctx.guild.get_member(user_id)
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        await ctx.send('Muted role does not exist. Please use &muterole_create to create it.')
        return
    if member:
        await member.add_roles(role, reason=reason)
        await ctx.send(f'Muted {member} for reason: {reason}')
    else:
        await ctx.send('User not found or not in the server')

# Command to unmute a user by ID
@bot.command()
@check_blacklist()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, user_id: int):
    member = ctx.guild.get_member(user_id)
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if member and role:
        await member.remove_roles(role)
        await ctx.send(f'Unmuted {member}')
    else:
        await ctx.send('Command error: Invalid user ID, user not found, or not muted.')

@bot.command(name='clear')
@check_blacklist()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: str):
    if amount == 'all':
        await ctx.channel.purge()
    else:
        await ctx.channel.purge(limit=(int(amount) + 1))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(f"You don't have the necessary permissions to run this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        # Already handled in the check, so do nothing
        return
    else:
        # For other errors, you might want to send a message or log the error
        await ctx.send(f'An error occurred: {str(error)}')
# =================== Dev Easter Egg ===================
# Humanized Bot xd

async def send_message(channel_id, content):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(content)

@bot.command(name='message')
@commands.has_permissions(administrator=True)
async def testmsg(ctx, channel: discord.TextChannel, *, content: str):
    await send_message(channel.id, content)
    confirmation_message = await ctx.send(f'Message sent to {channel.mention}')

# ================ Music Function ======================
queue = []
IDLE_TIMEOUT = 30
current_player = None
volume_level = 0.8  # Default volume level
last_channel = None # Store the last active channel
streaming_mode = False
genre_urls = {
    'lofi': ['https://www.youtube.com/watch?v=jfKfPfyJRdk'],

    'deep_house': ['https://youtu.be/cnVPm1dGQJc?si=5g08aZZPQl5c2mtn', 'https://youtu.be/DsAd2Brhr-M?si=mFBVQn77MpqvsrIj', 'https://youtu.be/ZiyYqg75v7Y?si=hGyWqzuRYNnbU6if', 'https://youtu.be/B-rrm46WGhE?si=hi23i1aLSs7GUmHG'],

    'hardstyle': ['https://youtu.be/U3ZxZEFo1lk?si=c1ExdwWLuem8jgJZ', 'https://youtu.be/I6Tgl33CAjc?si=20pUmynbbnB5Uuwt', 'https://youtu.be/QhYlAM40oUY?si=7ovc1y3ng_QEOwJ8'],

    'synthwave': ['https://youtu.be/k3WkJq478To?si=rf_xpFYGhRZ0Wsay', 'https://youtu.be/cCTaiJZAZak?si=zu17yQiXAR_PYEO3',],

    'progressive_house': ['https://youtu.be/jaE6M5Lr0mo?si=gP8jpPGMBq7ZN2Fp', 'https://youtu.be/CEbXiuDKRlM?si=HN8Svh7AChUqxhx1', 'https://youtu.be/GQ3qAnkrLzI?si=OcAcK0A_TLN_fMR4', 'https://youtu.be/8NsEHIU_iuE?si=lqEvAlpcEJEHcSkK'],
    # Add more genres and URLs as needed
}

async def ensure_voice(ctx):
    global last_active_channel
    if ctx.author.voice:
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()
            last_active_channel = ctx.channel
    else:
        await ctx.send("You are not connected to a voice channel.", delete_after=20)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.thumbnail = data.get('thumbnail')

    @classmethod
    async def from_query(cls, query, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        ytdl_format_options = {
        'format': 'bestaudio',
        'noplaylist': 'True',
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

    # Regular expression to check if the query is a URL
        url_regex = re.compile(
            r'^(https?://)?(www\.)?(youtube\.com|youtu\.?be)/.+$'
        )

        try:
            if url_regex.match(query):            
            #Directly extract info from the URL
                info = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
            else:            
            # If not URL, treat it as a search query
                search_query = f"ytsearch:{query}"
                info = await loop.run_in_executor(None, lambda: ytdl.extract_info(search_query, download=False)['entries'][0])

            # Log: Display fetched information

            if not info:
                raise commands.CommandError("No results found for the provided query.")

            url = info.get('url')
            title = info.get('title')
            thumbnail = info.get('thumbnail')
            webpage_url = info.get('webpage_url')
            data = {'title': title, 'url': webpage_url, 'thumbnail': thumbnail}
    
            return cls(discord.FFmpegPCMAudio(url), data=data)

        except yt_dlp.utils.DownloadError as e:
            raise commands.CommandError(f"Download error: {e}")
        except IndexError:
            raise commands.CommandError("No results found. Please try a different query or URL.")
        except Exception as e:
        # Log the exact error
            print(f"An unexpected error occurred: {str(e)}")
            raise commands.CommandError(f"An unexpected error occurred: {str(e)}")
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        ytdl_format_options = {
            'format': 'bestaudio/best',
            'noplaylist': 'True',
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

        info = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in info:
            info = info['entries'][0]

        data = {
            'title': info.get('title'),
            'url': info.get('url'),
        }

        if stream:
            return cls(discord.FFmpegPCMAudio(info['url']), data=data)
        else:
            return cls(discord.FFmpegPCMAudio(info['url']), data=data)
        
@bot.command(name='play', help='Joins the voice channel and plays a song')
@check_blacklist()
async def play(ctx, *, query):
    global current_player, last_channel, streaming_mode
    last_channel = ctx.channel  
    await ensure_voice(ctx)

    if streaming_mode:
        embed = discord.Embed(title="Streaming Mode", description="Cannot add songs while in 24/7 streaming mode.", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    async with ctx.typing():
        player = await YTDLSource.from_query(query, loop=bot.loop)
        player.volume = volume_level  # Set the volume
        queue.append(player)

        if not ctx.voice_client.is_playing():
            await play_next_song(ctx)
        else:
            embed = discord.Embed(title="Added to Queue", description=f'[{player.title}]({player.url})', color=discord.Color.blue())
            if player.thumbnail:
                embed.set_thumbnail(url=player.thumbnail)
            await ctx.send(embed=embed)

async def play_next_song(ctx):
    global current_player

    if len(queue) > 0:
        player = queue.pop(0)
        current_player = player

        if ctx.voice_client.is_connected():  # Ensure bot is still connected
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))

        embed = discord.Embed(title="Now Playing", description=f'[{player.title}]({player.url})', color=discord.Color.green())
        embed.set_thumbnail(url=player.data['thumbnail'])  # Display the thumbnail
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Queue", description="Queue is empty.", color=discord.Color.orange())
        await ctx.send(embed=embed)
        await check_idle_disconnect(ctx)

async def check_idle_disconnect(ctx):
    await asyncio.sleep(IDLE_TIMEOUT)  # Wait for the idle timeout
    if ctx.voice_client and not ctx.voice_client.is_playing() and not queue:
        await ctx.voice_client.disconnect()
        embed = discord.Embed(title="Disconnected", description="Disconnected due to inactivity.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='pause', help='This command pauses the song')
@check_blacklist()
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        embed = discord.Embed(title="Paused", description="The song has been paused.", color=discord.Color.yellow())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", description="The bot is not playing anything at the moment.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='resume', help='Resumes the song')
@check_blacklist()
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        embed = discord.Embed(title="Resumed", description="The song has been resumed.", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", description="The bot was not playing anything before this. Use play command", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='stop', help='Stops the currently playing song')
@check_blacklist()
async def stop(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        embed = discord.Embed(title="Stopped", description="The current song has been stopped.", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", description="The bot is not playing anything at the moment.", color=discord.Color.red())
        await ctx.send(embed=embed)
    await check_idle_disconnect(ctx)

@bot.command(name='queue', help='Displays the current song queue')
@check_blacklist()
async def display_queue(ctx):
    if len(queue) > 0:
        queue_list = "\n".join([f"{i + 1}. [{song.title}]({song.url})" for i, song in enumerate(queue)])
        embed = discord.Embed(title="Current Queue", description=f"{queue_list}", color=discord.Color.blue())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Queue", description="The queue is empty.", color=discord.Color.orange())
        await ctx.send(embed=embed)

@bot.command(name='skip', help='Skips the current song')
@check_blacklist()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        embed = discord.Embed(title="Skipped", description="The current song has been skipped.", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Error", description="The bot is not playing anything at the moment.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='volume_up', help='Increases the volume by 10%')
@check_blacklist()
async def volume_up(ctx):
    global volume_level
    if volume_level < 1.0:
        volume_level = min(volume_level + 0.1, 1.0)
        if current_player:
            current_player.volume = volume_level
        embed = discord.Embed(title="Volume Up", description=f'Volume increased to {int(volume_level * 100)}%', color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Volume", description='Volume is already at maximum.', color=discord.Color.orange())
        await ctx.send(embed=embed)

@bot.command(name='volume_down', help='Decreases the volume by 10%')
@check_blacklist()
async def volume_down(ctx):
    global volume_level
    if volume_level > 0.0:
        volume_level = max(volume_level - 0.1, 0.0)
        if current_player:
            current_player.volume = volume_level
        embed = discord.Embed(title="Volume Down", description=f'Volume decreased to {int(volume_level * 100)}%', color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Volume", description='Volume is already at minimum.', color=discord.Color.orange())
        await ctx.send(embed=embed)

@bot.command(name='clear_queue', help='Clears the entire music queue')
@check_blacklist()
async def clear_queue(ctx):
    global queue

    if len(queue) > 0:
        queue.clear()


        embed = discord.Embed(title="Queue Cleared", description="The music queue has been cleared.", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="Queue Empty", description="The queue is already empty.", color=discord.Color.orange())
        await ctx.send(embed=embed)

@bot.command(name='disconnect', help='Disconnects the bot from the voice channel')
@check_blacklist()
async def disconnect(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

        # Clear the queue and reset variables
        queue.clear()
        global current_player, streaming_mode
        current_player = None
        streaming_mode = False

        embed = discord.Embed(title="Disconnected", description="Disconnected from the voice channel.", color=discord.Color.green())
        await ctx.send(embed=embed, delete_after=20)
    else:
        embed = discord.Embed(title="Idling", description="I'm not connected to any voice channel.", color=discord.Color.red())
        await ctx.send(embed=embed, delete_after=20)

@bot.command(name='stream247', help='Starts streaming the chosen genre 24/7')
@check_blacklist()
async def start_stream(ctx, genre: str):
    global streaming_mode
    streaming_mode = True
    await ensure_voice(ctx)

    genre = genre.lower()
    if genre not in genre_urls:
        await ctx.send(f"Invalid genre. Available genres are: {', '.join(genre_urls.keys())}")
        return

    playlist = genre_urls[genre]
    embed = discord.Embed(title="Now Playing", description=f"Streaming {genre.capitalize()} music 24/7", color=discord.Color.green())
    await ctx.send(embed=embed)
    async def play_next_video():
        if not ctx.voice_client:
            return  # Ensure the bot is still connected to a voice channel before playing the next video.

        video_url = random.choice(playlist)

        try:
            player = await YTDLSource.from_url(video_url, loop=bot.loop, stream=True)
            if ctx.voice_client:
                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_video(), bot.loop))
        except Exception as e:
            print(f"Error playing video: {e}")
            embed = discord.Embed(title='Error', description='An error occurred while trying to start the stream.', color=discord.Color.red())
            await ctx.send(embed=embed)

    await play_next_video()  # Start playing the first video in the playlist

    while streaming_mode:
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            await play_next_video()
        await asyncio.sleep(5)  # Check every 5 seconds if the stream has stopped

@bot.command(name='stop247', help='Stops the 24/7 streaming.')
@check_blacklist()
async def stop_streaming(ctx):
    global streaming_mode
    streaming_mode = False

    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # Stop the current streaming video

        # Clear any remaining videos in the queue
        queue.clear()
    else:
        await ctx.send(embed=discord.Embed(title="Error", description="The bot is not streaming anything at the moment.", color=discord.Color.red()))

    if ctx.voice_client and ctx.voice_client.is_connected():
        await ctx.voice_client.disconnect()  # Optionally, disconnect from the voice channel
        await ctx.send(embed=discord.Embed(title="Streaming Stopped", description="Exited 24/7 streaming mode.", color=discord.Color.red()))

# =============================== Member Count ================================
@bot.command(name='usercount', help='Let you know how many members are in the current server.')
@check_blacklist()
@commands.cooldown(1, 60, BucketType.user)  # 1 use per 60 seconds per user
async def usercount(ctx):
    guild = ctx.guild  # Get the server (guild) the command was issued in
    member_count = guild.member_count  # Get the number of members in the server
    await ctx.send(f'This server has {member_count} members!')

@usercount.error
async def usercount_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'Too fast. Please try again after {int(error.retry_after)} seconds.')


# =============================== BLACKLISTING USERS ==========================
# Command to blacklist/unblacklist users
@bot.command()
async def blacklist(ctx, action: str, member: discord.Member):
    if ctx.author.id != DEV_USER_ID:
        await ctx.send("You do not have permission to use this command.")
        return
    
    # Convert member to user ID
    user_id = member.id

    # Perform blacklist/unblacklist action
    if action == 'add':
        if user_id not in blacklisted_users:
            blacklisted_users.add(user_id)
            save_blacklist()  # Save updated blacklist to file
            logging.info(f"User ID {user_id} added to blacklist by {ctx.author}.")
            await ctx.send(f"User {member} has been blacklisted.")
        else:
            await ctx.send(f"User {member} is already blacklisted.")
    elif action == 'remove':
        if user_id in blacklisted_users:
            blacklisted_users.remove(user_id)
            save_blacklist()  # Save updated blacklist to file
            logging.info(f"User ID {user_id} removed from blacklist by {ctx.author}.")
            await ctx.send(f"User {member} has been removed from the blacklist.")
        else:
            await ctx.send(f"User {member} is not currently blacklisted.")
    else:
        await ctx.send("Invalid action. Use `add` or `remove`.")
# ========================== Bot Statistics ===================================
start_time = time.time()
command_invokes = 0

@bot.event
async def on_command(ctx):
    global command_invokes
    command_invokes += 1

@bot.command()
async def stats(ctx):
    # Calculate uptime
    uptime_seconds = int(time.time() - start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Get the number of guilds (servers) and users
    guild_count = len(bot.guilds)
    user_count = len(set(bot.get_all_members()))

    # Get latency (ping)
    latency = round(bot.latency * 1000)  # in milliseconds

    # Build the stats message
    stats_message = (
        f"**Bot Statistics**\n"
        f"Servers: {guild_count}\n"
        f"Users: {user_count}\n"
        f"Uptime: {hours}h {minutes}m {seconds}s\n"
        f"Latency: {latency}ms\n"
        f"Commands Invoked: {command_invokes}"
    )

    await ctx.send(stats_message)

# =============================================================================
if __name__ == "__main__":
    bot.run(token)