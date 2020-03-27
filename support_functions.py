# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 11:47:57 2020

@author: JOANRR
"""
import numpy as np
import dash_html_components as html
from pandas import read_excel
import plotly.graph_objs as go

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
    trace = go.Scatter3d(x = x, y = y, z = z, mode='markers', marker=dict( color = fdf['Composite score'],\
                                                            colorscale = 'RdYlGn',\
                                                            opacity=0.8,\
                                                            showscale = True,
                                                            cmin = 3,
                                                            cmid = 6,
                                                            cmax = 9,
                                                            colorbar = {"thickness": 20, "len": 0.66, "x": 0.9, "y": 0.5}
                                                            ),\
                        marker_size=8,\
                        hovertemplate = '<b>%{text}</b><br>' +\
                                         '%{hovertext}<br>' +\
                                         'dD = %{x:.2f}<br>dP = %{y:.2f}<br>dH = %{z:.2f}',
                        text = fdf['Solvent Name'],\
                        hovertext = [f'GSK score  = {value:.2f}' for value in fdf['Composite score']])

    return trace




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

def create_report(data = None):
    if data is None:
        text = [html.H2('A Tool for Straightforward Selection of Functional Green Solvents for Printed Electronics'),
                html.Em('Christian Larsen, Petter Lundberg, Shi Tang,... Ludvig Edman'),
                html.P([html.A(['Link to the sutdy'], href = 'http://www.opeg-umu.se/')]),
                html.Details([html.Summary(html.B('Abstract')),
                html.P('The emerging field of printed electronics is directly dependent on the use of large volumes of printing and coating solvents, which frequently are deposited and evaporated within open spaces available to workers during the fabrication process. In this context, it is very unfortunate that many [T...] made freely available to colleagues and the public on the web site: ???')
                ])]
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
    
    
        text = [html.H2('{}'.format(data['Solvent Name'])),
                html.P('CAS: {}'.format(data['CAS Number'])),
                html.P('Hansen coordinates: dD = {:.1f}, dP = {:.1f}, dH = {:.1f}'.format(*data['Hansen coordinates'])),
                html.P('Melting Point: {:.0f}°C \t \t Boiling point:  {:.0f}°C'.format(data['Melting Point (°C)'], data['Boiling Point (°C)'])),
                html.B('GSK green solvent selection scores'),
                html.P('Overall score: {:.1f}'.format(data['Composite score'])),
                html.P(scores),
                html.B('Globally harmonized System of Classification and Labelling of Chemical'),
                html.Div([
                html.P(hazard_html),
                html.P(precaution_html)], style = {'height' : '200px', 'overflow-y': 'scroll'})]
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

def GSK_calculator2(df, scores):
    k = 0
    gmean = 1
    for element in scores:
        if len(element):
            gmean *= ((df[element]).prod(axis =1)).pow(1/len(element))
            k += 1
    return np.power(gmean,1/k).round(2)