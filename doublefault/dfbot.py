#/usr/bin/python3

import discord
import json
import sys
import time
import re
import datetime
import discord.user
import traceback
import asyncio
import argparse

#
class DoubleFault(discord.Client):
    def __init__(self,
                 config_file = "/var/lib/doublefault/config.json",
                 account_file = "/var/lib/doublefault/account.json",
                 verbose=False):
        super().__init__()

        self.start_time = time.time()

        self.config = json.load(open(config_file))
        self.account = json.load(open(account_file))

        self.discord_servers = {}
        for server_desc in self.config["greeting-servers"]:
            self.discord_servers[server_desc[0]] = server_desc[1]
            pass

        self.my_servers = {} # The severs that the bot belongs
        self.self_rolls = {}
        self.current_log = None
        self.verbose = verbose
        pass


    async def on_member_join(self, member):
        server = member.guild

        if not member.guild.name in self.discord_servers.keys():
            return

        # self.new_members.append(member)

        server_spec = self.discord_servers[member.guild.name]
        
        info_channel_name = server_spec.get("info-channel")
        if info_channel_name is None: info_channel_name = "info"

        info_channel = discord.utils.find(lambda channel: channel.name == info_channel_name, server.channels)

        greetings_main = server_spec.get("greetings-main")
        if greetings_main is not None:
            message = greetings_main.format(member, server)
        else:
            # Reasonable default message.
            message = "Welcome!"
            pass

        greetings_info = server_spec.get("greetings-info")
        if info_channel is not None and greetings_info is not None:
            message = message + "  " + greetings_info.format(info_channel)
            pass

        # await self.send_message(server, message)
        pass


    async def on_message(self, message):
        # If I'm dispatching the message that I sent, ignore
        if message.author == self.user:
            return

        # PM
        if message.guild is None:
            if message.author.bot:
                await self.handle_bot_pm(message)
            else:
                await self.handle_pm(message)
                pass
            return

        #
        await self.handle_server_message(message)
        return


    async def handle_server_message(self, message):
        # Handing the message
        pass

    # Handling PM from person
    async def handle_pm(self, message):
        reply = "ping"
        if reply is not None:
            await message.channel.send(reply)
            pass
        return

    # Handling PM from bot
    async def handle_bot_pm(self, message):
        if message.author.name.lower().startswith("gymhuntrbot"):
            # self.handle_gymhuntr_bot(message)
            pass
        pass

    # Handling of reaction
    async def on_raw_reaction_add(self, reaction_event):
        # reaction_event is a RawReactionActionEvent
        await self.add_remove_reaction_role(True, # reaction_event.event_type == REACTION_ADD? but, event_type doesn't exist.
                                            reaction_event.channel_id,
                                            reaction_event.message_id,
                                            reaction_event.user_id,
                                            reaction_event.guild_id)
        pass
        
    async def on_raw_reaction_remove(self, reaction_event):
        # reaction_event is a RawReactionActionEvent
        await self.add_remove_reaction_role(False,
                                            reaction_event.channel_id,
                                            reaction_event.message_id,
                                            reaction_event.user_id,
                                            reaction_event.guild_id)
        pass


    async def add_remove_reaction_role(self, adding, channel_id, message_id, user_id, guild_id):
        
        channel = self.get_channel(channel_id)

        if channel.name[:10] != "self-roles":
            # this is not a self-roles channel
            return

        message = await channel.fetch_message(message_id)

        server = await self.fetch_guild(guild_id)
        perms = channel.permissions_for(message.author)
        if not perms.manage_roles:
            self.nag( "no role management")
            pass

        member = server.get_member(user_id)
        if member is None:
            member = await server.fetch_member(user_id)
            pass

        if member is None:
            self.nag("could not get member instance from user id {}".format(user_id))
            pass

        role_name = message.content
        if role_name[:3] == '<@&':
            role_id = int(role_name[3:-1])
            roll_match = False
            for role in server.roles:
                if role.id == role_id:
                    roll_match = True
                    if adding:
                        try:
                            await member.add_roles(role)
                            self.nag( "ADD: %s to %s" % (role.name, member.name))
                        except discord.Forbidden:
                            self.nag("Cannot add role %s to %s" % (role.name, member.name))
                            pass
                        pass
                    else:
                        try:
                            await member.remove_roles(role)
                            self.nag( "REMOVE: %s from %s" % (role.name, member.name))
                        except discord.Forbidden:
                            self.nag("Cannot remove role %s from %s" % (role.name, member.name))
                            pass
                        pass
                    break
                pass
            if not roll_match:
                self.nag( "Role %s/%s not found" % (role_name, role_id))
                for role in server.roles:
                    self.nag("%s : %s" % (role.name, role.id))
                    pass
                pass
            pass
        else:
            self.nag( "NOPE: %s" % role_name)
            pass
        return

    async def on_ready(self):
        # self.guilds - all of servers that the bot is in.
        # Convenient cache for my servers
        for server in self.guilds:
            # Using None for server - a bit of hack
            submap = {None: server}
            for channel in server.channels:
                submap[channel.name] = channel
                pass
            self.my_servers[server.name] = submap
            pass

        await self.setup_reaction_roles()
        return

    async def setup_reaction_roles(self):
        # setting up the source / destination pairs
        reaction_roles = self.config.get("reaction-roles")
        for reaction_role in reaction_roles:
            server_name = reaction_role.get("server")
            server = self.my_servers.get(server_name)
            if server is None:
                self.nag("%s does not exist.\n" % server_name)
                continue
            channel_name = reaction_role.get("channel")
            channel = server.get(channel_name)
            if channel is None:
                self.nag("%s/%s does not exist.\n" % (server_name, channel_name))
                continue
            pass
        pass

    def nag(self, message):
        if self.verbose:
            print(message)
            pass
        pass

    pass

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--config",  dest="config",  help="bot config",  default="/var/lib/doublefault/config.json")
parser.add_argument("--account", dest="account", help="bot account", default="/var/lib/doublefault/account.json")
args = parser.parse_args()
    
bot = DoubleFault(config_file=args.config, account_file=args.account)
bot.run(bot.account["token"], bot=True)
