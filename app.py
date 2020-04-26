from bokeh.io import curdoc, output_notebook
from bokeh.models.tools import HoverTool
from bokeh.models import DateRangeSlider,  ColumnDataSource, PreText, Select, Range1d, RadioButtonGroup, Div
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column, row
import bokeh
import pandas as pd
import numpy as np
df_confirmed = pd.read_csv('data/confirmed.csv', parse_dates=[0])
df_death = pd.read_csv('data/death.csv', parse_dates=[0])
df_recovered = pd.read_csv('data/recovered.csv', parse_dates=[0])

df_confirmed.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
df_death.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
df_recovered.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

regions_death = df_death.columns[1:]
regions_confirmed = df_confirmed.columns[1:]
regions_recovered = df_recovered.columns[1:]


def create_source(region, case='confirmed', date_range=None):
    if case == 'confirmed':
        df = df_confirmed
    elif case == 'death':
        df = df_death
    elif case == 'recovered':
        df = df_recovered
    if date_range is not None:
        mask = (df['date'] > np.datetime64(date_range[0])) & (
            df['date'] <= np.datetime64(date_range[1]))
        df = df.loc[mask]
    datasets = df[['date']].copy()
    datasets.loc[:, 'region'] = df[region]
    return ColumnDataSource(datasets)


def make_plot(source, title, case='confirmed', sizing_mode=None):
    if sizing_mode is None:
        plt = figure(x_axis_type='datetime')
    else:
        plt = figure(x_axis_type='datetime', sizing_mode=sizing_mode)
    plt.title.text = title
    plt.line('date', 'region', source=source, color='green')
    plt.circle('date', 'region', size=5, source=source)
    hover = HoverTool(tooltips=[('Date', '@date{%F}'), (case.capitalize()+' case', '@region')],
                      formatters={'date': 'datetime'})
    plt.add_tools(hover)
    # fixed attributes
    plt.xaxis.axis_label = "Date"
    plt.yaxis.axis_label = "Total cases"
    plt.axis.axis_label_text_font_style = "bold"
    plt.grid.grid_line_alpha = 0.3
    return plt


def update(date_range=None):
    plt.title.text = case.capitalize() + " case in " + region
    newdata = create_source(region, case, date_range).data
    source.data.update(newdata)


def handle_region_change(attrname, old, new):
    global region
    region = region_select.value
    update()
    return


def handle_case_change(attrname, old, new):
    global case
    cases = ["confirmed", "recovered", "death"]
    case = cases[new]
    update()


def handle_range_change(attrname, old, new):
    global slider_value
    # print(attrname, old, new)
    # print(range_slider.value)
    # print(range_slider.value_as_datetime)
    slider_value = range_slider.value_as_datetime
    update(date_range=slider_value)

# Default value


stats = PreText(text='', width=500)
case = "confirmed"
region = 'Indonesia'
source = create_source(region, case)

total_data = len(source.data['date'])-1
case_date = pd.to_datetime(source.data['date'])
slider_value = case_date[0], case_date[-1]
# widgets
case_select = RadioButtonGroup(
    labels=["Confirmed", "Recovered", "Death"], active=0)
region_select = Select(value=region, title='Country/Region',
                       options=list(regions_confirmed))

range_slider = DateRangeSlider(
    start=slider_value[0], end=slider_value[1], value=(0, slider_value[1]), title='Date')

# onchange
case_select.on_change('active', handle_case_change)
region_select.on_change('value', handle_region_change)
range_slider.on_change('value', handle_range_change)
plt = make_plot(source, case.capitalize() + " case in " +
                region, case, sizing_mode="stretch_width")
controls = column(region_select,  case_select, range_slider)
main_layout = row(controls, plt)
curdoc().add_root(main_layout)
curdoc().title = "Covid-19 case"
