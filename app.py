#import os
#import numpy as np
import dash
import dash_core_components as dcc
import dash_table
from dash_table.Format import Format
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import flask
from support_functions import update_Ra, create_report, solvents_trace, df2,filter_by_hazard, GSK_calculator, f2s, suggested_path, create_annotations

# Folder where I can find the local resources, such as images
STATIC_PATH = 'static'

# Main stylesheet, so far, fetching it from an open source webpage
#external_stylesheets = []
# I start the dash object instance, saved in the variable app
app = dash.Dash(__name__)

server = app.server # No sure that this line is necessary, not sure what it does...

#------------------- LOADING THE DATA -------------------------------------------
# Loading the Excel file with all the solvents and its properties (first sheet)
# The data is loaded in a DataFrame structure (see pandas library)
df = pd.read_excel('solventSelectionTool_table.xlsx', sheet_name = 0, header = 2)
df['index'] = df['Solvent Name']
df.set_index('index', inplace=True, drop=True) # The column name is set as a index, not sure is the wisest option
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
# Columns on the displayed table (WEIRD WAY, BUT RE-ADAPTED FROM BEFORE)
TABLE_COLUMNS = {'Solvent': 'Solvent Name', 'Ra' : 'Ra', 'G': 'Composite score',\
                 'bp (°C)' : 'Boiling Point (°C)'}
TYPE_COLUMNS = ['text', 'numeric', 'numeric', 'numeric']
FORMAT_COLUMNS = [Format(), Format(precision = 2), Format(precision = 2), Format(precision = 3)]
# Prepare the list to feed the table, adding the format two the desired precision
TABLE_DCC = [{"type" : coltype, "name": key, "id": value, 'format' : colformat} for key, value, coltype, colformat in zip(TABLE_COLUMNS.keys(), TABLE_COLUMNS.values(), TYPE_COLUMNS, FORMAT_COLUMNS)]





N_SOLVENTS = df.shape[0]
##----------------- Adding new columns -----------------------------------
df['Ra'] = update_Ra(df[HANSEN_COORDINATES])
df['GSK score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY])  # This is the GSK score according to the paper
df['Composite score'] = GSK_calculator(df, [WASTE, HEALTH, ENVIRONMENT, SAFETY]) # This is the composite score, that the user can modify, initial eq. to GSK


#----------------CONFIGURING THE INITAL 3D PLOT--------------------------------
# traces is a list of traces objects. Each trace correspond to a set of data in our plot. We have 3 sets of data
# (1) solvents, (2) the virtual solute and (3) the highlighted solvents
traces = [solvents_trace(df),
        go.Scatter3d(x = [], y = [], z =[], mode='markers',
                    marker=dict(color = 'black',symbol = 'circle', opacity = 1, size = 6),\
                    text = ['Your solute'],\
                    hovertemplate = '<b>%{text}</b><br><br>' +\
                                    'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f} <extra></extra>'),
        go.Scatter3d(x = [], y = [], z =[], mode='markers',
                     marker=dict(color = 'red', size = 10, symbol = 'circle-open', opacity=1.0,\
                                 line = dict(color = 'red', width = 4)),\
                     hoverinfo = 'skip')]
# Defining axis template        
axis_template = dict(showbackground = True, backgroundcolor = '#F0F0F0', gridcolor = '#808080', zerolinecolor = '#808080')

plot_layout = go.Layout(title = dict(text = 'Hansen Space<br>dD = ' + f2s(0) + '  dP = ' + f2s(0) + '  dH = ' + f2s(0),\
                                     y = 0.9, x = 0.5, xanchor = 'center', yanchor = 'top',\
                                     font  = dict(size = 20, family = 'Arial', color = 'rgb(50, 50, 50)')),
                        font = {'size' : 11},
                        paper_bgcolor= '#F0F0F0',
                        plot_bgcolor = '#F0F0F0',
                        margin =  dict(t =  .25, b =  .25,l =  .25, r =  .25),
                        hoverlabel = dict(bgcolor =  'black', font = {'color': 'white'}), 
                        scene= dict(aspectmode = "cube",
#                               aspectratio = {'x' : 1, 'y' : 2, 'z' : 2},
                               xaxis = dict(title = 'Dispersion (MPa)<sup>1/2</sup>', **axis_template),
                               yaxis = dict(title =  'Polarity (MPa)<sup>1/2</sup>', **axis_template ),
                               zaxis = dict(title = 'Hydrogen bonding (MPa)<sup>1/2</sup>', **axis_template),
                               camera = {"eye": {"x": 1.5, "y": 1.5, "z": 0.1}}
                               ),
                        showlegend = False,
                        clickmode =  'event+select',
                        autosize = True)

# Some of the callbacks will not exist at the beginning of the page.... check on that.
app.config['suppress_callback_exceptions'] = True


# Some text saved in variables
INTRO_TEXT = [html.Summary(html.B('How does it work?')),\
              html.P(['This app helps you to identify functional and environmentally green solvents. The likelihood to be functional is based on ',
              html.Span('Hansen solubility parameters (HSP)', title = 'Dispersion (dD), Polarity (dP) and Hydrogen bonding (dH)', className = 'hover-span'),', where a shorter distance in Hansen space ',  html.Span(['(R', html.Sub('a'),')'], title = r'Ra = [4(dD2 - dD1)^2 + (dP2 - dP1)^2 + (dH2 - dH1)^2]^(1/2)', className = 'hover-span'), ' correspond to a more similar solvent. The '  ,\
              html.Span(' greenness or composite score (G)', title = 'G = (Waste x Environemt x Health x Safety)^(1/4)', className = 'hover-span'),\
              ' is based on the GlaxoSmithKline (GSK) solvent sustainability guide, where a higher G means a greener alternative.']),\
              html.P(['(1) Use the radiobuttons on the left panel to either estimate the ',\
                      html.B('HSP coordinates'), ' of your solute from known functional solvent(s) or to manually enter the values. Then click ', html.B('UPDATE.')]),\
              html.P(['(2) The solute is highlighted in the ', html.B('Hansen space.'), ' Use the mouse to explore neighboring solvents. Click on the solvent or select it from the table to find more information.']),
              html.P(['(3) The ', html.B('Selection table'),' ranks the solvents based on the distance R', html.Sub('a'), ' to your solute, and specifies G.']),
              html.P(['(4) Click ', html.B('QUICK PATH'), ' to see a quick testing route towards a green and functional solvent.']),
              html.P(['(5) Use the ', html.B('Advanced options'), ' to refine your search. Click  ', html.B('UPDATE'), ' to apply your changes.'])]

REFERENCES_TEXT0 = ['Hansen solubility ', html.A('theory and parameters', href = 'https://www.stevenabbott.co.uk/practical-solubility/hsp-basics.php', target='_blank'), ' (Last accessed: 2018-10-22)', \
                     html.Br(),\
                     'GSK green solvent selection data from ',html.A('[1]', href = 'https://pubs.rsc.org/en/content/articlelanding/2016/gc/c6gc00611f', target='_blank'),\
                     ' and ', html.A('[2]', href = 'https://pubs.rsc.org/en/content/articlelanding/2011/gc/c0gc00918k', target='_blank'), html.Br(),\
                     'GHS statements from ', html.A('PubChem', href = 'https://pubchem.ncbi.nlm.nih.gov/', target='_blank'), ' (Last accessed: 2019-05-30)',\
                     ' and ', html.A('European Chemicals Agency (ECHA) C&L Inventory', href = 'https://echa.europa.eu/information-on-chemicals/cl-inventory-database/', target='_blank'), ' (Last accessed: 2019-05-30)']
REFERENCES_TEXT1 = ['Find the publication ', html.A('here', href = 'https://onlinelibrary.wiley.com/journal/15214095', target='_blank'), html.Br(),
                     'Made by the ', html.A('Organic Photonics and Electronics Group (OPEG)', href = 'http://www.opeg-umu.se/', target='_blank')] 


app.layout = html.Div([html.Div(className = 'row header-container',  children = [
       html.Img(src = r'\static\dash-logo.png',\
                alt = 'plotly-logo',id = 'logo', ),
       html.H4('A Tool for the Selection of a Functional Green Solvent',
                         id = 'header-title'),
       html.A(html.Img(src = r'\static\opeg-logo.png',\
                alt = 'opeg-logo',\
                    title = 'Organic Electronics and Photonics Group',
                    id = 'opeg-logo'), href = 'http://www.opeg-umu.se/', target='_blank')          
       ]),
       html.Div(className = 'row main-content',  children = [
        #---------- First column where the input options go-----------
        html.Div(className = 'column left', children = [
                        html.Div(id = 'radiobutton-div', className ='container', children = [
                            dcc.RadioItems(
                                    id = 'radiobutton-route',
                                    options=[
                                        {'label': 'Known functional solvent(s) of your solute', 'value': 1},
                                        {'label': 'Known HSP of your solute', 'value': 0}
                                    ],
                                    value = 1,
                                    style = {'margin-bottom' : '10px'}),                              
                            html.Div(id = 'solvent-list-div', hidden = False, children = [
                                dcc.Dropdown(
                                    id='solvent-list',
                                    options=[{'label': name, 'value': i} for name,i in zip(df['Solvent Name'],df.index)],
                                    value = [],
                                    placeholder = "Choose a solvent...",
                                    multi = True,
                                )] 
                           ),
                            html.Div(id = 'hansen-div', hidden = True, children = [
                                    html.Div(style = {'width': 'max-content','text-align' : 'right', 'margin': '0 auto'},\
                                             children = [
                                    html.P(['Dispersion:  ',
                                        dcc.Input(
                                            id = "dD-input",
                                            name = 'dD',
                                            type = 'number',
                                            placeholder="dD",
                                            style = {'width' : '80px'},
                                        ), ' (MPa)', html.Sup('1/2')]),
                
                                    html.P(['Polarity: ',
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
                        ]),
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
                                        n_clicks_timestamp = -2),
                            html.Button('QUICK PATH',
                                                id='button-path',
                                                title = 'Click to view a quick path to a green solvent',
                                                n_clicks = 0,
                                                n_clicks_timestamp = -1),
                            html.P('', id = 'error-path')                                        
                           ]),          

                        html.Div(id = 'filters-table-div', children = [
                            html.Details(id = 'filters-details', className = 'container',\
                                title = 'Advanced options for solvent filtering', children = [
                                html.Summary(html.B('Advanced options')),
                                html.Div( children = [
                                html.Div(id = 'distance-div',className = 'filters-type', children = [                                    
                                html.P(f'Show the {N_SOLVENTS:d}-first closest solvents:', id = 'distance-filter-text'),  

                                    dcc.Slider(
                                        id = 'distance-filter',
                                        min = 5,
                                        max = N_SOLVENTS,
                                        value = N_SOLVENTS,
                                        step = None,
                                        marks = {5: '5', 10 : '10', 25: '25', 50: '50', 100 : '100', N_SOLVENTS : 'all'}
                                        )
                                ]),
                                html.Div(id = 'greenness-div',className = 'filters-type', children = [
                                html.P(['Show solvents with G',\
                                        html.Span(id = 'greenness-indicator', children = ' > 0')]),  

                                    dcc.Slider(
                                        id = 'greenness-filter',
                                        min = 0,
                                        max = 8,
                                        value = 0,
                                        step = 1,
                                        marks = dict((i, str(i)) for i in range(0,9,2))
                                        )
                                ]),
                               html.Div(id = 'div-hazard-list',className = 'filters-type', children = [
                               html.P('Exclude solvents by hazard label'),
                                    dcc.Dropdown(
                                        id = 'hazard-list',
                                        options=[{'label': label + f': {text}', 'value': label} for text, label in zip(df2['Fulltext'][2:48],df2.index[2:48])],
                                        value = [],
                                        placeholder = "Hazards to exclude...",
                                        multi = True,
                                        style = {'text-align' : 'left'}),
                                ]),
                               html.Div(id = 'div-temperature-range',className = 'filters-type', children = [
                                    html.P(['Show solvents with the boiling point within ', html.Span(id='output-temperature-slider')]),
                                    dcc.RangeSlider(
                                        id='temperatures-range-slider',
                                        min=TEMPERATURE_RANGE[0],
                                        max=TEMPERATURE_RANGE[1],
                                        step = 5,
                                        value = TEMPERATURE_RANGE,
                                        marks={
                                            0: {'label': '0°C', 'style': {'color': '#77b0b1'}},
                                            100: {'label': '100°C', 'style': {'color': '#f50'}}}
                                    )]
                               ),
                                html.Div(id = 'checklist-div', className = 'filters-type',  children = [                                
                               html.P(html.Span('Define your own composite score (G)', className = 'hover-span', title = 'Uncheck the categories to be excluded from the G calculation')),
                               html.Div(style = {'text-align' : 'left'} , children = [
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
                                        ])
                                    ]),
                                ])
                            ]),
                        
            html.Div(id = 'table-div', children = [
                html.H5('Selection table', id = 'title-table', style = {'text-align' : 'center'}),
                dash_table.DataTable(
                    id='table',
                    columns = TABLE_DCC, # defined at the beginning
                    data = df[list(TABLE_COLUMNS.values())].to_dict('records'),
        #            fixed_rows = { 'headers': True, 'data': 0},
                    style_as_list_view = True,
                    row_selectable = 'single',
                    selected_rows = [],
                    sort_by = [],
                    sort_mode = 'single',
                    sort_action='native',
                    style_cell_conditional=[
                    {'if': {'column_id': 'Solvent Name'},
                        'textAlign': 'left','width': '20px','maxWidth': '100px'
                    }],
                    style_table= dict(#overflowY = 'scroll',
                                 # overflowX = 'auto',
                                 # height = '30vh',
                                 width = '100%',
                                 border = 'thin lightgrey solid'),
                    style_cell = {'minWidth': '0px', 'width': '20px','maxWidth': '75px', 'text-align':'center','textOverflow': 'ellipsis'},
                    )
                ])
            ])                          
                    ]),
        #----------- Second column, where the plot goes ----------------
        html.Div(className = 'column middle', children = [         
          html.Div(id = 'div-fig', children = [
                dcc.Graph(id='main-plot', 
                      figure= { "data": traces,
                                "layout": plot_layout,
                                },
                      config={"editable": False},
                      style = {'padding-bottom' : '10vh', 'max-width' : '42vw'}
                      )
                ]),
        ]),
        #----------- Third column, where the info goes (how it works + solvent info) ------------------------
        html.Div(id = 'column-right-div',className = 'column right', children = [
            html.Div(id = 'intro_div', className = 'container', children = 
                    html.Details(INTRO_TEXT,\
                                 id = 'div-instructions')
                    ),
            html.Div(id = 'report', className = 'container', children = create_report()),
        ]),

    ]),
    html.Div([html.Div('Sources', className = 'footer-col',\
                               style = {'font-size' : '3vmin','width' : 'min-content','max-width' : '20%'}),\
               html.Div(REFERENCES_TEXT0, className = 'footer-col', style = {'max-width' : '50%'}),\
               html.Div(REFERENCES_TEXT1, className = 'footer-col', style = {'max-width' : '20%'})],\
                  className = 'row sources-container')
])

# Updates the height o fthe info container based on the Details tabe is open or not
# @app.callback(Output('report', 'style'),
#               [Input('div-instructions', 'n_clicks')])
# def update_report_div_max_length(n):
# #    print(n)
#     if n is None or n % 2 == 1:
#         return  {'overflow-y': 'auto', 'height' : 'auto', 'max-height' : '30vh'}
#     else:
#         return  {'overflow-y': 'auto', 'height' : 'auto', 'max-height' : '80vh'}

# Updates the  information on the temperature filter
@app.callback(
    dash.dependencies.Output('output-temperature-slider', 'children'),
    [dash.dependencies.Input('temperatures-range-slider', 'value')])
def update_temperature_output(value):
    return '{}°C and {} °C'.format(*value)

# Selector of the method to choose your solute parameters, hides/shows the Input
@app.callback([Output('hansen-div', 'hidden'),
               Output('solvent-list-div', 'hidden')],
            [Input('radiobutton-route', 'value')])
def show_input_method(method):
    if method == 1:
        return True, False
    else:
        return False, True 

# Creates the report of the selected solvent
@app.callback(Output('report', 'children'),
             [Input('table','selected_rows')],
             [State('table','data'),
              State('table','columns')])
def update_report(selected_row, data, columns):
    if selected_row == []:
        # No solvent selected, emty report
        return create_report()
    else:
        # I first take the name of the selected Solvent (only one is allowed to be selected)
        n = selected_row[0]
        name_solvent = data[n]['Solvent Name'] # Selecet the name of the solvent from the key:" Solvent name"
        
        return create_report(df.loc[name_solvent])
    
# If a solvent is clicked on the graph, it updates selects the same solvent from the table (and therefore, creates a report)
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

# updates text from the greeness filter
@app.callback(Output('greenness-indicator', 'children'),
             [Input('greenness-filter','value')])
def update_GSK_filter(value):
    return f' > {value:d}'

# Updates text from the number-of-solvents filter
@app.callback(Output('distance-filter-text', 'children'),
             [Input('distance-filter','value')])
def update_distance_filter(value):
    return f'Show only the {value:d}-first closest solvents:'

# Main callaback, which gathers all the info and responds to it
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
               Output('radiobutton-route', 'value'),
               Output('dD-input', 'value'),
               Output('dP-input', 'value'),
               Output('dH-input', 'value'),
               Output('error-path', 'children'),
               Output('main-plot', 'clickData')],
              [Input('button-update', 'n_clicks_timestamp'),
               Input('button-reset', 'n_clicks_timestamp'),
               Input('button-path', 'n_clicks_timestamp')],
              [State('main-plot', 'figure'),
               State('radiobutton-route', 'value'),
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
               State('temperatures-range-slider', 'value')])
def main_plot(update,reset,path, figure,method, dD, dP, dH, greenness,ndistance, solvent_list, hazard_list, waste, health, environment, safety, Trange):
    # Determine which button has been clicked
    ctx = dash.callback_context

    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
#    print(button_id)
        
    # If the Reset button is click, reinitialize all the values
    if button_id == 'button-reset':
        dD, dP, dH, greenness, ndistance,method,solvent_list, hazard_list, waste, health, environment, safety, Trange = \
        None, None, None, 0, N_SOLVENTS, 1, [], [], WASTE, HEALTH, ENVIRONMENT, SAFETY, TEMPERATURE_RANGE
    
    # Choose the HSP based on the selected method by the user
    if method == 0:
        dDinput, dPinput, dHinput =  dD, dP, dH
       
        solvent_list = []
    else:
        dDinput, dPinput, dHinput =  None, None, None
        if len(solvent_list):
            dD, dP, dH = df[HANSEN_COORDINATES].loc[solvent_list].mean().round(2)
        else:
            dD, dP, dH = None, None, None
        
    
    # Change the title, which contains the current values for dP, dD and dH
    figure['layout']['title']['text'] = 'Hansen Space<br>dD = ' + f2s(dD) + '  dP = ' + f2s(dP) + '  dH = ' + f2s(dH)
    # Updatesthe Ra based on the new Hansen coordinates
    df['Ra'] = update_Ra(df[HANSEN_COORDINATES], [dD,dP,dH])
    #    Update the trace that shows the "Virtual solvent" in case it is not one from the list
    if (len(solvent_list) > 1) or  (method == 0):
        # Only if the method is by numerical Input or if th list is larger than 1
        x0 = [dD] if dD != None else []
        y0 = [dP] if dP != None else []
        z0 = [dH] if dH != None else []
    else:
        x0,y0,z0 =  [],[],[]
        
    figure['data'][1]['x'] = x0
    figure['data'][1]['y'] = y0
    figure['data'][1]['z'] = z0
    
    #    Update the trace that highlights the selected solvents"
    if method == 0:
        # No highling of the solvents, as it is manually input
        x, y, z = [],[],[]
    else:
        if len(solvent_list) >= 1:
            x, y, z = [],[],[]
            for solvent in solvent_list:
                t, tt, ttt =  df[HANSEN_COORDINATES].loc[solvent]
                x.append(t), y.append(tt), z.append(ttt)
        else:
            x, y, z = dD, dP, dH

    figure['data'][2]['x'] = x
    figure['data'][2]['y'] = y
    figure['data'][2]['z'] = z
    

#    print('This items have been excluded for the GSK_score values')
#    [print(item) for item in WASTE if item not in waste]
#    [print(item) for item in HEALTH if item not in health]
#    [print(item) for item in ENVIRONMENT if item not in environment]
#    [print(item) for item in SAFETY if item not in safety]
    #   Updates the composite score based on the labels the user selected    
    df['Composite score'] = GSK_calculator(df, [waste, health, environment, safety])
#    print('The GSK score has been updated')
  
    # Now, we creat ethe filters for the data to show   
    # 1. Create the greeness filter
    if greenness > 0:
        greenness_filter = df['Composite score'] > greenness
    else:
        greenness_filter = True
    # 2. Creates the hazard filter
    hazard_filter = filter_by_hazard(hazard_list, df['Hazard Labels'])
    
    # 3. Creates the boiling temperature filter based in the range slider
    temperature_filter = (df['Boiling Point (°C)'] > Trange[0]) & (df['Boiling Point (°C)'] < Trange[1])
    # 4. Creates the overall filter, an AND product of all he filters (only the all True will survive)
    data_filter = greenness_filter & hazard_filter & temperature_filter
    

    
    error_path = '' # Error message in the case that we haven't defined the Ra yet

    # If show path has not been cliecked, just plot the data with the applied filters
    if button_id == 'button-update' or button_id == 'button-reset':
        # Updating hte first trace (main one) by with the data filtered and only the n-first values
        # OBS: needs some error managing in the cas of ndistance > the filtered data        
        figure['data'][0] = solvents_trace(df[data_filter].sort_values('Ra')[:ndistance])
        # Updating the table based on the filtered data 
        dff = df[list(TABLE_COLUMNS.values())][data_filter]
        # No annotations
        figure['layout']['scene']['annotations'] = []
    else:
        # QUICK PATH has been clicked. Now, has the the distance been defined?
        RA_EXIST =  not df['Ra'].isnull().all() # Check if all the values are null (meanning Ra is not defined)
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
            # It has not been defined, so just plot the data based on the filters
            dff = df[data_filter][:ndistance]
            # Update the error message and show the user what she should do
            if path > -1: # Chekc if it is the first call, so it doens't show the error initially
                error_path = 'First, you MUST define the solute coordinates.'
                
                
    # Sorts by the ascending distance in the Hansen space, by default

    dfs = dff.sort_values('Ra', ascending= True, inplace = False)[:ndistance]
    
    
    return figure, dfs.to_dict('records'), greenness, ndistance, solvent_list, hazard_list, waste, health, environment, safety, Trange, method, dDinput, dPinput, dHinput, error_path, None


# I need this lines to upload the images
@app.server.route('/static/<resource>')
def serve_static(resource):
    return flask.send_from_directory(STATIC_PATH, resource)

if __name__ == '__main__':
#    app.run_server(debug=True, port = 8051, host = '130.239.229.125') # wifi
    app.run_server(debug=True, port = 8051, host = '130.239.110.240') # LAN