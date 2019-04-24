import discord
import asyncio
import datetime
from discord.ext import commands

import config
from .utils import checks


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.api_url = "https://api.digitalocean.com/v2/"
        self.auth_header = {"Authorization": f"Bearer {config.digitalocean_key}"}
        self.size_slug = "s-4vcpu-8gb"
        self.region_slug = "blr1"
        self.busy = False
        self.server_running = False
        self.minecraft_channel = self.bot.get_channel(config.minecraft_channel)
        self.status_message_obj = None
        self.bot.loop.create_task(self.initialize_status())
        # self.current_operation =

    @checks.has_role("Minecraft")
    @commands.group(aliases=["mc"])
    async def minecraft(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Usage: minecraft/mc start|stop")

    async def initialize_status(self):
        droplet = await self.get_minecraft_droplet()
        if droplet is None:
            self.server_running = False
            await self.update_status_embed("Server offline")
        else:
            self.server_running = True
            await self.update_status_embed(
                "Server running", ip=droplet["networks"]["v4"][0]["ip_address"]
            )

    @minecraft.command()
    async def update(self, ctx):
        await self.initialize_status()

    async def get_minecraft_droplet(self):
        response = await self.bot.http_session.get(
            self.api_url + "droplets?tag_name=minecraft", headers=self.auth_header
        )
        if response.status == 200:
            response_json = await response.json()
            if response_json["meta"]["total"] > 0:
                return response_json["droplets"][0]

    async def get_latest_snapshot(self):
        response = await self.bot.http_session.get(
            self.api_url + "snapshots?resource_type=droplet", headers=self.auth_header
        )
        if response.status == 200:
            response_json = await response.json()
            for snapshot in response_json["snapshots"]:
                if snapshot["name"].startswith("minecraft"):
                    return snapshot

    @checks.has_role("Minecraft")
    @minecraft.command()
    async def start(self, ctx):
        if self.busy:
            await ctx.send(
                "There is already a server start/stop operation in progress."
            )
            return
        if self.server_running:
            await ctx.send("The server is already running.")
            return

        if (await self.get_minecraft_droplet()) is not None:
            await ctx.send("The server is already running.")
            self.server_running = True
            return

        self.busy = True
        snapshot = await self.get_latest_snapshot()
        droplet_json = {
            "name": "minecraft",
            "region": self.region_slug,
            "size": self.size_slug,
            "image": snapshot["id"],
            "ssh_keys": None,
            "backups": False,
            "ipv6": True,
            "user_data": None,
            "private_networking": None,
            "volumes": None,
            "tags": ["minecraft"],
        }
        response = await self.bot.http_session.post(
            self.api_url + "droplets", json=droplet_json, headers=self.auth_header
        )
        if response.status == 202:
            json = await response.json()
            print(json)
            action_request = await self.bot.http_session.get(
                json["links"]["actions"][0]["href"], headers=self.auth_header
            )
            action = (await action_request.json())["action"]
            await self.wait_until_complete(action)
            new_droplet = await self.get_minecraft_droplet()
            await self.update_status_embed(
                "Server running", ip=new_droplet["networks"]["v4"][0]["ip_address"]
            )
            self.server_running = True
            self.busy = False

    @checks.has_role("Minecraft")
    @minecraft.command()
    async def stop(self, ctx):
        if self.busy:
            await ctx.send(
                "There is already a server start/stop operation in progress."
            )
            return
        if not self.server_running:
            await ctx.send("The server is not running.")
            return

        droplet = await self.get_minecraft_droplet()

        if droplet is None:
            await ctx.send("The server is not running.")
            self.server_running = False
            return

        self.busy = True
        current_snapshot = await self.get_latest_snapshot()
        response = await self.bot.http_session.post(
            self.api_url + f"droplets/{droplet['id']}/actions",
            json={"type": "shutdown"},
            headers=self.auth_header,
        )
        json = await response.json()
        shutdown_action = json["action"]
        await self.wait_until_complete(shutdown_action)
        await self.create_snapshot(droplet)
        await self.destroy_droplet(droplet)
        await self.delete_snapshot(current_snapshot)
        await self.update_status_embed("Server offline")
        self.server_running = False
        self.busy = False

    async def wait_until_complete(self, action):
        while action["status"] != "completed":
            response = await self.bot.http_session.get(
                self.api_url + f"actions/{action['id']}", headers=self.auth_header
            )
            json = await response.json()
            action = json["action"]
            await asyncio.sleep(10)

    async def create_snapshot(self, droplet):
        droplet_id = droplet["id"]
        now = datetime.datetime.now()
        response = await self.bot.http_session.post(
            self.api_url + f"droplets/{droplet_id}/actions",
            json={
                "type": "snapshot",
                "name": f"minecraft {now.strftime('%d-%m-%y %H:%M')}",
            },
            headers=self.auth_header,
        )
        if response.status in range(200, 300):
            action = (await response.json())["action"]
            print("Created snapshot action")
            await self.update_status_embed("Creating snapshot")
            await self.wait_until_complete(action)
            await self.update_status_embed("Created snapshot")

    async def destroy_droplet(self, droplet):
        response = await self.bot.http_session.delete(
            self.api_url + f"droplets/{droplet['id']}", headers=self.auth_header
        )
        if response.status == 204:
            print("Droplet destroyed")

    async def delete_snapshot(self, snapshot):
        snapshot_id = snapshot["id"]
        response = await self.bot.http_session.delete(
            self.api_url + f"snapshots/{snapshot_id}", headers=self.auth_header
        )
        if response.status == 204:
            print("Snapshot deleted")

    async def get_status_message(self):
        async for message in self.minecraft_channel.history():
            if message.author.id == self.bot.user.id and len(message.embeds) == 1:
                self.status_message_obj = message
                return message

    async def update_status_embed(self, status, ip=None):
        embed = discord.Embed(
            title="Minecraft Server Status", timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="Status", value=status)
        if ip is not None:
            embed.add_field(name="IP", value=ip)
        if (
            self.status_message_obj is not None
            or (await self.get_status_message()) is not None
        ):
            await self.status_message_obj.edit(embed=embed)
        else:
            await self.minecraft_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Minecraft(bot))
