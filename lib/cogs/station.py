import logging
import datetime
from typing import Optional

import discord
from bokeh.io import export_png
from discord import Embed
from discord.ext.commands import Cog, command, BucketType, cooldown

from ..bot import get_prefix
from ..db import db
from ..utils.get_cfs_data import get_daily_site_data, get_latest_values, get_station_name
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


def get_stations(user_id):
    sites = db.records('SELECT stations.StationID, StationName FROM stations '
                       'INNER JOIN subscriptions ON stations.StationID = subscriptions.StationID '
                       'WHERE subscriptions.UserID = ?', user_id)
    return sites


async def no_subs_msg(bot, context):
    msg = f'{context.author.mention} You are not subscribed to any stations. You can add a station with the ' \
          f'{get_prefix(bot, context.message)[-1]}add_station command. Valid station IDs ' \
          f'can be found using the National Water Information System Mapper ' \
          f'(https://maps.waterdata.usgs.gov/mapper/index.html)'
    await context.send(msg)


class Station(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name='list_stations', aliases=['show_stations', 'stations'])
    @cooldown(3, 30, BucketType.user)
    async def list_stations(self, ctx):
        logger.debug(f'{ctx.author.display_name} has requested a list of stations')
        sites = get_stations(ctx.author.id)
        if len(sites) == 0:
            logger.debug('Did not find any stations in the database.')
            await no_subs_msg(self.bot, ctx)
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
        station_name = get_station_name(station)
        if station_name:
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
            station_name = cfs_data['value']['timeSeries'][0]['sourceInfo']['siteName']
            last_measurement = cfs_data['value']['timeSeries'][0]['values'][0]['value'][-1]['value']
            fig = create_line_charts(cfs_data)
            pic = export_png(fig, filename='temp/station_report.png')
            desc = f'The first graph is a USGS generated graph requesting data from the previous ' \
                   f'30 days although they often only graph data from the previous week. The lower graph ' \
                   f'is bot generated using USGS data from the previous 30 days.\n\nCurrent flow: {last_measurement}'
            embed = Embed(title=f"Station report for {station_name} ({station})", description=desc)
            """
            The Discord application will cache the image content so we need to use the data filter with the USGS link 
            to ensure that the url also changes on a daily basis
            """
            current_date = datetime.datetime.today()
            month_past = current_date - datetime.timedelta(days=30)
            embed.set_image(url=f'https://waterdata.usgs.gov/nwisweb/graph?agency_cd=USGS&site_no={station}&parm_cd=00060&startDT={month_past:%Y-%m-%d}')
            await ctx.send(embed=embed)
            await ctx.send(file=discord.File(pic))
        else:
            stations = get_stations(ctx.author.id)
            station_ids = [station[0] for station in stations]
            station_names = [station[1] for station in stations]
            if not station_ids:
                await no_subs_msg(self.bot, ctx)
            cfs_data = get_daily_site_data(station_ids)
            figs = create_line_charts(cfs_data)
            latest_values = get_latest_values(cfs_data)
            embed = Embed(title=f'Station report for {ctx.author.display_name}\'s station subscriptions')
            embed.add_field(name="Station ID", value='\n'.join([str(station_id) for station_id in station_ids]))
            embed.add_field(name="Station Name",
                            value='\n'.join([name[:40] + '...' if len(name) > 44 else name for name in station_names]))
            embed.add_field(name="Latest CFS Value", value='\n'.join([data[1] for data in latest_values]))
            await ctx.send(embed=embed)
            for station_idx, fig in enumerate(figs):
                pic = export_png(fig, filename=f'temp/{station_ids[station_idx]}_report.png')
                await ctx.send(file=discord.File(pic))
            desc = f'Line graph of streamflow data for all stations subcribed to by {ctx.author.display_name}'

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("station")


def setup(bot):
    bot.add_cog(Station(bot))
