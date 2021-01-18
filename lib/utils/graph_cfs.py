import datetime

from bokeh.plotting import figure

from .get_cfs_data import get_station_name


def create_line_charts(json_data):
    figs = []
    for station_data in json_data['value']['timeSeries']:
        if 'Streamflow' in station_data['variable']['variableName']:
            cfs_values = []
            time_values = []
            for data_value in station_data['values'][0]['value']:
                cfs_values.append(data_value['value'])
                time_values.append(datetime.datetime.strptime(data_value['dateTime'][:10], '%Y-%m-%d'))

            fig = figure(
                title=get_station_name(station_data['sourceInfo']['siteCode'][0]['value']),
                plot_width=800,
                plot_height=300,
                x_axis_type="datetime",
                x_axis_label="Date",
                y_axis_label="Streamflow Rate (Cubic Feet/Second)",
                tools=[]  # Users only see the PNG export so no point in including tool icons
            )
            fig.line(time_values, cfs_values, color='navy', alpha=0.5)

            figs.append(fig)

    return figs
