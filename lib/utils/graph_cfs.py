import datetime

from bokeh.plotting import figure


def create_line_charts(json_data, chart_title=''):
    figs = []
    for station in json_data['value']['timeSeries']:
        if 'Streamflow' in station['variable']['variableName']:
            cfs_values = []
            time_values = []
            for data_value in station['values'][0]['value']:
                cfs_values.append(data_value['value'])
                time_values.append(datetime.datetime.strptime(data_value['dateTime'][:10], '%Y-%m-%d'))

            fig = figure(
                title=chart_title,
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
