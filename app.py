#import os
#import numpy as np
import dash
import dash_core_components as dcc
import dash_table
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import flask
from support_functions import update_Ra, create_report, solvents_trace, df2,filter_by_hazard, GSK_calculator

# Folder where I can find the local resources, such as images
STATIC_PATH = 'static'


# Main stylesheet, so far, fetching it from an open source webpage
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# I start the dash object instance, saved in the variable app
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

server = app.server # No sure that this line is necessaru, not sure what it does...
#------------------- LOADING THE DATA -------------------------------------------
# Loading the Excel file with all the solvents and its properties (first sheet)
# The data is loaded in a DataFrame structure (see pandas library)
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 0, header = 2)
df.set_index('Solvent Name', inplace=True, drop=False) # The column name is set as a index, not sure is the wisest option
df = df[1:] # Here I am manually dropping the first row, as it is empty
##----------------- DEFINITION OF SOME GLOBAL VARIABLES -------------------------
# Now I put on different lists the columns that are somehow subgroups, which will make it easier to call them later on
HANSEN_COORDINATES = ['dD - Dispersion','dP - Polarity','dH - Hydrogen bonding'] # Columns' namesdefining the Hansen coordinates
WASTE = ['Incineration','Recycling','Biotreatment','VOC Emissions'] # Columns' names defining the waste score
HEALTH = ['Health Hazard', 'Exposure Potential']                    # Columns' names defining the health score
ENVIRONMENT = ['Aquatic Impact', 'Air Impact']                      # Idem
SAFETY = ['Flammability and Explosion', 'Reactivity and Stability'] #Idem
# Temperature range limits (min and max) that will be used in the Range Slidere later on. And offset of 5°C is added
TEMPERATURE_RANGE = [df['Melting Point (°C)'].min(axis = 0)-5, df['Boiling Point (°C)'].max(axis = 0)+5]
# Columns on the displayed table
TABLE_COLUMNS = {'Solvent': 'Solvent Name', 'Ra' : 'Ra', 'Composite score': 'Composite score',\
                 'mp (°C)': 'Melting Point (°C)', 'bp (°C)' : 'Boiling Point (°C)'}
##----------------- Adding new columns -----------------------------------
df['Ra'] = update_Ra(df[HANSEN_COORDINATES])
df['GSK score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY])  # This is the GSK score according to the paper
df['Composite score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY]) # This is the composite score, that the user can modify, initial eq. to GSK

#----------------CONFIGURING THE INITAL 3D PLOT--------------------------------
# traces is a list of traces objects. Each trace correspond to a set of data in our plot. We have 3 sets of data
# (1) solvents, (2) the virtual solute and (3) the highlighted solvents
traces = [solvents_trace(df,None),
        go.Scatter3d(x = [], y = [], z =[], mode='markers', marker=dict(color = 'black',
                                                        symbol = 'circle'),\
                                                        marker_size=8,\
                                                        text = ['Virtual solvent'],\
                                                        hovertemplate = '<b>%{text}</b><br><br>' +\
                                     'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f} <extra></extra>'),
        go.Scatter3d(x = [], y = [], z =[], mode='markers', marker=dict(color = 'black',
                                                                symbol = 'circle-open',\
                                                                opacity=0.8),\
                        marker_line_width = 4, marker_size = 8, marker_line_color="black",\
                        hoverinfo = 'skip')]
axis_template = {
    "showbackground": True,
    "backgroundcolor": '#F0F0F0',
    "gridcolor": '#808080',
    "zerolinecolor": '#808080',
}

plot_layout = go.Layout(height = 400, width = 600,
                        title = None,
                        font = {'size' : 11},
                        paper_bgcolor= '#F0F0F0',
                        plot_bgcolor = '#F0F0F0',
                        margin =  {"t": .25, "b": .25, "l": .25, "r": .25},
                        hoverlabel = {'bgcolor' : '#def192'}, 
                        scene={"aspectmode": "cube",
                               "xaxis": {"title": 'Dispersion (MPa)<sup>1/2</sup>', **axis_template},
                               "yaxis": {"title": 'Polarity (MPa)<sup>1/2</sup>', **axis_template },
                               "zaxis": {"title":'Hydrogen bonding (MPa)<sup>1/2</sup>', **axis_template },
                               "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 0.1}}
                               },
                        showlegend = False,
                        clickmode =  'event+select')

# Some of the callbacks will not exist at the beginning of the page.... check on that.
app.config['suppress_callback_exceptions']=True


app.layout = html.Div([html.Div(className = 'row',  children = [
        html.H3('Selection of Functional Green Solvent'),
        html.Div(className = 'column left', children = [
                html.Div(id = 'hansen-div', className = 'main-inputs-container',  children = [
                    html.P(['Type the ',html.Div(['Hansen parameters', html.Span('Some info about them', className = 'tooltiptext')], className = 'tooltip'),' of the solute...']),
                        html.Div(style = {'width': '225px', 'text-align' : 'right', 'align-content': 'center'}, children = [
                        html.P(['Dispersion:  ',
                            dcc.Input(
                                id = "dD-input",
                                name = 'dD',
                                type = 'number',
                                placeholder="dD",
                                style = {'width' : '80px'},
                            )]),
    
                        html.P(['Polarization: ',
                            dcc.Input(
                                id = "dP-input",
                                type = 'number',
                                placeholder="dP",
                                style = {'width' : '80px'},
                            )]),
                        html.P(['H bonding:  ',
                            dcc.Input(
                                id = "dH-input",
                                type = 'number',
                                placeholder="dH",
                                style = {'width' : '80px'},
                            )
                        ])
                    ])
                ]),
                html.Div(id = 'solvent-list-div', className = 'main-inputs-container', children = [
                    html.P('...or alternatively, select from the list the known functional solvent(s) of your solute:'),
                    dcc.Dropdown(
                        id='solvent-list',
                        options=[{'label': name, 'value': i} for name,i in zip(df['Solvent Name'],df.index)],
                        value = [],
                        placeholder = "Choose a solvent...",
                        multi = True,
                    )] 
               ),
                html.P('Refine the solvent search by applying different filters'),
                html.Div(id = 'filters-div', children = [
                    html.Details(className = 'main-inputs-container', children = [
                       html.Summary(html.B('Exclude solvents by hazard labels')),
                       html.Div(id = 'div-hazard-list',className = 'filters-type', children = [
                            html.P('Removes solvents with the following hazard labels:'),
                            dcc.Dropdown(
                                id = 'hazard-list',
                                options=[{'label': label, 'value': label} for text, label in zip(df2['Fulltext'][2:48],df2.index[2:48])],
                                value = [],
                                placeholder = "Remove hazards...",
                                multi = True,
                                )
                        ]),
                    ]),
                    html.Details(className = 'main-inputs-container', children = [
                        html.Summary(html.B(['Filter by ',html.Div(['composite score', html.Span(['= (waste * environment * health * safety)', html.Sup('1/4')], className = 'tooltiptext')], className = 'tooltip'),' value'])),  
                        html.Div(id = 'greenness-div',className = 'filters-type', children = [
                            html.P('Shows only the solvents above the selected score:'),
                            html.Div(id = 'greenness-indicator', children = 'Greenness > 0'),
                            dcc.Slider(
                            id = 'greenness-filter',
                            min = 0,
                            max = 8,
                            value = 0,
                            step = 1,
                            )
                        ],  style = {'width' : '100%', 'text-align' : 'center'}),
                    ]),
                    html.Details(className = 'main-inputs-container', children = [
                       html.Summary(html.B('Recalculate composite score')),                    
                        html.Div(id = 'checklist-div',className = 'filters-type',  children = [
                            html.P('The unchecked scores will be excluded from the final composite score'),
                            html.P(html.Em('Waste')),
                            dcc.Checklist(id = 'checklist-waste',
                                          options = [{'label': name, 'value': name} for name in WASTE],
                                          value = WASTE,
                                          labelStyle={'display': 'inline-block', 'width' : '50%'}
                                          ),
                            html.P(html.Em('Health')),
                            dcc.Checklist(id = 'checklist-health',
                                          options = [{'label': name, 'value': name} for name in HEALTH],
                                          value = HEALTH,
                                          labelStyle={'display': 'inline-block', 'width' : '50%'}
                                          ),
                            html.P(html.Em('Environment')),              
                            dcc.Checklist(id = 'checklist-environment',
                                          options = [{'label': name, 'value': name} for name in ENVIRONMENT],
                                          value = ENVIRONMENT,
                                          labelStyle={'display': 'inline-block', 'width' : '50%'}
                                          ),
                            html.P(html.Em('Safety')),  
                            dcc.Checklist(id = 'checklist-safety',
                                          options = [{'label': name, 'value': name} for name in SAFETY],
                                          value = SAFETY,
                                          labelStyle={'display': 'inline-block', 'width' : '50%'}
                                          )
                            ]),
                        ]),
                    html.Details(className = 'main-inputs-container', children = [
                        html.Summary(html.B('Filter by melting and boiling points')),
                            dcc.RangeSlider(
                                id='temperatures-range-slider',
                                min=TEMPERATURE_RANGE[0],
                                max=TEMPERATURE_RANGE[1],
                                step = 5,
                                value=TEMPERATURE_RANGE,
                                marks={
                                    0: {'label': '0°C', 'style': {'color': '#77b0b1'}},
                                    100: {'label': '100°C', 'style': {'color': '#f50'}}}
                            ),
                        html.P(id='output-temperature-slider')
                    ])
                ]),
            ]),
            html.Div(className = 'column middle', children = [
                html.Div(id = 'buttons-div', className  = 'buttons-container', children = [
                    html.Button('UPDATE',
                                id='button-update',
                                title = 'Click here to update the plot and table',
                                n_clicks = 1),
                    html.Button('RESET',
                                id='button-reset',
                                title = 'Click here to Reset the app'),
                   ]),                       
              html.Div([
                    dcc.Graph(id='main-plot', 
                          figure= { "data": traces,
                                    "layout": plot_layout,
                                    },
                          config={"editable": False, "scrollZoom": False},
                          style = {'margin-bottom' : '25px', 'display':'inline-block', 'text-align' : 'center'})
                ]),
                html.Div(id = 'table-div', children = [
                    dash_table.DataTable(
                        id='table',
                        columns=[{"name": key, "id": value} for key, value in TABLE_COLUMNS.items()],
                        data = df[list(TABLE_COLUMNS.values())].to_dict('records'),
            #            fixed_rows = { 'headers': True, 'data': 0},
                        style_as_list_view = True,
                        row_selectable = 'single',
                        selected_rows = [],
                        sort_by = [],
                        sort_mode = 'single',
                        sort_action='custom',
                        style_cell_conditional=[
                        {'if': {'column_id': 'Solvent Name'},
                            'textAlign': 'left','width': '20px','maxWidth': '50px'
                        }],
                        style_table={'overflowY': 'scroll',
                                     'overflowx': 'auto',
                                     'height' : '300px',
                                     'maxHeight': '400px',
                                     'minWidth': '300px',
                                     'width': '100%',
                                     'maxWidth': '600px',
                                     'border': 'thin lightgrey solid'},
                        style_cell={'minWidth': '0px', 'width': '20px','maxWidth': '50px',
                                    'whiteSpace': 'normal', 'text-align':'center'
                                    },
#                        style_data_conditional = [  {
#                            'if': {
#                                'column_id': 'Solvent Name',
#                                'filter_query': '{Composite score} > 6'
#                            },
#                            'backgroundColor': '#3D9970',
#                            'color': 'white',
#                        }],
                        )
                    ], style = {'margin-top' : '20px', 'align-content': 'center', 'text-align' : 'center'}
                ),  
            ]),
            html.Div(className = 'column right', children = [
                html.Div(id = 'report', className = 'big-container ', children = create_report(),
                 style = {'overflow-y': 'auto', 'height' : '600px'}),
                 html.Div(['Data taken from this ', html.A('reference', href = 'https://www.umu.se/globalassets/personalbilder/petter-lundberg/Profilbild.jpg?w=185'),\
                         html.Br(),
                         'You can find the paper in ',html.A('here', href = 'https://www.hitta.se/petter+lundberg/ume%C3%A5/person/~STlsww5X4'), html.Br(),
                         "Checkout OPEG's group webpage"])
            ])
        ], style = {'width' : '100%'})
] )

@app.callback(Output('button-update', 'n_clicks'),
              [Input('button-reset', 'n_clicks')]
        )
def reset_all(n_clicks):
    return 0


@app.callback(
    dash.dependencies.Output('output-temperature-slider', 'children'),
    [dash.dependencies.Input('temperatures-range-slider', 'value')])
def update_temperature_output(value):
    return 'You have solvents between mp of {}°C and bp of {} °C'.format(*value)

@app.callback([Output('dD-input', 'value'),
               Output('dP-input', 'value'),
               Output('dH-input', 'value')],
            [Input('solvent-list', 'value')],
           [State('button-update', 'n_clicks'),
           State('dD-input', 'value'),
           State('dP-input', 'value'),
           State('dH-input', 'value')])
def update_hansen_parameters_by_list(solvent_list, n_clicks, dD, dP, dH ):   
    N = len(solvent_list)
    if N > 0:
        dD, dP, dH = df[HANSEN_COORDINATES].loc[solvent_list].mean().round(2)
    elif n_clicks == 0:
        dD, dP, dH = None, None, None

#    print(n_clicks, dD, dP, dH)
    return  dD, dP, dH

@app.callback(Output('report', 'children'),
             [Input('table','selected_rows')],
             [State('table','data'),
              State('table','columns')])
def update_report(selected_row, data, columns):
    if selected_row == []:
        return create_report()
    else:
        # I first take the name of the selected Solvent
        n = selected_row[0]
        name_solvent = data[n]['Solvent Name'] # Selecet the name of the solvent from the key:" Solvent name"
        
        return create_report(df.loc[name_solvent])

@app.callback(Output('table', 'selected_rows'),
              [Input('main-plot', 'clickData')],
              [State('table', 'data')])
def update_selected_solvent(clicked_data, data):
    if clicked_data is None:
        selected_rows = []
    else:
        solvent_selected = clicked_data['points'][0]['text']
        if solvent_selected == 'Virtual solvent':
            selected_rows = []
        else:
            for i,solvent in enumerate(data):
                if solvent['Solvent Name'] == solvent_selected: break
            selected_rows = [i]
    return selected_rows


@app.callback([Output('greenness-indicator', 'children'),
              Output('table', 'sort_by')],
             [Input('greenness-filter','value')])
def update_GSK_filter(value):
    sort_by = [{'column_id': 'Ra', 'direction': 'asc'}]
    return f'Composite score > {value:d}', sort_by


@app.callback([Output('main-plot', 'figure'),
               Output('table', 'data'),
               Output('greenness-filter','value'),
               Output('solvent-list', 'value'),
               Output('hazard-list', 'value'),
               Output('checklist-waste', 'value'),
               Output('checklist-health', 'value'),
               Output('checklist-environment', 'value'),
               Output('checklist-safety', 'value'),
               Output('temperatures-range-slider', 'value')],
              [Input('button-update', 'n_clicks')],
              [State('table', 'sort_by'),
               State('main-plot', 'figure'),
               State('dD-input', 'value'),
               State('dP-input', 'value'),
               State('dH-input', 'value'),
               State('greenness-filter','value'),               
               State('solvent-list', 'value'),
               State('hazard-list', 'value'),
               State('checklist-waste', 'value'),
               State('checklist-health', 'value'),
               State('checklist-environment', 'value'),
               State('checklist-safety', 'value'),
               State('temperatures-range-slider', 'value')])
def display_virtual_solvent(n_clicks, sort_by, figure, dD, dP, dH, greenness, solvent_list, hazard_list, waste, health, environment, safety, Trange):
    # If the Reset button is click, reinitialize all the values
    if n_clicks == 0:
        sort_by, dD, dP, dH,greenness, solvent_list, hazard_list, waste, health, environment, safety, Trange = \
        [], None, None, None, 0, [], [], WASTE, HEALTH, ENVIRONMENT, SAFETY, TEMPERATURE_RANGE 
    # Updates based on the new Hansen coordinates
    df['Ra'] = update_Ra(df[HANSEN_COORDINATES], [dD,dP,dH])
    figure['data'][1]['x'] = [dD] if dD != None else []
    figure['data'][1]['y'] = [dP] if dP != None else []
    figure['data'][1]['z'] = [dH] if dH != None else []
    
    # Update the composite score based on the labels the user selected
#    print('This items have been excluded for the GSK_score values')
#    [print(item) for item in WASTE if item not in waste]
#    [print(item) for item in HEALTH if item not in health]
#    [print(item) for item in ENVIRONMENT if item not in environment]
#    [print(item) for item in SAFETY if item not in safety]
    df['Composite score'] = GSK_calculator(df, [waste, health, environment, safety])
#    print('The GSK score has been updated')
    
    
    if len(solvent_list) > 1:
        x, y, z = [],[],[]
        for solvent in solvent_list:
            dD, dP, dH =  df[HANSEN_COORDINATES].loc[solvent]
            x.append(dD), y.append(dP), z.append(dH)
    else:
        x, y, z = dD, dP, dH
    figure['data'][2]['x'] = x
    figure['data'][2]['y'] = y
    figure['data'][2]['z'] = z
        
    # Updates based on the greeness filter
    if greenness > 0:
        greenness_filter = df['Composite score'] > greenness
    else:
        greenness_filter = True
    hazard_filter = filter_by_hazard(hazard_list, df['Hazard Labels'])
    temperature_filter = (df['Melting Point (°C)'] > Trange[0]) & (df['Boiling Point (°C)'] < Trange[1])
    data_filter = greenness_filter & hazard_filter & temperature_filter

    figure['data'][0] = solvents_trace(df, data_filter)
    
    # Updates based on the data excluded
    dff = df[list(TABLE_COLUMNS.values())][data_filter]

    # If the sorting button have been clicked, it sorts according to the action (ascending or descending)
    # if not, sorts by the ascending distance in the Hansen space, by default
    if len(sort_by):
        dfs = dff.sort_values(
            sort_by[0]['column_id'],
            ascending= sort_by[0]['direction'] == 'asc',
            inplace=False
        )
        
    else:
        # Default sorting applied
#        print('Default sorting applied') 
        dfs = dff.sort_values('Ra', ascending= True, inplace = False)

    return figure, dfs.to_dict('records'), greenness, solvent_list, hazard_list, waste, health, environment, safety, Trange


# I need this lines to upload the images
@app.server.route('/static/<resource>')
def serve_static(resource):
    return flask.send_from_directory(STATIC_PATH, resource)

if __name__ == '__main__':
#    app.run_server(debug=True, port = 8051, host = '130.239.229.125')
    app.run_server(debug=True, port = 8051)#, host = '130.239.110.240')