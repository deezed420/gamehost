from discord.ext import tasks
from discord import app_commands
import discord
import json

with open('config_v2.json', 'r') as f:
    config = json.load(f)

token = config['bot']['token']

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client)

server_configs = {}  # Store server-specific configurations

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    check_empty_channels.start()
    await tree.sync()
    print('Synced')

@tasks.loop(seconds=1)
async def check_empty_channels():
    for server_id, server_data in list(server_configs.items()):
        guild = client.get_guild(server_id)
        if guild:
            target_channel_id = server_data['target_channel_id']
            target_category_id = server_data['target_category_id']
            user_channels = server_data['user_channels']
            
            for channel_id, channel in list(user_channels.items()):
                if len(channel.members) == 0:
                    await channel.delete()
                    del user_channels[channel_id]

@client.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    server_id = guild.id
    server_data = server_configs.get(server_id)

    if not server_data: return

    target_channel_id = server_data['target_channel_id']
    target_category_id = server_data['target_category_id']
    user_channels = server_data['user_channels']

    if after.channel and after.channel.id == target_channel_id:
        if member.id in user_channels:
            await member.move_to(user_channels[member.id])
        else:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(connect=True)
            }
            category = guild.get_channel(target_category_id)
            channel_name = f"{member.display_name}'s room"
            channel = await category.create_voice_channel(channel_name, overwrites=overwrites)
            user_channels[member.id] = channel
            await member.move_to(channel)
    
    if before.channel and before.channel.id == target_channel_id:
        if before.channel.name == f"{member.display_name}'s room":
            if member.id in user_channels:
                del user_channels[member.id]

@tree.command(name="help", description="Shows the help menu.")
async def help(interaction):
    embed = discord.Embed(title="Help Menu",description="The help menu for Game Host.\n\nHere are the commands you can use:",colour=0x00b0f4)
    embed.add_field(name="/help",value="Brings up this menu.",inline=True)
    embed.add_field(name="/bind",value="Bind the bot to a certain channel.",inline=True)

    await interaction.response.send_message(embed=embed)

@tree.command(name="bind", description="Sets the bot up.")
@app_commands.describe(channel="The create channel.", category="The room category. If empty, will be the same category as the create channel.")
async def bind(interaction, channel: discord.VoiceChannel, category: discord.CategoryChannel = None):
    server_id = interaction.guild_id
    if server_id not in server_configs:
        server_configs[server_id] = {
            'target_channel_id': None,
            'target_category_id': None,
            'user_channels': {}
        }
    
    if not category: category = channel.category
    
    server_data = server_configs[server_id]
    server_data['target_channel_id'] = channel.id
    server_data['target_category_id'] = category.id
    
    embed = discord.Embed(title="Binding menu",description=f"You have now binded Game Host to {channel}.",colour=0x00b0f4)
    embed.add_field(name="Discord support",value="https://discord.gg/gYhaWJz8UZ",inline=True)
    
    await interaction.response.send_message(embed=embed)

client.run(token)