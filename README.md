# Streamflow Grapher Discord Bot

A discord bot for monitoring your favorite streams and rivers.

## How it works

Streamflow Grapher Bot allows users to subscribe to various streamflow sensor 
stations and request a current streamflow report for these stations.

The default command prefix for Streamflow Grapher Bot is `!` as shown in the below examples.

Find a station using the [National Water Information System Mapping Tool](https://maps.waterdata.usgs.gov/mapper/index.html) and
make note of the location's "Site Number." Tell the bot you want to subscribe
to the station using the command `!add_station SiteNumber`. For example,
to subscribe to the "GREEN RIVER NEAR GREENDALE, UT" station with a site number of 
09234500, the command would be `!add_station 09234500`.

You won't need to commit these site numbers to memory. To list out the stations you're
subscribed to, and to get their site numbers, use the command `!list_stations`.

You can request a report of a given station using the `!station_report StationID` command
(e.g. `!station_report 09234500`). The report includes a USGS created graph of streamflow 
data along with a bot generated line graph also of streamflow data. Both graphs request the 
previous 30 days worth of streamflow data but you may find that the USGS graph does not 
actually extend that far back in the past. 

## Commands

- `!add_station StationID`
    - Aliases: `monitor_station` `subscribe_station`
    - Description: Subscribes the user to the given station.

- `!help`
    - Aliases: None
    - Description: Offers a help menu describing how to use the available commands.

 - `!list_stations`
    - Aliases: `show_stations` `stations`
   - Description: Sends a message listing out the station subscriptions of the requesting user.
    
- `!station_report StationID`
    - Aliases: `report`
    - Description: Sends a message containing two graphs of the last 30 days of streamflow data
    in cubic feet per second. The first graph is USGS generated and may not be able to provide all
      30 days of the past in their graphs.
    
