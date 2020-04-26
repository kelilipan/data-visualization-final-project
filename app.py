from bokeh.io import curdoc, output_notebook
from bokeh.models.tools import HoverTool
from bokeh.models import ColumnDataSource, PreText, Select, Range1d, RadioButtonGroup, Div
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import column, row
import bokeh
import pandas as pd

df_confirmed = pd.read_csv('data/confirmed.csv', parse_dates=[0])
df_death = pd.read_csv('data/death.csv', parse_dates=[0])
df_recovered = pd.read_csv('data/recovered.csv', parse_dates=[0])

df_confirmed.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
df_death.rename(columns={'Unnamed: 0': 'date'}, inplace=True)
df_recovered.rename(columns={'Unnamed: 0': 'date'}, inplace=True)

regions_death = df_death.columns[1:]
regions_confirmed = df_confirmed.columns[1:]
regions_recovered = df_recovered.columns[1:]


def create_source(region, case='confirmed'):
    if case == 'confirmed':
        df = df_confirmed
    elif case == 'death':
        df = df_death
    elif case == 'recovered':
        df = df_recovered
    datasets = df[['date']].copy()
    datasets.loc[:, 'region'] = df[region]
    return ColumnDataSource(datasets)


def make_plot(source, title, case='confirmed'):
    plt = figure(x_axis_type='datetime')
    print(source)
    plt.title.text = title
    plt.line('date', 'region', source=source, color='green')
    plt.circle('date', 'region', size=5, source=source)
    hover = HoverTool(tooltips=[('Date', '@date{%F}'), ('Confirmed case', '@Albania')],
                      formatters={'date': 'datetime'})
    plt.add_tools(hover)
    # fixed attributes
    plt.xaxis.axis_label = "Date"
    plt.yaxis.axis_label = "Total cases"
    plt.axis.axis_label_text_font_style = "bold"
    plt.grid.grid_line_alpha = 0.3
    return plt


def update():
    plt.title.text = case.capitalize() + " case in " + region
    newdata = create_source(region, case).data
    print(region, case)
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


# Default value
stats = PreText(text='', width=500)
case = "confirmed"
region = 'Indonesia'
source = create_source(region, case)

# widgets
case_select = RadioButtonGroup(
    labels=["Confirmed", "Recovered", "Death"], active=0)
region_select = Select(value=region, title='Country/Region',
                       options=list(regions_confirmed))

# onchange
case_select.on_change('active', handle_case_change)
region_select.on_change('value', handle_region_change)

plt = make_plot(source, case.capitalize() + " case in " + region, case)
controls = column(region_select,  case_select)
curdoc().add_root(row(plt, controls))
curdoc().title = "Covid-19 case"
