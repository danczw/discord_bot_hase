# imports
import logging
import os
import random

import discord
import dotenv
import openai
from discord.ext import commands

from commands import get_dice_results, get_server_info, get_weather_info

# ----------------------------------- SETUP -----------------------------------

# setup logging
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)

# load environment variables depending on local dev or prod env
is_docker = os.environ.get("ENV_DOCKER", False)

KEYS = {
    "DISCORD_TOKEN": "",
    "OPENAI_API_KEY": "",
    "OPENWEATHER_API_KEY": "",
    "BINGMAPS_API_KEY": ""
}

if is_docker:
    for key in KEYS:
        KEYS[key] = os.environ.get(key, "").strip("''")
else:
    dotenv.load_dotenv()
    for key in KEYS:
        KEYS[key] = os.getenv(key, "")

for key in KEYS:
    if key == "":
        raise ValueError(f"No token found. Please set {str(key)} in .env file.")

# initiate bot
intents = discord.Intents.all()
client = discord.Client(intents=intents)
intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)


# connect bot
@bot.event
async def on_ready():
    logger.info(f"Running in docker: {is_docker}")
    logger.info(f"Logged in as {bot.user.name} - {bot.user.id}")


# ------------------------------ COMMANDS - BASIC -----------------------------

# command - show meta data to user
@bot.command(name="info", help="Get meta data about the Server.")
async def info(ctx):
    response = get_server_info(ctx)

    await ctx.send(response)


# command - show weather data to user
@bot.command(name="weather", help="Get weather data for a location.")
async def weather(ctx, _location):
    location = _location.title()
    response = get_weather_info(ctx, location, KEYS)

    logger.info(f"Sending weather data for {location}")
    await ctx.send(response)


# ------------------------------- COMMANDS - FUN ------------------------------

# command - greet the user
@bot.command(name="hello", help="Says hello... or maybe not.")
async def hello(ctx):
    quote = [
        "Whad up?",
        "Not you again...",
        "Nice!"
    ]

    response = random.choice(quote)
    await ctx.send(response)


# command - roll a dice
@bot.command(
    name="dice",
    help="Simulates rolling a dice, e.g. '$dice 3'. Max _rolls is 10"
)
async def dice(ctx, _rolls: int = 0):
    response = get_dice_results(_rolls)

    await ctx.send(response)


# ------------------------------- COMMANDS - GPT ------------------------------

# talk to the bot
@bot.command(
    name="write",
    help="Let the bot write something for you, e.g. '$write a poem'."
)
async def gpt_text(ctx, *, _message):

    # use GPT3 to create an answer
    openai.api_key = KEYS["OPENAI_API_KEY"]
    response = openai.Completion.create(engine="text-davinci-003",
                                        prompt=_message,
                                        max_tokens=200,
                                        n=1,
                                        temperature=0.8,
                                        frequency_penalty=1.1)

    logger.info("Sending GPT3 text response.")
    await ctx.send(response.choices[0].text)


# code the bot
@bot.command(
    name="code",
    help="Let the bot write code for you, e.g. '$code python function ...'."
)
async def gpt_code(ctx, *, _message):

    # use GPT3 to create an answer
    openai.api_key = KEYS["OPENAI_API_KEY"]
    response = openai.Completion.create(engine="code-cushman-001",
                                        prompt=_message,
                                        max_tokens=200,
                                        n=1
                                        # temperature=0.8,
                                        # frequency_penalty=1.1
                                        )

    # TODO: format code response

    logger.info(response.choices[0].text)
    logger.info("Sending GPT3 coding response.")
    await ctx.send(":warning: - command still in beta:\n\n" + response.choices[0].text)


# --------------------------- EVENT HANDLING - USER  --------------------------

# new user - greet user and notify owner
@bot.event
async def on_member_join(member):
    await member.send(
        f"""
        Welcome to **{member.guild.name}**

        Pleased to have you with us, make sure to stay respectful.
        Type '*$help*' in any channel to find available commands.
        """
    )
    await member.guild.owner.send(f"{member} just joined {member.guild.name}.")

    # TODO: move to .env
    # role = discord.utils.get(member.guild.roles, name = "XXXX")
    # await member.add_roles(role)


# ------------------------------- ERROR HANDLING ------------------------------

# bot error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        logger.info(f"User {ctx.author} does not have the correct role.")
        await ctx.send("You do not have the correct role for this command.")
    if isinstance(error, commands.errors.CommandNotFound):
        logger.info(f"User {ctx.author} entered an invalid command.")
        await ctx.send("Not a viable comment. Type '$help'")


# ---------------------------------- RUN BOT  ---------------------------------

# initiate bot
bot.run(KEYS["DISCORD_TOKEN"])
