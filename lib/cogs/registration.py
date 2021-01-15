from discord.ext.commands import Cog

from ..db import db


class Registration(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("registration")

    @Cog.listener()
    async def on_member_join(self, member):
        db.execute("INSERT INTO users (UserID) VALUES (?)", member.id)
        print(f"Registered {member.display_name} in {member.guild.name}.")

    @Cog.listener()
    async def on_member_remove(self, member):
        db.execute("DELETE FROM users WHERE UserID = ?", member.id)
        print(f"{member.display_name} has left {member.guild.name}. User ({member.id}) removed from database.")


def setup(bot):
    bot.add_cog(Registration(bot))
