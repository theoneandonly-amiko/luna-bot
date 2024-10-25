import discord
import random
import os
import requests
import asyncio
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.no_user_responses = [
        "You want to match with thin air? Good luck with that! 😆",
        "Looks like you’re trying to match with a ghost! 👻",
        "Are you planning to match with yourself? That's a bold move! 😂",
        "Air is not a good match, try mentioning a friend! 🌬️",
        "Sorry, but I can't match you with invisible people! 👀",
        "Maybe try mentioning a user instead of just talking to the void? 🤔",
        "Matching with nothing is quite the challenge, huh? 😅",
        "Your soulmate must be really elusive if they're not here! 🕵️‍♂️",
        "Looks like you’re destined to be a solo act! 🎭",
        "Finding a match in the void, are we? Good luck! 🕳️",
]
    # Function to fetch a random pet GIF from the local assets folder
    def fetch_random_gif(self):
        asset_folder = 'assets/pet'
        gif_files = [f for f in os.listdir(asset_folder) if f.endswith('.gif')]
        if not gif_files:
            return None
        return random.choice(gif_files)
    
    # Function to fetch a random grab GIF from the local assets folder
    def fetch_random_grab_gif(self):
        asset_folder = 'assets/grab'
        gif_files = [f for f in os.listdir(asset_folder) if f.endswith('.gif')]
        if not gif_files:
            return None
        return os.path.join(asset_folder, random.choice(gif_files))

    # Function to fetch a random slap GIF from the local assets folder
    def fetch_random_slap_gif(self):
        asset_folder = 'assets/slap'
        gif_files = [f for f in os.listdir(asset_folder) if f.endswith('.gif')]
        if not gif_files:
            return None
        return os.path.join(asset_folder, random.choice(gif_files))

    # Function to fetch a random slap GIF from the local assets folder
    def fetch_random_hug_gif(self):
        asset_folder = 'assets/hug'
        gif_files = [f for f in os.listdir(asset_folder) if f.endswith('.gif')]
        if not gif_files:
            return None
        return os.path.join(asset_folder, random.choice(gif_files))

    def fetch_random_tape_gif(self):
        asset_folder = 'assets/tape'
        gif_files = [f for f in os.listdir(asset_folder) if f.endswith('.gif')]
        if not gif_files:
            return None
        return random.choice(gif_files)

    @commands.command(name='tape')
    async def tape_user(self, ctx, member: discord.Member):
        if member == ctx.author:
            await ctx.send("You can't tape yourself! 😄")
            return

        # List of random responses
        responses = [
            "You've been taped! Get ready for some fun! 🎉",
            "Taping in progress! Hope you're ready! 😂",
            "Surprise! You've been taped! 🤣",
            "Watch out! Here comes the tape! 🎊",
            "Tape time! You're it! 😜"
        ]


     # Pet command
    @commands.command(name='pet')
    
    async def pet(self, ctx: commands.Context, *users: discord.User):
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

        pet_gif = self.fetch_random_gif()

        if len(valid_users) == 1:
            user = valid_users[0]
            if user == self.bot.user:
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
                    "{0} cannot resist to pet {1} and they just did it.*",
                    "{0} petted {1} because they're too cute to not being petted."
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
                "{0} just come and pet the cutest creature in the world: {1}.",
                "{0} cannot resist to pet {1} and they just did it.",
                "{0} tickles {1}'s belly.",
                "{0} petted {1} because they're too cute to not being petted."
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

    @commands.command(name='tape')
    async def tape_user(self, ctx: commands.Context, member: discord.Member):
        if member == ctx.author:
            funny_responses = [
                "Why did you even try taping yourself? 🤔",
                "Self-taping? That's a bold move! 😆",
                "You're supposed to tape others, not yourself! 🙈",
                "Well, that's one way to get yourself stuck! 😂",
                "Self-tape mode activated! Someone needs to help you! 😜",
                "Guess you really love yourself, huh? 🤔",
                "Do you need some tape therapy? 😂"
            ]
            response = random.choice(funny_responses)
            await ctx.send(response)
            return

        tape_gif = self.fetch_random_tape_gif()

        if member == self.bot.user:
            bot_responses = [
                "You want to tape me? How dare you! 😳",
                "Taping the bot? Are you sure about that? 😏",
                "I'm flattered, but I'm just a bot—no tape for me! 🤖",
                "You can't tape the bot! I'm untouchable! 🚫",
                "Clever attempt, but I can't be taped! 🤖✨",
                "Nice try! I'm a bot, and I'm already \"wrapped\" in code! 😂"
            ]
            response = random.choice(bot_responses)
            await ctx.send(response)
            return

        response_messages = [
            "{0} has successfully taped {1}! Watch out, they're stuck now! 🎉",
            "{0} just taped {1}—what a surprise! 🎈",
            "{0} couldn't resist and taped {1} like a pro! 🏆",
            "{0} taped {1} because they're the perfect target for fun! 🤣",
            "{0} has wrapped {1} in tape! Now they're a present! 🎁",
            "{0} just made {1} a part of the tape club! 🤪",
            "{0} can't help but tape {1} — the fun is too good! 😜",
            "Look out! {0} just taped {1} for some mischievous fun! 😈"
        ]
        response = random.choice(response_messages).format(ctx.author.mention, member.mention)
        
        if tape_gif:
            tape_gif_path = os.path.join('assets/tape', tape_gif)
            file = discord.File(tape_gif_path, filename=tape_gif)

            embed = discord.Embed(
                description=response,
                color=discord.Color.blue()
            )
            embed.set_image(url=f"attachment://{tape_gif}")

            await ctx.send(file=file, embed=embed)
        else:
            await ctx.send(response)

    # Grab command
    @commands.command(name='grab')
    
    async def grab(self, ctx, *users: discord.User):
        if not users:
            await ctx.send("Uh, who to grab? Air? Space? 🤔")
            return

        user = random.choice(users)
        if self.bot.user in users and ctx.author in users and len(users) == 2:
            grabs = [
                "{0} grabs {1} by the arm and.",
                "Look, {0} and {1} are grabbing each other.",
                "{0} just stole {1} from the road.",
                "{0} just come and picked {1} up."
            ]
            grab_gif = self.fetch_random_grab_gif()
            response = random.choice(grabs).format(ctx.author.mention, self.bot.user.mention, user.mention)

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
        elif user == self.bot.user:
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
            grab_gif = self.fetch_random_grab_gif()
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

    @commands.command(name='slap')
    async def slap(self, ctx, *users: discord.User):
        if not users:
            await ctx.send("Who are you trying to slap? The air? Invisible forces? 🤔")
            return

        user = random.choice(users)
    
        if self.bot.user in users and ctx.author in users and len(users) == 2:
            slaps = [
            "{0} slaps {1}, but it's a mutual understanding slap.",
            "Oh, look! {0} and {1} are slapping each other in harmony.",
            "{0} slapped {1}, and {1} doesn't mind it.",
            "Looks like {0} just gave {1} a friendly slap!"
            ]
            slap_gif = self.fetch_random_slap_gif()
            response = random.choice(slaps).format(ctx.author.mention, self.bot.user.mention)

            if slap_gif:
                file = discord.File(slap_gif, filename=os.path.basename(slap_gif))

                embed = discord.Embed(
                description=response,
                color=discord.Color.red()
                )
                embed.set_image(url=f"attachment://{os.path.basename(slap_gif)}")

                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(response)
    
        elif user == self.bot.user:
            bot_responses = [
            "I can't slap myself, but maybe you can help me out! 😅",
            "Nice try! How about you slap someone else instead? 😏",
            "I'm not programmed to slap myself, how about you try?",
            "Slap me? That's not possible! Try another victim. 🧐",
            "Slapping myself? That's a bit too self-destructive for me! 😜"
            ]
            response = random.choice(bot_responses)
            await ctx.send(response)
    
        elif user == ctx.author:
            self_slap_responses = [
            "Trying to slap yourself? Bold move! 🤔",
            "Slapping yourself won't work... unless you're really flexible. 😄",
            "Why would you slap yourself? You deserve better! 💪",
            "Self-slap? Maybe reconsider that plan! 😬"
            ]
            response = random.choice(self_slap_responses)
            await ctx.send(response)
    
        else:
            slaps = [
            "{0} delivers a mighty slap to {1}! 💥",
            "{0} just slapped {1} across the face! Ouch! 😱",
            "Boom! {0} slapped {1} with full force! 😤",
            "{0} slapped {1} and it's quite a scene! 😲",
            "{0} went ahead and slapped {1}... Are they okay? 😬"
            ]
            slap_gif = self.fetch_random_slap_gif()
            response = random.choice(slaps).format(ctx.author.mention, user.mention)

            if slap_gif:
                file = discord.File(slap_gif, filename=os.path.basename(slap_gif))

                embed = discord.Embed(
                description=response,
                color=discord.Color.dark_red()
            )
                embed.set_image(url=f"attachment://{os.path.basename(slap_gif)}")

                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(response)

    @commands.command(name='hug')
    async def hug(self, ctx, *users: discord.User):
        if not users:
            await ctx.send("Who are you trying to hug? Yourself? A ghost? 🤔")
            return

        user = random.choice(users)

        if self.bot.user in users and ctx.author in users and len(users) == 2:
            hugs = [
            "{0} hugs {1}, and it's a heartwarming moment. 🤗",
            "Look at {0} and {1} sharing a hug! So wholesome. 💖",
            "{0} gave {1} the coziest hug ever!",
            "{0} and {1} just shared a sweet hug!"
            ]
            hug_gif = self.fetch_random_hug_gif()
            response = random.choice(hugs).format(ctx.author.mention, self.bot.user.mention)

            if hug_gif:
                file = discord.File(hug_gif, filename=os.path.basename(hug_gif))

                embed = discord.Embed(
                description=response,
                color=discord.Color.green()
                )
                embed.set_image(url=f"attachment://{os.path.basename(hug_gif)}")

                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(response)

        elif user == self.bot.user:
            bot_responses = [
            "I would love to hug myself, but I need help with that! 😅",
            "You can hug me, but I can't hug myself! 😏",
            "I'm not made to hug myself, maybe you can try!",
            "Hug me? I'm always here for you! 🤗",
            "I'll gladly accept a hug, but I can't hug back! 😜"
            ]
            response = random.choice(bot_responses)
            await ctx.send(response)

        elif user == ctx.author:
            self_hug_responses = [
            "Hugging yourself? That's self-love at its finest! 💪",
            "A self-hug? You must be in need of some extra warmth! 😊",
            "Nothing wrong with hugging yourself, but maybe someone else needs a hug too! 💖",
            "You deserve all the hugs, even from yourself! 🤗"
            ]
            response = random.choice(self_hug_responses)
            await ctx.send(response)

        else:
            hugs = [
            "{0} gives {1} a big, warm hug! 🤗",
            "{0} just wrapped {1} in a tight embrace. 💖",
            "{0} gave {1} a comforting hug! 👐",
            "Aww, {0} gave {1} a sweet hug! So cute! 🥰"
            ]
            hug_gif = self.fetch_random_hug_gif()
            response = random.choice(hugs).format(ctx.author.mention, user.mention)

            if hug_gif:
                file = discord.File(hug_gif, filename=os.path.basename(hug_gif))

                embed = discord.Embed(
                description=response,
                color=discord.Color.purple()
                )
                embed.set_image(url=f"attachment://{os.path.basename(hug_gif)}")

                await ctx.send(file=file, embed=embed)
            else:
                await ctx.send(response)

    @commands.command(name='roll', help='Rolls a dice.')
    
    async def roll(self, ctx, sides: int = 6):
        if sides < 1 or sides > 100:
            await ctx.send('Please choose a number of sides between 1 and 100.')
            return
        result = random.randint(1, sides)
        await ctx.send(f'🎲 You rolled a {result} on a {sides}-sided dice!')

    @commands.command(name='flip', help='Flips a coin')
    async def flip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        await ctx.send(result)

    @commands.command(name='8ball', help='Ask the magic 8-ball a question')
    async def eight_ball(self, ctx, *, question: str = None):
        if question is None:
            no_question_responses = [
            "You need to ask a question!",
            "I can't answer a question you haven't asked!",
            "Ask me something, don't leave me hanging!",
            "You forgot to ask a question. Try again!",
            "The 8-ball cannot predict nothing... ask a question!",
            "What do you want to know? Nothing?"
            ]
            await ctx.send(random.choice(no_question_responses))
            return
        
        responses = [
            "Yes", "No", "Maybe", "Ask again later",
            "Definitely", "I don't think so", "Of course!", "Not in a million years", "I wouldn't count on it",
            'Absolutely', 'Not sure', 'Probably', 'Absolutely not', 'Without a doubt', 'Reply hazy. Try again.', "It is certain.", "It is decidedly so.", "Yes, definitely.", "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.", "Signs point to yes.", "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.", "Don't count on it.", "My sources say no.", "Outlook not so good.", "Very doubtful."
        ]
        answer = random.choice(responses)
        await ctx.send(f'{answer}')

    @commands.command()
    async def battle(self, ctx, user1: discord.Member, user2: discord.Member):
        if user1 == user2:
            await ctx.send("You can't battle yourself!")
            return

        user1_hp = 100
        user2_hp = 100

        attack_responses = [
            "⚔️ {attacker} screams in {defender}'s ear, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} bites {defender}'s nose, causing **__-{damage}__** damage!",
            "⚔️ {attacker} gives {defender} a wet willy, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} tickles {defender} mercilessly, causing **__-{damage}__** damage!",
            "⚔️ {attacker} sneezes on {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} throws a rubber chicken at {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} does an awkward dance in front of {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} unleashes a dad joke on {defender}, dealing **__-{damage}__** damage from cringe!",
            "⚔️ {attacker} hurls a moldy sandwich at {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} threw a slice of pizza at {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} unleashed a flurry of finger snaps at {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} bonked {defender} with a rubber mallet, causing **__-{damage}__** damage!",
            "⚔️ {attacker} swung a pillow at {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} challenged {defender} to a dance-off and won, causing **__-{damage}__** damage from embarrassment!",
            "⚔️ {attacker} roasted {defender} with a savage insult, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} threw a bucket of ice water on {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} pulled {defender}'s leg... literally, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} squirted {defender} with a water gun, causing **__-{damage}__** damage!",
            "⚔️ {attacker} gave {defender} a brutal tickle attack, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} taunts {defender} about their failed love affairs, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} exposes a shocking secret about {defender}'s past, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} tried drowning {defender} in the toilet, causing **__-{damage}__** damage!",
            "⚔️ {attacker} threw themselves at {defender}, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} drags {defender} across the floor, dealing **__-{damage}__** damage!",
            "⚔️ {attacker} threw a hairdryer at {defender}, causing **__-{damage}__** damage!",
            "⚔️ {attacker} grabs a plate of food from a nearby table and smashes it over {defender}'s head, caused **__-{damage}__** damage!",
            "⚔️ {attacker} ripped {defender}'s jeans, causing **__-{damage}__** damage from embarrassment!",
            "⚔️ {attacker} accuses {defender} of stealing their other half, caused **__-{damage}__** damage"
        ]

        heal_responses = [
            "🩹 {attacker} eats a mysterious herb and regains **__+{heal}__** HP!",
            "🩹 {attacker} takes a quick nap and recovers **__+{heal}__** HP!",
            "🩹 {attacker} drinks a strange potion and heals for **__+{heal}__** HP!",
            "🩹 {attacker} meditates for a moment, recovering **__+{heal}__** HP!",
            "🩹 {attacker} finds a magical cookie, healing for **__+{heal}__** HP!",
            "🩹 {attacker} picked up their makeup, healing **__+{heal}__** HP!",
            "🩹 {attacker} did a quick yoga pose, recovering **__+{heal}__** HP!",
            "🩹 {attacker} had a cup of herbal tea and healed for **__+{heal}__** HP!",
            "🩹 {attacker} found an energy drink on the ground and healed for **__+{heal}__** HP!",
            "🩹 {attacker} struck a power pose, regaining **__+{heal}__** HP!",
            "🩹 {attacker} brushed their hair, recovering **__+{heal}__** HP!",
            "🩹 {attacker} put on some cool shades and healed for **__+{heal}__** HP!",
            "🩹 {attacker} sat down for a nice cup of coffee, healing **__+{heal}__** HP!",
            "🩹 {attacker} took a selfie to boost morale, regaining **__+{heal}__** HP!",
            "🩹 {attacker} watched a funny cat video and felt rejuvenated, healing **__+{heal}__** HP!",
            "🩹 {attacker} takes a moment to monologue about their tragic past, regaining **__+{heal}__** HP!",
            "🩹 {attacker} fans themselves with a melodramatic sigh, regaining **__+{heal}__** HP!"
        ]


        def create_battle_embed():
            embed = discord.Embed(title="An epic battle has started!", color=discord.Color.red())
            embed.add_field(name=user1.display_name, value=f"HP: {user1_hp}", inline=True)
            embed.add_field(name="VS", value="\u200B", inline=True)
            embed.add_field(name=user2.display_name, value=f"HP: {user2_hp}", inline=True)
            return embed

        message = await ctx.send(embed=create_battle_embed())
        current_attacker = user1

        while user1_hp > 0 and user2_hp > 0:
            if random.randint(1, 5) == 1:  # calculate to give a chance to heal instead of attack
                heal = random.randint(5, 20)
                if current_attacker == user1:
                    user1_hp = min(100, user1_hp + heal)
                else:
                    user2_hp = min(100, user2_hp + heal)

                response = random.choice(heal_responses).format(
                    attacker=current_attacker.display_name,
                    heal=heal
                )
            else:
                damage = random.randint(5, 20)
                if current_attacker == user1:
                    user2_hp = max(0, user2_hp - damage)
                else:
                    user1_hp = max(0, user1_hp - damage)

                response = random.choice(attack_responses).format(
                    attacker=current_attacker.display_name,
                    defender=user2.display_name if current_attacker == user1 else user1.display_name,
                    damage=damage
                )

            embed = create_battle_embed()
            await message.edit(content=response, embed=embed)
            await asyncio.sleep(2.5)

            current_attacker = user2 if current_attacker == user1 else user1

        winner = user1 if user2_hp == 0 else user2
        await ctx.send(f"{winner.display_name} wins the battle!")

    @commands.command(name='cat')
    async def cat_percent(self, ctx):
        percentage = random.randint(0, 100)
        embed = discord.Embed(
            title="Cat Percentage",
            description=f"{ctx.author.mention}, you look {percentage}% like a cat! 🐱",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(name='kurin')
    async def kurin_percent(self, ctx):
        custom_emoji = "<a:kurin:1277596648817557566>"
        custom_emoji_id = "1277596648817557566"
        percentage = random.randint(0, 100)
        embed = discord.Embed(
            title = "Kuru kuru~! Kururin!",
            description=f"{ctx.author.mention} hyperkuru rate is {percentage}%! {custom_emoji}",
            color=discord.Color.purple()
        )
        message = await ctx.send(embed=embed)

        emoji = discord.PartialEmoji(name='cat_emoji', id=int(custom_emoji_id))
        await message.add_reaction(emoji)
        
    @commands.command(name='meme', help='Get a random meme from the internet')
    async def meme(self, ctx):
        response = requests.get('https://api.imgflip.com/get_memes')
        if response.status_code == 200:
            data = response.json()
            meme = random.choice(data['data']['memes'])
            await ctx.send(meme['url'])
        else:
            await ctx.send("Couldn't fetch a meme, sorry!")
            
    @commands.command(name='choose', help='Makes a decision for you.')
    
    async def choose(self, ctx, *choices: str):
        if len(choices) < 2:
            await ctx.send('You need to provide at least two choices. If not then you already have your decision, duh. 🤷‍♀️')
            return
        decision = random.choice(choices)
        await ctx.send(f'Well, I choose: {decision}')

    @commands.command(name='messup')
    async def messup(self, ctx):
        # Check if the user replied to a message
        if ctx.message.reference:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            original_text = message.content
        else:
            # If no reply, take the message before the command
            async for msg in ctx.channel.history(limit=2):
                if msg != ctx.message:
                    original_text = msg.content
                    break
        
        if not original_text:
            await ctx.send("Couldn't find any message to mess up! 😅")
            return

        # Mess up the message by shuffling the words, letters, and adding random capitalization
        messed_up_text = self.extreme_messup(original_text)
        await ctx.send(f"{messed_up_text}")

    def extreme_messup(self, message):
        words = message.split()

        # Shuffle the words
        random.shuffle(words)

        messed_up_words = []
        for word in words:
            # Shuffle the letters within each word
            word_list = list(word)
            random.shuffle(word_list)

            # Randomly capitalize letters
            messed_up_word = ''.join(
                random.choice([char.upper(), char.lower()]) for char in word_list
            )
            messed_up_words.append(messed_up_word)

        return " ".join(messed_up_words)


    @commands.command(name='match')
    async def match(self, ctx, user1: discord.User = None, user2: discord.User = None):
        if user1 is None or user2 is None:
            response = random.choice(self.no_user_responses)
            await ctx.send(response)
            return
        user1_name_part = user1.name[:len(user1.name)//2]
        user2_name_part = user2.name[len(user2.name)//2:]
        ship_name = user1_name_part + user2_name_part
        compatibility = random.randint(0, 100)

        if compatibility >= 90:
            judgment = "A perfect match! ❤️"
        elif 80 <= compatibility < 90:
            judgment = "Amazing match! 🥰"
        elif 70 <= compatibility < 80:
            judgment = "Pretty good! 😎"
        elif 50 <= compatibility < 70:
            judgment = "Could be better. 😏"
        elif 30 <= compatibility < 50:
            judgment = "Not looking great... 😬"
        elif 10 <= compatibility < 30:
            judgment = "It's a bit rocky. 🥴"
        else:
            judgment = "Total mismatch... 😭"

        embed = discord.Embed(
            title="💞 Matchmaking Result 💞",
            description=f"**{user1.mention}** ❤️ **{user2.mention}**\n\n"
                        f"**Ship Name**: *{ship_name}*\n\n"
                        f"**Compatibility**: {compatibility}% {judgment}\n\n",
            color=discord.Color.magenta()
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))
