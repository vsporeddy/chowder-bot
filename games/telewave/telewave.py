"""
    Read each other's minds
"""
import asyncio
import discord
import json
import random
from collections import deque
from chowder import chowder

with open("games/telewave/telewave_config.json", "r") as read_file:
    config = json.load(read_file)


class TelewaveTeam:
    def __init__(self, players, name, score):
        self.guessers = deque(players)
        self.psychic = self.guessers.popleft()
        self.score = score
        self.name = name

    def to_string(self):
        return f"{self.psychic.name}, {', '.join([g.name for g in self.guessers])}"

    def mention_guessers(self):
        return f"{', '.join([g.mention for g in self.guessers])}"

    def mention(self):
        return f"{self.psychic.mention}, {', '.join([g.mention for g in self.guessers])}"

    def rotate_psychic(self):
        self.guessers.append(self.psychic)
        self.psychic = self.guessers.popleft()

    def get_players(self):
        return [self.psychic] + list(self.guessers)


async def start(bot, ctx, players):
    await ctx.send(f"Starting a game of **telewave** with {', '.join([p.mention for p in players])}")
    random.shuffle(players)
    team_names = get_team_names()

    # Per official Wavelength rules - the team going second starts with a 1 point lead
    team1 = TelewaveTeam(players[:len(players)//2], name=team_names[0], score=0)
    team2 = TelewaveTeam(players[len(players)//2:], name=team_names[1], score=1)
    winners = await play(bot, ctx, team1, team2)

    await ctx.send(f"GG, **{winners.name}** wins")
    return winners.get_players()


async def play(bot, ctx, team1, team2):
    max_score = config["max_score"]
    going_again = False
    while team1.score < max_score and team2.score < max_score:
        await wait(ctx, going_again, team1)
        prompt = get_prompt()
        answer = random.randint(0, 100)

        await display(
            ctx, team1, team2, prompt, max_score,
            text=f"\u200B\n\n\n**{team1.psychic.mention}** is thinking of a clue"
        )

        clue = await get_clue(bot, team1.psychic, prompt, answer)

        # await ctx.send(f"Hold tight {chowder.get_collective_name()}, I just DMed {team1.psychic.mention} the prompt")

        await display(
            ctx, team1, team2, prompt, max_score,
            text=f"\u200B\n\n\n**{team1.psychic.mention}**'s clue: \"*{clue}*\""
        )

        guess = await get_guess(bot, ctx, team1)

        await display(
            ctx, team1, team2, prompt, max_score,
            text=f"\u200B\n\n\n**{team1.psychic.mention}**'s clue: \"*{clue}*\"\n"
                 f"**{team1.name}**'s guess: **{guess}**"
        )

        counter_guess = await get_counter_guess(bot, ctx, team2)

        prev_score = team1.score
        result_text = await update_scores(team1, team2, answer, guess, counter_guess)
        await display(ctx, team1, team2, prompt, max_score, text=result_text)

        team1.rotate_psychic()

        # Per official Wavelength rules - if you score 4 you get to go again
        going_again = team1.score - prev_score == 4
        if not going_again:
            team1, team2 = team2, team1

    return team1 if team1.score > team2.score else team2


async def get_clue(bot, psychic, prompt, answer):
    greeting = chowder.get_greeting().format(name=chowder.get_name(psychic))
    dm = await psychic.send(
        f"{greeting}, you're the psychic - here's your prompt: **{prompt[0]} ⟵ {answer} ⟶ {prompt[1]}**\n"
        f"you got {config['timeout']} minutes to respond with your clue"
    )
    return (await bot.wait_for("message",  check=lambda m: m.author == psychic and m.channel == dm.channel)).content


async def get_guess(bot, ctx, team):
    msg = await ctx.send(
        f"{team.mention_guessers()}: "
        f"y'all have {config['timeout']} minutes to submit your guesses. I'll be taking the average."
    )

    def check_guess(guess):
        return guess.author in waiting_for_guess and \
                guess.channel == msg.channel and \
                guess.content.isnumeric()

    waiting_for_guess = team.guessers.copy()
    avg_guess = 0.0
    while waiting_for_guess:
        guess = await bot.wait_for("message", check=check_guess)
        guess_val = float(guess.content)
        if guess_val > 100 or guess_val < 0:
            await ctx.send(f"{guess.author.mention} it's gotta be an integer between 0 and 100 (inclusive), ya dick")
        else:
            avg_guess += guess_val
            waiting_for_guess.remove(guess.author)
    return round(avg_guess/len(team.guessers), 2)


async def get_counter_guess(bot, ctx, team):
    msg = await ctx.send(f"Team representative {team.psychic.mention}, you think the answer is `higher` or `lower`?")

    def check_counter_guess(guess):
        return guess.author == team.psychic and \
                guess.channel == msg.channel and \
                guess.content == "higher" or guess.content == "lower"
    counter_guess = (await bot.wait_for("message", check=check_counter_guess)).content
    return lambda answer, guess: answer > guess if counter_guess == "higher" else answer < guess


async def update_scores(team1, team2, answer, guess, counter_guess):
    delta = abs(answer - guess)
    result_text = "\u200B\n\n\n"
    if delta <= 2:
        team1.score += 4
        result_text += f"DANG **{team1.name}** y'all were on the MONEY."
    elif 2 < delta <= 6:
        team1.score += 3
        result_text += f"Not bad **{team1.name}**, in the green."
    elif 6 < delta <= 10:
        team1.score += 2
        result_text += f"Uhh at least you get points I guess, **{team1.name}**."
    else:
        result_text += f"Not on the same wavelength today, huh **{team1.name}**?"
    result_text += f"\nAnswer was **{answer}** and you guessed **{guess}**."

    if delta > 2 and counter_guess(answer, guess):
        team2.score += 1
        result_text += f"\n**{team2.name}** get a point for being right."
    return result_text


async def wait(ctx, going_again, team):
    await ctx.send(f"Round boutta start in **{config['wait_time']}** seconds...")
    if going_again:
        await ctx.send(f"{team.name} gets to go again because they hit the red zone.")
    await asyncio.sleep(config["wait_time"])


async def display(ctx, team1, team2, prompt, max_score, text):
    embed = discord.Embed(
            title=f"{prompt[0]}  ⟵  0\n vs.\n{prompt[1]}  ⟶  100",
            description=text,
            color=discord.Colour.dark_gold()
        )

    embed.add_field(name="\u200B", value="\u200B")
    embed.add_field(name=f"__{team1.name}__: {team1.score}", inline=False, value=team1.to_string())
    embed.add_field(name=f"__{team2.name}__: {team2.score}", inline=False, value=team2.to_string())
    embed.set_image(url=config["banner"])
    # embed.set_thumbnail(url=config["thumbnail"])
    embed.set_footer(text=f"Score limit: {max_score}, {team1.name}'s turn")

    await ctx.send(embed=embed)


def get_prompt():
    prompt = random.choice(config["prompts"])
    config["prompts"].remove(prompt)
    return prompt


def get_team_names():
    return random.choice(config["team_names"])
