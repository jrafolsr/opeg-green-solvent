#import os
#import numpy as np
import dash
import numpy as np
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# Load the data in a dataframe structure
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet = 0, header = 2)
# Drop first row as it is empty
df = df[1:]
# Add extra columns with calculated parameters
df['Hansen coordinates']= [[df['dD - Dispersion'].iloc[i], df['dP - Polarity'].iloc[i], df['dH - Hydrogen bonding'].iloc[i]] for i in range(df.shape[0])]
list_GSK_scores = df.columns.values[7:18]
df['Waste'] = (df['Incineration']*df['Recycling']*df['Biotreatment']*df['VOC Emissions'])**0.25
df['Environment']  =(df['Aquatic Impact']*df['Air Impact'])**0.5
df['Health'] = (df['Health Hazard']*df['Exposure Potential'])**0.5
df['Safety'] = (df['Flammability and Explosion']*df['Reactivity and Stability'])**0.25
df['Greenness'] = round((df['Waste']*df['Environment']*df['Health']*df['Safety'])**0.25,2)

x = df['dD - Dispersion']
y = df['dP - Polarity']
z = df['dH - Hydrogen bonding']

traces = [go.Scatter3d(x = x, y = y, z = z, mode='markers', marker=dict(size=8,\
                                                        color = df['Greenness'],\
                                                        colorscale = 'RdYlGn',\
                                                        opacity=0.8,\
                                                        showscale = True),
                    hovertemplate = '<b>%{text}</b><br>' +\
                                     '%{hovertext}<br>' +\
                                     'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f}',
                    text = df['Solvent Name'],\
                    hovertext = [f'Greenness  = {value:.2f}' for value in df['Greenness']]),
        go.Scatter3d(x = [np.nan], y = [np.nan], z =[np.nan], mode='markers', marker=dict(size=12,\
                                                        color = 'black',\
                                                        opacity=0.8,\
                                                        symbol ='diamond'),\
                                    hovertemplate = '<b>Virtual solvent</b><br><br>' +\
                                     'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f}')]

plot_layout = go.Layout(height=600, title = None,
                paper_bgcolor='white',
                margin =  {"t": 0, "b": 0, "l": 0, "r": 0},
                scene={"aspectmode": "cube",
                       "xaxis": {"title": 'dD - Dispersion', },
                       "yaxis": {"title": 'dP - Polarity', },
                       "zaxis": {"title":'dH - Hydrogen bonding' }},
                showlegend = False)





app.layout = html.Div([
    html.H2('OPEG lab app for Green Solvent '),
    html.Div(className = 'row',  children = [
        html.Div([        
            dcc.Graph(id='main-plot', 
                  figure= { "data": traces,
                            "layout": plot_layout,
                            },
                          config={"editable": False, "scrollZoom": False},)],
            style = {'width' : '60%', 'display': 'inline-block'}        
            ),
            html.Div([
                html.Button('Update plot', id='update-plot'),    
                html.Div(children = [
                    dcc.Input(
                        id = "dD-input",
                        type = 'number',
                        placeholder="dD value",
                ),
                    dcc.Input(
                        id = "dP-input",
                        type = 'number',
                        placeholder="dP value",
                    ),
                    dcc.Input(
                        id = "dH-input",
                        type = 'number',
                        placeholder="dH value",
                    ), 
                    html.Button('Find known solvent', id='filter-by-solvent-value')
                ]),  
                dcc.Dropdown(
                    id='solvent-list',
                    options=[{'label': name, 'value': i} for name,i in zip(df['Solvent Name'],df.index)],
                    value = [],
                    placeholder = "Choose a solvent...",
                    multi = True
                     ),                
                html.Button('Find virtual solvent', id='filter-by-solvent-gmean')
                ],
            style = {'width' : '40%', 'display': 'inline-block'}
            )            
            ]
    )
    
])



@app.callback([Output('main-plot', 'figure'),
               Output('dD-input', 'value'),
               Output('dP-input', 'value'),
               Output('dH-input', 'value')],
              [Input('filter-by-solvent-gmean', 'n_clicks')],
              [State('main-plot', 'figure'),
               State('solvent-list', 'value')])
def display_virtual_solvent(_, figure, solvent_index):
    N = len(solvent_index)
    if N == 0:
        figure['data'][1]['x'] = [np.nan]
        figure['data'][1]['y'] = [np.nan]
        figure['data'][1]['z'] = [np.nan]
        dD, dP, dH = None, None, None
    else:
        
        virtual_solvent = np.array(df['Hansen coordinates'].loc[solvent_index[0]])
        for p in solvent_index[1:]:
            virtual_solvent += np.array(p)
        virtual_solvent = virtual_solvent/N
        figure['data'][1]['x'] = [virtual_solvent[0]]
        figure['data'][1]['y'] = [virtual_solvent[1]]
        figure['data'][1]['z'] = [virtual_solvent[2]]
        dD, dP, dH = [round(i,2) for i in virtual_solvent]
    return figure, dD, dP, dH

#@app.callback([Output('main-plot', 'figure')],
#              [Input('update-plot', 'n_clicks')],
#              [State('main-plot', 'figure')])
#def update_plot_, figure, )


if __name__ == '__main__':
    app.run_server(debug=True, port = 8051)