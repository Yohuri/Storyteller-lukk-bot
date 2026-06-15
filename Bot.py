import discord
from discord.ext import commands
import random
import re
import os
import json

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Armazenar rolagens salvas por servidor e usuário
saved_rolls = {}

def get_user_rolls(guild_id, user_id):
    """Retorna as rolagens salvas do usuário"""
    key = f"{guild_id}_{user_id}"
    if key not in saved_rolls:
        saved_rolls[key] = {}
    return saved_rolls[key]

def parse_dice(dice_str):
    """Extrai número de dados de uma string como '5d10' ou '3d10'"""
    match = re.match(r'(\d+)d10', dice_str.lower())
    if match:
        return int(match.group(1))
    return None

def parse_combined_roll(roll_str, user_rolls):
    """Extrai rolagens combinadas como '-attack-+-skill1-'"""
    # Remove espaços
    roll_str = roll_str.replace(' ', '')
    
    # Extrai nomes entre hífens, separados por +
    # Padrão: -name1- ou -name1-+-name2- ou -name1-+-name2-+-name3- etc
    parts = re.findall(r'-([a-zA-Z0-9_]+)-', roll_str)
    
    if not parts:
        return None, "Formato inválido para rolagem combinada. Use: `-name1-+-name2-`"
    
    total_dice = 0
    for part in parts:
        if part in user_rolls:
            num_dice = parse_dice(user_rolls[part])
            if num_dice:
                total_dice += num_dice
        else:
            return None, f"Rolagem '{part}' não encontrada."
    
    return total_dice, None

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')

@bot.command(name='s')
async def roll(ctx, *, arg):
    try:
        user_rolls = get_user_rolls(ctx.guild.id, ctx.author.id)
        
        # Comando: !s save name Xd10
        if arg.lower().startswith('save '):
            parts = arg.split(' ', 2)
            if len(parts) < 3:
                await ctx.send("Formato inválido! Use: `!s save name Xd10` (ex: `!s save attack 5d10`)")
                return
            
            roll_name = parts[1].lower()
            dice_str = parts[2]
            
            if not re.match(r'^\d+d10$', dice_str.lower()):
                await ctx.send("Formato inválido! Use apenas `Xd10` (ex: `5d10`)")
                return
            
            user_rolls[roll_name] = dice_str
            await ctx.send(f"✅ Rolagem `{roll_name}` salva como `{dice_str}`")
            return
        
        # Comando: !s list
        if arg.lower() == 'list':
            if not user_rolls:
                await ctx.send("Você não tem nenhuma rolagem salva.")
                return
            
            list_str = "📋 **Suas Rolagens Salvas:**\n"
            for name, dice in user_rolls.items():
                list_str += f"  • `{name}`: {dice}\n"
            await ctx.send(list_str)
            return
        
        # Comando: !s name dif Y (rolagem simples salva)
        # Comando: !s -name1-+-name2- dif Y (rolagem combinada)
        # Comando: !s Xd10 dif Y (rolagem direta)
        
        match = re.search(r'(.*?)\s+(?:dif|diff|d)\s+(\d+)$', arg.lower())
        if not match:
            await ctx.send("Formato inválido! Use: `!s [Xd10|name|-name1-+-name2-] dif Y` (ex: `!s 4d10 dif 6` ou `!s -attack-+-skill1- dif 7`)")
            return
        
        roll_input = match.group(1).strip()
        difficulty = int(match.group(2))
        
        if difficulty < 1 or difficulty > 10:
            await ctx.send("Dificuldade deve estar entre 1 e 10.")
            return
        
        # Determinar número de dados
        num_dice = None
        
        # Tenta parse como rolagem direta (Xd10)
        if re.match(r'^\d+d10$', roll_input):
            num_dice = parse_dice(roll_input)
        
        # Tenta parse como rolagem combinada (-name1-+-name2-)
        elif '-' in roll_input and '+' in roll_input:
            num_dice, error = parse_combined_roll(roll_input, user_rolls)
            if error:
                await ctx.send(f"❌ Erro: {error}")
                return
        
        # Tenta parse como rolagem salva simples
        elif roll_input in user_rolls:
            num_dice = parse_dice(user_rolls[roll_input])
        
        else:
            await ctx.send(f"❌ Rolagem '{roll_input}' não encontrada. Use `!s list` para ver suas rolagens salvas.")
            return
        
        if num_dice is None or num_dice <= 0:
            await ctx.send("Formato inválido de dados!")
            return
        
        if num_dice > 100:
            await ctx.send("Número de dados não pode exceder 100.")
            return
        
        # Executar rolagem
        rolls = [random.randint(1, 10) for _ in range(num_dice)]
        total_successes = 0
        for die in rolls:
            if die == 10: total_successes += 2
            elif die >= difficulty: total_successes += 1
            elif die == 1: total_successes -= 1
        
        rolls_str = ", ".join(map(str, rolls))
        await ctx.send(f"{ctx.author.mention} - Roll: ({rolls_str})\n\n**{total_successes} Sucessos!**")
    
    except Exception as e:
        await ctx.send(f"Erro: {str(e)}")

token = os.getenv('DISCORD_TOKEN')
if __name__ == "__main__":
    bot.run(token)
