from bokeh.io import curdoc, output_notebook
from bokeh.models.tools import HoverTool
from bokeh.models import DateRangeSlider,  ColumnDataSource, PreText, Select, Range1d, RadioButtonGroup, Div, CustomJS, Button
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column, row
import bokeh
import pandas as pd
import numpy as np
from os.path import dirname, join
# import data
df_confirmed = pd.read_csv(
    join(dirname(__file__), 'data', 'confirmed.csv'), parse_dates=['date'])
df_death = pd.read_csv(join(dirname(__file__), 'data',
                            'death.csv'), parse_dates=['date'])
df_recovered = pd.read_csv(
    join(dirname(__file__), 'data', 'recovered.csv'), parse_dates=['date'])

df_confirmed.drop("Unnamed: 0", axis=1, inplace=True)
df_death.drop("Unnamed: 0", axis=1, inplace=True)
df_recovered.drop("Unnamed: 0", axis=1, inplace=True)
regions_death = df_death.columns[0:-1]
regions_confirmed = df_confirmed.columns[0:-1]
regions_recovered = df_recovered.columns[0:-1]
total_death_case = dict(df_death.iloc[-1, ])
total_recovered_case = dict(df_recovered.iloc[-1, ])
total_confirmed_case = dict(df_confirmed.iloc[-1, ])


def create_source(region, case, date_range=None):
    if case == 'confirmed':
        plot = df_confirmed[region]
    elif case == 'death':
        plot = df_death[region]
    elif case == 'recovered':
        plot = df_recovered[region]
    if case == "all":
        df = pd.DataFrame(data={
            'date': df_death['date'],
            'death': df_death[region],
            'recovered': df_recovered[region],
            'plot': df_confirmed[region]
        })
    else:
        df = pd.DataFrame(data={
            'date': df_death['date'],
            'plot': plot
        })
    if date_range is not None:
        mask = (df['date'] > np.datetime64(date_range[0])) & (
            df['date'] <= np.datetime64(date_range[1]))
        df = df.loc[mask]
    return ColumnDataSource(df)


def make_plot(source, title, case='confirmed', sizing_mode=None):
    if sizing_mode is None:
        plt = figure(x_axis_type='datetime', name='plt')
    else:
        plt = figure(x_axis_type='datetime',
                     sizing_mode=sizing_mode, name='plt', height=800)
    plt.title.text = title
    plt.line('date', 'plot', source=source, color='dodgerblue', line_width=2,
             name='case', legend_label=case)
    plt.circle('date', 'plot', size=5, color="dodgerblue", source=source)

    hover = HoverTool(tooltips=[('Date', '@date{%F}'), ('Total case', '@plot')],
                      formatters={'date': 'datetime'})
    plt.add_tools(hover)
    plt.legend.location = "top_left"
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
    from pprint import pprint
    from bokeh.models.glyphs import Line
    global case
    cases = ["confirmed", "recovered", "death", 'all']
    case = cases[new]
    update()

    # pprint(plt.properties(with_bases=True))
    if case == 'confirmed' or case == "all":
        color = 'dodgerblue'
    elif case == 'death':
        color = 'red'
    elif case == 'recovered':
        color = "green"

    if case != "all":
        plt.legend.items = [
            (case, [plt.renderers[0]])
        ]
        plt.renderers[0].glyph.line_color = color
        plt.renderers[1].glyph.line_color = color
        try:
            plt.renderers[2].visible = False
            plt.renderers[3].visible = False
        except IndexError:
            print(False)
    else:
        try:
            plt.renderers[2].visible = True
            plt.renderers[3].visible = True
            plt.legend.items = [
                ("confirmed", [plt.renderers[0]]),
                ("death", [plt.renderers[2]]),
                ("recovered", [plt.renderers[3]])
            ]
            plt.renderers[0].glyph.line_color = 'dodgerblue'
            plt.renderers[1].glyph.line_color = 'dodgerblue'
        except IndexError:
            plt.vbar('date', top='recovered', width=1, line_width=5, source=source, color='green',
                     name='recovered', legend_label="recovered")
            plt.step(x='date', y='death', source=source, color='red', line_width=2,
                     name='death', legend_label="death")


def handle_range_change(attrname, old, new):
    global slider_value
    slider_value = range_slider.value_as_datetime
    update(date_range=slider_value)


def change_theme():
    global theme
    if theme == "caliber":
        theme = 'dark_minimal'
    else:
        theme = "caliber"
    curdoc().theme = theme


# Default value
stats = PreText(text='', width=500)
case = "confirmed"
region = 'Indonesia'
source = create_source(region, case)
total_data = len(source.data['date'])-1
case_date = pd.to_datetime(source.data['date'])
slider_value = case_date[0], case_date[-1]
theme = 'dark_minimal'

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


# widgets
case_select = RadioButtonGroup(
    labels=["Confirmed", "Recovered", "Death", "All"], active=0, name="case_select")
region_select = Select(value=region, title='Country/Region',
                       options=list(regions_confirmed), name="region_select")
range_slider = DateRangeSlider(
    start=slider_value[0], end=slider_value[1], value=(0, slider_value[1]), title='Date', name="range_slider")
button = Button(label="Change theme", button_type="success")
# onchange
region_select.on_change('value', handle_region_change)

code = """
    var death = document.getElementById("total-Death");
    var recovered = document.getElementById("total-Recovered");
    var confirmed = document.getElementById("total-Confirmed");
    var region = cb_obj.value
    death.innerHTML = death_case[region]
    recovered.innerHTML = recovered_case[region]
    confirmed.innerHTML = confirmed_case[region]
"""

js_on_change_region = CustomJS(
    args=dict(source=source, death_case=total_death_case, confirmed_case=total_confirmed_case, recovered_case=total_recovered_case), code=code)
region_select.js_on_change('value', js_on_change_region)

case_select.on_change('active', handle_case_change)
range_slider.on_change('value', handle_range_change)
button.on_click(change_theme)
plt = make_plot(source, case.capitalize() + " case in " +
                region, case, sizing_mode="stretch_both")

# Layouting
about_text = """
    <div style="width:300px;">
        <ul class="list-group">
            <li class="list-group-item">Anvaqta Tangguh Wisesa</li>
            <li class="list-group-item">Rachma Indira</li>
            <li class="list-group-item">Rachmansyah Adhi Widhianto</li>
        </ul>
    </div>
"""
about = Div(text=about_text, width_policy="max")
controls = column(region_select,  case_select, range_slider, button,
                  confirmed_case, death_case, recovered_case,  row(about, sizing_mode="stretch_width"))
main_layout = row(controls, plt, sizing_mode="stretch_height")

curdoc().add_root(main_layout)
curdoc().title = "Covid-19 case"
curdoc().theme = theme
