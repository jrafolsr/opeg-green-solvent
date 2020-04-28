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
from support_functions import update_Ra, create_report, solvents_trace, df2,filter_by_hazard, GSK_calculator, f2s, suggested_path, create_annotations

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
TEMPERATURE_RANGE = [df['Boiling Point (°C)'].min(axis = 0)-5, df['Boiling Point (°C)'].max(axis = 0)+5]
# Columns on the displayed table
TABLE_COLUMNS = {'Solvent': 'Solvent Name', 'Ra' : 'Ra', 'Composite score': 'Composite score',\
                 'mp (°C)': 'Melting Point (°C)', 'bp (°C)' : 'Boiling Point (°C)'}
N_SOLVENTS = df.shape[0]
##----------------- Adding new columns -----------------------------------
df['Ra'] = update_Ra(df[HANSEN_COORDINATES])
df['GSK score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY])  # This is the GSK score according to the paper
df['Composite score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY]) # This is the composite score, that the user can modify, initial eq. to GSK

#----------------CONFIGURING THE INITAL 3D PLOT--------------------------------
# traces is a list of traces objects. Each trace correspond to a set of data in our plot. We have 3 sets of data
# (1) solvents, (2) the virtual solute and (3) the highlighted solvents
traces = [solvents_trace(df,None),
        go.Scatter3d(x = [], y = [], z =[], mode='markers', marker=dict(color = 'black',
                                                        symbol = 'circle',\
                                                        opacity = 1),\
                                            marker_size=6,\
                                            text = ['Your solute'],\
                                            hovertemplate = '<b>%{text}</b><br><br>' +\
                                     'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f} <extra></extra>'),
        go.Scatter3d(x = [], y = [], z =[], mode='markers', marker=dict(
                                                                color = 'red',
                                                                size = 10,
                                                                symbol = 'circle-open',\
                                                                opacity=1.0),\
                        marker_line_color="red", marker_line_width = 4,\
                        hoverinfo = 'skip')]
axis_template = {
    "showbackground": True,
    "backgroundcolor": '#F0F0F0',
    "gridcolor": '#808080',
    "zerolinecolor": '#808080',
}

plot_layout = go.Layout(title = {'text': 'Hansen Space<br>dD = ' + f2s(0) + '  dP = ' + f2s(0) + '  dH = ' + f2s(0),\
                                 'y':0.9,'x':0.5, 'xanchor': 'center', 'yanchor': 'top',\
                                 'font' : {'size' : 20, 'family' :  'Arial', 'color' : 'rgb(50, 50, 50)'}},
                        font = {'size' : 11},
                        paper_bgcolor= '#F0F0F0',
                        plot_bgcolor = '#F0F0F0',
                        margin =  {"t": .25, "b": .25, "l": .25, "r": .25},
                        hoverlabel = {'bgcolor' : 'black', 'font' : {'color': 'white'}}, 
                        scene={"aspectmode": "cube",
#                               "aspectratio" : {'x' : 1, 'y' : 2, 'z' : 2},
                               "xaxis": {"title": 'Dispersion (MPa)<sup>1/2</sup>', **axis_template},
                               "yaxis": {"title": 'Polarity (MPa)<sup>1/2</sup>', **axis_template },
                               "zaxis": {"title":'Hydrogen bonding (MPa)<sup>1/2</sup>', **axis_template },
                               "camera": {"eye": {"x": 1.5, "y": 1.5, "z": 0.1}}
                               },
                        showlegend = False,
                        clickmode =  'event+select',
                        autosize = True)

# Some of the callbacks will not exist at the beginning of the page.... check on that.
app.config['suppress_callback_exceptions']=True


# Some text saved in variables
INTRO_TEXT = [html.Summary(html.B('HOW DOES IT WORK?')),\
              html.P(['This app is design to help you identify functional and environmentally green solvents. The likelihood to be functional is based on ',
              html.Span('Hansen solubility parameters (HSP)', title = 'Dispersion (dD), Polarity (dP) and Hydrogen bonding (dH)', className = 'hover-span'),', where a shorter distance ', html.Span('(Ra)', title = r'Ra = [4(dD2 - dD1)^2 + (dP2 - dP1)^2 + (dH2 - dH1)^2]^(1/2)', className = 'hover-span'),' in Hansen space correspond to a more similar solvent. The greenness score is based on the GlaxoSmithKline (GSK) solvent sustainability guide, where a higher composite score is a greener alternative.']),\
              html.P(['(1) Use the right panel to either enter the ', html.B('HSP coordinates'),' of your solute directly, or estimate it from known functional ', html.B('solvent(s)'),' using the dropdown menu. Then click ', html.B('UPDATE.')]),\
              html.P(['(2) The position of your solute is shown in the ',html.B('HANSEN SPACE.'), ' Use the graph to explore neighboring solvents. Find more information about certain solvent by clicking on it, or selecting it from the table. The color and size guides you in a sustainable direction.']),
              html.P(['(3) The ', html.B('SELECTION TABLE'),' ranks the solvents based on the distance Ra to your solute, and specifies the composite score and other useful information solvents.'])]

REFERENCES_TEXT = ['Hansen solubility ', html.A('theory and parameters', href = 'https://www.stevenabbott.co.uk/practical-solubility/hsp-basics.php', target='_blank'), ' (Last accessed: 2018-10-22)', \
                     html.Br(),\
                     'GSK green solvent selection data from ',html.A('[1]', href = 'https://pubs.rsc.org/en/content/articlelanding/2016/gc/c6gc00611f', target='_blank'),\
                     ' and ', html.A('[2]', href = 'https://pubs.rsc.org/en/content/articlelanding/2011/gc/c0gc00918k', target='_blank'), html.Br(),\
                     'GHS statements from ', html.A('PubChem', href = 'https://pubchem.ncbi.nlm.nih.gov/', target='_blank'), ' (Last accessed: 2019-05-30)',\
                     ' and ', html.A('European Chemicals Agency (ECHA) C&L Inventory', href = 'https://echa.europa.eu/information-on-chemicals/cl-inventory-database/', target='_blank'), ' (Last accessed: 2019-05-30)', html.Br(),\
                     'Find the publication on ', html.A('The Amazing Journal', href = 'https://www.umu.se/globalassets/personalbilder/petter-lundberg/Profilbild.jpg?w=185', target='_blank'), html.Br(),
                     'Made by the ', html.A('Organic Photonics and Electronics group (OPEG)', href = 'http://www.opeg-umu.se/', target='_blank')] 


app.layout = html.Div([html.Div(className = 'row',  children = [
        #----------- First column, where the info goes ------------------------
        html.Div(className = 'column left', children = [
            html.H4('Selection of Functional Green Solvent'),
            html.Div(id = 'intro_div', className = 'big-container', children = 
                    html.Details(INTRO_TEXT, title = 'Click the triangle to open or close the panel', open = 'open')
                    ),
            html.Div(id = 'report', className = 'big-container', children = create_report(),
             style = {'overflow-y': 'auto', 'height' : '400px'}),
             html.Div([html.Div(html.H6('Sources'), style = {'width' : '25%','display':'inline-block','vertical-align': 'top'}),html.Div(REFERENCES_TEXT, style = {'width' : '70%', 'display':'inline-block','vertical-align': 'top'})], className = 'big-container', style = {'font-size' : 'xx-small'})
        ]),
        #----------- Second column, where the plot and table go----------------
        html.Div(className = 'column middle', children = [                     
          html.Div([
                dcc.Graph(id='main-plot', 
                      figure= { "data": traces,
                                "layout": plot_layout,
                                },
                      config={"editable": False},
                      style = {'width' : '100%'}
                      )
            ]),
            html.Div(id = 'table-div', children = [
                html.H5('Selection table', style = {'text-align' : 'center'}),
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
                        'textAlign': 'left','width': '20px','maxWidth': '100px'
                    }],
                    style_table={'overflowY': 'scroll',
                                 'overflowX': 'auto',
                                 'height' : '300px',
                                 'maxHeight': '400px',
                                 'minWidth': '300px',
                                 'width': '100%',
                                 'maxWidth': '800px',
                                 'border': 'thin lightgrey solid'},
                    style_cell={'minWidth': '0px', 'width': '20px','maxWidth': '75px', 'text-align':'center','textOverflow': 'ellipsis'
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
        #---------- Third column, where the plot and filter options go-----------
        html.Div(className = 'column right', children = [
                        html.Div(id = 'HSP-values', children = [None, None, None], hidden = True),
                        html.Div(id = 'buttons-div', className  = 'buttons-container', children = [
                            html.Button('UPDATE',
                                        id='button-update',
                                        title = 'Click here to update the plot and table',
                                        n_clicks = 0,
                                        n_clicks_timestamp = -1),
                            html.Button('RESET',
                                        id='button-reset',
                                        title = 'Click here to Reset the app',
                                        n_clicks = 0,
                                        n_clicks_timestamp = -1),                                        
                           ]),                     
                        html.Div(id = 'hansen-div', className = 'main-inputs-container',  children = [
                            html.P(['Type the ', html.Span('HSP', title = 'Hansen solubility parameters', className = 'hover-span'),' coordinates of your solute...']),
                                html.Div(style = {'width': 'max-content','text-align' : 'right', 'margin-left': 'auto',
  'margin-right': 'auto'}, children = [
                                html.P(['Dispersion:  ',
                                    dcc.Input(
                                        id = "dD-input",
                                        name = 'dD',
                                        type = 'number',
                                        placeholder="dD",
                                        style = {'width' : '80px'},
                                    ), ' (MPa)', html.Sup('1/2')]),
            
                                html.P(['Polarization: ',
                                    dcc.Input(
                                        id = "dP-input",
                                        type = 'number',
                                        placeholder="dP",
                                        style = {'width' : '80px'},
                                    ), ' (MPa)', html.Sup('1/2')]),
                                html.P(['H bonding:  ',
                                    dcc.Input(
                                        id = "dH-input",
                                        type = 'number',
                                        placeholder="dH",
                                        style = {'width' : '80px'},
                                    ), ' (MPa)', html.Sup('1/2')
                                ])
                            ])
                        ]),
                        html.Div(id = 'solvent-list-div', className = 'main-inputs-container', children = [
                            html.P('...or alternatively, select from the list the known functional solvent(s) of your solute:',\
                                   title = 'Will be marked with red circles in the plot'),
                            dcc.Dropdown(
                                id='solvent-list',
                                options=[{'label': name, 'value': i} for name,i in zip(df['Solvent Name'],df.index)],
                                value = [],
                                placeholder = "Choose a solvent...",
                                multi = True,
                            )] 
                       ),
                        html.Div(['The solvents in the ', html.B('SELECTION TABLE'), ' are ranked with increasing distance (Ra) to the defined solute (black circle). For a functional and sustainable solvent, ',html.Em(['"the closer and ', html.B('the greener'), ' the better".']),\
                                  html.P('You can also refine the solvent selection by applying the following filters:')],
                                         style = {'font-size' : 'small', 'margin-bottom' : '10px'}),
                        html.Div(id = 'filters-div', children = [
                            html.Details(className = 'main-inputs-container',  title = 'Suggested route', children = [
                                html.Summary(html.B(['Suggested path to green paradise'])),  
                                html.Div(id = 'path-div',className = 'filters-type', children = [
                                    html.P(f'Proposed path to find the greenest functional solvent :'),
                                    html.Button('SHOW PATH',
                                                id='button-path',
                                                title = 'Click here to view the suggested route',
                                                n_clicks = 0,
                                                n_clicks_timestamp = -1,
                                                style = {'width' : '200px'}),
                                    html.P('', id = 'error-path')
                                ],  style = {'width' : '100%', 'text-align' : 'center'}),
                            ]),
                            html.Details(className = 'main-inputs-container',  title = 'Show only the N closest candidates', children = [
                                html.Summary(html.B(['Show less solvents'])),  
                                html.Div(id = 'distance-div',className = 'filters-type', children = [
                                    html.P(f'Shows only the {N_SOLVENTS:d}-first closest solvents:', id = 'distance-filter-text'),
                                    dcc.Slider(
                                        id = 'distance-filter',
                                        min = 5,
                                        max = N_SOLVENTS,
                                        value = N_SOLVENTS,
                                        step = None,
                                        marks = {5: '5', 10 : '10', 25: '25', 50: '50', 100 : '100', N_SOLVENTS : 'all'}
                                        )
                                ],  style = {'width' : '100%', 'text-align' : 'center'}),
                            ]),
                            html.Details(className = 'main-inputs-container', title = 'Filter out the "less" green solvents', children = [
                                html.Summary(html.B(['Filter by ',\
                                                     html.Span('composite score', title = 'G = (Waste x Environemt x Health x Safety)^(1/4)', className = 'hover-span'),\
                                                     ' value'])),  
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
                               html.Summary(html.B('Exclude solvents by hazard labels')),
                               html.Div(id = 'div-hazard-list',className = 'filters-type', children = [
                                    html.P('Remove solvents with the following hazard labels:'),
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
                                html.Summary(html.B('Filter by boiling point range')),
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
                            ]),                                    
                            html.Details(className = 'main-inputs-container', title = 'It will use only the selected categories to calculate the composite score', children = [
                               html.Summary(html.B('Define your own composite score')),                    
                                html.Div(id = 'checklist-div',className = 'filters-type',  children = [
                                    html.P('Uncheck the catergories to be excluded from the final composite score'),
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
                        ]),
                    ])
        ], style = {'width' : '100%'})
] )

#@app.callback(Output('button-update', 'n_clicks'),
#              [Input('button-reset', 'n_clicks')]
#        )
#def reset_all(n_clicks):
#    return 0


@app.callback(
    dash.dependencies.Output('output-temperature-slider', 'children'),
    [dash.dependencies.Input('temperatures-range-slider', 'value')])
def update_temperature_output(value):
    return 'You have solvents between bp of {}°C and {} °C'.format(*value)

@app.callback([Output('dD-input', 'value'),
               Output('dP-input', 'value'),
               Output('dH-input', 'value')],
            [Input('solvent-list', 'value')],
           [State('dD-input', 'value'),
           State('dP-input', 'value'),
           State('dH-input', 'value')])
def update_hansen_parameters_by_list(solvent_list, dD, dP, dH):   
    N = len(solvent_list)
    if N == 0:
        dD, dP, dH = None, None, None
    else: 
        dD, dP, dH = df[HANSEN_COORDINATES].loc[solvent_list].mean().round(2)
        
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
        if solvent_selected == 'Your solute':
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


@app.callback(Output('distance-filter-text', 'children'),
             [Input('distance-filter','value')])
def update_distance_filter(value):
    return f'Shows only the {value:d}-first closest solvents:'


@app.callback([Output('main-plot', 'figure'),
               Output('table', 'data'),
               Output('greenness-filter','value'),
               Output('distance-filter', 'value'),
               Output('solvent-list', 'value'),
               Output('hazard-list', 'value'),
               Output('checklist-waste', 'value'),
               Output('checklist-health', 'value'),
               Output('checklist-environment', 'value'),
               Output('checklist-safety', 'value'),
               Output('temperatures-range-slider', 'value'),
               Output('error-path', 'children')],
              [Input('button-update', 'n_clicks_timestamp'),
               Input('button-reset', 'n_clicks_timestamp'),
               Input('button-path', 'n_clicks_timestamp')],
              [State('table', 'sort_by'),
               State('main-plot', 'figure'),
               State('dD-input', 'value'),
               State('dP-input', 'value'),
               State('dH-input', 'value'),
               State('greenness-filter','value'),
               State('distance-filter', 'value'),               
               State('solvent-list', 'value'),
               State('hazard-list', 'value'),
               State('checklist-waste', 'value'),
               State('checklist-health', 'value'),
               State('checklist-environment', 'value'),
               State('checklist-safety', 'value'),
               State('temperatures-range-slider', 'value'),
               State('HSP-values', 'children')])
def display_virtual_solvent(update,reset,path, sort_by, figure, dD, dP, dH, greenness,ndistance, solvent_list, hazard_list, waste, health, environment, safety, Trange, HSP):
    # If the Reset button is click, reinitialize all the values
    if reset >=  update:
        sort_by, dD, dP, dH, greenness, ndistance, solvent_list, hazard_list, waste, health, environment, safety, Trange = \
        [], None, None, None, 0, N_SOLVENTS, [], [], WASTE, HEALTH, ENVIRONMENT, SAFETY, TEMPERATURE_RANGE
        
    # Change the title, which contains the current values for dP, dD and dH
    figure['layout']['title']['text'] = 'Hansen Space<br>dD = ' + f2s(dD) + '  dP = ' + f2s(dP) + '  dH = ' + f2s(dH)
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
            t, tt, ttt =  df[HANSEN_COORDINATES].loc[solvent]
            x.append(t), y.append(tt), z.append(ttt)
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
    # Creates the hazard filter
    hazard_filter = filter_by_hazard(hazard_list, df['Hazard Labels'])
    # Creates the boiling temperature filter based in the range slider
    temperature_filter = (df['Boiling Point (°C)'] > Trange[0]) & (df['Boiling Point (°C)'] < Trange[1])
    # AND product of allt he filters, only the all True will survive
    data_filter = greenness_filter & hazard_filter & temperature_filter
    
    # Send the data to plot with the filter and only the n-first values
    # OBS: needs some error managign in the cas of ndistance > the filtered data
    error_path = ''
    if update >= path or reset >= path:
        figure['data'][0] = solvents_trace(df[data_filter].sort_values('Ra')[:ndistance])
        # Updates based on the data excluded
        dff = df[list(TABLE_COLUMNS.values())][data_filter]
        figure['layout']['scene']['annotations'] = []
    else:
        # Is the distance defined?
        RA_EXIST =  not df['Ra'].isnull().all()
        if RA_EXIST:
            # Add here the PATH algorithm
            if len(solvent_list) == 1: solvent = df.loc[solvent_list[0]]
            else: solvent = None
            dfpath = suggested_path(df[data_filter], ref_solvent = solvent)
            figure['data'][0] = solvents_trace(dfpath, show_path = True)
            # Updates based on the data excluded
            dff = dfpath[list(TABLE_COLUMNS.values())]
            figure['layout']['scene']['annotations'] = create_annotations(dfpath)
            
        else:
            dff = df
            error_path = 'ERROR: You MUST define the solute coordinates.'
    # If the sorting button have been clicked, it sorts according to the action (ascending or descending)
    # if not, sorts by the ascending distance in the Hansen space, by default
    if len(sort_by):
        dfs = dff.sort_values(
            sort_by[0]['column_id'],
            ascending= sort_by[0]['direction'] == 'asc',
            inplace = False
        )
    else:
        # Default sorting applied
#        print('Default sorting applied') 
        dfs = dff.sort_values('Ra', ascending= True, inplace = False)
    
    dfs = dfs[:ndistance]
    
    return figure, dfs.to_dict('records'), greenness, ndistance, solvent_list, hazard_list, waste, health, environment, safety, Trange, error_path


# I need this lines to upload the images
@app.server.route('/static/<resource>')
def serve_static(resource):
    return flask.send_from_directory(STATIC_PATH, resource)

if __name__ == '__main__':
#    app.run_server(debug=True, port = 8051, host = '130.239.229.125') # wifi
    app.run_server(debug=True, port = 8051, host = '130.239.110.240') # LAN