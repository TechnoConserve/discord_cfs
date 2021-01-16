__version__ = "0.0.15"

from asyncio import sleep
from glob import glob

import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from discord import Embed, HTTPException, Forbidden
from discord import Intents
from discord.ext.commands import Bot as BotBase, CommandNotFound, BadArgument, CommandOnCooldown, when_mentioned_or, \
    Context

from ..db import db

OWNER_IDS = [208449015015145472]
COGS = [path.split('\\')[-1][:-3] for path in glob('./lib/cogs/*.py')]


def get_prefix(bot, message):
    prefix = db.field("SELECT Prefix FROM guilds WHERE GuildID = ?", message.guild.id)
    return when_mentioned_or(prefix)(bot, message)


class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f'\t{cog} ready')

    @property
    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])


class Bot(BotBase):
    def __init__(self):
        self.VERSION = __version__
        self.TOKEN = None
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        self.stdout = None
        self.scheduler = AsyncIOScheduler()

        db.autosave(self.scheduler)

        super().__init__(
            command_prefix=get_prefix,
            owner_ids=OWNER_IDS,
            intents=Intents.all(),
        )

    def setup(self):
        for cog in COGS:
            self.load_extension(f'lib.cogs.{cog}')

        print('Setup complete')

    def run(self):
        print('Running setup...')
        self.setup()

        with open('./lib/bot/token.0', 'r', encoding='utf-8') as tf:
            self.TOKEN = tf.read()

        print('Running bot...')
        super().run(self.TOKEN, reconnect=True)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)
            else:
                await ctx.send("I'm not ready to recieve commands. Please wait a few seconds.")

    async def on_connect(self):
        print('\tbot connected')

    async def on_disconnect(self):
        print('Bot disconnected')

    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("[!] Something went wrong with that command.")
        else:
            await self.stdout.send('[!] An error occurred.')

        raise

    async def on_command_error(self, context, exception):
        if isinstance(exception, BadArgument):
            pass
        elif isinstance(exception, CommandNotFound):
            pass
        elif isinstance(exception, CommandOnCooldown):
            await context.send(f"[!] Woah, woah, woah. Slow your roll buddy. "
                               f"That command is on cooldown for {exception.retry_after:,.2f} more seconds")
        elif isinstance(exception, HTTPException):
            await context.send("[!] Unable to send message.")
        elif isinstance(exception, Forbidden):
            await context.send("[!] I don't have permission to do that.")
        elif hasattr(exception, 'original'):
            raise exception.original
        else:
            raise exception

    async def on_ready(self):
        if not self.ready:
            self.guild = self.get_guild(786104547113566218)
            self.stdout = self.get_channel(789670241663582238)
            self.scheduler.start()

            self.update_db()

            mst_tz = pytz.timezone('MST')  # Mountain Standard Time
            current_time = datetime.now().astimezone(mst_tz)
            embed = Embed(title='Now online!',
                          description='A bot to monitor your favorite rivers and streams.',
                          color=0x99CCFF,
                          timestamp=current_time)
            fields = [('Version', self.VERSION, True),
                      ('Bot Amazingness Level', 'Maximum', True),
                      ('Data Source', 'USGS National Water Information System (https://waterdata.usgs.gov)', False)]
            embed.set_author(name='Streamflow Grapher Bot', icon_url=self.guild.icon_url)
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            await self.stdout.send(embed=embed)

            print('\twaiting for cogs...')
            while not self.cogs_ready.all_ready:
                await sleep(0.5)

            self.ready = True
            print('\tbot ready!')
        else:
            print('Bot reconnected.')

    async def on_message(self, message):
        if not message.author.bot:
            await self.process_commands(message)

    def update_db(self):
        db.multiexec('INSERT OR IGNORE INTO guilds (GuildID) VALUES (?)',
                     ((guild.id,) for guild in self.guilds))

        db.multiexec('INSERT OR IGNORE INTO users (UserID) VALUES (?)',
                     ((member.id,) for member in self.guild.members if not member.bot))

        to_remove = []
        stored_members = db.column('SELECT UserID from users')
        for id_ in stored_members:
            if not self.guild.get_member(id_):
                to_remove.append(id_)

        db.multiexec('DELETE FROM users WHERE UserID = ?',
                     ((id_,) for id_ in to_remove))

        db.commit()


bot = Bot()
