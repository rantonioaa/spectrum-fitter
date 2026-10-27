#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2026 R. Amaya-Almazán
"""
Created on Sun Apr 26 12:49:13 2020

@author: rantonioaa
"""

from astropy.io import fits
from astropy import units as u
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,\
                                   AutoMinorLocator)
from astropy.visualization import quantity_support
from specutils import Spectrum1D
from specutils.spectra import SpectralRegion
from specutils.fitting import fit_lines, fit_generic_continuum
from astropy.modeling.powerlaws import PowerLaw1D
from astropy.modeling import models, custom_model
from astropy.modeling.tabular import Tabular1D, Tabular2D
from astropy.modeling import Fittable1DModel, Parameter
import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# --- Widget keys: modern Streamlit requires a unique key per widget.
# The original code reused key=i / key=j / key=_wk() ... for every field of a
# component, which raises DuplicateWidgetID on Streamlit >= 1.14.
import itertools as _itertools
_widget_counter = _itertools.count()

def _wk():
    return 'w%d' % next(_widget_counter)

def _region(lo, hi):
    """SpectralRegion con validación: el mínimo debe ser menor que el máximo.

    Los number_input sin `value` arrancaban en 0.0 para ambos límites, así que
    SpectralRegion(0, 0) lanzaba 'Lower bound must be strictly less than the
    upper bound' en cuanto se marcaba una región.
    """
    if lo >= hi:
        st.error('Región inválida: el mínimo (' + str(lo) + ') debe ser menor '
                 'que el máximo (' + str(hi) + ').')
        st.stop()
    return SpectralRegion(lo*u.AA, hi*u.AA)

quantity_support()

st.markdown('# Programa para ajustar espectros')
            


#filename = 'b2_1633.fc.spec_090130rf.fits'

filetype = st.radio('Tipo de archivo:',('fits','txt'))

filename = st.file_uploader('Escoge el archivo:',type=filetype)

distintivo = st.text_input('Escribe un nombre distintivo para este ajuste')


# Sin archivo no hay nada que ajustar: se detiene aquí en lugar de lanzar
# una excepción (fits.open(None) / read_csv(None)) en el primer render.
if filename is None:
    st.info('Sube un espectro (fits o txt) para comenzar el ajuste.')
    st.stop()



if filetype == 'fits':
    
    st.warning('El programa está pensado para usarse con espectros del Observatorio Steward\
     en el marco de referencia del reposo y normalizado,\
     si es un espectro de otro observatorio el header del\
     fits debe tener los parámetros CD1_1, CRPIX1 y CRVAL1.')
    
    st.info('Si el navegador pregunta "Source file changed", selecciona "Always run"')
    
    hdul = fits.open(filename)
    
    hdr = hdul[0].header
    
    DL = hdr['CD1_1']
    l0 = (1 - hdr['CRPIX1'])*DL + hdr['CRVAL1']
    
    data = hdul[0].data
    
    L=[]
    L.append(l0)
    
    for i in range(len(data)-1):
        L.append(L[i]+DL)
    
    hdul.close()
    
    data = np.array(data).byteswap().newbyteorder()
    lamb = L*u.AA
    flux = data*u.Unit('erg cm-2 s-1 AA-1')
    

    
if filetype == 'txt':
    file = pd.read_csv(filename,names=['lamb','flux'],delim_whitespace=True)
    L = np.array(file.lamb)
    data = np.array(file.flux)
    lamb = L*u.AA
    flux = data*u.Unit('erg cm-2 s-1 AA-1')
    



#st.write(flux)


#st.write(int(np.floor(data[0])),int(np.ceil(data[0])),int(round(np.mean(data[0]))))
spec = Spectrum1D(spectral_axis=lamb,flux=flux)

#continuo

st.markdown('## Ajuste del continuo')

st.info('Selecciona los parámetros en la barra lateral.')

st.sidebar.markdown('# Modificador de parámetros iniciales')

st.sidebar.markdown('## Parámetros de la ley de potencias')



amplitude = st.sidebar.slider('Amplitud del modelo al punto de referencia:',\
                              np.floor(min(data)),np.ceil(max(data)),np.mean(data))

refpoint = st.sidebar.slider('Punto de referencia:',int(min(L)),int(max(L)),int(np.mean(L)))

alpha = st.sidebar.slider('Índice de la ley de potencias (alfa):',value=2.0,\
                          min_value=0.0,max_value=3.0,step=0.01)

st.write('Visualización del espectro con la Ley de Potencias con los parámetros seleccionados:')

powerlaw = PowerLaw1D(amplitude=amplitude,x_0=refpoint,alpha=alpha)

df = pd.DataFrame({'lambda':np.array(L),'flux':data,'powerlaw':np.array(powerlaw(lamb))})

fig = px.line(df,x='lambda',y=['flux','powerlaw'])

st.plotly_chart(fig)
 




ajuste_bool = st.radio('Desea que el programa encuentre el mejor ajuste tomando \
los parámetros iniciales dados:',('Sí','No, dejar parámetros iniciales seleccionados fijos'))

if ajuste_bool == 'Sí':
    
    metodo = st.selectbox('Método que desea utilizar:',('Método de ajuste',\
                                                        'Método de ajuste de continuo'))
    
    if metodo == 'Método de ajuste':
        
        st.info('Este método ajusta el continuo al espectro tal y como está')
        
        bounds_bool = st.radio('Desea incluir límites para los parámetros iniciales:'\
                               ,('Sí','No'))
        
        if bounds_bool == 'Sí':
            
        
            st.info('Selecciona los límites de los parámetros de la ley de potencias en \
                    la barra lateral')
            
            bounds_amp = st.sidebar.slider('Límites de la amplitud',min(data),max(data),\
                                           [min(data),\
                                            max(data)])
            
            bounds_refpoint = st.sidebar.slider('Límites del punto de referencia:',\
                                                int(min(L)),int(max(L)),\
                                                [int(min(L)),\
                                                   int(max(L))])
        
            bounds_alpha = st.sidebar.slider('Límites del índice de la ley de\
                                             potencias (alfa):',value=[1.0,2.0],\
                              min_value=0.0,max_value=3.0,step=0.01)

        st.info('Selecciona las que sean necesarias:')
    
        exc_reg = st.checkbox('Regiones del espectro para excluir en el ajuste del continuo')
        inc_reg = st.checkbox('Regiones del espectro para incluir en el ajuste del continuo')
        
        if exc_reg == True and inc_reg == True:
            ne = st.number_input('Cuántas regiones quieres excluir:',min_value=1,\
                                 max_value=5,step=1,value=1)
            ni = st.number_input('Cuántas regiones quieres incluir:',min_value=1,\
                                 max_value=5,step=1,value=1)
            
            spectralregions_ex = []
            spectralregions_in = []
    
    
            st.write('Selecciona el mínimo y máximo (Angstroms) de cada región a excluir:')
    
            for i in range(ne):
                st.write('Región',i+1)
    
                # Por defecto una banda estrecha: excluir todo el espectro deja el ajuste sin datos
                _rlo = st.number_input('Mínimo:', key=_wk(), value=float(min(L)))
                _rhi = st.number_input('Máximo:', key=_wk(), value=float(min(L) + 0.05*(max(L)-min(L))))
                spectralregions_ex.append(_region(_rlo, _rhi))
                
            st.write('Selecciona el mínimo y máximo (Angstroms) de cada región a incluir:')
    
            for j in range(ni):
                st.write('Región',j+1)
    
                _rlo = st.number_input('Mínimo:', key=_wk(), value=float(min(L)))
                _rhi = st.number_input('Máximo:', key=_wk(), value=float(max(L)))
                spectralregions_in.append(_region(_rlo, _rhi))
    
            if bounds_bool == 'No':
                
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha),\
                                          exclude_regions=spectralregions_ex,\
                                          window=spectralregions_in)
            if bounds_bool == 'Sí':
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha,\
                                          bounds={'amplitude':bounds_amp,\
                                                  'x_0':bounds_refpoint,\
                                                  'alpha':bounds_alpha}),\
                                          exclude_regions=spectralregions_ex,\
                                          window=spectralregions_in)
    
            cont = fitcont_model(lamb)
            cont_ = np.array(cont)
    
            #espectro sin continuo
    
            lamb_ = L*u.AA
            flux_ = (data-cont_)*u.Unit('erg cm-2 s-1 AA-1')
    
            spec_ = Spectrum1D(spectral_axis=lamb_,flux=flux_)
            
            
            
            fig_ = plt.figure()
            plt.plot(lamb_,flux_)
            plt.plot(lamb_,np.zeros_like(L),c='k',linestyle='--')
            plt.xlabel('Longitud de onda (Angstroms)')
            plt.ylabel('Flujo normalizado')
            
            df = pd.DataFrame({'Longitud de onda':L,'Flujo normalizado':data-cont_,'Cero':np.zeros_like(L)})
            
            
            
            fig = go.Figure([\
                go.Scatter(name='Espectro sin continuo',\
                           x = df['Longitud de onda'],\
                           y = df['Flujo normalizado'],\
                           mode = 'lines',\
                           showlegend=True),\
                go.Scatter(name='Linea en cero',\
                           x = df['Longitud de onda'],\
                           y = df['Cero'],\
                           line = dict(dash='dash',color='grey',width=1),\
                           showlegend=False)\
                                ])
            
            st.plotly_chart(fig)
    
    
        if exc_reg == True and inc_reg == False:
            ne = st.number_input('Cuántas regiones quieres excluir:',min_value=1,\
                                 max_value=5,step=1,value=1)
    
            st.write('Selecciona el mínimo y máximo (Angstroms) de cada región a excluir:')
    
            spectralregions_ex = []
    
            for i in range(ne):
                st.write('Región',i+1)
                # Por defecto una banda estrecha: excluir todo el espectro deja el ajuste sin datos
                _rlo = st.number_input('Mínimo:', key=_wk(), value=float(min(L)))
                _rhi = st.number_input('Máximo:', key=_wk(), value=float(min(L) + 0.05*(max(L)-min(L))))
                spectralregions_ex.append(_region(_rlo, _rhi))
    
            
            if bounds_bool == 'No':
                
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha),\
                                          exclude_regions=spectralregions_ex)
            if bounds_bool == 'Sí':
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha,\
                                          bounds={'amplitude':bounds_amp,\
                                                  'x_0':bounds_refpoint,\
                                                  'alpha':bounds_alpha}),\
                                          exclude_regions=spectralregions_ex)
                
                
            
    
            cont = fitcont_model(lamb)
            cont_ = np.array(cont)
    
            #espectro sin continuo
    
            lamb_ = L*u.AA
            flux_ = (data-cont_)*u.Unit('erg cm-2 s-1 AA-1')
    
            spec_ = Spectrum1D(spectral_axis=lamb_,flux=flux_)
            
            fig_ = plt.figure()
            plt.plot(lamb_,flux_)
            plt.plot(lamb_,np.zeros_like(L),c='k',linestyle='--')
            plt.xlabel('Longitud de onda (Angstroms)')
            plt.ylabel('Flujo normalizado')
            
            df = pd.DataFrame({'Longitud de onda':L,'Flujo normalizado':data-cont_,\
                               'Cero':np.zeros_like(L)})
            
            fig = go.Figure([\
                go.Scatter(name='Espectro sin continuo',\
                           x = df['Longitud de onda'],\
                           y = df['Flujo normalizado'],\
                           mode = 'lines',\
                           showlegend=True),\
                go.Scatter(name='Linea en cero',\
                           x = df['Longitud de onda'],\
                           y = df['Cero'],\
                           line = dict(dash='dash',color='grey',width=1),\
                           showlegend=False)\
                                ])
            
            
            st.plotly_chart(fig)
    
    
        if exc_reg == False and inc_reg == True:
            ni = st.number_input('Cuántas regiones quieres incluir:',min_value=1,\
                                 max_value=5,step=1,value=1)
    
            st.write('Selecciona el mínimo y máximo (Angstroms) de cada región a incluir:')
    
            spectralregions_in = []
    
            for i in range(ni):
                st.write('Región',i+1)
                
                _rlo = st.number_input('Mínimo:', key=_wk(), value=float(min(L)))
                _rhi = st.number_input('Máximo:', key=_wk(), value=float(max(L)))
                spectralregions_in.append(_region(_rlo, _rhi))
            
            if bounds_bool == 'No':
                
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha),\
                                          window=spectralregions_in)
            if bounds_bool == 'Sí':
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha,\
                                          bounds={'amplitude':bounds_amp,\
                                                  'x_0':bounds_refpoint,\
                                                  'alpha':bounds_alpha}),\
                                          window=spectralregions_in)    
            
            
    
            cont = fitcont_model(lamb)
            cont_ = np.array(cont)
    
            #espectro sin continuo
    
            lamb_ = L*u.AA
            flux_ = (data-cont_)*u.Unit('erg cm-2 s-1 AA-1')
    
            spec_ = Spectrum1D(spectral_axis=lamb_,flux=flux_)
            
            fig_ = plt.figure()
            plt.plot(lamb_,flux_)
            plt.plot(lamb_,np.zeros_like(L),c='k',linestyle='--')
            plt.xlabel('Longitud de onda (Angstroms)')
            plt.ylabel('Flujo normalizado')
            
            df = pd.DataFrame({'Longitud de onda':L,'Flujo normalizado':data-cont_,\
                               'Cero':np.zeros_like(L)})
            fig = go.Figure([\
                go.Scatter(name='Espectro sin continuo',\
                           x = df['Longitud de onda'],\
                           y = df['Flujo normalizado'],\
                           mode = 'lines',\
                           showlegend=True),\
                go.Scatter(name='Linea en cero',\
                           x = df['Longitud de onda'],\
                           y = df['Cero'],\
                           line = dict(dash='dash',color='grey',width=1),\
                           showlegend=False)\
                                ])
            
            st.plotly_chart(fig)

        if exc_reg == False and inc_reg == False:
            
            # Espectro completo: sin regiones de exclusión ni de inclusión
            if bounds_bool == 'No':
                
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,                                                    x_0=refpoint,alpha=alpha))
            if bounds_bool == 'Sí':
                fitcont_model = fit_lines(spec,PowerLaw1D(amplitude=amplitude,                                                    x_0=refpoint,alpha=alpha,                                          bounds={'amplitude':bounds_amp,                                                  'x_0':bounds_refpoint,                                                  'alpha':bounds_alpha}))
            
            cont = fitcont_model(lamb)
            cont_ = np.array(cont)
    
            #espectro sin continuo
    
            lamb_ = L*u.AA
            flux_ = (data-cont_)*u.Unit('erg cm-2 s-1 AA-1')
    
            spec_ = Spectrum1D(spectral_axis=lamb_,flux=flux_)
            
            fig_ = plt.figure()
            plt.plot(lamb_,flux_)
            plt.plot(lamb_,np.zeros_like(L),c='k',linestyle='--')
            plt.xlabel('Longitud de onda (Angstroms)')
            plt.ylabel('Flujo normalizado')
            
            df = pd.DataFrame({'Longitud de onda':L,'Flujo normalizado':data-cont_,                               'Cero':np.zeros_like(L)})
            fig = go.Figure([                go.Scatter(name='Espectro sin continuo',                           x = df['Longitud de onda'],                           y = df['Flujo normalizado'],                           mode = 'lines',                           showlegend=True),                go.Scatter(name='Linea en cero',                           x = df['Longitud de onda'],                           y = df['Cero'],                           line = dict(dash='dash',color='grey',width=1),                           showlegend=False)                                ])
            
            st.plotly_chart(fig)


    if metodo == 'Método de ajuste de continuo':
        
        st.info('Este método ajusta el continuo al espectro suavizado usando un \
                filtro mediano para remover los picos')
        
        bounds_bool = st.radio('Desea incluir límites para los parámetros iniciales:',('Sí','No'))
        
        if bounds_bool == 'Sí':
            
        
            st.info('Selecciona los límites de los parámetros de la ley de potencias en \
                    la barra lateral')
            
            bounds_amp = st.sidebar.slider('Límites de la amplitud',min(data),max(data),\
                                           [min(data),\
                                            max(data)])
            
            bounds_refpoint = st.sidebar.slider('Límites del punto de referencia:',\
                                                min(L),max(L),\
                                                [min(L),\
                                                   max(L)])
        
            bounds_alpha = st.sidebar.slider('Límites del índice de la ley de\
                                             potencias (alfa):',value=[1.0,2.0],\
                              min_value=0.0,max_value=3.0,step=0.01)
            
        
        exreg_bool = st.radio('Desea excluir una o más regiones del espectro:',('Sí','No'))
        
        if exreg_bool == 'Sí':
            
            ne = st.number_input('Cuántas regiones quieres excluir:',min_value=1,\
                                 max_value=5,step=1,value=1)
    
            st.write('Selecciona el mínimo y máximo (Angstroms) de cada región a excluir:')
    
            spectralregions_ex = []
    
            for i in range(ne):
                st.write('Región',i+1)
                # Por defecto una banda estrecha: excluir todo el espectro deja el ajuste sin datos
                _rlo = st.number_input('Mínimo:', key=_wk(), value=float(min(L)))
                _rhi = st.number_input('Máximo:', key=_wk(), value=float(min(L) + 0.05*(max(L)-min(L))))
                spectralregions_ex.append(_region(_rlo, _rhi))
    
                
            if bounds_bool == 'No':
                
                fitcont_model = fit_generic_continuum(spec,model=PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha),\
                                          exclude_regions=spectralregions_ex)
            if bounds_bool == 'Sí':
                fitcont_model = fit_generic_continuum(spec,model=PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha,\
                                          bounds={'amplitude':bounds_amp,\
                                                  'x_0':bounds_refpoint,\
                                                  'alpha':bounds_alpha}),\
                                          exclude_regions=spectralregions_ex)
    
        if exreg_bool == 'No':
            
            if bounds_bool == 'No':
                
                fitcont_model = fit_generic_continuum(spec,model=PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha))
            if bounds_bool == 'Sí':
                fitcont_model = fit_generic_continuum(spec,model=PowerLaw1D(amplitude=amplitude,\
                                                    x_0=refpoint,alpha=alpha,\
                                          bounds={'amplitude':bounds_amp,\
                                                  'x_0':bounds_refpoint,\
                                                  'alpha':bounds_alpha}))
            
        
        # st.write(np.transpose(fitcont_model.param_sets)[0])
        cont = fitcont_model(lamb)
        cont_ = np.array(cont)

        #espectro sin continuo

        lamb_ = L*u.AA
        flux_ = (data-cont_)*u.Unit('erg cm-2 s-1 AA-1')

        spec_ = Spectrum1D(spectral_axis=lamb_,flux=flux_)
        
        fig_ = plt.figure()
        plt.plot(lamb_,flux_)
        plt.plot(lamb_,np.zeros_like(L),c='k',linestyle='--')
        plt.xlabel('Longitud de onda (Angstroms)')
        plt.ylabel('Flujo normalizado')
        
        df = pd.DataFrame({'Longitud de onda':L,'Flujo normalizado':data-cont_,\
                           'Cero':np.zeros_like(L)})
            
        fig = go.Figure([\
            go.Scatter(name='Espectro sin continuo',\
                       x = df['Longitud de onda'],\
                       y = df['Flujo normalizado'],\
                       mode = 'lines',
                       showlegend=True),\
            go.Scatter(name='Linea en cero',\
                       x = df['Longitud de onda'],\
                       y = df['Cero'],\
                       line = dict(dash='dash',color='grey',width=1),\
                       showlegend=False)\
                            ])
        
        
        
        st.plotly_chart(fig)
            
            
        
        

        
if ajuste_bool == 'No, dejar parámetros iniciales seleccionados fijos':
    
    powerlaw = PowerLaw1D(amplitude=amplitude,x_0=refpoint,alpha=alpha)
    cont = powerlaw(lamb)
    cont_ = np.array(cont)
    
    #espectro sin continuo

    lamb_ = L*u.AA
    flux_ = (data-cont_)*u.Unit('erg cm-2 s-1 AA-1')

    spec_ = Spectrum1D(spectral_axis=lamb_,flux=flux_)
    
    fig_ = plt.figure()
    plt.plot(lamb_,flux_)
    plt.plot(lamb_,np.zeros_like(L),c='k',linestyle='--')
    plt.xlabel('Longitud de onda (Angstroms)')
    plt.ylabel('Flujo normalizado')
    
    df = pd.DataFrame({'Longitud de onda':L,'Flujo normalizado':data-cont_,\
                   'Cero':np.zeros_like(L)})
        
    fig = go.Figure([\
        go.Scatter(name='Espectro sin continuo',\
                   x = df['Longitud de onda'],\
                   y = df['Flujo normalizado'],\
                   mode = 'lines',
                   showlegend=True),\
        go.Scatter(name='Linea en cero',\
                   x = df['Longitud de onda'],\
                   y = df['Cero'],\
                   line = dict(dash='dash',color='grey',width=1),\
                   showlegend=False)\
                        ])
        
    st.plotly_chart(fig)


if st.radio('Desea exportar el espectro sin continuo como archivo de texto:',\
            ('No','Sí'),key=1) == 'Sí':

    
    file_sp = np.savetxt(distintivo+'_woc.txt',np.c_[L,flux_],fmt='%10.6f',\
                        header='lambda   spectrum')
    st.success('Listo. Exportado a la carpeta donde se encuentra este programa.\
               Lo encuentras como '+str(distintivo)+'_woc.txt')
        











   
    
### Ajuste del perfil de la línea

st.markdown('## Ajuste del perfil')
            
parametros_bool = st.radio('¿Desea usar archivo de parámetros para las componentes?',('No','Sí'))
    
if parametros_bool == 'No':
    
    st.write('Selecciona el tipo de componentes que quieres usar para el ajuste \
             y a continuación el número de componentes')
    
    checkbox_gauss = st.checkbox('Gaussiana')
    checkbox_lorentz = st.checkbox('Lorentziana')
    #checkbox_temphierro = st.checkbox('Template de Hierro')
    
    
if parametros_bool == 'Sí':
    
    params = st.file_uploader('Escoge el archivo de parámetros (tiene que tener extensión .txt):',type='txt',key='comp')
    
    # El radio 'Sí' se puede elegir antes de subir el archivo: sin él no hay tabla.
    if params is None:
        st.info('Sube el archivo de parámetros de las componentes (.txt).')
        st.stop()
    
    table_params = pd.read_csv(params,delim_whitespace=True)
    
    st.write(table_params)
    
    num_comps = len(table_params.prof_type) #Número de componentes
    num_l,num_g=0,0
    
    table_g = table_params[table_params['prof_type']=='g'].reset_index(drop=True)
    table_l = table_params[table_params['prof_type']=='l'].reset_index(drop=True)
    
    
    
    num_g = len(table_g) #Número de gaussianas
    
    num_l = len(table_l) #Número de lorentzianas
    
    
    
    if num_g != 0:
        checkbox_gauss = True
        num_gauss = num_g
    if num_g == 0:
        checkbox_gauss = False
        
    
    if num_l != 0:
        checkbox_lorentz = True
        num_lorentz = num_l
    if num_l == 0:
        checkbox_lorentz = False
        
    
checkbox_temphierro = st.checkbox('Utilizar un template de Fe II')

# Sin gaussianas, lorentzianas ni template de Fe II no hay modelo que ajustar:
# antes esto terminaba en NameError (models_ / models_aj) más abajo.
if checkbox_gauss == False and checkbox_lorentz == False and checkbox_temphierro == False:
    st.warning('Selecciona al menos una gaussiana, una lorentziana o un template de Fe II.')
    st.stop()  
    


if checkbox_temphierro == True:
    
    rango_hierro = st.selectbox('En qué rango espectral (reposo) quiere trabajar:',\
                 ('1435-2033 Angstroms','2200-3400 Angstroms','4000-7000 Angstroms',\
                  '4000-5500 Angstroms (Multiple components)'))
    
    ### Modelos del Hierro
    if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
        or rango_hierro == '4000-7000 Angstroms':
            
        tempsA,tempsB,tempsOPT = [],[],[]
        
        # Los grids de templates no tienen todos 50 entradas: el de Fe II
        # optico se genero con np.arange(700,3100,100) -> 24 anchos Doppler
        # (700-3000 km/s, indice i = 700+100*(i-1)). Cargamos las que existan
        # en lugar de asumir 50.
        _prefijos = {'1435-2033 Angstroms': 'Hierro/Carbono/FE_UV_A',
                     '2200-3400 Angstroms': 'Hierro/Magnesio/FE_UV_B',
                     '4000-7000 Angstroms': 'Hierro/Hidrogeno/FE_OPT-1_'}
        _pref = _prefijos[rango_hierro]
        _idx = [j for j in range(50) if os.path.exists(_pref + str(j+1) + '.dat')]
        if not _idx:
            st.error('No hay ningún template de ' + rango_hierro + ' en '
                     + os.path.dirname(_pref) + '/.')
            st.stop()
        if len(_idx) < 50:
            st.caption('Templates de ' + rango_hierro + ': ' + str(len(_idx))
                       + ' disponibles (índices ' + str(_idx[0]+1) + '-' + str(_idx[-1]+1) + ').')
        
        for i in _idx:
            
            if rango_hierro == '1435-2033 Angstroms':
                tempA = np.loadtxt('Hierro/Carbono/FE_UV_A'+str(i+1)+'.dat')
                tempsA.append(tempA)
            
            if rango_hierro == '2200-3400 Angstroms':
                tempB = np.loadtxt('Hierro/Magnesio/FE_UV_B'+str(i+1)+'.dat')
                tempsB.append(tempB)
                
            if rango_hierro == '4000-7000 Angstroms':
                tempOPT = np.loadtxt('Hierro/Hidrogeno/FE_OPT-1_'+str(i+1)+'.dat')
                tempsOPT.append(tempOPT)
    
    if rango_hierro == '4000-5500 Angstroms (Multiple components)':
        
        doppler = np.arange(700,2900,100)
        
        tempsOPT_f,tempsOPT_g,tempsOPT_p,tempsOPT_s,tempsOPT_Zw = [],[],[],[],[]
        
        for i in range(len(doppler)):
        
            tempOPT_f = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(doppler[i])+'FeII/fe_f.txt')
            tempsOPT_f.append(tempOPT_f)
                
            tempOPT_g = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(doppler[i])+'FeII/fe_g.txt')
            tempsOPT_g.append(tempOPT_g)
                
            tempOPT_p = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(doppler[i])+'FeII/fe_p.txt')
            tempsOPT_p.append(tempOPT_p)
                
            tempOPT_s = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(doppler[i])+'FeII/fe_s.txt')
            tempsOPT_s.append(tempOPT_s)
                
            tempOPT_Zw = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(doppler[i])+'FeII/fe_IZw1.txt')
            tempsOPT_Zw.append(tempOPT_Zw)
        
  
    
    
    st.sidebar.markdown('## Parámetros del template de Hierro')
    
    if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
        or rango_hierro == '4000-7000 Angstroms':
            
            
    
        hierro_amp = st.sidebar.slider('Amplitud',min_value=0.0,max_value=max(data-cont_)/2,\
                                       value=0.01,step=0.0001)
        
        hierro_smooth = st.sidebar.slider('Suavidad del template',min_value=1,\
                                          max_value=len(_idx),value=min(10,len(_idx)),step=1)
            
        hierro_shift = st.sidebar.slider('Desplazamiento del template',\
                                         min_value=-50.0,max_value=50.0,value=0.0,step=0.5)
        
    
        if rango_hierro == '1435-2033 Angstroms':
            
            def temp_hierroA(x,amplitud=1.0,smooth=10,shift=0.0):
                       
                hierroA = tempsA[int(smooth-1)]
                   
                return np.interp(x,hierroA[:,0]+shift,amplitud*hierroA[:,1])
            
            modelHierro = custom_model(temp_hierroA)
            
            
        if rango_hierro == '2200-3400 Angstroms':
            
            def temp_hierroB(x,amplitud=1.0,smooth=10,shift=0.0):
                     
                hierroB = tempsB[int(smooth-1)]
                  
                return np.interp(x,hierroB[:,0]+shift,amplitud*hierroB[:,1])
            
            modelHierro = custom_model(temp_hierroB)
            
            
        if rango_hierro == '4000-7000 Angstroms':
            
            def temp_hierroOPT(x,amplitud=1.0,smooth=10,shift=0.0):
                        
                hierroOPT = tempsOPT[int(smooth-1)]
                  
                return np.interp(x,hierroOPT[:,0]+shift,amplitud*hierroOPT[:,1])
            
            modelHierro = custom_model(temp_hierroOPT)
            
        
        init_modelHierro = modelHierro(hierro_amp,hierro_smooth,hierro_shift)
        
        
        
        
    if rango_hierro == '4000-5500 Angstroms (Multiple components)':
        
        param_fe = st.radio('¿Desea usar archivo de parámetros iniciales para el template?',('No','Sí'))
        
        
        if param_fe == 'Sí':
            
            params_fe = st.file_uploader('Escoge el archivo de parámetros (tiene que tener extensión .txt):',type='txt',key='temp')
    
            if params_fe is None:
                st.info('Sube el archivo de parámetros iniciales del template (.txt).')
                st.stop()
    
            tpfe = pd.read_csv(params_fe,delim_whitespace=True)
    
            st.write(tpfe)
            
            tpfe_f = tpfe[tpfe.group == 'f']
            tpfe_g = tpfe[tpfe.group == 'g']
            tpfe_s = tpfe[tpfe.group == 's']
            tpfe_p = tpfe[tpfe.group == 'p']
            tpfe_Zw= tpfe[tpfe.group == 'zw']
            
            # st.write(tpfe_g.amax.values[0])
            
            
        
        
        hierro_smooth_ = st.sidebar.slider('Ancho Doppler en km/s',min_value=700,\
                                          max_value=2800,value=1000,step=100)
        
        ## Grupo F
            
        st.sidebar.markdown('### Grupo de líneas F')
        
        class modelHierro_f(Fittable1DModel):
            
            amplitud = Parameter(default=1.0)
            shift = Parameter(default=0.0,bounds=(-20,20))
            doppler = Parameter(default=1000,fixed=True)
            
            @staticmethod
            def evaluate(x,amplitud,shift,doppler):
                
                global tempsOPT_f
                    
                doppler_ = np.arange(700,2900,100)
                
                for i in range(len(doppler_)):
                    if doppler == doppler_[i]:
                        index = i
                
                hierroOPT_f = tempsOPT_f[int(index)]
                  
                return np.interp(x,hierroOPT_f[:,0]+shift,amplitud*hierroOPT_f[:,1])
        
        if param_fe == 'No':
            
        
            hierro_amp_f = st.sidebar.slider('Amplitud',min_value=0.0,max_value=max(data-cont_)/2,\
                                           value=0.04,step=0.001,key=_wk())
                
            amp_f_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            hierro_shift_f = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=-20.0,max_value=20.0,value=0.0,step=0.5,key=_wk())
                
            shift_f_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
            
        
        if param_fe == 'Sí':
            
            hierro_amp_f = st.sidebar.slider('Amplitud',min_value=tpfe_f.amin.values[0],max_value=tpfe_f.amax.values[0],\
                                           value=tpfe_f.amp.values[0],step=0.001,key=_wk())
            
            if tpfe_f.amp_fixed.values[0] == 0:
                
                amp_f_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            if tpfe_f.amp_fixed.values[0] == 1:
                
                amp_f_fixed = st.sidebar.checkbox('Fijar amplitud',value=True,key=_wk())
                
                
            hierro_shift_f = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=tpfe_f.smin.values[0],max_value=tpfe_f.smax.values[0],\
                                                 value=tpfe_f['shift'].values[0],step=0.5,key=_wk())
                
            if tpfe_f.shift_fixed.values[0] == 0:
                
                shift_f_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
                
            if tpfe_f.shift_fixed.values[0] == 1:
                
                shift_f_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=True,key=_wk())
                
            
            
            
        
        init_modelHierro_f = modelHierro_f(hierro_amp_f,hierro_shift_f,hierro_smooth_)
        
        init_modelHierro_f.amplitud.fixed = amp_f_fixed
        init_modelHierro_f.shift.fixed = shift_f_fixed
            
        
        ## Grupo G
        
        st.sidebar.markdown('### Grupo de líneas G')
        
        class modelHierro_g(Fittable1DModel):
            
            amplitud = Parameter(default=1.0)
            shift = Parameter(default=0.0,bounds=(-20,20))
            doppler = Parameter(default=1000,fixed=True)
            
            @staticmethod
            def evaluate(x,amplitud,shift,doppler):
                
                global tempsOPT_g
                    
                doppler_ = np.arange(700,2900,100)
                
                for i in range(len(doppler_)):
                    if doppler == doppler_[i]:
                        index = i
                
                hierroOPT_g = tempsOPT_g[int(index)]
                  
                return np.interp(x,hierroOPT_g[:,0]+shift,amplitud*hierroOPT_g[:,1])
            
        if param_fe == 'No':
            
        
            hierro_amp_g = st.sidebar.slider('Amplitud',min_value=0.0,max_value=max(data-cont_)/2,\
                                           value=0.04,step=0.001,key=_wk())
                
            amp_g_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            hierro_shift_g = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=-20.0,max_value=20.0,value=0.0,step=0.5,key=_wk())
                
            shift_g_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
            
        
        if param_fe == 'Sí':
            
            hierro_amp_g = st.sidebar.slider('Amplitud',min_value=tpfe_g.amin.values[0],max_value=tpfe_g.amax.values[0],\
                                           value=tpfe_g.amp.values[0],step=0.001,key=_wk())
            
            if tpfe_g.amp_fixed.values[0] == 0:
                
                amp_g_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            if tpfe_g.amp_fixed.values[0] == 1:
                
                amp_g_fixed = st.sidebar.checkbox('Fijar amplitud',value=True,key=_wk())
                
                
            hierro_shift_g = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=tpfe_g.smin.values[0],max_value=tpfe_g.smax.values[0],\
                                                 value=tpfe_g['shift'].values[0],step=0.5,key=_wk())
                
            if tpfe_g.shift_fixed.values[0] == 0:
                
                shift_g_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
                
            if tpfe_g.shift_fixed.values[0] == 1:
                
                shift_g_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=True,key=_wk())
        
        
        
        init_modelHierro_g = modelHierro_g(hierro_amp_g,hierro_shift_g,hierro_smooth_)
        
        init_modelHierro_g.amplitud.fixed = amp_g_fixed
        init_modelHierro_g.shift.fixed = shift_g_fixed
        
        
        ## Grupo S
        
        st.sidebar.markdown('### Grupo de líneas S')
        
        class modelHierro_s(Fittable1DModel):
            
            amplitud = Parameter(default=1.0)
            shift = Parameter(default=0.0,bounds=(-20,20))
            doppler = Parameter(default=1000,fixed=True)
            
            @staticmethod
            def evaluate(x,amplitud,shift,doppler):
                
                global tempsOPT_s
                    
                doppler_ = np.arange(700,2900,100)
                
                for i in range(len(doppler_)):
                    if doppler == doppler_[i]:
                        index = i
                
                hierroOPT_s = tempsOPT_s[int(index)]
                  
                return np.interp(x,hierroOPT_s[:,0]+shift,amplitud*hierroOPT_s[:,1])
            
        if param_fe == 'No':
            
        
            hierro_amp_s = st.sidebar.slider('Amplitud',min_value=0.0,max_value=max(data-cont_)/2,\
                                           value=0.04,step=0.001,key=_wk())
                
            amp_s_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            hierro_shift_s = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=-20.0,max_value=20.0,value=0.0,step=0.5,key=_wk())
                
            shift_s_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
            
        if param_fe == 'Sí':
            
            hierro_amp_s = st.sidebar.slider('Amplitud',min_value=tpfe_s.amin.values[0],max_value=tpfe_s.amax.values[0],\
                                           value=tpfe_s.amp.values[0],step=0.001,key=_wk())
            
            if tpfe_s.amp_fixed.values[0] == 0:
                
                amp_s_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            if tpfe_s.amp_fixed.values[0] == 1:
                
                amp_s_fixed = st.sidebar.checkbox('Fijar amplitud',value=True,key=_wk())
                
                
            hierro_shift_s = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=tpfe_s.smin.values[0],max_value=tpfe_s.smax.values[0],\
                                                 value=tpfe_s['shift'].values[0],step=0.5,key=_wk())
                
            if tpfe_s.shift_fixed.values[0] == 0:
                
                shift_s_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
                
            if tpfe_s.shift_fixed.values[0] == 1:
                
                shift_s_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=True,key=_wk())
        
        
        init_modelHierro_s = modelHierro_s(hierro_amp_s,hierro_shift_s,hierro_smooth_)
        
        init_modelHierro_s.amplitud.fixed = amp_s_fixed
        init_modelHierro_s.shift.fixed = shift_s_fixed
            
        ## Grupo P            
        
        st.sidebar.markdown('### Grupo de líneas P')
        
        class modelHierro_p(Fittable1DModel):
            
            amplitud = Parameter(default=1.0)
            shift = Parameter(default=0.0,bounds=(-20,20))
            doppler = Parameter(default=1000,fixed=True)
            
            @staticmethod
            def evaluate(x,amplitud,shift,doppler):
                
                global tempsOPT_p
                    
                doppler_ = np.arange(700,2900,100)
                
                for i in range(len(doppler_)):
                    if doppler == doppler_[i]:
                        index = i
                
                hierroOPT_p = tempsOPT_p[int(index)]
                  
                return np.interp(x,hierroOPT_p[:,0]+shift,amplitud*hierroOPT_p[:,1])
            
        if param_fe == 'No':
            
        
            hierro_amp_p = st.sidebar.slider('Amplitud',min_value=0.0,max_value=max(data-cont_)/2,\
                                           value=0.04,step=0.001,key=_wk())
                
            amp_p_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                   
            hierro_shift_p = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=-20.0,max_value=20.0,value=0.0,step=0.5,key=_wk())
                
            shift_p_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
            
            
        if param_fe == 'Sí':
            
            hierro_amp_p = st.sidebar.slider('Amplitud',min_value=tpfe_p.amin.values[0],max_value=tpfe_p.amax.values[0],\
                                           value=tpfe_p.amp.values[0],step=0.001,key=_wk())
            
            if tpfe_p.amp_fixed.values[0] == 0:
                
                amp_p_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            if tpfe_p.amp_fixed.values[0] == 1:
                
                amp_p_fixed = st.sidebar.checkbox('Fijar amplitud',value=True,key=_wk())
                
                
            hierro_shift_p = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=tpfe_p.smin.values[0],max_value=tpfe_p.smax.values[0],\
                                                 value=tpfe_p['shift'].values[0],step=0.5,key=_wk())
                
            if tpfe_p.shift_fixed.values[0] == 0:
                
                shift_p_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
                
            if tpfe_p.shift_fixed.values[0] == 1:
                
                shift_p_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=True,key=_wk())
            
        
        
        init_modelHierro_p = modelHierro_p(hierro_amp_p,hierro_shift_p,hierro_smooth_)
        
        init_modelHierro_p.amplitud.fixed = amp_p_fixed
        init_modelHierro_p.shift.fixed = shift_p_fixed
            
        
        ## I Zw 1
        
        st.sidebar.markdown('### Grupo de líneas del objeto I Zw 1')
        
        class modelHierro_Zw(Fittable1DModel):
            
            amplitud = Parameter(default=1.0)
            shift = Parameter(default=0.0,bounds=(-20,20))
            doppler = Parameter(default=1000,fixed=True)
            
            @staticmethod
            def evaluate(x,amplitud,shift,doppler):
                
                global tempsOPT_Zw
                    
                doppler_ = np.arange(700,2900,100)
                
                for i in range(len(doppler_)):
                    if doppler == doppler_[i]:
                        index = i
                
                hierroOPT_Zw = tempsOPT_Zw[int(index)]
                  
                return np.interp(x,hierroOPT_Zw[:,0]+shift,amplitud*hierroOPT_Zw[:,1])
        
        if param_fe == 'No':
            
        
            hierro_amp_Zw = st.sidebar.slider('Amplitud',min_value=0.0,max_value=max(data-cont_)/2,\
                                           value=0.01,step=0.0001,key=_wk())
                
            amp_Zw_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            hierro_shift_Zw = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=-20.0,max_value=20.0,value=0.0,step=0.5,key=_wk())
                
            shift_Zw_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
            
        if param_fe == 'Sí':
            
            hierro_amp_Zw = st.sidebar.slider('Amplitud',min_value=tpfe_Zw.amin.values[0],max_value=tpfe_Zw.amax.values[0],\
                                           value=tpfe_Zw.amp.values[0],step=0.001,key=_wk())
            
            if tpfe_Zw.amp_fixed.values[0] == 0:
                
                amp_Zw_fixed = st.sidebar.checkbox('Fijar amplitud',value=False,key=_wk())
                
            if tpfe_Zw.amp_fixed.values[0] == 1:
                
                amp_Zw_fixed = st.sidebar.checkbox('Fijar amplitud',value=True,key=_wk())
                
                
            hierro_shift_Zw = st.sidebar.slider('Desplazamiento del template',\
                                             min_value=tpfe_Zw.smin.values[0],max_value=tpfe_Zw.smax.values[0],\
                                                 value=tpfe_Zw['shift'].values[0],step=0.5,key=_wk())
                
            if tpfe_Zw.shift_fixed.values[0] == 0:
                
                shift_Zw_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=False,key=_wk())
                
            if tpfe_Zw.shift_fixed.values[0] == 1:
                
                shift_Zw_fixed = st.sidebar.checkbox('Fijar desplazamiento',value=True,key=_wk())
            
        
        
        init_modelHierro_Zw = modelHierro_Zw(hierro_amp_Zw,hierro_shift_Zw,hierro_smooth_)
        
        init_modelHierro_Zw.amplitud.fixed = amp_Zw_fixed
        init_modelHierro_Zw.shift.fixed = shift_Zw_fixed
    



def kmstoangs(ancho,centro,mode='g'):   #Función para convertir FWHM en km/s a 
                                        #FWHM (Lorentziana) y SIGMA (Gaussiana) en Angstroms
            
            if mode == 'l':
                ##FWHM
                return ancho*centro/300000
            if mode == 'g':
                ##SIGMA
                return (ancho*centro/300000)/2.35
            
def angstokms(ancho,centro,mode='g'):
    if mode == 'l':
        
        return (ancho*300000)/centro
        
    if mode == 'g':
        
        return (ancho*300000*2.35)/centro
            


            
st.sidebar.markdown('## Parámetros iniciales de las componentes')

if checkbox_gauss == True and checkbox_lorentz == True:
    if parametros_bool == 'No':
        
        num_gauss = st.number_input('Número de Gaussianas que desea usar'\
                                    ,min_value=1,max_value=10,step=1,value=1)
        
        num_lorentz = st.number_input('Número de Lorentzianas que desea usar'\
                                    ,min_value=1,max_value=10,step=1,value=1)
        
        
    
    
    st.warning('Sólo es necesario especificar los límites de los parámetros \
               si se quiere obtener un "best fit".')
    
    gaussians_aj=[]
    gaussians=[]
    lorentzians_aj=[]
    lorentzians=[]
    
    for i in range(num_gauss):
        
        
        
        if i==0:
            st.sidebar.markdown('### Parámetros de las gaussianas')
        
        st.sidebar.markdown('Parámetros de la gaussiana '+str(i+1))
        #st.write('Límites de los parámetros de la gaussiana',i+1)
        
        
        if parametros_bool == 'No':
            
            #amplitud
            
            amplitude = st.sidebar.slider('Amplitud de la gaussiana:',\
                                          min(data-cont_),max(data-cont_),\
                                          np.mean(data-cont_),key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',value=max(data-cont_),key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la gaussiana:',int(min(L)),\
                                     int(max(L)),int(np.mean(L)),key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=mean-5,key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=mean+5,key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la gaussiana (km/s)',\
                                       value=2000.0,min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=30000,key=_wk())
            
        
        if parametros_bool == 'Sí':
            
            #amplitud
            
            amplitude = st.sidebar.slider('Amplitud de la gaussiana:',\
                                          min(data-cont_),max(data-cont_),\
                                          table_g['amplitude'][i],key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',value=table_g['amin'][i],key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',value=table_g['amax'][i],key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la gaussiana:',float(min(L)),\
                                     float(max(L)),table_g['center'][i],key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=table_g['cmin'][i],key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=table_g['cmax'][i],key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la gaussiana (km/s)',\
                                       value=table_g['fwhm'][i],min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',value=table_g['fmin'][i],key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=table_g['fmax'][i],key=_wk())
        
        
        #models
        
        gaussians_aj.append(models.Gaussian1D(amplitude,mean,kmstoangs(fwhm,mean),\
                                bounds={'amplitude':[amp_min,amp_max],\
                                        'mean':[mean_min,mean_max],\
                               'stddev':[kmstoangs(fwhm_min,mean),\
                                         kmstoangs(fwhm_max,mean)]}))
        
        gaussians.append(models.Gaussian1D(amplitude,mean,kmstoangs(fwhm,mean)))
        
        
    for j in range(num_lorentz):
        
        
        
        if j==0:
            st.sidebar.markdown('### Parámetros de las lorentzianas')
        
        st.sidebar.markdown('Parámetros de la lorentziana '+str(j+1))
        #st.write('Límites los parámetros de la lorentziana',j+1)
        
        if parametros_bool == 'No':
            
        
            #amplitude
            
            amplitude = st.sidebar.slider('Amplitud de la lorentziana:',\
                                          min(data-cont_),max(data-cont_),\
                                          np.mean(data-cont_),key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',\
                                              value=max(data-cont_),key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la lorentziana:',int(min(L)),\
                                     int(max(L)),int(np.mean(L)),key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=mean-5,key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=mean+5,key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la lorentziana (km/s)',\
                                       value=2000.0,min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=30000,key=_wk())
            
        if parametros_bool == 'Sí':
            
        
            #amplitude
            
            amplitude = st.sidebar.slider('Amplitud de la lorentziana:',\
                                          float(min(data-cont_)),float(max(data-cont_)),\
                                          table_l['amplitude'][j],key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',value=table_l['amin'][j],key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',\
                                              value=table_l['amax'][j],key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la lorentziana:',float(min(L)),\
                                     float(max(L)),table_l['center'][j],key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=table_l['cmin'][j],key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=table_l['cmax'][j],key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la lorentziana (km/s)',\
                                       value=table_l['fwhm'][j],min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',value=table_l['fmin'][j],key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=table_l['fmax'][j],key=_wk())
        
        
        lorentzians_aj.append(models.Lorentz1D(amplitude,mean,kmstoangs(fwhm,mean,mode='l'),\
                                bounds={'amplitude':[amp_min,amp_max],\
                                        'x_0':[mean_min,mean_max],\
                               'fwhm':[kmstoangs(fwhm_min,mean,mode='l'),\
                                         kmstoangs(fwhm_max,mean,mode='l')]}))
        
        lorentzians.append(models.Lorentz1D(amplitude,mean,kmstoangs(fwhm,mean,mode='l')))
    
    
    #Espectro con componentes sin ajustar
    
    models_ = gaussians[0]
    models_aj = gaussians_aj[0]
    
    all_comps = []
    header_comps=''
    
    
    if num_gauss > 1:
        for k in range(num_gauss):
            if k+1 <= range(num_gauss)[-1]:
                models_ = models_ + gaussians[k+1]
                models_aj = models_aj + gaussians_aj[k+1]
            else:
                break
            
    models_ = models_ + lorentzians[0]
    models_aj = models_aj + lorentzians_aj[0]
    
        
    if num_lorentz > 1:
        for k in range(num_lorentz):
            if k+1 <= range(num_lorentz)[-1]:
                models_ = models_ + lorentzians[k+1]
                models_aj = models_aj + lorentzians_aj[k+1]
            else:
                break
            
    
    
    st.info('Los parámetros pueden ser manipulados en la barra lateral.')
    
    fig_ = plt.figure()
    plt.plot(lamb_,flux_,label=None)
    
    ESPECTRO = go.Scatter(x=lamb_,y=flux_,name='Espectro')
    
    if checkbox_temphierro == True:
        
        
        if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
            or rango_hierro == '4000-7000 Angstroms':
            
            plt.plot(L,init_modelHierro(L))
            
            models_aj = models_aj + init_modelHierro
            models_ = models_ + init_modelHierro
            
        
        if rango_hierro == '4000-5500 Angstroms (Multiple components)':
            
            plt.plot(L,init_modelHierro_f(L))
            
            models_aj = models_aj + init_modelHierro_f
            models_ = models_ + init_modelHierro_f
            
            
            plt.plot(L,init_modelHierro_g(L))
            
            models_aj = models_aj + init_modelHierro_g
            models_ = models_ + init_modelHierro_g
            
            
            plt.plot(L,init_modelHierro_s(L))
            
            models_aj = models_aj + init_modelHierro_s
            models_ = models_ + init_modelHierro_s
            
            
            plt.plot(L,init_modelHierro_p(L))
            
            models_aj = models_aj + init_modelHierro_p
            models_ = models_ + init_modelHierro_p
            
            
            plt.plot(L,init_modelHierro_Zw(L))
            
            models_aj = models_aj + init_modelHierro_Zw
            models_ = models_ + init_modelHierro_Zw
            
            
        

    
    plt.plot(L,models_(L),c='k')         
    
    MODELO = go.Scatter(x=L,y=models_(L),name='Modelo')
    
    ESPMOD = [ESPECTRO,MODELO]
    
    PLOTS_G,PLOTS_L = [],[]
    
    for i in range(len(gaussians)):
        plt.plot(L,gaussians[i](L),label='Gaussiana '+str(i+1))
        PLOTS_G.append(go.Scatter(x=L,y=gaussians[i](L),name='Gaussiana '+str(i+1)))
        
        all_comps.append(gaussians[i](L))
        header_comps = header_comps + 'Gaussiana '+str(i+1)+'   '
    
    for j in range(len(lorentzians)):
        plt.plot(L,lorentzians[j](L),label='Lorentziana '+str(j+1))
        PLOTS_L.append(go.Scatter(x=L,y=lorentzians[j](L),name='Lorentziana '+str(j+1)))
        
        all_comps.append(lorentzians[j](L))
        header_comps = header_comps + 'Lorentziana '+str(j+1)+'   '
    
    plt.xlabel('Longitud de onda (Angstroms)')
    plt.ylabel('Flujo normalizado')
    plt.legend()
    
    fig = go.Figure(ESPMOD+PLOTS_G+PLOTS_L)
    
    if checkbox_temphierro == True:
        
        if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
            or rango_hierro == '4000-7000 Angstroms':
        
            plotHierro = go.Scatter(x=L,y=init_modelHierro(L),name='Template Fe II')
            fig.add_trace(plotHierro)
            
        
        if rango_hierro == '4000-5500 Angstroms (Multiple components)':
            
            plotHierro_f = go.Scatter(x=L,y=init_modelHierro_f(L),name='Fe II - F group')
            fig.add_trace(plotHierro_f)
            
            plotHierro_g = go.Scatter(x=L,y=init_modelHierro_g(L),name='Fe II - G group')
            fig.add_trace(plotHierro_g)
            
            plotHierro_s = go.Scatter(x=L,y=init_modelHierro_s(L),name='Fe II - S group')
            fig.add_trace(plotHierro_s)
            
            plotHierro_p = go.Scatter(x=L,y=init_modelHierro_p(L),name='Fe II - P group')
            fig.add_trace(plotHierro_p)
            
            plotHierro_Zw = go.Scatter(x=L,y=init_modelHierro_Zw(L),name='Fe II - I Zw 1')
            fig.add_trace(plotHierro_Zw)
    
    
    fig.update_layout(xaxis_title='Longitud de onda (Angstroms)',yaxis_title='Flujo normalizado',\
                      width=700,height=800)
        
    st.plotly_chart(fig)
    
    export = np.array([L,data,cont_,flux_,models_(L)])
    
    full_export = np.concatenate((export,all_comps)).T
    
    
if checkbox_gauss == True and checkbox_lorentz == False:
    
    
    if parametros_bool == 'No':
        
        num_gauss = st.number_input('Número de Gaussianas que desea usar'\
                                    ,min_value=1,max_value=10,step=1,value=1)
    
    
    st.warning('Sólo es necesario especificar los límites de los parámetros \
               si se quiere obtener un "best fit".')
    
    gaussians_aj=[]
    gaussians=[]
    
    for i in range(num_gauss):
        
        
        
        if i==0:
            st.sidebar.markdown('### Parámetros de las gaussianas')
        
        st.sidebar.markdown('Parámetros de la gaussiana '+str(i+1))
        #st.write('Límites de los parámetros de la gaussiana',i+1)
        
        
#        #amplitud
#        amplitude = st.sidebar.slider('Amplitud de la gaussiana:',\
#                                      min(data-cont_),max(data-cont_),\
#                                      np.mean(data-cont_),key=_wk())
#
#        amp_min = st.sidebar.number_input('Mínimo de amplitud',key=_wk())
#        amp_max = st.sidebar.number_input('Máximo de amplitud',value=max(data-cont_),key=_wk())
#        
#        
#        #centro
#        mean = st.sidebar.slider('Centro de la gaussiana:',min(L),\
#                                 max(L),int(np.mean(L)),key=_wk())
#        
#        mean_min = st.sidebar.number_input('Valor mínimo del centro',\
#                                           value=mean-5,key=_wk())
#        mean_max = st.sidebar.number_input('Valor máximo del centro',\
#                                           value=mean+5,key=_wk())
#        
#        #fwhm
#        
#        fwhm = st.sidebar.slider('FWHM de la gaussiana (km/s)',\
#                                   value=2000.0,min_value=0.0,max_value=30000.0,\
#                                   step=0.01,key=_wk())
#        
#        fwhm_min = st.sidebar.number_input('Mínimo de FWHM',key=_wk())
#        fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=30000,key=_wk())
        
        
        if parametros_bool == 'No':
            
            #amplitud
            
            amplitude = st.sidebar.slider('Amplitud de la gaussiana:',\
                                          min(data-cont_),max(data-cont_),\
                                          np.mean(data-cont_),key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',value=max(data-cont_),key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la gaussiana:',int(min(L)),\
                                     int(max(L)),int(np.mean(L)),key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=mean-5,key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=mean+5,key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la gaussiana (km/s)',\
                                       value=2000.0,min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=30000,key=_wk())
            
        
        if parametros_bool == 'Sí':
            
            #amplitud
            
            amplitude = st.sidebar.slider('Amplitud de la gaussiana:',\
                                          min(data-cont_),max(data-cont_),\
                                          table_g['amplitude'][i],key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',value=table_g['amin'][i],key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',value=table_g['amax'][i],key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la gaussiana:',float(min(L)),\
                                     float(max(L)),table_g['center'][i],key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=table_g['cmin'][i],key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=table_g['cmax'][i],key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la gaussiana (km/s)',\
                                       value=table_g['fwhm'][i],min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',value=table_g['fmin'][i],key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=table_g['fmax'][i],key=_wk())
        
        
        #models
        
        gaussians_aj.append(models.Gaussian1D(amplitude,mean,kmstoangs(fwhm,mean),\
                                bounds={'amplitude':[amp_min,amp_max],\
                                        'mean':[mean_min,mean_max],\
                               'stddev':[kmstoangs(fwhm_min,mean),\
                                         kmstoangs(fwhm_max,mean)]}))
        
        gaussians.append(models.Gaussian1D(amplitude,mean,kmstoangs(fwhm,mean)))
        
    #Espectro con componentes sin ajustar
    
    models_ = gaussians[0]
    models_aj = gaussians_aj[0]
    
    all_gaussians = []
    header_gauss=''
    
    if num_gauss > 1:
        for k in range(num_gauss):
            if k+1 <= range(num_gauss)[-1]:
                models_ = models_ + gaussians[k+1]
                models_aj = models_aj + gaussians_aj[k+1]
            else:
                break
    
    st.info('Los parámetros pueden ser manipulados en la barra lateral.')
    
    fig_ = plt.figure()
    plt.plot(lamb_,flux_,label=None)
    
    ESPECTRO = go.Scatter(x=lamb_,y=flux_,name='Espectro')

    if checkbox_temphierro == True:
        
                      
        if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
            or rango_hierro == '4000-7000 Angstroms':
            
            plt.plot(L,init_modelHierro(L))
            
            models_aj = models_aj + init_modelHierro
            models_ = models_ + init_modelHierro
            
        
        if rango_hierro == '4000-5500 Angstroms (Multiple components)':
            
            plt.plot(L,init_modelHierro_f(L))
            
            models_aj = models_aj + init_modelHierro_f
            models_ = models_ + init_modelHierro_f
            
            
            plt.plot(L,init_modelHierro_g(L))
            
            models_aj = models_aj + init_modelHierro_g
            models_ = models_ + init_modelHierro_g
            
            
            plt.plot(L,init_modelHierro_s(L))
            
            models_aj = models_aj + init_modelHierro_s
            models_ = models_ + init_modelHierro_s
            
            
            plt.plot(L,init_modelHierro_p(L))
            
            models_aj = models_aj + init_modelHierro_p
            models_ = models_ + init_modelHierro_p
            
            
            plt.plot(L,init_modelHierro_Zw(L))
            
            models_aj = models_aj + init_modelHierro_Zw
            models_ = models_ + init_modelHierro_Zw
            
            

    plt.plot(lamb_,models_(L),label=None,c='k')
    
    MODELO = go.Scatter(x=L,y=models_(L),name='Modelo')
    
    ESPMOD = [ESPECTRO,MODELO]
    
    PLOTS_G = []
        
    for i in range(len(gaussians)):
        plt.plot(L,gaussians[i](L),label='Gaussiana '+str(i+1))
        PLOTS_G.append(go.Scatter(x=L,y=gaussians[i](L),name='Gaussiana '+str(i+1)))
        
        all_gaussians.append(gaussians[i](L))
        header_gauss = header_gauss + 'Gaussiana '+str(i+1)+'   '
        
    plt.xlabel('Longitud de onda (Angstroms)')
    plt.ylabel('Flujo normalizado')
    plt.legend()
    
    fig = go.Figure(ESPMOD+PLOTS_G)
    
    if checkbox_temphierro == True:
        
        if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
            or rango_hierro == '4000-7000 Angstroms':
        
            plotHierro = go.Scatter(x=L,y=init_modelHierro(L),name='Template Fe II')
            fig.add_trace(plotHierro)
            
        
        if rango_hierro == '4000-5500 Angstroms (Multiple components)':
            
            plotHierro_f = go.Scatter(x=L,y=init_modelHierro_f(L),name='Fe II - F group')
            fig.add_trace(plotHierro_f)
            
            plotHierro_g = go.Scatter(x=L,y=init_modelHierro_g(L),name='Fe II - G group')
            fig.add_trace(plotHierro_g)
            
            plotHierro_s = go.Scatter(x=L,y=init_modelHierro_s(L),name='Fe II - S group')
            fig.add_trace(plotHierro_s)
            
            plotHierro_p = go.Scatter(x=L,y=init_modelHierro_p(L),name='Fe II - P group')
            fig.add_trace(plotHierro_p)
            
            plotHierro_Zw = go.Scatter(x=L,y=init_modelHierro_Zw(L),name='Fe II - I Zw 1')
            fig.add_trace(plotHierro_Zw)
            
    
    fig.update_layout(xaxis_title='Longitud de onda (Angstroms)',yaxis_title='Flujo normalizado',\
                      width=700,height=800)
      
        
    st.plotly_chart(fig)
    
    export = np.array([L,data,cont_,flux_,models_(L)])
    
    full_export = np.concatenate((export,all_gaussians)).T
    
    
    
    
        
    
if checkbox_gauss == False and checkbox_lorentz == True:
    
    
    if parametros_bool == 'No':
        
        num_lorentz = st.number_input('Número de Lorentzianas que desea usar'\
                                    ,min_value=1,max_value=10,step=1,value=1)
    
    
    st.warning('Sólo es necesario especificar los límites de los parámetros \
               si se quiere obtener un "best fit".')
    
    lorentzians_aj=[]
    lorentzians=[]
    
    
        
    
    for j in range(num_lorentz):
        
        
        
        if j==0:
            st.sidebar.markdown('### Parámetros de las lorentzianas')
        
        st.sidebar.markdown('Parámetros de la lorentziana '+str(j+1))
        #st.write('Límites los parámetros de la lorentziana',j+1)
        
        
#        #amplitud
#        
#        amplitude = st.sidebar.slider('Amplitud de la lorentzian:',\
#                                      min(data-cont_),max(data-cont_),\
#                                      np.mean(data-cont_),key=_wk())
#
#        amp_min = st.sidebar.number_input('Mínimo de amplitud',key=_wk())
#        amp_max = st.sidebar.number_input('Máximo de amplitud',value=max(data-cont_),key=_wk())
#        
#        
#        #centro
#        mean = st.sidebar.slider('Centro de la lorentziana:',min(L),\
#                                 max(L),int(np.mean(L)),key=_wk())
#        
#        mean_min = st.sidebar.number_input('Valor mínimo del centro',\
#                                           value=mean-5,key=_wk())
#        mean_max = st.sidebar.number_input('Valor máximo del centro',\
#                                           value=mean+5,key=_wk())
#        
#        #fwhm
#        
#        fwhm = st.sidebar.slider('FWHM de la lorentziana (km/s)',\
#                                   value=2000.0,min_value=0.0,max_value=30000.0,\
#                                   step=0.01,key=_wk())
#        
#        fwhm_min = st.sidebar.number_input('Mínimo de FWHM',key=_wk())
#        fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=30000,key=_wk())
        
        
        if parametros_bool == 'No':
            
        
            #amplitude
            
            amplitude = st.sidebar.slider('Amplitud de la lorentziana:',\
                                          min(data-cont_),max(data-cont_),\
                                          np.mean(data-cont_),key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',\
                                              value=max(data-cont_),key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la lorentziana:',float(min(L)),\
                                     float(max(L)),float(np.mean(L)),key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=mean-5,key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=mean+5,key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la lorentziana (km/s)',\
                                       value=2000.0,min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=30000,key=_wk())
            
        if parametros_bool == 'Sí':
            
        
            #amplitude
            
            amplitude = st.sidebar.slider('Amplitud de la lorentziana:',\
                                          min(data-cont_),max(data-cont_),\
                                          table_l['amplitude'][j],key=_wk())
    
            amp_min = st.sidebar.number_input('Mínimo de amplitud',value=table_l['amin'][j],key=_wk())
            amp_max = st.sidebar.number_input('Máximo de amplitud',\
                                              value=table_l['amax'][j],key=_wk())
            
            
            #centro
            mean = st.sidebar.slider('Centro de la lorentziana:',float(min(L)),\
                                     float(max(L)),table_l['center'][j],key=_wk())
            
            mean_min = st.sidebar.number_input('Valor mínimo del centro',\
                                               value=table_l['cmin'][j],key=_wk())
            mean_max = st.sidebar.number_input('Valor máximo del centro',\
                                               value=table_l['cmax'][j],key=_wk())
            
            #fwhm
    
            fwhm = st.sidebar.slider('FWHM de la lorentziana (km/s)',\
                                       value=table_l['fwhm'][j],min_value=0.0,max_value=30000.0,\
                                       step=0.01,key=_wk())
            
            fwhm_min = st.sidebar.number_input('Mínimo de FWHM',value=table_l['fmin'][j],key=_wk())
            fwhm_max = st.sidebar.number_input('Máximo de FWHM',value=table_l['fmax'][j],key=_wk())
        
        
        #models
        
        lorentzians_aj.append(models.Lorentz1D(amplitude,mean,kmstoangs(fwhm,mean,mode='l'),\
                                bounds={'amplitude':[amp_min,amp_max],\
                                        'x_0':[mean_min,mean_max],\
                               'fwhm':[kmstoangs(fwhm_min,mean,mode='l'),\
                                         kmstoangs(fwhm_max,mean,mode='l')]}))
        
                
        lorentzians.append(models.Lorentz1D(amplitude,mean,kmstoangs(fwhm,mean,mode='l')))
    
    
    #Espectro con componentes sin ajustar
    
    models_ = lorentzians[0]
    models_aj = lorentzians_aj[0]
    
    all_lorentzians = []
    header_lorentz=''
    
        
    if num_lorentz > 1:
        for k in range(num_lorentz):
            if k+1 <= range(num_lorentz)[-1]:
                models_ = models_ + lorentzians[k+1]
                models_aj = models_aj + lorentzians_aj[k+1]
            else:
                break
        
    st.info('Los parámetros pueden ser manipulados en la barra lateral.')
    
    fig_ = plt.figure()
    plt.plot(lamb_,flux_,label=None)
    
    ESPECTRO = go.Scatter(x=lamb_,y=flux_,name='Espectro')
    
    if checkbox_temphierro == True:
        
                      
        if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
            or rango_hierro == '4000-7000 Angstroms':
            
            plt.plot(L,init_modelHierro(L))
            
            models_aj = models_aj + init_modelHierro
            models_ = models_ + init_modelHierro
            
        
        if rango_hierro == '4000-5500 Angstroms (Multiple components)':
            
            plt.plot(L,init_modelHierro_f(L))
            
            models_aj = models_aj + init_modelHierro_f
            models_ = models_ + init_modelHierro_f
            
            
            plt.plot(L,init_modelHierro_g(L))
            
            models_aj = models_aj + init_modelHierro_g
            models_ = models_ + init_modelHierro_g
            
            
            plt.plot(L,init_modelHierro_s(L))
            
            models_aj = models_aj + init_modelHierro_s
            models_ = models_ + init_modelHierro_s
            
            
            plt.plot(L,init_modelHierro_p(L))
            
            models_aj = models_aj + init_modelHierro_p
            models_ = models_ + init_modelHierro_p
            
            
            plt.plot(L,init_modelHierro_Zw(L))
            
            models_aj = models_aj + init_modelHierro_Zw
            models_ = models_ + init_modelHierro_Zw
            
            
    
    plt.plot(lamb_,models_(L),label=None,c='k')
    
    MODELO = go.Scatter(x=L,y=models_(L),name='Modelo')
    
    ESPMOD = [ESPECTRO,MODELO]
    
    PLOTS_L = []
    
    for j in range(len(lorentzians)):
        plt.plot(L,lorentzians[j](L),label='Lorentziana '+str(j+1))
        PLOTS_L.append(go.Scatter(x=L,y=lorentzians[j](L),name='Lorentziana '+str(j+1)))
                
        all_lorentzians.append(lorentzians[j](L))
        header_lorentz = header_lorentz + 'Lorentziana '+str(j+1)+'   '
    
    plt.xlabel('Longitud de onda (Angstroms)')
    plt.ylabel('Flujo normalizado')
    plt.legend()
    
    fig = go.Figure(ESPMOD+PLOTS_L)
    
    if checkbox_temphierro == True:
        
        if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
            or rango_hierro == '4000-7000 Angstroms':
        
            plotHierro = go.Scatter(x=L,y=init_modelHierro(L),name='Template Fe II')
            fig.add_trace(plotHierro)
            
        
        if rango_hierro == '4000-5500 Angstroms (Multiple components)':
            
            plotHierro_f = go.Scatter(x=L,y=init_modelHierro_f(L),name='Fe II - F group')
            fig.add_trace(plotHierro_f)
            
            plotHierro_g = go.Scatter(x=L,y=init_modelHierro_g(L),name='Fe II - G group')
            fig.add_trace(plotHierro_g)
            
            plotHierro_s = go.Scatter(x=L,y=init_modelHierro_s(L),name='Fe II - S group')
            fig.add_trace(plotHierro_s)
            
            plotHierro_p = go.Scatter(x=L,y=init_modelHierro_p(L),name='Fe II - P group')
            fig.add_trace(plotHierro_p)
            
            plotHierro_Zw = go.Scatter(x=L,y=init_modelHierro_Zw(L),name='Fe II - I Zw 1')
            fig.add_trace(plotHierro_Zw)
            
    
    fig.update_layout(xaxis_title='Longitud de onda (Angstroms)',yaxis_title='Flujo normalizado',\
                      width=700,height=800)
     
        
    st.plotly_chart(fig)
    
    export = np.array([L,data,cont_,flux_,models_(L)])
    
    full_export = np.concatenate((export,all_lorentzians)).T
    

# Un template de Fe II por sí solo no define models_aj en los rangos de una
# sola plantilla (1435-2033, 2200-3400, 4000-7000): hace falta al menos una
# gaussiana o lorentziana. Antes eso terminaba en NameError justo al ajustar.
if 'models_aj' not in dir():
    st.error('No hay modelo que ajustar: añade al menos una gaussiana o una '
             'lorentziana además del template de Fe II.')
    st.stop()

full_aj = st.radio('Desea que el programa encuentre el mejor ajuste tomando \
los parámetros iniciales y los límites introducidos:',('Sí','No, dejar parámetros iniciales seleccionados fijos'))



if full_aj == 'Sí':
    
    fullfit_window = st.radio('¿Desea especificar un rango en el cual se llevará acabo el ajuste?',\
                              ('No, se ajustará todo el espectro','Sí'))
    
    if fullfit_window != 'Sí':
        fullmodel = fit_lines(spec_,models_aj)
        
    if fullfit_window == 'Sí':
        min_window_ff = st.number_input('Mínimo:',key=_wk(),value=min(L),min_value=min(L),max_value=max(L))
        max_window_ff = st.number_input('Máximo:',key=_wk(),value=max(L),min_value=min(L),max_value=max(L))
        
        fullmodel = fit_lines(spec_,models_aj,\
                window=SpectralRegion(min_window_ff*u.AA,max_window_ff*u.AA))
    
    st.success('Ajuste completado.')
    
    param_file = st.radio('Desea que los parámetros encontrados sean guardados \
                          automáticamente en un archivo de texto:',\
                              ('No','Sí'))
    
    if param_file == 'Sí':
        import datetime
        

        
        date_time = datetime.datetime.now()
        
        pf = open(distintivo+'_params.txt','a')
        
        
        pf.write('\n\n'+str(date_time))
    
    st.markdown('## Ajuste final')
        
    params = np.transpose(fullmodel.param_sets)[0]   #Parámetros de salida del ajuste
    
    # st.write(params)
    
    st.write('Fueron encontrados los siguientes valores para las parámetros:')        
        
    if checkbox_gauss == True and checkbox_lorentz == True:
            
        full_gaussians=[]
        full_lorentzians=[]
        
        for x in range(num_gauss):
            
            full_gaussians.append(models.Gaussian1D(amplitude=params[3*x],\
                                                           mean=params[(3*x)+1],\
                                                           stddev=params[(3*x)+2]))
            
            st.write('Gaussiana '+str(x+1),': Amplitud:',np.round(params[3*x],3),\
                     'Centro:',np.round(params[(3*x)+1],3),\
                     'FWHM (km/s):',np.round(angstokms(np.round(params[(3*x)+2],3),\
                                           np.round(params[(3*x)+1],3)),3))
                
            if param_file == 'Sí':
                
                pf.write('\nGaussiana '+str(x+1)+': Amplitud: '+str(np.round(params[3*x],3))+\
                     ' Centro: '+str(np.round(params[(3*x)+1],3))+\
                     ' FWHM (km/s): '+str(np.round(angstokms(np.round(params[(3*x)+2],3),\
                                           np.round(params[(3*x)+1],3)),3)))
            
        for y in range(num_lorentz):
            
            full_lorentzians.append(models.Lorentz1D(params[3*(num_gauss+y)],\
                                                           params[(3*(num_gauss+y))+1],\
                                                           params[(3*(num_gauss+y))+2]))
            
            st.write('Lorentziana '+str(y+1),': Amplitud:',np.round(params[3*(num_gauss+y)],3)\
                            ,'Centro:',np.round(params[(3*(num_gauss+y))+1],3),\
                            'FWHM (km/s):',np.round(angstokms(np.round(params[(3*(num_gauss+y))+2],3),\
                                   np.round(params[(3*(num_gauss+y))+1],3),mode='l'),3))
            
            if param_file == 'Sí':
                
                pf.write('\nLorentziana '+str(y+1)+': Amplitud: '+str(np.round(params[3*(num_gauss+y)],3))\
                                +' Centro: '+str(np.round(params[(3*(num_gauss+y))+1],3))+\
                                ' FWHM (km/s): '+str(np.round(angstokms(np.round(params[(3*(num_gauss+y))+2],3),\
                                       np.round(params[(3*(num_gauss+y))+1],3),mode='l'),3)))
                   
        
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
            
                final_hierro = modelHierro(params[-3],params[-2],params[-1])
                
                st.write('Temp. Hierro: Amplitud: ',np.round(params[-3],3),\
                         'Suavizado: ',params[-2],\
                         'Desplazamiento: ',np.round(params[-1],3))
                
                if param_file == 'Sí':
                    pf.write('\nTemp. Hierro: Amplitud: '+str(np.round(params[-3],3))+\
                         ' Suavizado: '+str(params[-2])+' Desplazamiento: '+str(np.round(params[-1],3)))
                        
            
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                st.write('Fe II Template: Ancho Doppler:',hierro_smooth_)
                if param_file == 'Sí':
                    pf.write('\nFe II Template: Ancho Doppler: '+str(hierro_smooth_))
                
                
                final_hierro_f = modelHierro_f(params[-10],params[-9])
                
                st.write('Fe II - Grupo F: Amplitud: ',np.round(params[-10],3),\
                         'Desplazamiento: ',np.round(params[-9],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo F: Amplitud: '+str(np.round(params[-10],3))+\
                         ' Desplazamiento: '+str(np.round(params[-9],3)))
                        
                
                final_hierro_g = modelHierro_g(params[-8],params[-7])
                
                st.write('Fe II - Grupo G: Amplitud: ',np.round(params[-8],3),\
                         'Desplazamiento: ',np.round(params[-7],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo G: Amplitud: '+str(np.round(params[-8],3))+\
                         ' Desplazamiento: '+str(np.round(params[-7],3)))
                        
                        
                final_hierro_s = modelHierro_s(params[-6],params[-5])
                
                st.write('Fe II - Grupo S: Amplitud: ',np.round(params[-6],3),\
                         'Desplazamiento: ',np.round(params[-5],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo S: Amplitud: '+str(np.round(params[-6],3))+\
                         ' Desplazamiento: '+str(np.round(params[-5],3)))
                        
                        
                final_hierro_p = modelHierro_p(params[-4],params[-3])
                
                st.write('Fe II - Grupo P: Amplitud: ',np.round(params[-4],3),\
                         'Desplazamiento: ',np.round(params[-3],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo P: Amplitud: '+str(np.round(params[-4],3))+\
                         ' Desplazamiento: '+str(np.round(params[-3],3)))
                        
                
                final_hierro_Zw = modelHierro_Zw(params[-2],params[-1])
                
                st.write('Fe II - I Zw 1: Amplitud: ',np.round(params[-2],3),\
                         'Desplazamiento: ',np.round(params[-1],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - I Zw 1: Amplitud: '+str(np.round(params[-2],3))+\
                         ' Desplazamiento: '+str(np.round(params[-1],3)))
                
                
        
        fullfit = full_gaussians[0]
        
        all_comps = []
        header_comps=''
        
        for x in range(num_gauss-1):
            
            fullfit = fullfit + full_gaussians[x+1]
            
        for y in range(num_lorentz):
            
            fullfit = fullfit + full_lorentzians[y]
            
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
                
                fullfit = fullfit + final_hierro
                
                
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                fullfit = fullfit + final_hierro_f + final_hierro_g + final_hierro_s\
                    + final_hierro_p + final_hierro_Zw
            
        fig_ = plt.figure()
        plt.plot(lamb_,flux_,label=None)
        plt.plot(lamb_,fullfit(L),c='k')
        
        fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2])
        
        ESPECTRO = go.Scatter(x=lamb_,y=flux_,name='Espectro')
        fig.add_trace(ESPECTRO,row=1,col=1)
        
        MODELO = go.Scatter(x=lamb_,y=fullfit(L),name='Modelo')
        fig.add_trace(MODELO,row=1,col=1)
        
        res = np.array(flux_).byteswap().newbyteorder()-np.array(fullfit(L)).byteswap().newbyteorder()
        RESIDUO = go.Scatter(x=lamb_,y=res,\
                             name='Residuo')
        fig.add_trace(RESIDUO,row=2, col=1)
        
        ESPMOD = [ESPECTRO,MODELO]
        
        PLOTS_G,PLOTS_L = [],[]
        
        for i in range(len(full_gaussians)):
            plt.plot(L,full_gaussians[i](L),label='Gaussiana '+str(i+1))
            fig.add_trace(go.Scatter(x=L,y=full_gaussians[i](L),\
                                     name='Gaussiana '+str(i+1)),row=1,col=1)
                
            all_comps.append(full_gaussians[i](L))
            header_comps = header_comps + 'Gaussiana'+str(i+1)+'   '
        
        for j in range(len(full_lorentzians)):
            plt.plot(L,full_lorentzians[j](L),label='Lorentziana '+str(j+1))
            fig.add_trace(go.Scatter(x=L,y=full_lorentzians[j](L),\
                                      name='Lorentziana'+str(j+1)),row=1,col=1)
            
            all_comps.append(full_lorentzians[j](L))
            header_comps = header_comps + 'Lorentziana'+str(j+1)+'   '
        
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
                
            
                plt.plot(L,final_hierro(L),label='Template Fe II')
                fig.add_trace(go.Scatter(x=L,y=final_hierro(L),name='Template Fe II'),\
                              row=1,col=1)
                
                all_comps.append(final_hierro(L))
                header_comps = header_comps + 'FeII'
                
            
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                plt.plot(L,final_hierro_f(L),label='Fe II - F group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_f(L),name='Fe II - F group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_g(L),label='Fe II - G group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_g(L),name='Fe II - G group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_s(L),label='Fe II - S group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_s(L),name='Fe II - S group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_p(L),label='Fe II - P group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_p(L),name='Fe II - P group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_Zw(L),label='Fe II - I Zw 1')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_Zw(L),name='Fe II - I Zw 1'),\
                              row=1,col=1)
                    
                    
                
                all_comps.append(final_hierro_f(L))
                header_comps = header_comps + 'FeII_F'
                
                all_comps.append(final_hierro_g(L))
                header_comps = header_comps + 'FeII_G'
                
                all_comps.append(final_hierro_s(L))
                header_comps = header_comps + 'FeII_S'
                
                all_comps.append(final_hierro_p(L))
                header_comps = header_comps + 'FeII_P'
                
                all_comps.append(final_hierro_Zw(L))
                header_comps = header_comps + 'FeII_Zw'
                
            
        
        
        plt.xlabel('Longitud de onda (Angstroms)')
        plt.ylabel('Flujo normalizado')
        plt.legend()
        
        
        fig.update_layout(xaxis_title='Longitud de onda (Angstroms)',\
                          yaxis_title='Flujo normalizado',width=700,height=800)
        
            
        st.plotly_chart(fig)
        
        export = np.array([L,data,cont_,flux_,fullfit(L)])
    
        full_export = np.concatenate((export,all_comps)).T
    
            
    if checkbox_gauss == True and checkbox_lorentz == False:
        
        # st.write(params)
        
        full_gaussians=[]
                
        for x in range(num_gauss):
            
            full_gaussians.append(models.Gaussian1D(amplitude=params[3*x],\
                                                           mean=params[(3*x)+1],\
                                                           stddev=params[(3*x)+2]))
            
            st.write('Gaussiana '+str(x+1),': Amplitud:',np.round(params[3*x],3),\
                     'Centro:',np.round(params[(3*x)+1],3),\
                     'FWHM (km/s):',np.round(angstokms(np.round(params[(3*x)+2],3),np.round(params[(3*x)+1],3)),3))
            
            if param_file == 'Sí':
                
                pf.write('\nGaussiana '+str(x+1)+': Amplitud: '+str(np.round(params[3*x],3))+\
                     ' Centro: '+str(np.round(params[(3*x)+1],3))+\
                     ' FWHM (km/s): '+str(np.round(angstokms(np.round(params[(3*x)+2],3),\
                                           np.round(params[(3*x)+1],3)),3)))
                
        
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
            
                final_hierro = modelHierro(params[-3],params[-2],params[-1])
                
                st.write('Temp. Hierro: Amplitud: ',np.round(params[-3],3),\
                         'Suavizado: ',params[-2],\
                         'Desplazamiento: ',np.round(params[-1],3))
                
                if param_file == 'Sí':
                    pf.write('\nTemp. Hierro: Amplitud: '+str(np.round(params[-3],3))+\
                         ' Suavizado: '+str(params[-2])+' Desplazamiento: '+str(np.round(params[-1],3)))
                        
            
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                st.write('Fe II Template: Ancho Doppler:',hierro_smooth_)
                if param_file == 'Sí':
                    pf.write('\nFe II Template: Ancho Doppler: '+str(hierro_smooth_))
                
                
                final_hierro_f = modelHierro_f(params[-15],params[-14],params[-13])
                
                st.write('Fe II - Grupo F: Amplitud: ',np.round(params[-15],3),\
                         'Desplazamiento: ',np.round(params[-14],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo F: Amplitud: '+str(np.round(params[-15],3))+\
                         ' Desplazamiento: '+str(np.round(params[-14],3)))
                        
                
                final_hierro_g = modelHierro_g(params[-12],params[-11],params[-10])
                
                st.write('Fe II - Grupo G: Amplitud: ',np.round(params[-12],3),\
                         'Desplazamiento: ',np.round(params[-11],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo G: Amplitud: '+str(np.round(params[-12],3))+\
                         ' Desplazamiento: '+str(np.round(params[-11],3)))
                        
                        
                final_hierro_s = modelHierro_s(params[-9],params[-8],params[-7])
                
                st.write('Fe II - Grupo S: Amplitud: ',np.round(params[-9],3),\
                         'Desplazamiento: ',np.round(params[-8],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo S: Amplitud: '+str(np.round(params[-9],3))+\
                         ' Desplazamiento: '+str(np.round(params[-8],3)))
                        
                        
                final_hierro_p = modelHierro_p(params[-6],params[-5],params[-4])
                
                st.write('Fe II - Grupo P: Amplitud: ',np.round(params[-6],3),\
                         'Desplazamiento: ',np.round(params[-5],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo P: Amplitud: '+str(np.round(params[-6],3))+\
                         ' Desplazamiento: '+str(np.round(params[-5],3)))
                        
                
                final_hierro_Zw = modelHierro_Zw(params[-3],params[-2],params[-1])
                
                st.write('Fe II - I Zw 1: Amplitud: ',np.round(params[-3],3),\
                         'Desplazamiento: ',np.round(params[-2],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - I Zw 1: Amplitud: '+str(np.round(params[-3],3))+\
                         ' Desplazamiento: '+str(np.round(params[-2],3)))
        
        
        fullfit = full_gaussians[0]
        
        all_gaussians = []
        header_gauss=''
        
        for x in range(num_gauss-1):
            
            fullfit = fullfit + full_gaussians[x+1]
            
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
                
                fullfit = fullfit + final_hierro
                
                
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                fullfit = fullfit + final_hierro_f + final_hierro_g + final_hierro_s\
                    + final_hierro_p + final_hierro_Zw

            
        fig_ = plt.figure()
        plt.plot(lamb_,flux_,label=None)
        plt.plot(lamb_,fullfit(L),c='k')
        
        fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2])
        
        ESPECTRO = go.Scatter(x=lamb_,y=flux_,name='Espectro')
        fig.add_trace(ESPECTRO,row=1,col=1)
        
        MODELO = go.Scatter(x=lamb_,y=fullfit(L),name='Modelo')
        fig.add_trace(MODELO,row=1,col=1)
        
        res = np.array(flux_).byteswap().newbyteorder()-np.array(fullfit(L)).byteswap().newbyteorder()
        RESIDUO = go.Scatter(x=lamb_,y=res,\
                             name='Residuo')
        fig.add_trace(RESIDUO,row=2, col=1)
            
        ESPMOD = [ESPECTRO,MODELO]
        
        PLOTS_G = []
        
        for i in range(len(full_gaussians)):
            plt.plot(L,full_gaussians[i](L),label='Gaussiana '+str(i+1))
            fig.add_trace(go.Scatter(x=L,y=full_gaussians[i](L),\
                                     name='Gaussiana '+str(i+1)),row=1,col=1)
            
            all_gaussians.append(full_gaussians[i](L))
            header_gauss = header_gauss + 'Gaussiana'+str(i+1)+'   '
        
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
                
            
                plt.plot(L,final_hierro(L),label='Template Fe II')
                fig.add_trace(go.Scatter(x=L,y=final_hierro(L),name='Template Fe II'),\
                              row=1,col=1)
                
                all_gaussians.append(final_hierro(L))
                header_gauss = header_gauss + 'FeII'
                
            
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                plt.plot(L,final_hierro_f(L),label='Fe II - F group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_f(L),name='Fe II - F group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_g(L),label='Fe II - G group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_g(L),name='Fe II - G group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_s(L),label='Fe II - S group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_s(L),name='Fe II - S group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_p(L),label='Fe II - P group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_p(L),name='Fe II - P group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_Zw(L),label='Fe II - I Zw 1')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_Zw(L),name='Fe II - I Zw 1'),\
                              row=1,col=1)
                    
                    
                
                all_gaussians.append(final_hierro_f(L))
                header_gauss = header_gauss + 'FeII_F'
                
                all_gaussians.append(final_hierro_g(L))
                header_gauss = header_gauss + 'FeII_G'
                
                all_gaussians.append(final_hierro_s(L))
                header_gauss = header_gauss + 'FeII_S'
                
                all_gaussians.append(final_hierro_p(L))
                header_gauss = header_gauss + 'FeII_P'
                
                all_gaussians.append(final_hierro_Zw(L))
                header_gauss = header_gauss + 'FeII_Zw'
                
        plt.xlabel('Longitud de onda (Angstroms)')
        plt.ylabel('Flujo normalizado')
        plt.legend()
        
               
        fig.update_layout(xaxis_title='Longitud de onda (Angstroms)',\
                          yaxis_title='Flujo normalizado',width=700,height=800)
            
        st.plotly_chart(fig)
        
        export = np.array([L,data,cont_,flux_,fullfit(L)])
    
        full_export = np.concatenate((export,all_gaussians)).T
        
    if checkbox_gauss == False and checkbox_lorentz == True:
        
        
        full_lorentzians=[]
        
                    
        for y in range(num_lorentz):
            
            full_lorentzians.append(models.Lorentz1D(params[3*(y)],\
                                                           params[(3*(y))+1],\
                                                           params[(3*(y))+2]))
            
            st.write('Lorentziana '+str(y+1),': Amplitud:',np.round(params[3*(y)],3)\
                            ,'Centro:',np.round(params[(3*(y))+1],3),\
                            'FWHM (km/s):',np.round(angstokms(np.round(params[(3*(y))+2],3),\
                                   np.round(params[(3*(y))+1],3),mode='l'),3))
                
            if param_file == 'Sí':
                
                pf.write('\nLorentziana '+str(y+1)+': Amplitud: '+str(np.round(params[3*(y)],3))\
                                +' Centro: '+str(np.round(params[(3*(y))+1],3))+\
                                ' FWHM (km/s): '+str(np.round(angstokms(np.round(params[(3*(y))+2],3),\
                                       np.round(params[(3*(y))+1],3),mode='l'),3)))
        
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
            
                final_hierro = modelHierro(params[-3],params[-2],params[-1])
                
                st.write('Temp. Hierro: Amplitud: ',np.round(params[-3],3),\
                         'Suavizado: ',params[-2],\
                         'Desplazamiento: ',np.round(params[-1],3))
                
                if param_file == 'Sí':
                    pf.write('\nTemp. Hierro: Amplitud: '+str(np.round(params[-3],3))+\
                         ' Suavizado: '+str(params[-2])+' Desplazamiento: '+str(np.round(params[-1],3)))
                        
            
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                st.write('Fe II Template: Ancho Doppler:',hierro_smooth_)
                if param_file == 'Sí':
                    pf.write('\nFe II Template: Ancho Doppler: '+str(hierro_smooth_))
                
                
                final_hierro_f = modelHierro_f(params[-15],params[-14],params[-13])
                
                st.write('Fe II - Grupo F: Amplitud: ',np.round(params[-15],3),\
                         'Desplazamiento: ',np.round(params[-14],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo F: Amplitud: '+str(np.round(params[-15],3))+\
                         ' Desplazamiento: '+str(np.round(params[-14],3)))
                        
                
                final_hierro_g = modelHierro_g(params[-12],params[-11],params[-10])
                
                st.write('Fe II - Grupo G: Amplitud: ',np.round(params[-12],3),\
                         'Desplazamiento: ',np.round(params[-11],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo G: Amplitud: '+str(np.round(params[-12],3))+\
                         ' Desplazamiento: '+str(np.round(params[-11],3)))
                        
                        
                final_hierro_s = modelHierro_s(params[-9],params[-8],params[-7])
                
                st.write('Fe II - Grupo S: Amplitud: ',np.round(params[-9],3),\
                         'Desplazamiento: ',np.round(params[-8],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo S: Amplitud: '+str(np.round(params[-9],3))+\
                         ' Desplazamiento: '+str(np.round(params[-8],3)))
                        
                        
                final_hierro_p = modelHierro_p(params[-6],params[-5],params[-4])
                
                st.write('Fe II - Grupo P: Amplitud: ',np.round(params[-6],3),\
                         'Desplazamiento: ',np.round(params[-5],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - Grupo P: Amplitud: '+str(np.round(params[-6],3))+\
                         ' Desplazamiento: '+str(np.round(params[-5],3)))
                        
                
                final_hierro_Zw = modelHierro_Zw(params[-3],params[-2],params[-1])
                
                st.write('Fe II - I Zw 1: Amplitud: ',np.round(params[-3],3),\
                         'Desplazamiento: ',np.round(params[-2],3))
                
                if param_file == 'Sí':
                    pf.write('\nFe II - I Zw 1: Amplitud: '+str(np.round(params[-3],3))+\
                         ' Desplazamiento: '+str(np.round(params[-2],3)))
                    
        
        fullfit = full_lorentzians[0]
        
        all_lorentzians = []
        header_lorentz=''
        
        for x in range(num_lorentz-1):
            
            fullfit = fullfit + full_lorentzians[x+1]
        
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
                
                fullfit = fullfit + final_hierro
                
                
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                fullfit = fullfit + final_hierro_f + final_hierro_g + final_hierro_s\
                    + final_hierro_p + final_hierro_Zw   
        
                    
        fig_ = plt.figure()
        plt.plot(lamb_,flux_,label=None)
        plt.plot(lamb_,fullfit(L),c='k')
        
        fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2])
        
        ESPECTRO = go.Scatter(x=lamb_,y=flux_,name='Espectro')
        fig.add_trace(ESPECTRO,row=1,col=1)
        
        MODELO = go.Scatter(x=lamb_,y=fullfit(L),name='Modelo')
        fig.add_trace(MODELO,row=1,col=1)
        
        res = np.array(flux_).byteswap().newbyteorder()-np.array(fullfit(L)).byteswap().newbyteorder()
        RESIDUO = go.Scatter(x=lamb_,y=res,\
                             name='Residuo')
        fig.add_trace(RESIDUO,row=2, col=1)
        
        ESPMOD = [ESPECTRO,MODELO]
        
        PLOTS_L = []
        
        
        
        for j in range(len(full_lorentzians)):
            plt.plot(L,full_lorentzians[j](L),label='Lorentziana '+str(j+1))
            fig.add_trace(go.Scatter(x=L,y=full_lorentzians[j](L),\
                                      name='Lorentziana '+str(j+1)),row=1,col=1)
            
            all_lorentzians.append(full_lorentzians[j](L))
            header_lorentz = header_lorentz + 'Lorentziana'+str(j+1)+'   '
        
        if checkbox_temphierro == True:
            
            if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
                or rango_hierro == '4000-7000 Angstroms':
                
            
                plt.plot(L,final_hierro(L),label='Template Fe II')
                fig.add_trace(go.Scatter(x=L,y=final_hierro(L),name='Template Fe II'),\
                              row=1,col=1)
                
                all_lorentzians.append(final_hierro(L))
                header_lorentz = header_lorentz + 'FeII'
                
            
            if rango_hierro == '4000-5500 Angstroms (Multiple components)':
                
                plt.plot(L,final_hierro_f(L),label='Fe II - F group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_f(L),name='Fe II - F group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_g(L),label='Fe II - G group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_g(L),name='Fe II - G group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_s(L),label='Fe II - S group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_s(L),name='Fe II - S group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_p(L),label='Fe II - P group')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_p(L),name='Fe II - P group'),\
                              row=1,col=1)
                    
                plt.plot(L,final_hierro_Zw(L),label='Fe II - I Zw 1')
                fig.add_trace(go.Scatter(x=L,y=final_hierro_Zw(L),name='Fe II - I Zw 1'),\
                              row=1,col=1)
                    
                    
                
                all_lorentzians.append(final_hierro_f(L))
                header_lorentz = header_lorentz + 'FeII_F'
                
                all_lorentzians.append(final_hierro_g(L))
                header_lorentz = header_lorentz + 'FeII_G'
                
                all_lorentzians.append(final_hierro_s(L))
                header_lorentz = header_lorentz + 'FeII_S'
                
                all_lorentzians.append(final_hierro_p(L))
                header_lorentz = header_lorentz + 'FeII_P'
                
                all_lorentzians.append(final_hierro_Zw(L))
                header_lorentz = header_lorentz + 'FeII_Zw'
        
        
        plt.xlabel('Longitud de onda (Angstroms)')
        plt.ylabel('Flujo normalizado')
        plt.legend()
        
        
        fig.update_layout(xaxis_title='Longitud de onda (Angstroms)',\
                          yaxis_title='Flujo normalizado',width=700,height=800)
            
        st.plotly_chart(fig)
        
        export = np.array([L,data,cont_,flux_,fullfit(L)])
    
        full_export = np.concatenate((export,all_lorentzians)).T
    
    
    
    
    st.write(full_export)
    
    if param_file == 'Sí':
        pf.close()
        
    export_bool = st.radio('Desea exportar los resultados como archivo de texto:',\
            ('No','Sí'),key=2)
    if  export_bool== 'Sí':
        
            
        if checkbox_gauss == True and checkbox_lorentz == True:
            
            np.savetxt(distintivo+'_fit.txt',full_export,fmt='%10.6f',\
                                header='Lambda   Espectro   Continuo   EspectroSC   Ajuste   '\
                                +header_comps)
            fig_.set_size_inches([12,9])
            fig_.savefig(distintivo+'.pdf')
            export_bool='No'
        
        if checkbox_gauss == True and checkbox_lorentz == False:
            
            np.savetxt(distintivo+'_fit.txt',full_export,fmt='%10.6f',\
                                header='Lambda   Espectro   Continuo   EspectroSC   Ajuste   '\
                                +header_gauss)
            fig_.set_size_inches([12,9])
            fig_.savefig(distintivo+'.pdf')
            export_bool='No'
            
        if checkbox_gauss == False and checkbox_lorentz == True:
            
            np.savetxt(distintivo+'_fit.txt',full_export,fmt='%10.6f',\
                                header='Lambda   Espectro   Continuo   EspectroSC   Ajuste   '\
                                +header_lorentz)
            fig_.set_size_inches([12,9])
            fig_.savefig(distintivo+'.pdf')
            export_bool='No'
            
        st.success('Listo. Exportado a la carpeta donde se encuentra este programa.\
                    Lo encuentras como '+str(distintivo)+'_fit.txt y '+str(distintivo)+'.pdf')
    
        
        
if full_aj == 'No, dejar parámetros iniciales seleccionados fijos':
    
    st.warning('Ok. Ninguna optimización de parámetros fue realizada.')
    
    st.write(full_export)
    
    
    export_bool = st.radio('Desea exportar los resultados como archivo de texto:',\
            ('No','Sí'),key=3)
    if  export_bool== 'Sí':
        
            
        if checkbox_gauss == True and checkbox_lorentz == True:
            
            np.savetxt(distintivo+'_fit_manual.txt',full_export,fmt='%10.6f',\
                                header='Lambda   Espectro   Continuo   EspectroSC   Ajuste   '\
                                +header_comps)
            fig_.set_size_inches([12,9])
            fig_.savefig(distintivo+'_manual.pdf')
            export_bool=='No'
        
        if checkbox_gauss == True and checkbox_lorentz == False:
            
            np.savetxt(distintivo+'_fit_manual.txt',full_export,fmt='%10.6f',\
                                header='Lambda   Espectro   Continuo   EspectroSC   Ajuste   '\
                                +header_gauss)
            fig_.set_size_inches([12,9])
            fig_.savefig(distintivo+'_manual.pdf')
            export_bool='No'
            
        if checkbox_gauss == False and checkbox_lorentz == True:
            
            np.savetxt(distintivo+'_fit_manual.txt',full_export,fmt='%10.6f',\
                                header='Lambda   Espectro   Continuo   EspectroSC   Ajuste   '\
                                +header_lorentz)
            fig_.set_size_inches([12,9])
            fig_.savefig(distintivo+'_manual.pdf')
            export_bool='No'
            
        st.success('Listo. Exportado a la carpeta donde se encuentra este programa.\
                   Los encuentras como '+str(distintivo)+'_fit_manual.txt y '+str(distintivo)+'_manual.pdf')
    
    
st.warning('Sí vas a ajustar otro espectro con los mismos parámetros, selecciona primero "No" en exportar archivo.')
st.info('Para ajustar un espectro con otros parámetros, presiona "F5" en tu teclado o refresca la página y selecciona otro archivo')

        






