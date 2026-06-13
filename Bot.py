import discord
from discord.ext import commands
import random
import re
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')

@bot.command(name='s')
async def roll(ctx, *, arg):
    try:
        match = re.search(r'(\d+)d10\s+(?:dif|diff|d)\s+(\d+)', arg.lower())
        if not match:
            await ctx.send("Formato inválido! Use: `!s Xd10 dif Y` (ex: `!s 4d10 dif 6`)")
            return
        num_dice = int(match.group(1))
        difficulty = int(match.group(2))
        if num_dice <= 0 or num_dice > 100:
            await ctx.send("Número de dados deve estar entre 1 e 100.")
            return
        rolls = [random.randint(1, 10) for _ in range(num_dice)]
        total_successes = 0
        for die in rolls:
            if die == 10: total_successes += 2
            elif die >= difficulty: total_successes += 1
            elif die == 1: total_successes -= 1
        rolls_str = ", ".join(map(str, rolls))
        await ctx.send(f"Roll: ({rolls_str})\n\n**{total_successes} Sucessos!**")
    except Exception as e:
        await ctx.send(f"Erro: {str(e)}")

token = os.getenv('DISCORD_TOKEN')
if __name__ == "__main__":
    bot.run(token)
