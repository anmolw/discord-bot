from discord.ext import commands

import config


def is_owner_check(message):
    return message.author.id == config.owner_id


def has_role_check(role, message):
    return role in [role.name for role in message.author.roles]


def has_role(role):
    return commands.check(lambda ctx: has_role_check(role, ctx.message))


def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))


def trivia_whitelist():
    return commands.check(lambda ctx: ctx.message.channel.id in config.trivia_whitelist or is_owner_check(ctx.message))
