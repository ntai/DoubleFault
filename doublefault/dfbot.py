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
import logging

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

        self.servers = {} # The severs that the bot belongs
        self.channel_maps = {} # Channel map per server
        self.my_roles = {} # The severs that the bot belongs
        self.self_rolls = {}

        self.echo_map = {}

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


    async def handle_server_message(self, message):
        # Handing the message
        self.nag( "got server message" )

        if message.role_mentions is not None:
            await self.maybe_echo(message)
            pass
        pass

    async def maybe_echo(self, message):
        for role in message.role_mentions:
            self.nag("contains role %s" % role.name)
            pass
        server = message.guild
        if not server.id in self.echo_map:
            self.nag("message's server %s has no echo map." % server.name)
            return
        echo_map = self.echo_map[server.id]
        do_echo = False
        src_channel = message.channel
        for role in message.role_mentions:
            if role.id in echo_map:
                dest_channel = echo_map[role.id]
                if dest_channel.id != src_channel.id:
                    #
                    do_echo = True
                    await dest_channel.send("%s/#%s: %s" % (message.author.name, src_channel.name, message.content))
                    break
                pass
            pass
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
        # This is busted.  permissions_for() is broken.
        # perms = channel.permissions_for(message.author)
        # if not perms.manage_roles:
        #     self.nag( "no role management")
        #     pass

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

    async def on_ready(self):
        # self.guilds - all of servers that the bot is in.
        # Convenient cache for my servers
        for server in self.guilds:
            self.servers[server.id] = server
            self.servers[server.name] = server

            # Using None for server - a bit of hack
            channel_map_by_id = {None: server}
            channel_map_by_name = {None: server}
            for channel in server.channels:
                channel_map_by_id[channel.id] = channel
                channel_map_by_name[channel.name] = channel
                pass

            self.channel_maps[server.id] = (channel_map_by_id, channel_map_by_name)

            role_map_by_name = {None: server}
            role_map_by_id = {None: server}
            for role in server.roles:
                role_map_by_name[role.name] = role
                role_map_by_id[role.id] = role
                pass
            self.my_roles[server.id] = (role_map_by_id, role_map_by_name)
            pass

        self.setup_reaction_roles()
        self.setup_message_echo()
        return

    def setup_reaction_roles(self):
        # setting up the source / destination pairs
        reaction_roles = self.config.get("reaction-roles")
        for reaction_role in reaction_roles:
            server_name = reaction_role.get("server")
            server = self.servers.get(server_name)
            if server is None:
                self.nag("I don't belong to server '%s'" % server_name)
                pass
            if not server.id in self.channel_maps:
                self.nag("I have no channel map for '%s'" % server_name)
                continue
            (channel_map_by_id, channel_map_by_name) = self.channel_maps.get(server.id)
            channel_name = reaction_role.get("channel")
            channel = channel_map_by_name.get(channel_name)
            if channel is None:
                self.nag("%s/%s does not exist.\n" % (server_name, channel_name))
                continue
            pass
        pass

    def setup_message_echo(self):
        # setting up the source / destination pairs
        echoes = self.config.get("echo")
        if echoes is None:
            self.nag("no echoes")
            pass

        for echo in echoes:
            server_name = echo.get("server")
            server = self.servers[server_name]
            if server is None:
                self.nag("I don't belong to server %s" % server_name)
                continue

            if not server.id in self.channel_maps:
                self.nag("I have no channel map for '%s'" % server_name)
                continue
            (channel_map_by_id, channel_map_by_name) = self.channel_maps[server.id]

            channel_name = echo.get("channel")
            channel = channel_map_by_name.get(channel_name)
            if channel is None:
                self.nag("channel map %s/%s does not exist.\n" % (server_name, channel_name))
                continue

            if not server.id in self.my_roles:
                self.nag("role map %s/%s does not exist.\n" % (server_name, channel_name))
                pass
            (roles_by_id, roles_by_name) = self.my_roles[server.id]
            role_name = echo.get("role")
            role = roles_by_name.get(role_name)
            if role is None:
                self.nag("%s/%s does not exist.\n" % (server_name, role_name))
                continue
            
            # server/role-mentioned = channel
            if not server.id in self.echo_map:
                self.echo_map[server.id] = {}
                pass
            self.echo_map[server.id][role.id] = channel
            self.nag( "echo map established %s/%s = %s" % (server.name, role.name, channel.name))
            pass

        pass

    def nag(self, message):
        logging.info(message)
        pass

    pass

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config",  dest="config",  help="bot config",  default="/var/lib/doublefault/config.json")
    parser.add_argument("--account", dest="account", help="bot account", default="/var/lib/doublefault/account.json")
    args = parser.parse_args()

    bot = DoubleFault(config_file=args.config, account_file=args.account, verbose=True)
    bot.run(bot.account["token"], bot=True)
    pass
