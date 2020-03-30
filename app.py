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


STATIC_PATH = 'static'


#external_stylesheets = [r'.\static\style.css']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)


server = app.server

# Load the data in a dataframe structure
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 0, header = 2)
df.set_index('Solvent Name', inplace=True, drop=False)
# Drop first row as it is empty
df = df[1:]
HANSEN_COORDINATES = ['dD - Dispersion','dP - Polarity','dH - Hydrogen bonding']
WASTE = ['Incineration','Recycling','Biotreatment','VOC Emissions']
HEALTH = ['Health Hazard', 'Exposure Potential']
ENVIRONMENT = ['Aquatic Impact', 'Air Impact']
SAFETY = ['Flammability and Explosion', 'Reactivity and Stability']
df['GSK score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY])
df['Ra'] = update_Ra(df[HANSEN_COORDINATES])
df['Composite score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY])

traces = [solvents_trace(df,None),
        go.Scatter3d(x = [], y = [], z =[], mode='markers', marker=dict(color = 'black',
                                                        symbol = 'circle'),\
                                     marker_size=8,\
                                    text = ['Virtual solvent'],\
                                    hovertemplate = '<b>%{text}</b><br><br>' +\
                                     'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f}'),
        go.Scatter3d(x = [], y = [], z =[], mode='markers', marker=dict(color = 'black',
                                                                symbol = 'circle-open',\
                                                                opacity=0.8),\
                        marker_line_width = 4, marker_size = 8, marker_line_color="black",\
                        hoverinfo = 'skip'
                                            )]
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
        html.Div([
                html.H3('Selection of Functional Green Solvents'),
                html.Div(id = 'hansen-div', className = 'main-inputs-container',  children = [
                html.P('Type the Hansen parameters of the solute...'),
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
                html.Div(id = 'filters-div',className = 'big-container', children = [
                    html.Details([
                       html.Summary('Refine the solvent search by applying different filters'),
                       html.Div(id = 'div-hazard-list',className = 'filters-type', children = [
                            html.P('Remove solvent with the following hazard labels:'),
                            dcc.Dropdown(
                                id = 'hazard-list',
                                options=[{'label': label, 'value': label} for text, label in zip(df2['Fulltext'][2:48],df2.index[2:48])],
                                value = [],
                                placeholder = "Remove hazards...",
                                multi = True,
                                )
                        ]),
                        html.Div(id = 'checklist-div',className = 'filters-type',  children = [
                            html.P('Remove the following scores from the calculation:'),
                            html.Details( className = 'details-div', children = [
                                html.Summary(html.B('Exclude scores')),
                                dcc.Checklist(id = 'checklist-waste',
                                              options = [{'label': name, 'value': name} for name in WASTE],
                                              value = WASTE
                                              ),
                                dcc.Checklist(id = 'checklist-health',
                                              options = [{'label': name, 'value': name} for name in HEALTH],
                                              value = HEALTH
                                              ),
                                dcc.Checklist(id = 'checklist-environment',
                                              options = [{'label': name, 'value': name} for name in ENVIRONMENT],
                                              value = ENVIRONMENT
                                              ),
                                dcc.Checklist(id = 'checklist-safety',
                                              options = [{'label': name, 'value': name} for name in SAFETY],
                                              value = SAFETY
                                              )
                            ]),
                        ]),
                        html.Div(id = 'greenness-div',className = 'filters-type', children = [
                            html.P('Show only the solvents above the selected score:'),
                            html.B(html.Div(id = 'greenness-indicator', children = 'Greenness > 0')),
                            dcc.Slider(
                            id = 'greenness-filter',
                            min = 0,
                            max = 8,
                            value = 0,
                            step = 1,
                            )
                        ],  style = {'width' : '30%'}),
                    ])
                ]),
            html.P(),
            html.Div(id = 'report', className = 'big-container', children = create_report(),
                     style = {'display' : 'block','height' : '500px', 'overflow-y': 'auto'})     
            ],
            style = {'width' : '45%', 'display': 'inline-block','margin-right' : '20px'}        
            ),
            html.Div([
                html.Div(id = 'buttons-div', className  = 'buttons-container', children = [
                    html.Button('UPDATE',
                                id='button-update',
                                title = 'Click here to update the plot and table',
                                style = {'background-color': '#C0C0C0', 'margin' : '10px'}),
                    html.Button('RESET',
                                id='button-reset',
                                title = 'Click here to Reset the app',
                                style = {'background-color': '#C0C0C0','margin' : '10px'}),
                   ]),                       
               html.Div(['Data taken from this reference',html.Br(),
                         'You can find the paper in here', html.Br(),
                         "Checkout OPEG's group webpage"], style = {'display' : 'inline-block', 'width' : '55%','vertical-align':'top','margin-top': '3.6rem'}),                                         
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
                        columns=[{"name": i, "id": i} for i in df.columns[[-1, -2,0]]],
                        data = df[['Solvent Name', 'Composite score', 'Ra']].to_dict('records'),
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
                                     'height' : '300px',
                                     'maxHeight': '400px',
                                     'minWidth': '300px',
                                     'width': '100%',
                                     'maxWidth': '600px',
                                     'border': 'thin lightgrey solid'},
                        style_cell={'minWidth': '0px', 'width': '20px','maxWidth': '50px',
                                    'whiteSpace': 'normal', 'text-align':'center'
                                    }                
                        )
                    ], style = {'margin-top' : '20px', 'align-content': 'center', 'text-align' : 'center'}
                )
            ],           
            style = {'width' : '50%', 'display': 'inline-block', 'vertical-align':'top'}
            )            
            ]
    )
] )

@app.callback([Output('solvent-list', 'value'),
               Output('hazard-list', 'value'),
               Output('greenness-filter','value'),
               Output('checklist-waste', 'value'),
               Output('checklist-health', 'value'),
               Output('checklist-environment', 'value'),
               Output('checklist-safety', 'value'),
               Output('button-GSK-score', 'n_clicks')],
              [Input('button-reset', 'n_clicks')]
        )
def reset_all(n_clicks):
    return [],[], 0, WASTE, HEALTH, ENVIRONMENT, SAFETY, 0

@app.callback([Output('main-plot', 'figure'),
               Output('table', 'data')],
              [Input('button-update', 'n_clicks'),
               Input('greenness-filter','value'),
               Input('table', 'sort_by')],
              [State('main-plot', 'figure'),
               State('dD-input', 'value'),
               State('dP-input', 'value'),
               State('dH-input', 'value'),
               State('solvent-list', 'value'),
               State('hazard-list', 'value'),
               State('checklist-waste', 'value'),
               State('checklist-health', 'value'),
               State('checklist-environment', 'value'),
               State('checklist-safety', 'value')])
def display_virtual_solvent(_, greenness, sort_by, figure, dD, dP, dH, solvent_list, hazard_list, waste, health, environment, safety):
    # Updates based on the new Hansen coordinates
    df['Ra'] = update_Ra(df[HANSEN_COORDINATES], [dD,dP,dH])
    figure['data'][1]['x'] = [dD] if dD != None else []
    figure['data'][1]['y'] = [dP] if dP != None else []
    figure['data'][1]['z'] = [dH] if dH != None else []
    
    # Update the Compound score based on the labels the user selected
#    print('This items have been excluded for the GSK_score values')
#    [print(item) for item in WASTE if item not in waste]
#    [print(item) for item in HEALTH if item not in health]
#    [print(item) for item in ENVIRONMENT if item not in environment]
#    [print(item) for item in SAFETY if item not in safety]
    df['Composite score'] = GSK_calculator(df, [waste, health, environment, safety])
    print('The GSK score has been updated')
    
    
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
    greenness_filter = df['Composite score'] > greenness
    hazard_filter = filter_by_hazard(hazard_list, df['Hazard Labels'])
    data_filter = greenness_filter & hazard_filter

    figure['data'][0] = solvents_trace(df, data_filter)
    
    # Updates based on the data excluded
    dff = df[['Solvent Name', 'Composite score', 'Ra']][data_filter]

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

    return figure, dfs.to_dict('records')

@app.callback([Output('dD-input', 'value'),
               Output('dP-input', 'value'),
               Output('dH-input', 'value')],
            [Input('solvent-list', 'value')])
def update_hansen_parameters_by_list(solvent_list):
    N = len(solvent_list)
    if N > 0:
        dD, dP, dH = df[HANSEN_COORDINATES].loc[solvent_list].mean().round(2)
    else:
        dD, dP, dH = None, None, None
#        df['Ra'] = update_Ra(df['Hansen coordinates'], [dD,dP,dH])
#    print(dD, dP, dH)
    return  dD, dP, dH

@app.callback(Output('report', 'children'),
             [Input('table','selected_rows')],
             [State('table','data')])
def update_report(selected_row, data):
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
    return f'Compound score > {value:d}', sort_by



@app.server.route('/static/<resource>')
def serve_static(resource):
    return flask.send_from_directory(STATIC_PATH, resource)

if __name__ == '__main__':
    app.run_server(debug=True, port = 8051)