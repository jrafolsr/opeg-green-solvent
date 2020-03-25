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
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet = 0, header = 2)
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
app = dash.Dash(__name__)

app.layout = html.Div([            dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df.columns[[-1, -2,0]]],
            data = df[['Solvent Name', 'Greenness', 'Ra']].to_dict('records'),
#            fixed_rows = { 'headers': True, 'data': 0},
            style_as_list_view = True,
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
            )], style = {'width':'60%'})

if __name__ == '__main__':
    app.run_server(debug=True)