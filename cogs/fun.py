import discord
import random
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ========================== Fun Commands ==============================
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
    @commands.command(name='grab')
    
    async def grab(self, ctx, *users: discord.User):
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
    @commands.command(name='compliment', aliases=['nice', 'sweet'])
    
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
    @commands.command(name='roll', help='Rolls a dice.')
    
    async def roll(self, ctx, sides: int = 6):
        if sides < 1 or sides > 100:
            await ctx.send('Please choose a number of sides between 1 and 100.')
            return
        result = random.randint(1, sides)
        await ctx.send(f'🎲 You rolled a {result} on a {sides}-sided dice!')

    # 8-Ball Command
    @commands.command(name='8ball', help='Answers a yes/no question.')
    
    async def eight_ball(self, ctx, *, question: str = None):
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
    @commands.command(name='flip', help='Flips a coin.')
    async def flip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        await ctx.send(f'🪙 The coin landed on {result}!')

    # Make a decision for your life, lmao
    @commands.command(name='choose', help='Makes a decision for you.')
    
    async def choose(self, ctx, *choices: str):
        if len(choices) < 2:
            await ctx.send('You need to provide at least two choices. If not then you already have your decision, duh. 🤷‍♀️')
            return
        decision = random.choice(choices)
        await ctx.send(f'Well, I choose: {decision}')

    # Urban Dictionary
    @commands.command(name='urban', help='Searches Urban Dictionary for a definition.')
    
    async def urban(self, ctx, *, term: str | None = None):
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
    @commands.command()
    async def battle(self, ctx, user1: discord.Member, user2: discord.Member):
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

async def setup(bot):
    await bot.add_cog(Fun(bot))