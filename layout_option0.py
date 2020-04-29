# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 09:47:01 2020

@author: JOANRR
"""

app.layout = html.Div([html.Div(className = 'row',  children = [
        html.Div(className = 'column left', children = [
                html.H3('Selection of Functional Green Solvent'),
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
            style = {}        
            ),
            html.Div(className = 'column right', children = [
                html.Div(id = 'buttons-div', className  = 'buttons-container', children = [
                    html.Button('UPDATE',
                                id='button-update',
                                title = 'Click here to update the plot and table',
                                n_clicks = 1,
                                style = {'background-color': '#C0C0C0', 'margin' : '10px'}),
                    html.Button('RESET',
                                id='button-reset',
                                title = 'Click here to Reset the app',
                                style = {'background-color': '#C0C0C0','margin' : '10px'}),
                   ]),                       
               html.Div(['Data taken from this ', html.A('reference', href = 'https://www.umu.se/globalassets/personalbilder/petter-lundberg/Profilbild.jpg?w=185'),\
                         html.Br(),
                         'You can find the paper in ',html.A('here', href = 'https://www.hitta.se/petter+lundberg/ume%C3%A5/person/~STlsww5X4'), html.Br(),
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
            style = {'columns': '600px 2'}
            )            
            ]
    )
] )