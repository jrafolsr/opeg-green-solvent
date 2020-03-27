#import os
#import numpy as np
import dash
import numpy as np
import dash_core_components as dcc
import dash_table
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
from support_functions import update_Ra, create_report, solvents_trace, df2,filter_by_hazard, GSK_calculator2

#external_stylesheets = [r'.\static\style.css']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)


server = app.server

# Load the data in a dataframe structure
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 0, header = 2)
df.set_index('Solvent Name', inplace=True, drop=False)
# Drop first row as it is empty
df = df[1:]
# Add extra columns with calculated parameters
df['Hansen coordinates']= [np.array([df['dD - Dispersion'].iloc[i], df['dP - Polarity'].iloc[i], df['dH - Hydrogen bonding'].iloc[i]]) for i in range(df.shape[0])]
list_GSK_scores = df.columns.values[7:18]
df['Waste'] = [np.array([df['Incineration'].iloc[i], df['Recycling'].iloc[i], df['Biotreatment'].iloc[i], df['VOC Emissions'].iloc[i]]) for i in range(df.shape[0])]
df['Environment'] = [np.array([df['Aquatic Impact'].iloc[i], df['Air Impact'].iloc[i]]) for i in range(df.shape[0])]
df['Health'] = [np.array([df['Health Hazard'].iloc[i], df['Exposure Potential'].iloc[i]]) for i in range(df.shape[0])]
df['Safety'] = [np.array([df['Flammability and Explosion'].iloc[i], df['Reactivity and Stability'].iloc[i]]) for i in range(df.shape[0])]
df['Ra'] = np.nan
WASTE = ['Incineration','Recycling','Biotreatment','VOC Emissions']
HEALTH = ['Health Hazard', 'Exposure Potential']
ENVIRONMENT = ['Aquatic Impact', 'Air Impact']
SAFETY = ['Flammability and Explosion', 'Reactivity and Stability']
df['Composite score'] = GSK_calculator2(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY])

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
                        font = {'size' : 12},
                        paper_bgcolor= '#F0F0F0',
                        plot_bgcolor = '#F0F0F0',
                        margin =  {"t": 0, "b": 0, "l": 0, "r": 0},
                        scene={"aspectmode": "cube",
                               "xaxis": {"title": 'Dispersion dD (MPa)<sup>1/2</sup>', **axis_template},
                               "yaxis": {"title": 'Polarity dP (MPa)<sup>1/2</sup>', **axis_template },
                               "zaxis": {"title":'Hydrogen bonding dH (MPa)<sup>1/2</sup>', **axis_template }},
                        showlegend = False,
                        clickmode =  'event+select')





app.layout = html.Div([html.Div(className = 'row',  children = [
        html.Div([
                html.H3('Selection of Functional Green Solvents'),
                html.Div(children = [
                    html.P([' Dispersion: ',
                        dcc.Input(
                            id = "dD-input",
                            name = 'dDha',
                            type = 'number',
                            placeholder="dD",
                            debounce = True,
                            style = {'width' : '80px'},
                        ),
                    ' Polarization: ',
                        dcc.Input(
                            id = "dP-input",
                            type = 'number',
                            placeholder="dP",
                            debounce = True,
                            style = {'width' : '80px'},
                        ),
                    ' H bonding: ',
                        dcc.Input(
                            id = "dH-input",
                            type = 'number',
                            placeholder="dH",
                            debounce = True,
                            style = {'width' : '80px'},
                        )
                    ])
                ]),
            dcc.Graph(id='main-plot', 
                  figure= { "data": traces,
                            "layout": plot_layout,
                            },
                  config={"editable": False, "scrollZoom": False},
                  style = {'margin-bottom' : '25px'}),
            html.P(),
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
                             'maxHeight': '300px',
                             'minWidth': '300px',
                             'maxWidth': '600px',
                             'border': 'thin lightgrey solid'},
                style_cell={'minWidth': '0px', 'width': '20px','maxWidth': '50px',
                            'whiteSpace': 'normal', 'text-align':'center'
            }                
                )
            ],
            style = {'max-Width' : '60%', 'display': 'inline-block','margin-right': '50px'}        
            ),
            html.Div([
                html.Div(id = 'div-solvent-list', children = [
                    dcc.Dropdown(
                        id='solvent-list',
                        options=[{'label': name, 'value': i} for name,i in zip(df['Solvent Name'],df.index)],
                        value = [],
                        placeholder = "Choose a solvent...",
                        multi = True,
                    )] , style = {'width' : '50%','display': 'inline-block'}
               ),
               html.Div(id = 'div-hazard-list', children = [          
                    dcc.Dropdown(
                        id = 'hazard-list',
                        options=[{'label': label, 'value': label} for text, label in zip(df2['Fulltext'][2:48],df2.index[2:48])],
                        value = [],
                        placeholder = "Remove hazards...",
                        multi = True
                    ),
                ], style = {'width' : '50%','display': 'inline-block'}
                ),
                html.Div( id = 'checklist-container', children = [
                    html.Details([html.Summary(html.B('Exclude scores')),
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
                html.Button('Plot virtual solvent', id='virtual-solvent', style = {'width': '50%', 'background-color': '#C0C0C0'}),
                html.Div([
                    html.B(html.Div(id = 'greenness-indicator', children = 'Greenness > 0')),
                    dcc.Slider(
                    id = 'greenness-filter',
                    min = 0,
                    max = 8,
                    value = 0,
                    step = 1,
                )], style = {'width' : '200px', 'display': 'inline-block', 'margin-left' : '20px'}), 
                html.Div(id = 'report', children = create_report()
             )
                ],
            

            style = {'width' : '40%', 'display': 'inline-block', 'vertical-align':'top', 'margin-top' : '3.6rem'}
            )            
            ]
    )
] )



@app.callback([Output('main-plot', 'figure'),
               Output('table', 'data')],
              [Input('virtual-solvent', 'n_clicks'),
               Input('greenness-filter','value'),
               Input('table', 'sort_by')],
              [State('main-plot', 'figure'),
               State('dD-input', 'value'),
               State('dP-input', 'value'),
               State('dH-input', 'value'),
               State('solvent-list', 'value'),
               State('hazard-list', 'value')])
def display_virtual_solvent(_, greenness, sort_by, figure, dD, dP, dH, solvent_list, hazard_list):
#    print(dD, dP, dH)
    
    # Updates based on the new Hansen coordinates
    df['Ra'] = update_Ra(df['Hansen coordinates'], [dD,dP,dH])
    figure['data'][1]['x'] = [dD] if dD != None else []
    figure['data'][1]['y'] = [dP] if dP != None else []
    figure['data'][1]['z'] = [dH] if dH != None else []
    
    if len(solvent_list) > 1:
        x, y, z = [],[],[]
        for solvent in solvent_list:
            dD, dP, dH = df['Hansen coordinates'].loc[solvent]
            x.append(dD), y.append(dP), z.append(dH)
    else:
        x, y, z = [],[],[]
    figure['data'][2]['x'] = x
    figure['data'][2]['y'] = y
    figure['data'][2]['z'] = z
        
    # Updates based on the greeness filter
    greenness_filter = df['Composite score'] > greenness
    hazard_filter = filter_by_hazard(hazard_list, df['Hazard Labels'])
    data_filter = greenness_filter & hazard_filter
    if greenness > 0:
        figure['data'][0] = solvents_trace(df, data_filter)
    
    # Updates based on the data excluded
    dff = df[['Solvent Name', 'Composite score', 'Ra']][data_filter]

    # In the sorting bitton have been clicked, it sort according to the action (ascending or descending)
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
            [Input('solvent-list', 'value')],
            [State('dD-input', 'value'),
             State('dP-input', 'value'),
             State('dH-input', 'value')])
def update_hansen_parameters_by_list(solvent_index,  dD, dP, dH):
    N = len(solvent_index)
    if N > 0:
        dD, dP, dH = df['Hansen coordinates'].loc[solvent_index].mean().round(2)
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
             [Input('greenness-filter','value'),
              Input('virtual-solvent', 'n_clicks')])
def update_greenness(value, _):
    sort_by = [{'column_id': 'Ra', 'direction': 'asc'}]
    return f'Greenness > {value:d}', sort_by

#@app.callback(Output('test','children'),
#        [Input('checklist-waste', 'value')])
#def checklist_scores(value):
#    print(value)
#    return ''

if __name__ == '__main__':
    app.run_server(debug=True, port = 8051)