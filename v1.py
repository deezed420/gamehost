import discord
from discord.ext import commands, tasks
import json

with open('config.json', 'r') as f: config = json.load(f)

token = config['bot']['token']
target_channel_id = int(config['channel']['target_channel_id'])
category_id = int(config['channel']['target_category_id'])

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

user_channels = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    check_empty_channels.start()

@tasks.loop(seconds=1)
async def check_empty_channels():
    for channel_id, channel in list(user_channels.items()):
        if len(channel.members) == 0:
            await channel.delete()
            del user_channels[channel_id]

@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.id == target_channel_id:
        guild = member.guild
        if member.id in user_channels:
            await member.move_to(user_channels[member.id])
        else:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(connect=True)
            }
            category = guild.get_channel(category_id)
            channel_name = f"{member.display_name}'s room"
            channel = await category.create_voice_channel(channel_name, overwrites=overwrites)
            user_channels[member.id] = channel
            await member.move_to(channel)
    if before.channel and before.channel.id == target_channel_id:
        if before.channel.name == f"{member.display_name}'s room":
            if member.id in user_channels:
                del user_channels[member.id]

bot.run(token)
