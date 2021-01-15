import logging

from discord.ext.commands import Cog, command, has_permissions, CheckFailure

from ..db import db

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class Log(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("log")

    @Cog.listener()
    async def on_member_update(self, before, after):
        if before.display_name != after.display_name:
            logger.info(f'{before.display_name} changed their name to {after.display_name}')

    @Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.author.bot:
            pass

    @Cog.listener()
    async def on_message_delete(self, message):
        pass


def setup(bot):
    bot.add_cog(Log(bot))
