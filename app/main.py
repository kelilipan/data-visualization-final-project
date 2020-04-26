from bokeh.io import curdoc, output_notebook
from bokeh.models.tools import HoverTool
from bokeh.models import DateRangeSlider,  ColumnDataSource, PreText, Select, Range1d, RadioButtonGroup, Div, CustomJS
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column, row
import bokeh
import pandas as pd
import numpy as np
from os.path import dirname, join
# import data
df_confirmed = pd.read_csv(
    join(dirname(__file__), 'data', 'confirmed.csv'), parse_dates=[0])
df_death = pd.read_csv(join(dirname(__file__), 'data',
                            'death.csv'), parse_dates=[0])
df_recovered = pd.read_csv(
    join(dirname(__file__), 'data', 'recovered.csv'), parse_dates=[0])

df_confirmed.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
df_death.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
df_recovered.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

regions_death = df_death.columns[1:]
regions_confirmed = df_confirmed.columns[1:]
regions_recovered = df_recovered.columns[1:]


def create_source(region, case, date_range=None):
    if case == 'confirmed':
        plot = df_confirmed[region]
    elif case == 'death':
        plot = df_death[region]
    elif case == 'recovered':
        plot = df_recovered[region]
    df = pd.DataFrame(data={
        'date': df_death['date'],
        'death': df_death.iloc[-1, df_confirmed.columns.get_loc(region)],
        'recovered': df_recovered.iloc[-1, df_confirmed.columns.get_loc(region)],
        'confirmed': df_confirmed.iloc[-1, df_confirmed.columns.get_loc(region)],
        'plot': plot
    })
    if date_range is not None:
        # print(date_range)
        mask = (df['date'] > np.datetime64(date_range[0])) & (
            df['date'] <= np.datetime64(date_range[1]))
        df = df.loc[mask]
    return ColumnDataSource(df)


def make_plot(source, title, case='confirmed', sizing_mode=None):
    if sizing_mode is None:
        plt = figure(x_axis_type='datetime', name='plt')
    else:
        plt = figure(x_axis_type='datetime',
                     sizing_mode=sizing_mode, name='plt')
    plt.title.text = title
    plt.line('date', 'plot', source=source, color='green')
    plt.circle('date', 'plot', size=5, source=source)
    hover = HoverTool(tooltips=[('Date', '@date{%F}'), (case.capitalize()+' case', '@plot')],
                      formatters={'date': 'datetime'})
    plt.add_tools(hover)
    # fixed attributes
    plt.xaxis.axis_label = "Date"
    plt.yaxis.axis_label = "Total cases"
    plt.axis.axis_label_text_font_style = "bold"
    plt.grid.grid_line_alpha = 0.3
    return plt


def update(date_range=None, force=False):
    global region, case, plt
    plt.title.text = case.capitalize() + " case in " + region
    newdata = create_source(region, case, date_range).data
    source.data.update(newdata)


def handle_region_change(attrname, old, new):
    global region
    region = region_select.value
    update()


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

# html template
total_case_template = ("""
    <div style="width:300px;">
        <div class="card text-center w-100">
            <div class="card-header bg-{color}">
                <h4 class="m-0">{case}</h4>
            </div>
            <div class="card-body p-2">
                <h3><strong id="total-{case}">{total}</strong></h3>
            </div>
        </div>
    </div>
      """)

death_count = df_death.iloc[-1, df_death.columns.get_loc(region)]
confirmed_count = df_confirmed.iloc[-1, df_confirmed.columns.get_loc(region)]
recovered_count = df_recovered.iloc[-1, df_recovered.columns.get_loc(region)]
death_case = Div(text=total_case_template.format(
    case="Death", color='danger', total=death_count), width_policy="max")
confirmed_case = Div(text=total_case_template.format(
    case="Confirmed", color='primary', total=confirmed_count), width_policy="max")
recovered_case = Div(text=total_case_template.format(
    case="Recovered", color='success', total=recovered_count), width_policy="max")
testo = "var a = []"
code = """
    var death = document.getElementById("total-Death");
    var recovered = document.getElementById("total-Recovered");
    var confirmed = document.getElementById("total-Confirmed");
    death.innerHTML = source.data.death[0]
    recovered.innerHTML = source.data.recovered[0]
    confirmed.innerHTML = source.data.confirmed[0]
"""

js_on_change_region = CustomJS(args=dict(source=source), code=code)

# widgets
case_select = RadioButtonGroup(
    labels=["Confirmed", "Recovered", "Death"], active=0, name="case_select")
region_select = Select(value=region, title='Country/Region',
                       options=list(regions_confirmed), name="region_select")
range_slider = DateRangeSlider(
    start=slider_value[0], end=slider_value[1], value=(0, slider_value[1]), title='Date', name="range_slider")

# onchange
region_select.on_change('value', handle_region_change)
region_select.js_on_change('value', js_on_change_region)

case_select.on_change('active', handle_case_change)
range_slider.on_change('value', handle_range_change)
plt = make_plot(source, case.capitalize() + " case in " +
                region, case, sizing_mode="stretch_width")

# Layouting
controls = column(region_select,  case_select, range_slider,
                  death_case, confirmed_case, recovered_case)
main_layout = row(controls, plt)

curdoc().add_root(main_layout)
curdoc().title = "Covid-19 case"
