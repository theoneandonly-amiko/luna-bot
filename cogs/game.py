import discord
from discord.ext import commands
import random
import asyncio

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.number_game = None
        self.scramble_game = None

        # Define themed word lists for the scramble game
        self.scramble_word_themes = {
            "programming": ["function", "variable", "algorithm", "loop", "exception", "debugging", "module", "object", "inheritance", "syntax"],
            "fruits": ["pineapple", "blueberry", "blackberry", "raspberry", "pomegranate", "nectarine", "cantaloupe", "apricot", "grapefruit", "dragonfruit"],
            "animals": ["dolphin", "elephant", "koala", "giraffe", "octopus", "penguin", "rhinoceros", "sloth", "toucan", "walrus"],
            "countries": ["australia", "brazil", "canada", "denmark", "estonia", "finland", "greece", "honduras", "iceland", "jamaica"],
            "space": ["astronaut", "blackhole", "comet", "galaxy", "nebula", "orbit", "quasar", "rocket", "supernova", "telescope"],
            "food": ["cheesecake", "dumplings", "frittata", "lasagna", "muffin", "nachos", "pancake", "samosa", "tacos", "waffles"],
            "movies": ["inception", "matrix", "gladiator", "incredibles", "parasite", "pulpfiction", "rainman", "rocky", "titanic", "wonderwoman"],
            "sports": ["basketball", "cricket", "gymnastics", "hockey", "lacrosse", "marathon", "soccer", "surfing", "tennis", "volleyball"]
        }
# Virtual battle
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

    # Hangman
    @commands.command()
    async def hangman(self, ctx):
        self.word_themes = {
        "programming": ["python", "javascript", "ruby", "java", "swift", "html", "css", "php", "scala", "kotlin"],
        "fruits": ["apple", "banana", "cherry", "grape", "kiwi", "lemon", "mango", "orange", "peach", "strawberry"],
        "animals": ["elephant", "giraffe", "hippopotamus", "kangaroo", "lion", "monkey", "penguin", "rhinoceros", "tiger", "zebra"],
        "countries": ["argentina", "brazil", "canada", "denmark", "egypt", "france", "germany", "hungary", "india", "japan"],
        "space": ["asteroid", "comet", "galaxy", "nebula", "planet", "quasar", "rocket", "star", "supernova", "universe"],
        "food": ["burger", "cupcake", "donut", "falafel", "gelato", "hamburger", "lasagna", "nachos", "pizza", "sushi"],
        "movies": ["avatar", "inception", "jumanji", "matrix", "nomadland", "ocean's", "parasite", "riddick", "titanic"],
        "sports": ["baseball", "basketball", "cricket", "football", "golf", "hockey", "soccer", "tennis", "volleyball", "wrestling"]
        }

        theme = random.choice(list(self.word_themes.keys()))
        word = random.choice(self.word_themes[theme])
        self.hangman_game = {
            "word": word,
            "theme": theme,
            "guessed": set(),
            "wrong_attempts": 0,
            "max_attempts": 8,
            "clues": 3,  # Max number of clues
            "clue_letters": set()  # Track revealed letters for clues
        }
        game = self.hangman_game
        await ctx.send(f"Game started! The word is in the theme '{game['theme']}' and has {len(word)} letters.")
        await ctx.send(f"You have {game['clues']} clues remaining. Use `am/hangclue` to reveal a letter, `am/hangguess [letter]` to guess a letter.")

    @commands.command()
    async def hangguess(self, ctx, letter: str):
        if not hasattr(self, 'hangman_game'):
            await ctx.send("Start a game with am/hangman first.")
            return

        game = self.hangman_game
        word = game["word"]
        guessed = game["guessed"]

        if letter in guessed:
            await ctx.send("You already guessed that letter.")
            return

        guessed.add(letter)
        if letter in word:
            display_word = ' '.join([l if l in guessed else '_' for l in word])
            if '_' not in display_word:
                await ctx.send(f"Congratulations! You guessed the word: {word}")
                del self.hangman_game
            else:
                await ctx.send(f"Good guess! {display_word}")
        else:
            game["wrong_attempts"] += 1
            if game["wrong_attempts"] >= game["max_attempts"]:
                await ctx.send(f"Game over! The word was {word}.")
                del self.hangman_game
            else:
                await ctx.send(f"Wrong guess. {game['max_attempts'] - game['wrong_attempts']} attempts left.")

    @commands.command()
    async def hangclue(self, ctx):
        if not hasattr(self, 'hangman_game'):
            await ctx.send("Start a game with am/hangman first.")
            return

        game = self.hangman_game
        if game["clues"] <= 0:
            await ctx.send("No clues remaining!")
            return

        word = game["word"]
        available_letters = [l for l in word if l not in game["guessed"] and l not in game["clue_letters"]]
        if not available_letters:
            await ctx.send("No more letters to reveal!")
            return

        clue_letter = random.choice(available_letters)
        game["clue_letters"].add(clue_letter)
        game["clues"] -= 1

        display_word = ' '.join([l if l in game["guessed"] or l in game["clue_letters"] else '_' for l in word])
        await ctx.send(f"Clue revealed: {clue_letter}")
        await ctx.send(f"Current word: {display_word}")
        await ctx.send(f"You have {game['clues']} clues remaining.")


    # Rock, Paper, Scissors
    @commands.command()
    async def rps(self, ctx, choice: str):
        choices = ["rock", "paper", "scissors"]
        if choice not in choices:
            await ctx.send("Invalid choice! Please choose rock, paper, or scissors.")
            return

        bot_choice = random.choice(choices)
        if choice == bot_choice:
            result = "It's a tie!"
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
        else:
            result = "You lose!"

        await ctx.send(f"You chose {choice}. I chose {bot_choice}. {result}")


    # Number Guessing
    @commands.command()
    async def numberguess(self, ctx):
        if self.number_game:
            await ctx.send("A game is already in progress. Finish it before starting a new one.")
            return

        self.number_game = {
            "number": random.randint(1, 100),
            "tries": 0
        }
        await ctx.send(f"I'm thinking about a number now. Guess the number between 1 and 100. Use `am/numguess [number]` to guess the number that you think it's right!")

    @commands.command()
    async def numguess(self, ctx, number: int):
        if not self.number_game:
            await ctx.send("Start a game with am/numberguess first.")
            return

        game = self.number_game
        target_number = game["number"]
        game["tries"] += 1

        if number < target_number:
            await ctx.send("Too low! Try again.")
        elif number > target_number:
            await ctx.send("Too high! Try again.")
        else:
            await ctx.send(f"Congratulations! You guessed the number {target_number} in {game['tries']} tries.")
            self.number_game = None

    # Word Scramble
    @commands.command()
    async def scramble(self, ctx):
        if self.scramble_game:
            await ctx.send("A game is already in progress. Finish it before starting a new one.")
            return

        theme = random.choice(list(self.scramble_word_themes.keys()))
        word = random.choice(self.scramble_word_themes[theme])
        scrambled = ''.join(random.sample(word, len(word)))
        self.scramble_game = {
            "word": word,
            "scrambled": scrambled,
            "theme": theme
        }
        await ctx.send(f"Scramble game started! The theme is '{theme}'. Unscramble this word: `{scrambled}`. Use `am/guess [answer] to unscramble the word!`")

    @commands.command()
    async def guess(self, ctx, *, guess: str):
        if not self.scramble_game:
            await ctx.send("Start a game with am/scramble first.")
            return

        game = self.scramble_game
        word = game["word"]

        if guess.lower() == word:
            await ctx.send(f"Congratulations! You unscrambled the word: `{word}`")
            self.scramble_game = None
        else:
            await ctx.send("Incorrect guess. Try again!")

    # Roulette
    @commands.command()
    async def bet(self, ctx, bet: str):
        if bet not in ["red", "black"] + [str(i) for i in range(0, 37)]:
            await ctx.send("Invalid bet! Choose red, black, or a number between 0 and 36.")
            return

        # Notify the user that the ball is rolling
        await ctx.send("The ball is rolling...")

        # Delay for 10 seconds
        await asyncio.sleep(10)

        # Generate the result
        result = random.randint(0, 36)
        color = "red" if result % 2 == 0 else "black"

        # Determine win or loss
        if bet == str(result):
            await ctx.send(f"The ball landed on {result}. You win!")
        elif bet == color:
            await ctx.send(f"The ball landed on {result} ({color}). You win!")
        else:
            await ctx.send(f"The ball landed on {result} ({color}). You lose.")


    # Memory Game
    @commands.command()
    async def memory(self, ctx):
        self.memory_game = {
            "board": self.create_memory_board(),
            "revealed": [[False] * 4 for _ in range(4)],
            "first_flip": None,
            "found_pairs": set(),
            "total_pairs": 8
        }
        game = self.memory_game
        await ctx.send("Memory game started! Use `am/memflip <row> <col>` to flip a card. The board is 4x4, coordinates is the number within range of 0 and 3.")

    @commands.command()
    async def memflip(self, ctx, row: int, col: int):
        if not hasattr(self, 'memory_game'):
            await ctx.send("Start a game with am/memory first.")
            return

        game = self.memory_game
        board = game["board"]
        revealed = game["revealed"]

        # Check if the coordinates are valid
        if row < 0 or row >= 4 or col < 0 or col >= 4:
            await ctx.send("Invalid coordinates! Coordinates must be between 0 and 3.")
            return

        # Check if the card is already revealed
        if revealed[row][col]:
            await ctx.send("Card already revealed!")
            return

        # Reveal the card
        revealed[row][col] = True
        await ctx.send(f"Card at ({row}, {col}) is {board[row][col]}.")

        # Handle the first and second flip
        if game["first_flip"] is None:
            game["first_flip"] = (row, col)
        else:
            first_row, first_col = game["first_flip"]
            first_value = board[first_row][first_col]
            second_value = board[row][col]

            if first_value == second_value:
                game["found_pairs"].add(first_value)
                await ctx.send(f"Found a pair: {first_value}!")
                if len(game["found_pairs"]) == game["total_pairs"]:
                    await ctx.send("Congratulations! You've found all pairs!")
                    del self.memory_game
            else:
                await ctx.send("No match. Flipping cards back.")
                # Hide cards after a short delay
                await asyncio.sleep(2)
                revealed[first_row][first_col] = False
                revealed[row][col] = False

            # Reset first flip
            game["first_flip"] = None

        # Show the board (for debugging or game progress)
        await ctx.send(f"Current board:\n```{self.board_to_string(board, revealed)}```")

    def create_memory_board(self):
        # Create a board with pairs of numbers
        numbers = list(range(1, 9)) * 2  # 8 pairs
        random.shuffle(numbers)
        board = [numbers[i:i+4] for i in range(0, len(numbers), 4)]  # 4x4 board
        return board

    def board_to_string(self, board, revealed):
        # Convert board to string for display
        return "\n".join(" ".join(str(board[i][j]) if revealed[i][j] else "X" for j in range(4)) for i in range(4))


async def setup(bot):
    await bot.add_cog(Games(bot))