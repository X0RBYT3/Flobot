import discord
from discord.ext import commands


def setup(client):
    client.add_cog(MessageParser(client))


class MessageParser(commands.Cog):
    """
    Unused as of now, will contain
    - Crosslink implementation for server
    - Belt acceptance detection.
    """

    def __init__(self, client):
        self.client = client
        self.belts = {
            787696270675542066: "red",
            787696266401939497: "brown",
            787696274514247700: "black",
        }
        self.custom_roles = {}
