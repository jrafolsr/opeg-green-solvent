# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 11:47:57 2020

@author: JOANRR
"""
import numpy as np
import dash_html_components as html
from pandas import read_excel
import plotly.graph_objs as go

HANSEN_COORDINATES = ['dD - Dispersion','dP - Polarity','dH - Hydrogen bonding']
WASTE = ['Incineration','Recycling','Biotreatment','VOC Emissions'] # Columns' names defining the waste score
HEALTH = ['Health Hazard', 'Exposure Potential']                    # Columns' names defining the health score
ENVIRONMENT = ['Aquatic Impact', 'Air Impact']                      # Idem
SAFETY = ['Flammability and Explosion', 'Reactivity and Stability'] #Idem


df2 = read_excel('solventSelectionTool_table.xlsx', sheet_name = 1, header = 0, usecols=(0,1))
df2.set_index('Statements', inplace=True, drop=True)

def solvents_trace(df, show_path = False):
    """
    Creates the the main trace in the green-solvent program. It needs:
        - df: a DataFrame structure with the solvent info
        - show_path: if True, it will plot a line between the solvent from the df structure in the input order
    Returns:
        A trace, as a plotly object
    """
       
    x = df['dD - Dispersion']
    y = df['dP - Polarity']
    z = df['dH - Hydrogen bonding']
    
    hovertemplate = ['<b>{0:s}</b><br>Score = {1:.1f}<br>dD = {2:.1f}<br>dP = {3:.1f}<br>dH = {4:.1f} <extra>Ra = {5:.1f}<br>mp  = {6:.0f} °C<br>bp  = {7:.0f} °C<br>η  = {8:.2g} mPa∙s<br>𝜎  = {9:.2g} mN/m</extra>'.format(*data[['Solvent Name','Composite score','dD - Dispersion', 'dP - Polarity', 'dH - Hydrogen bonding' ,'Ra', 'Melting Point (°C)','Boiling Point (°C)', 'Viscosity (mPa.s)', 'Surface Tension (mN/m)']]) for index, data in df.iterrows()]  
                  
                                         
    # Some function that scales the size with the greeness score                                     
    size = 2*np.sqrt(3) * 3**(df['Composite score']/6).values
    size[np.isnan(size)] = 6
    size[df['Composite score'] < 3] = 6
    size[df['Composite score'] > 9] = 18
    
    # Just print lines when the SHOW PATH has been selected
    if show_path: mode = 'markers+lines'
    else: mode = 'markers'
    
    trace = go.Scatter3d(x = x, y = y, z = z,\
                         mode=mode,\
                         marker=dict(color = df['Composite score'],
                                    colorscale = 'RdYlGn',
                                    size = size,
                                    opacity = 1,
                                    showscale = True,
                                    cmin = 3,
                                    cmid = 6,
                                    cmax = 9,
                                    colorbar = dict(title = 'G',\
                                                thickness = 20, len = 0.66, x = 0.9, y = 0.5,\
                                                xanchor = 'center',  yanchor = 'middle'),
                                    line = dict(width = .25, color = 'rgb(50, 50, 50)')
                                    ),\
                        line = dict(color = 'rgb(50, 50, 50)', width = 3, dash = 'dot'),\
                        hovertemplate = hovertemplate,
                        text = df['Solvent Name'])

    return trace


def update_Ra(hansen_coordinates, reference = [None] * 3):
    """Calculates the Hansen parameter as Ra**2 = 4(dD - dD_0)**2 + (dP - dP_0)**2 + (dH - dH_0)**2.
        - hansen_coordinates: a DataFrame the three Hansen coordinates columns
        - reference: 3-element vector to which to calculate the distance"""
    for value in reference:
        if value == None:
            return np.nan
    distance = (hansen_coordinates - reference)**2
    Ra = 4*distance['dD - Dispersion'] + distance['dP - Polarity']+ distance['dH - Hydrogen bonding']
    return np.sqrt(Ra).round(2)

def create_report(data = None):
    if data is None:
        # text = [html.H3('Solvent Information'),
        #         html.P('CAS', title = 'The CAS universally identifies the solvent'),
        #         html.P('Hansen coordinates: dD, dP, dH', title = 'The HSP of the solvent'),
        #         html.P('Melting Point: nan, boiling point: nan', title = 'Information about the melting and boiling points of the solvent'),
        #         html.P('Viscosity:  nan,  surface tension: nan', title = 'Information about the viscosity and surface tension of the solvent'),
        #         html.P(html.B('GSK green solvent selection scores')),
        #         html.P("GSK score: nan, User's adapted score: nan", title = 'The higher the "greener" the solvent is'),
        #         html.P('Detailed information of the scores of the solvent'),
        #         html.B('Globally harmonized System of Classification and Labelling of Chemical'),
        #         html.P('Detailed information about the classification and labelling of the solvent'),
        #         ]
        text = [html.H3('Solvent Information'),
                html.P('Click on a solvent from the Hansen Space plot or from the Selection table to display relevant information about it.')
                ]
        return text
    else:
        # Indices string
        scores = ''
        for label in WASTE + ENVIRONMENT + HEALTH + SAFETY:
            scores += '{:s}: {:.1f}; '.format(label, data.loc[label])
            
        # Hazard string
        if data['Hazard Labels'] == 'No Data':
            hazard_labels = ['No Data']
        elif data['Hazard Labels'] == 'Not Hazardous':
            hazard_labels = ['Not Hazardous']
        else:
            hazard_labels = data['Hazard Labels'].split(' ')
        hazard_html = []
        for hazard in hazard_labels:
            text_hazard = df2.Fulltext[df2.index == hazard].values[0]
            hazard_html.append('{:s}: {:s}'.format(hazard, text_hazard))
            hazard_html.append(html.Br())
            
        # Precaution string
        if data['Precautionary Labels'] == 'No Data':
            precaution_labels = ['No Data']
        elif data['Hazard Labels'] == 'Not Hazardous':
            precaution_labels = ['Not Hazardous']
        else:
            precaution_labels = data['Precautionary Labels'].split(' ')
        precaution_html = []
        for precaution in precaution_labels:
            splitted_precaution = precaution.split('+')
            text = ''
            for s_precaution in splitted_precaution:
                text_precaution = df2.Fulltext[df2.index == s_precaution].values[0]
                text += text_precaution
            precaution_html.append('{:s}: {:s}'.format(precaution, text))
            precaution_html.append(html.Br())
    
    
        text = [html.Img(src = '\\static\\' + '{0:s}.svg'.format(data['CAS Number']),\
                                 alt='Chemical strcuture',\
                                 title = 'Chemical strcuture of {}'.format(data['Solvent Name']),\
                                style = {'width' : '250px','max-height' : '125px','float':'right', 'margin-left' : '10px'}),
                html.H3('{}'.format(data['Solvent Name'])),
                html.P(['CAS: ', html.A(data['CAS Number'], href = 'https://pubchem.ncbi.nlm.nih.gov/compound/{}'.format(data['CAS Number']), target='_blank')]),
                html.P('Hansen coordinates: dD = {:.1f}, dP = {:.1f}, dH = {:.1f}'.format(*data[HANSEN_COORDINATES])),
                html.P('Melting point*: {:.0f} °C. Boiling point*:  {:.0f} °C.'.format(data['Melting Point (°C)'], data['Boiling Point (°C)'])),
                html.P([
                    'Viscosity*: {:.2f} mPa∙s. Surface tension*:  {:.2f} mN/m.'.format(data['Viscosity (mPa.s)'], data['Surface Tension (mN/m)']), 
                    html.Br(),
                    html.Span(html.I(html.Small(['* The solvent properties are from various sources, between 20-40 °C where applicable.', html.Br(), ' DISCLAIMER: Do not use these values for citation purposes. '])))
                    ]),
                html.P(html.B('GSK green solvent selection scores')),

                html.P("GSK score: {:.1f}, User's adapted score: {:.1f}".format(data['GSK score'],data['Composite score'])),
                html.P(scores),
                html.B('Globally harmonized System of Classification and Labelling of Chemical'),
                html.P(hazard_html),
                html.P(precaution_html)]
        return text
    
    
def filter_by_hazard(hazards_to_remove, data_hazards):
    """ 
    Excludes the solvents with the input hazards:
        - hazards_to_remove: list with the labels of the hazards to be excluded
        - data_hazards: DataFrame column with the labels for each solvent
    """
        
    hazards_filter = np.ones((data_hazards.shape[0]), dtype = bool)
    
    for hazard in hazards_to_remove:
#        print(hazard)
        for i, solvent in enumerate(data_hazards):
#            print(solvent)
            for solvent_hazard in solvent.split(' '):
                if solvent_hazard == hazard:
                    hazards_filter[i] = False
                    break
    return hazards_filter

def GSK_calculator(df, scores):
    """ 
    Updates the compounds score based on the selected scores only
        - df: DataFrame structure that should contain at least all the scores columns (that are at least 10)
        - scores: list of scores category, each element containing a list with the subcategories names
    """
    k = 0
    gmean = 1
    for element in scores:
        if len(element):
            gmean *= ((df[element]).prod(axis =1, skipna = False)).pow(1/len(element))
            k += 1
    if k > 0:
        gmean = np.power(gmean,1/k).round(1)
    else:
        gmean = np.nan
    return gmean

def f2s(x):
    """
    Just a simple numebr to string function. Needs a number.
    """
    if x is None:
        x = 0.0
    return f'{x: 3.1f}'


def suggested_path(df, ref_solvent = None, min_score = 1.0):
    """
    This function contains the algorithm that provides the suggested path to 
    "greeness" paradise. Needs:
        - df : DataFrame structure with all the necessary columns ('Solvent Name', 'Composite score' and 'Ra' at least)
        - ref_solvent: if no reference solvent Series is passed, it will filter all the solvents with score < min_score
        - min_score: minimum score to consider if no ref_solvent is passed
    Returns:
        A DataFrame structure with the sorted solvents that will leads you to the greeness paradise
    """
    flag = True
    solvent_path = []
    if ref_solvent is None:
        ref_GSK = min_score # Minimm GSK score to start the path with
    else:
        ref_GSK = ref_solvent['Composite score']
        solvent_path.append(ref_solvent['Solvent Name'])
    
    while True:
        # Filter and sort out the less green
        df1 = (df[(df['Composite score'] > ref_GSK) & (df['Ra'] > 0.0)]).sort_values(by = 'Ra', inplace = False)
        flag = (len(df1) == 0)
        
        if flag: break
    
        ref_solvent = df1.iloc[0]
        solvent_path.append(ref_solvent['Solvent Name'])
        ref_GSK = ref_solvent['Composite score']

    
    # In case some labels are not found, this workaround must be done
    index = df.index.intersection(solvent_path) # Form the intersection of two index objects
    # Now I have the index, I can locate the values and sort them again by Ra
    return (df.loc[index]).sort_values(by = 'Ra', inplace = False)


def create_annotations(df):
    """
    This function creates the annotations on the positions [dD, dP, dH], enumerating 
    the solvent on the DataFrame structure:
        - df: DataFrame structure with the solvents to enumerature, sequentially
    Returns:
        A list of dictionaries with the annotations data
    """
    annotations = []
    k = 0
    for x,y,z in df[HANSEN_COORDINATES].values:
        annotations.append(
            dict(showarrow=False,
                    x = x,
                    y = y,
                    z = z,
                    text = f'{k+1}',
                    xshift = 10,
                    yshift = 10,
                    font=dict(color="black",size=14)
                ))
        k += 1
    return annotations

def number2scientific(x):
    """Translates a number to a scientific notation in html + dash"""
    s = f'{x:.2e}'
    base, exponent = s.split('e')
    base = float(base)
    exponent= int(exponent)
    return ['{:.1f}∙10'.format(float(base)), html.Sup('{}'.format(exponent))]
    