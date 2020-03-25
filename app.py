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
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# Load the data in a dataframe structure
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 0, header = 2)
df2 = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 1, header = 0, usecols=(0,1))
# Drop first row as it is empty
df = df[1:]
# Add extra columns with calculated parameters
df['Hansen coordinates']= [np.array([df['dD - Dispersion'].iloc[i], df['dP - Polarity'].iloc[i], df['dH - Hydrogen bonding'].iloc[i]]) for i in range(df.shape[0])]
list_GSK_scores = df.columns.values[7:18]
df['Waste'] = (df['Incineration']*df['Recycling']*df['Biotreatment']*df['VOC Emissions'])**0.25
df['Environment']  =(df['Aquatic Impact']*df['Air Impact'])**0.5
df['Health'] = (df['Health Hazard']*df['Exposure Potential'])**0.5
df['Safety'] = (df['Flammability and Explosion']*df['Reactivity and Stability'])**0.25
df['Greenness'] = round((df['Waste']*df['Environment']*df['Health']*df['Safety'])**0.25,2)
df['Ra'] = np.nan


def update_Ra(coordinates, reference):
    """Calculates the Hansen parameter as Ra**2 = 4(dD - dD_0)**2 + (dP - dP_0)**2 + (dH - dH_0)**2.
        - coordinates: a Dataframe series cointaining a 3-elements array
        - reference: 3-element vector to which to calculate the distance"""
    for value in reference:
        if value == None:
            return np.nan
    distance = coordinates - reference
    Ra = [np.round(np.sqrt(4*d[0]**2 + d[1]**2 + d[2]**2),2) for d in distance]
    return Ra

def create_report(data = df.loc[25]):
    # Incides string
    scores = ''
    for label in data.index[8:18]:
        scores += '{:s}: {:.1f}; '.format(label, data.loc[label])
        
    # Hazard string
    hazard_labels = data['Hazard Labels'].split(' ')
    hazard_html = []
    for hazard in hazard_labels:
        text_hazard = df2.Fulltext[df2['Statements'] == hazard].values[0]
        hazard_html.append('{:s}: {:s}'.format(hazard, text_hazard))
        hazard_html.append(html.Br())
        
    # Precaution string
    precaution_labels = data['Precautionary Labels'].split(' ')
    precaution_html = []
    for precaution in precaution_labels:
        splitted_precaution = precaution.split('+')
        text = ''
        for s_precaution in splitted_precaution:
            text_precaution = df2.Fulltext[df2['Statements'] == s_precaution].values[0]
            text += text_precaution
        precaution_html.append('{:s}: {:s}'.format(precaution, text))
        precaution_html.append(html.Br())


    text = [html.H2('Solvent name: {}'.format(data['Solvent Name'])),
            html.P('CAS: {}'.format(data['CAS Number'])),
            html.P('Hansen coordinates: dD = {:.1f}, dP = {:.1f}, dH = {:.1f}'.format(*data['Hansen coordinates'])),
            html.P('Melting Point: {:.0f}°C \t \t Boiling point:  {:.0f}°C'.format(data['Melting Point (°C)'], data['Boiling Point (°C)'])),
            html.B('GSK green solvent selection scores'),
            html.P('Overall score: {:.1f}'.format(data['Greenness'])),
            html.P(scores),
            html.B('Globally harmonized System of Classification and Labelling of Chemical'),
            html.P(hazard_html),
            html.P(precaution_html)]
    return text

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
                        debounce = True,
                        style = {'width' : '30%'},
                ),
                    dcc.Input(
                        id = "dP-input",
                        type = 'number',
                        placeholder="dP value",
                        debounce = True,
                        style = {'width' : '30%'},
                    ),
                    dcc.Input(
                        id = "dH-input",
                        type = 'number',
                        placeholder="dH value",
                        debounce = True,
                        style = {'width' : '30%'},
                    )
                ]),  
                dcc.Dropdown(
                    id='solvent-list',
                    options=[{'label': name, 'value': i} for name,i in zip(df['Solvent Name'],df.index)],
                    value = [],
                    placeholder = "Choose a solvent...",
                    multi = True
                     ),                
                html.Button('Find virtual solvent', id='virtual-solvent')
                ],

            style = {'width' : '40%', 'display': 'inline-block', 'vertical-align':'top'}
            )            
            ]
    ),
        html.Div( [
            dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df.columns[[-1, -2,0]]],
            data = df[['Solvent Name', 'Greenness', 'Ra']].to_dict('records'),
#            fixed_rows = { 'headers': True, 'data': 0},
            style_as_list_view = True,
            row_selectable='single',
            selected_rows = [],
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
            ),
        ], style =  {'width' : '60%'},),
        html.Div(id = 'report', children = create_report(), 
             style = {'width':'40%','display': 'inline-block', 'vertical-align':'top'}
             )
])



@app.callback([Output('main-plot', 'figure'),
               Output('table', 'data')],
              [Input('virtual-solvent', 'n_clicks')],
              [State('main-plot', 'figure'),
               State('dD-input', 'value'),
               State('dP-input', 'value'),
               State('dH-input', 'value')])
def display_virtual_solvent(_, figure, dD, dP, dH):
#    print(dD, dP, dH)
    df['Ra'] = update_Ra(df['Hansen coordinates'], [dD,dP,dH])
    figure['data'][1]['x'] = [dD] if dD != None else [np.nan]
    figure['data'][1]['y'] = [dP] if dP != None else [np.nan]
    figure['data'][1]['z'] = [dH] if dH != None else [np.nan]
    data = (df[['Solvent Name', 'Greenness', 'Ra']]).sort_values('Ra').to_dict('records')
    return figure, data

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
    return  dD, dP, dH

@app.callback(Output('report', 'children'),
             [Input('table','selected_rows')])
def update_report(selected_row):
    if selected_row == []:
        return ''
    else:
        return create_report(df.iloc[selected_row[0]])



if __name__ == '__main__':
    app.run_server(debug=True, port = 8051)