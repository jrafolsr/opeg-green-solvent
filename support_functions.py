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


df2 = read_excel('solventSelectionTool_table.xlsx', sheet_name = 1, header = 0, usecols=(0,1))
df2.set_index('Statements', inplace=True, drop=True)


def solvents_trace(df, filter_solvent = None):
    """Sets the data for the main trace in the green-solvent program"""
    if filter_solvent is None:
        fdf = df
    else:
       fdf = df[filter_solvent]
       
    x = fdf['dD - Dispersion']
    y = fdf['dP - Polarity']
    z = fdf['dH - Hydrogen bonding']
    if fdf['Ra'].isnull().any():
        costumdata = np.vstack([df['Melting Point (°C)'], df['Boiling Point (°C)'], -1*np.ones(df['Ra'].shape)]).T
#        size = 6
    else:
        costumdata = fdf[['Melting Point (°C)', 'Boiling Point (°C)', 'Ra']]
#        s = fdf['Ra']- fdf['Ra'].nsmallest(2)[-1]
#        s [s< 0] = 0
#        size = 16*np.exp(-0.5*s/s.max())
    size = 2*np.sqrt(3) * 3**(fdf['Composite score']/6).values
    size[np.isnan(size)] = 6
    size[fdf['Composite score'] < 3] = 6
    size[fdf['Composite score'] > 9] = 18
#    print(size)
#    size = 6
    trace = go.Scatter3d(x = x, y = y, z = z,customdata = costumdata, mode='markers', marker=dict( color = fdf['Composite score'],\
                                                            colorscale = 'RdYlGn',\
                                                            opacity = 1,
                                                            showscale = True,
                                                            cmin = 3,
                                                            cmid = 6,
                                                            cmax = 9,
                                                            colorbar = {'title' : 'Composite<br>score',\
                                                                        "thickness": 20, "len": 0.66, "x": 0.9, "y": 0.5}
                                                            ),\
                        marker_size = size,  marker_line_width = .25,marker_line_color= 'black',\
                        hovertemplate = '<b>%{text}</b><br>' +\
                                         '%{hovertext}<br>' +\
                                         'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f} <extra>Ra = %{customdata[2]:.1f}<br>mp  = %{customdata[0]:.0f} °C<br>bp  = %{customdata[1]:.0f} °C</extra>',
                        text = fdf['Solvent Name'],\
                        hovertext = [f'Score  = {value:.2f}' for value in fdf['Composite score']])

    return trace




def update_Ra(hansen_coordinates, reference = [None] * 3):
    """Calculates the Hansen parameter as Ra**2 = 4(dD - dD_0)**2 + (dP - dP_0)**2 + (dH - dH_0)**2.
        - coordinates: a Dataframe the three Hansen coordinates columns
        - reference: 3-element vector to which to calculate the distance"""
    for value in reference:
        if value == None:
            return np.nan
    distance = (hansen_coordinates - reference)**2
    Ra = 4*distance['dD - Dispersion'] + distance['dP - Polarity']+ distance['dH - Hydrogen bonding']
    return np.sqrt(Ra).round(2)

def create_report(data = None):
    if data is None:
        text = [html.H3('Solvent Information'),
                html.P('CAS: xx-xx-xxx', title = 'The CAS universally identifies the solvent'),
                html.P('Hansen coordinates: dD = x, dP = x, dH = x', title = 'The HSP define bla bla...'),
                html.P('Melting Point: x °C \t \t Boiling point:  x °C', title = 'Information about the melting a boiling points of the solvent'),
                html.P(html.B('GSK green solvent selection scores')),
                html.P("GSK score: x, User's adapted score: x", title = 'The higher the "greener" the solvent is'),
                html.P('Some info about the scores that are given for each solvent'),
                html.B('Globally harmonized System of Classification and Labelling of Chemical'),
                html.P('Some info about the classification and labelling of the solvents'),
                ]
        return text
    else:
        # Indices string
        scores = ''
        for label in data.index[8:18]:
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
                html.P('CAS: {}'.format(data['CAS Number'])),
                html.P('Hansen coordinates: dD = {:.1f}, dP = {:.1f}, dH = {:.1f}'.format(*data[HANSEN_COORDINATES])),
                html.P('Melting Point: {:.0f}°C \t \t Boiling point:  {:.0f}°C'.format(data['Melting Point (°C)'], data['Boiling Point (°C)'])),
                html.P(html.B('GSK green solvent selection scores')),
                html.P("GSK score: {:.1f}, User's adapted score: {:.1f}".format(data['GSK score'],data['Composite score'])),
                html.P(scores),
                html.B('Globally harmonized System of Classification and Labelling of Chemical'),
                html.P(hazard_html),
                html.P(precaution_html)]
        return text
    
    
def filter_by_hazard(hazards_to_remove, data_hazards):
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
    k = 0
    gmean = 1
    for element in scores:
        if len(element):
            gmean *= ((df[element]).prod(axis =1, skipna = False)).pow(1/len(element))
            k += 1
    if k > 0:
        gmean = np.power(gmean,1/k).round(2)
    else:
        gmean = np.nan
    return gmean

def f2s(x):
    if x is None:
        x = 0.0
    return f'{x: 3.1f}'