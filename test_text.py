# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 15:17:47 2020

@author: JOANRR
"""
import dash
import dash_core_components as dcc
from dash.dependencies import Input, Output, State



app = dash.Dash(__name__)

# -*- coding: utf-8 -*-
"""
Created on Wed Mar 25 13:02:13 2020

@author: JOANRR
"""

import dash
import dash_table
import dash_html_components as html
import pandas as pd
import numpy as np

# Load the data in a dataframe structure
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 0, header = 2)
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
df['Ra'] = 5.45

df2 = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 1, header = 0, usecols=(0,1))

app = dash.Dash(__name__)


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

app.layout = html.Div([ 
        html.Div([dash_table.DataTable(
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
            )], style = {'width':'60%', 'display': 'inline-block'}),
        html.Div(id = 'report', children = create_report(), 
             style = {'width':'40%','display': 'inline-block', 'vertical-align':'top'})
        ])

@app.callback(Output('report', 'children'),
             [Input('table','selected_rows')])
def update_report(selected_row):
    if selected_row == []:
        return ''
    else:
        return create_report(df.iloc[selected_row[0]])


if __name__ == '__main__':
    app.run_server(debug=True)