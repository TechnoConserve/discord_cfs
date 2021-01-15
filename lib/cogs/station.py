import logging
from typing import Optional

import discord
from bokeh.io import export_png
from discord import Embed
from discord.ext.commands import Cog, command, BucketType, cooldown

from ..bot import get_prefix
from ..db import db
from ..utils.get_cfs_data import check_site_existence, get_daily_site_data
from ..utils.graph_cfs import create_line_charts

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


def subscribe_user(member, station_id):
    logger.debug(
        f'Checking if subscription to station with ID {station_id} already exists for user {member.display_name}')
    user_id = db.record('SELECT UserID FROM subscriptions WHERE UserID = ? AND StationID = ?',
                        member.id, station_id)
    if user_id:
        logger.debug('Subscription already exists!')
        return False

    logger.debug(f'Subscribing {member.display_name} to station {station_id}')
    db.execute('INSERT INTO subscriptions (UserID, StationID) VALUES (?, ?)', member.id, station_id)
    return True


class Station(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name='list_stations', aliases=['show_stations', 'stations'])
    @cooldown(3, 30, BucketType.user)
    async def list_stations(self, ctx):
        logger.debug(f'{ctx.author.display_name} has requested a list of stations')
        sites = db.records('SELECT stations.StationID, StationName FROM stations '
                           'INNER JOIN subscriptions ON stations.StationID = subscriptions.StationID '
                           'WHERE subscriptions.UserID = ?', ctx.author.id)
        if len(sites) == 0:
            logger.debug('Did not find any stations in the database.')
            msg = f'{ctx.author.mention} You are not subscribed to any stations. You can add a station with the ' \
                  f'{get_prefix(self.bot, ctx.message)[-1]}add_station command. Valid station IDs ' \
                  f'can be found using the National Water Information System Mapper ' \
                  f'(https://maps.waterdata.usgs.gov/mapper/index.html)'
            await ctx.send(msg)
        else:
            embed = Embed(title=f"Station List",
                          description=f'{ctx.author.mention} You are currently subscribed to the following stations',
                          color=ctx.author.color)
            embed.add_field(name="Station ID", value='\n'.join([str(site[0]) for site in sites]))
            embed.add_field(name="Station Name", value='\n'.join([site[1] for site in sites]))
            embed.set_footer(text='Additional sites can be found on the '
                                  'National Water Information System Mapper '
                                  'https://maps.waterdata.usgs.gov/mapper/index.html')
            await ctx.send(embed=embed)

    @command(name='add_station', aliases=['monitor_station', 'subscribe_station'])
    @cooldown(4, 45, BucketType.user)
    async def add_station(self, ctx, station: int):
        logger.debug(f'{ctx.author.display_name} has requested a subscription to the station with ID {station}')
        logger.debug(f'Checking if station {station} exists in the database already')
        station_name = db.record('SELECT StationName FROM stations WHERE StationID = ?', station)
        if station_name:
            station_name = station_name[0]  # Unpack from single element tuple
            logger.debug(f'Found matching database record for station ID {station}. Station name: {station_name}')
            subscribed = subscribe_user(ctx.author, station)
            if subscribed:
                await ctx.send(
                    f"Successfully subscribed {ctx.author.display_name} to station {station_name} ({station})!")
            else:
                await ctx.send(
                    f'{ctx.author.display_name} is already subscribed to station {station_name} ({station}).')
        else:
            logger.debug(f'Checking if station {station} exists in the USGS water data service')
            station_name = check_site_existence(station)
            if station_name:
                logger.debug(f'Adding station {station_name} with ID {station} to database')
                db.execute('INSERT INTO stations (StationID, StationName) VALUES (?, ?)', station, station_name)
                subscribed = subscribe_user(ctx.author, station)
                if subscribed:
                    await ctx.send(
                        f"Successfully subscribed {ctx.author.display_name} to station {station_name} ({station})!")
                else:
                    await ctx.send(
                        f'{ctx.author.display_name} is already subscribed to station {station_name} ({station}).')
            else:
                logger.debug(f"Can't find a valid station with ID {station}")
                await ctx.send(f'Unable to find matching station with ID of {station}. Please check the '
                               f'National Water Information System Mapper '
                               f'(https://maps.waterdata.usgs.gov/mapper/index.html) to confirm you have the correct '
                               f'ID')

    @command(name="station_report", aliases=['report'])
    async def station_report(self, ctx, station: Optional[int]):
        logger.debug(f'{ctx.author.display_name} has requested a station report. Provided station: {station}')
        if station:
            # If we're only reporting one station we can send to channel
            cfs_data = get_daily_site_data([station])
            fig = create_line_charts(cfs_data)
            pic = export_png(fig, filename='temp/station_report.png')
            embed = Embed(title=f"Station report for {cfs_data['value']['timeSeries'][0]['sourceInfo']['siteName']} ({station})",
                          description='Graph displays streamflow volume in cubic feet per second for the previous 30 days')
            embed.set_image(url=f'https://waterdata.usgs.gov/nwisweb/graph?agency_cd=USGS&site_no={station}&parm_cd=00060&period=30')
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File(pic))
        else:
            # Since we're reporting for all of the users subscriptions we'll DM the report so we don't
            # clog the channel
            await ctx.author.send()

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("station")


def setup(bot):
    bot.add_cog(Station(bot))
