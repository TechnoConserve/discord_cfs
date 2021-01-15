import logging

import requests

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
                .format(sites=','.join(sites)),
            headers=HEADERS
        )

    if response.status_code == 200:
        return response.json()
