import logging
import requests

from ..db import db

HEADERS = {
    'Accept-Encoding': 'gzip,deflate',
}

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


def check_site_existence(station_id):
    response = requests.get(
        'https://waterservices.usgs.gov/nwis/dv/?format=json&site={site}'.format(site=station_id),
        headers=HEADERS
    )
    if response.status_code == 200:
        content = response.json()
        return content['value']['timeSeries'][0]['sourceInfo']['siteName']


def get_latest_values(json_data):
    """
    Creates and returns a list of tuples matching station ID to the latest streamflow reading from the given json_data.
    :param json_data: Dictionary of streamflow data pulled from the USGS waterdata service.
    :return: list of tuples [(x, y), ...] where x equals the station ID and y equals the most recent CFS value in the
    given json_data
    """
    latest_data = []
    for station_data in json_data['value']['timeSeries']:
        latest_data.append(([station_data['sourceInfo']['siteCode'][0]['value']], station_data['values'][0]['value'][-1]['value']))
    return latest_data


def get_station_name(station_id: int):
    logger.debug(f'Checking if station {station_id} exists in the database already')
    station_name = db.record('SELECT StationName FROM stations WHERE StationID = ?', station_id)
    if station_name:
        station_name = station_name[0]  # Unpack from single element tuple
        logger.debug(f'Found matching database record for station ID {station_id}. Station name: {station_name}')
        return station_name
    else:
        logger.debug(f'Checking if station {station_id} exists in the USGS water data service')
        station_name = check_site_existence(station_id)
        if station_name:
            logger.debug(f'Adding station {station_name} with ID {station_id} to database')
            db.execute('INSERT INTO stations (StationID, StationName) VALUES (?, ?)', station_id, station_name)
            return station_name


def get_daily_site_data(sites: list):
    # USGS data filter docs: https://waterservices.usgs.gov/rest/Site-Service.html
    logger.debug(f'Getting CFS data for {sites}')
    if len(sites) == 1:
        site = sites[0]
        # parameterCd 00060 filters for discharge, cubic feet per second
        response = requests.get(
            f'https://waterservices.usgs.gov/nwis/dv/?format=json&parameterCd=00060&period=P30D&site={site}',
            headers=HEADERS
        )
    else:
        response = requests.get(
            'https://waterservices.usgs.gov/nwis/dv/?format=json&parameterCd=00060&period=P30D&sites={sites}'
                .format(sites=','.join(str(site) for site in sites)),
            headers=HEADERS
        )

    if response.status_code == 200:
        return response.json()
