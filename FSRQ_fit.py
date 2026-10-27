#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2026 R. Amaya-Almazán
"""
Created on Wed Jul  6 17:53:39 2022

@author: rantonioaa
"""

from astropy.io import fits
from astropy import units as u
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,\
                                   AutoMinorLocator)
from astropy.visualization import quantity_support
from specutils import Spectrum1D
from specutils.spectra import SpectralRegion
from specutils.fitting import fit_lines, fit_generic_continuum, fit_continuum
from astropy.modeling.powerlaws import PowerLaw1D
from astropy.modeling import models, custom_model
from astropy.modeling.tabular import Tabular1D, Tabular2D
from astropy.modeling import Fittable1DModel, Parameter
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from plotly.offline import init_notebook_mode, iplot

class modelHierroUVCIV(Fittable1DModel):
                
    #[init,min,max,fixed]

    hierro_amp = [0.01,0.0,0.1,False]
    hierro_smooth = [10,1,50,True] #ONLY CHANGE THE FIRST VALUE
    hierro_shift = [0,-20,20,False]
    
    amplitud = Parameter(default=hierro_amp[0],\
                         bounds=(hierro_amp[1],hierro_amp[2]),\
                             fixed=hierro_amp[3])
    smooth = Parameter(default=hierro_smooth[0],\
                       bounds=(hierro_smooth[1],hierro_smooth[2]),\
                           fixed=hierro_smooth[3])
    hierro_shift = Parameter(default=hierro_shift[0],\
                             bounds=(hierro_shift[1],hierro_shift[2]),\
                           fixed=hierro_shift[3])
        
    @staticmethod
    def evaluate(x,amplitud,smooth,shift):
        
        tempA = np.loadtxt('Hierro/Carbono/FE_UV_A'+str(int(smooth))+'.dat')
                     
                           
       
        return np.interp(x,tempA[:,0]+shift,amplitud*tempA[:,1])
    
    
class modelHierroUVMgII(Fittable1DModel):
                
    #[init,min,max,fixed]

    hierro_amp = [0.01,0.0,0.1,False]
    hierro_smooth = [10,1,50,True] #ONLY CHANGE THE FIRST VALUE
    hierro_shift = [0,-20,20,False]
    
    amplitud = Parameter(default=hierro_amp[0],\
                         bounds=(hierro_amp[1],hierro_amp[2]),\
                             fixed=hierro_amp[3])
    smooth = Parameter(default=hierro_smooth[0],\
                       bounds=(hierro_smooth[1],hierro_smooth[2]),\
                           fixed=hierro_smooth[3])
    hierro_shift = Parameter(default=hierro_shift[0],\
                             bounds=(hierro_shift[1],hierro_shift[2]),\
                           fixed=hierro_shift[3])
        
    @staticmethod
    def evaluate(x,amplitud,smooth,shift):
        
                           
        tempB = np.loadtxt('Hierro/Magnesio/FE_UV_B'+str(int(smooth))+'.dat')
            
        
        return np.interp(x,tempB[:,0]+shift,amplitud*tempB[:,1])


class modelHierroOPT(Fittable1DModel):
                
    #[init,min,max,fixed]

    hierro_amp = [0.1,0.0,1.0,False]
    hierro_smooth = [2500,700,3000,False] #ONLY CHANGE THE FIRST VALUE [700,3000]km/s
    hierro_shift = [0,-20,20,False]
    
    
    #DO NOT MODIFY--
    def width(y):
        return (y-600)/100
    hierro_smooth = [width(hierro_smooth[0]),width(hierro_smooth[1]),\
                     width(hierro_smooth[2]),hierro_smooth[3]]
    #--
    
    amplitud = Parameter(default=hierro_amp[0],\
                         bounds=(hierro_amp[1],hierro_amp[2]),\
                             fixed=hierro_amp[3])
    smooth = Parameter(default=hierro_smooth[0],\
                       bounds=(hierro_smooth[1],hierro_smooth[2]),\
                           fixed=hierro_smooth[3])
    hierro_shift = Parameter(default=hierro_shift[0],\
                             bounds=(hierro_shift[1],hierro_shift[2]),\
                           fixed=hierro_shift[3])
        
    @staticmethod
    def evaluate(x,amplitud,smooth,shift):
        
                    
        tempOPT = np.loadtxt('Hierro/Hidrogeno/FE_OPT_'+str(int(smooth))+'.dat')
            
        
        # hierroOPT = tempsOPT[int(smooth-1)]
       
        return np.interp(x,tempOPT[:,0]+shift,amplitud*tempOPT[:,1])

class modelHierro_f(Fittable1DModel):
            
    #[init,min,max,fixed]
    amp_f = [0.059,0.0,1.0,False]
    shift_f = [-3.91,-20,20,False]
    smooth_m = [1000,700,2800,True] #ONLY CHANGE THE FIRST VALUE/USE SAME VALUE FOR ALL GROUPS
    
    amplitud = Parameter(default=amp_f[0],\
                         bounds=(amp_f[1],amp_f[2]),\
                             fixed=amp_f[3])
    shift = Parameter(default=shift_f[0],\
                      bounds=(shift_f[1],shift_f[2]),\
                          fixed=shift_f[3])
    doppler = Parameter(default=smooth_m[0],\
                        bounds=(smooth_m[1],smooth_m[2]),\
                            fixed=smooth_m[3])
    
    @staticmethod
    def evaluate(x,amplitud,shift,doppler):
        
        
        tempOPT_f = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(int(doppler[0]))+'FeII/fe_f.txt')
          
        return np.interp(x,tempOPT_f[:,0]+shift,amplitud*tempOPT_f[:,1])
    
    
class modelHierro_g(Fittable1DModel):
    
    #[init,min,max,fixed]
    amp_g = [0.08,0.0,1.0,False]
    shift_g = [1.7,-20,20,False]
    smooth_m = [1000,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
    amplitud = Parameter(default=amp_g[0],\
                         bounds=(amp_g[1],amp_g[2]),\
                             fixed=amp_g[3])
    shift = Parameter(default=shift_g[0],\
                      bounds=(shift_g[1],shift_g[2]),\
                          fixed=shift_g[3])
    doppler = Parameter(default=smooth_m[0],\
                        bounds=(smooth_m[1],smooth_m[2]),\
                            fixed=smooth_m[3])
    
    @staticmethod
    def evaluate(x,amplitud,shift,doppler):
        
        
        
        tempOPT_g = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(int(doppler[0]))+'FeII/fe_g.txt')
            
          
        return np.interp(x,tempOPT_g[:,0]+shift,amplitud*tempOPT_g[:,1])
    

class modelHierro_s(Fittable1DModel):
    
    #[init,min,max,fixed]
    amp_s = [0.068,0.0,1.0,False]
    shift_s = [13.9,-20,20,False]
    smooth_m = [1000,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
    amplitud = Parameter(default=amp_s[0],\
                         bounds=(amp_s[1],amp_s[2]),\
                             fixed=amp_s[3])
    shift = Parameter(default=shift_s[0],\
                      bounds=(shift_s[1],shift_s[2]),\
                          fixed=shift_s[3])
    doppler = Parameter(default=smooth_m[0],\
                        bounds=(smooth_m[1],smooth_m[2]),\
                            fixed=smooth_m[3])
    
    @staticmethod
    def evaluate(x,amplitud,shift,doppler):
        
                    
        tempOPT_s = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(int(doppler[0]))+'FeII/fe_s.txt')
            
          
        return np.interp(x,tempOPT_s[:,0]+shift,amplitud*tempOPT_s[:,1])
    
    
class modelHierro_p(Fittable1DModel):
    
    #[init,min,max,fixed]
    amp_p = [0.054,0.0,1.0,True]
    shift_p = [5.6,-20,20,True]
    smooth_m = [1000,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
    amplitud = Parameter(default=amp_p[0],\
                         bounds=(amp_p[1],amp_p[2]),\
                             fixed=amp_p[3])
    shift = Parameter(default=shift_p[0],\
                      bounds=(shift_p[1],shift_p[2]),\
                          fixed=shift_p[3])
    doppler = Parameter(default=smooth_m[0],\
                        bounds=(smooth_m[1],smooth_m[2]),\
                            fixed=smooth_m[3])
    
    @staticmethod
    def evaluate(x,amplitud,shift,doppler):
        
        tempOPT_p = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(int(doppler[0]))+'FeII/fe_p.txt')
            
          
        return np.interp(x,tempOPT_p[:,0]+shift,amplitud*tempOPT_p[:,1])
    
    
class modelHierro_Zw(Fittable1DModel):
    
    #[init,min,max,fixed]
    amp_Zw = [0.071,0.0,1.0,False]
    shift_Zw = [-15,-20,20,False]
    smooth_m = [1000,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
    amplitud = Parameter(default=amp_Zw[0],\
                         bounds=(amp_Zw[1],amp_Zw[2]),\
                             fixed=amp_Zw[3])
    shift = Parameter(default=shift_Zw[0],\
                      bounds=(shift_Zw[1],shift_Zw[2]),\
                          fixed=shift_Zw[3])
    doppler = Parameter(default=smooth_m[0],\
                        bounds=(smooth_m[1],smooth_m[2]),\
                            fixed=smooth_m[3])
    
    @staticmethod
    def evaluate(x,amplitud,shift,doppler):
        
        tempOPT_Zw = np.loadtxt(\
                             'Hierro/Hidrogeno/FeII_template_4000_5500_Kovacevic/'\
                             +str(int(doppler[0]))+'FeII/fe_IZw1.txt')
            
          
        return np.interp(x,tempOPT_Zw[:,0]+shift,amplitud*tempOPT_Zw[:,1])


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
    



def Fit_Spec(L,FLUX,gaussians,inclContRegions=None,exclContRegions=None,hb_oiii=False,\
             feii_temp='4000-5500 Angstroms (Multiple components)',feii_params=None,\
             fit_window=None):
    
    lamb = L*u.AA
    flux = FLUX*u.Unit('erg cm-2 s-1 AA-1')
    
    spec = Spectrum1D(spectral_axis=lamb,flux=flux)
    
    
    ### Power-law
    
    amplitude = [np.mean(FLUX),min(FLUX),max(FLUX)]
    
    refpoint = [int(np.mean(L)),int(min(L)),int(max(L))]
    
    alpha = [1.0,0.0,3.0]
    
    cont_smooth = 0
    
    #### Fitting the model
    
    
    
    fitcont_model = fit_lines(spec,model=PowerLaw1D(amplitude=amplitude[0],\
                                                    x_0=refpoint[0],alpha=alpha[0],\
                                          bounds={'amplitude':amplitude[1:],\
                                                  'x_0':refpoint[1:],\
                                                  'alpha':alpha[1:]}),\
                                          window=inclContRegions)
    
    cont_params = np.transpose(fitcont_model.param_sets)[0]
    
    #### Fitting the model again!
    
    
    fitcont_model = fit_lines(spec,model=PowerLaw1D(amplitude=cont_params[0],\
                                    x_0=cont_params[1],alpha=cont_params[2],\
                                          bounds={'amplitude':amplitude[1:],\
                                                  'x_0':refpoint[1:],\
                                                  'alpha':alpha[1:]}),\
                                            exclude_regions=exclContRegions)
        
    #### Fitted continuum
    
    cont = fitcont_model(lamb)
    cont_ = np.array(cont)
    
    
    ### Spectrum without continuum
    
    new_flux = FLUX-cont_
    flux_ = new_flux*u.Unit('erg cm-2 s-1 AA-1')
    
    spec_ = Spectrum1D(spectral_axis=lamb,flux=flux_)
    
    ### Second model Continuum
    
    cont_params = np.transpose(fitcont_model.param_sets)[0]
    
    cont_powerlaw = PowerLaw1D(amplitude=cont_params[0],\
                               x_0=cont_params[1],alpha=cont_params[2],\
                               bounds={'amplitude':amplitude[1:],\
                                             'x_0':refpoint[1:],\
                                           'alpha':alpha[1:]})
    
        
    ### Gaussians or Lorentzians to fit the spectra
    
    g = []
    for i in range(len(gaussians)):
        
        mean_g1 = gaussians[i][0]
        amp_g1 = gaussians[i][1]
        fwhm_g1 = gaussians[i][2]
        
        g.append(models.Gaussian1D(amp_g1[0],mean_g1[0],kmstoangs(fwhm_g1[0],mean_g1[0],mode='g'),\
                           bounds={'amplitude':amp_g1[1:3],\
                                   'mean':mean_g1[1:3],\
                                    'stddev':[kmstoangs(fwhm_g1[1], mean_g1[0],mode='g'),\
                                              kmstoangs(fwhm_g1[2], mean_g1[0],mode='g')]}) )
        g[i].amplitude.fixed = amp_g1[3]
        g[i].mean.fixed = mean_g1[3]
        g[i].stddev.fixed = fwhm_g1[3]
        
                       
                
    
    
    
    
    if hb_oiii == True:
        
        ##### Constraints
        
        # FWHM tied 
        
        def tie_std(model):
            
            return model.stddev_3
        
        g[1].stddev.tied = tie_std
        g[2].stddev.tied = tie_std
        
        # Wavelength tied
        
        def tie_wave(model):
            
            return model.mean_3 * 4959/5007
            
        g[2].mean.tied = tie_wave
        
        # Amplitude tied
        
        def tie_amp(model):
            
            return model.amplitude_3 / 2.947
        
        g[2].amplitude.tied = tie_amp
    
    
    #### Lorentzian 1
    
    # amp_l1 = [0.5,0.0,max(FLUX-cont_)]
    # mean_l1 = [2798,2796,2800]
    # fwhm_l1 = [2000,1000,3000]
    
    
    # l1 = models.Gaussian1D(amp_l1[0],mean_l1[0],kmstoangs(fwhm_l1[0],mean_l1[0],mode='l'),\
    #                        bounds={'amplitude':amp_l1[1:],\
    #                                'x_0':mean_l1[1:],\
    #                                 'fwhm':[kmstoangs(fwhm_l1[1], mean_l1[0],mode='l'),\
    #                                           kmstoangs(fwhm_l1[2], mean_l1[0],mode='l')]})
    
    ##### Fix parameters - Uncomment the parameter to fix
    
    # l1.amplitude.fixed = True
    # l1.x_0.fixed = True
    # l1.fwhm.fixed = True
    
    ################### ADD MORE LORENTZIANS
    
    #### Full model before adding Fe II
    
    full_model = g[0]
    
    if len(g) > 1:
        
        for gaussian in g[1:]:
            full_model = full_model + gaussian
    
    
    
    #### Fe II Template
    
    # Select between these four options: '1435-2033 Angstroms', 
    # '2200-3400 Angstroms', '4000-7000 Angstroms',
    # '4000-5500 Angstroms (Multiple components)'
    
    
    
    rango_hierro = feii_temp
    
    
    
    if rango_hierro == '1435-2033 Angstroms' or rango_hierro == '2200-3400 Angstroms'\
        or rango_hierro == '4000-7000 Angstroms':

        
        if feii_params != None:
            
            amp_ = feii_params[0]
            shift_ = feii_params[1]
            smooth_ = feii_params[2]
            

        ## Model
        
        if rango_hierro == '1435-2033 Angstroms':
            
            
            if feii_params == None:
                
            
                amp_ = [0.01,0.0,0.1,False]
                smooth_ = [10,1,50,True] #ONLY CHANGE THE FIRST VALUE
                shift_ = [0,-20,20,False]
            
            init_modelHierro = modelHierroUVCIV(amp_[0],shift_[0],smooth_[0],\
                                             bounds={'amplitud':amp_[1:3],\
                                                     'shift':shift_[1:3],\
                                                     'doppler':smooth_[1:3]},\
                                             fixed={'amplitud':amp_[-1],\
                                                     'shift':shift_[-1],\
                                                     'doppler':smooth_[-1]})
            
            
        
        if rango_hierro == '2200-3400 Angstroms':
            
            if feii_params == None:
                
                amp_ = [0.01,0.0,0.1,False]
                smooth_ = [10,1,50,True] #ONLY CHANGE THE FIRST VALUE
                shift_ = [0,-20,20,False]
            
            init_modelHierro = modelHierroUVMgII(amp_[0],shift_[0],smooth_[0],\
                                             bounds={'amplitud':amp_[1:3],\
                                                     'shift':shift_[1:3],\
                                                     'doppler':smooth_[1:3]},\
                                             fixed={'amplitud':amp_[-1],\
                                                     'shift':shift_[-1],\
                                                     'doppler':smooth_[-1]})
                
        if rango_hierro == '4000-7000 Angstroms':
            
            if feii_params == None:
                
                amp_ = [0.01,0.0,0.1,False]
                smooth_ = [10,1,50,True] #ONLY CHANGE THE FIRST VALUE
                shift_ = [0,-20,20,False]
            
            init_modelHierro = modelHierroOPT(amp_[0],shift_[0],smooth_[0],\
                                             bounds={'amplitud':amp_[1:3],\
                                                     'shift':shift_[1:3],\
                                                     'doppler':smooth_[1:3]},\
                                             fixed={'amplitud':amp_[-1],\
                                                     'shift':shift_[-1],\
                                                     'doppler':smooth_[-1]})
            
            
        
        
        
        
        # Combining the template with the gaussians and/or lorentzians
        full_model = full_model + init_modelHierro
        
        
                
    if rango_hierro == '4000-5500 Angstroms (Multiple components)':
        
        
        #### Parameters initial values and bounds
        
        if feii_params == None:
            
            
            #[init,min,max,fixed]
            amp_f = [0.059,0.0,1.0,False]
            shift_f = [-3.91,-20,20,False]
            smooth_m = [2000,700,2800,False] #ONLY CHANGE THE FIRST VALUE/USES SAME VALUE FOR ALL GROUPS    
            
            amp_g = [0.08,0.0,1.0,False]
            shift_g = [1.7,-20,20,False]
            
            amp_s = [0.068,0.0,1.0,False]
            shift_s = [13.9,-20,20,False]
            
            amp_p = [0.054,0.0,1.0,True]
            shift_p = [5.6,-20,20,True]
            
            amp_Zw = [0.071,0.0,1.0,False]
            shift_Zw = [-15,-20,20,False]
            
        if feii_params != None:
            
            amp_f = feii_params[0][0]
            shift_f = feii_params[0][1]
            smooth_m = feii_params[0][2] #ONLY CHANGE THE FIRST VALUE/USES SAME VALUE FOR ALL GROUPS    
            
            amp_g = feii_params[1][0]
            shift_g = feii_params[1][1]
            
            amp_s = feii_params[2][0]
            shift_s = feii_params[2][1]
            
            amp_p = feii_params[3][0]
            shift_p = feii_params[3][1]
            
            amp_Zw = feii_params[4][0]
            shift_Zw = feii_params[4][1]
        
        ##### Model definition and constraints
        
        init_modelHierro_f = modelHierro_f(amp_f[0],shift_f[0],smooth_m[0],\
                                             bounds={'amplitud':amp_f[1:3],\
                                                     'shift':shift_f[1:3],\
                                                     'doppler':smooth_m[1:3]})
        
        init_modelHierro_g = modelHierro_g(amp_g[0],shift_g[0],smooth_m[0],\
                                             bounds={'amplitud':amp_g[1:3],\
                                                     'shift':shift_g[1:3],\
                                                     'doppler':smooth_m[1:3]})
            
        init_modelHierro_s = modelHierro_s(amp_s[0],shift_s[0],smooth_m[0],\
                                             bounds={'amplitud':amp_s[1:3],\
                                                     'shift':shift_s[1:3],\
                                                     'doppler':smooth_m[1:3]})
            
        init_modelHierro_p = modelHierro_p(amp_p[0],shift_p[0],smooth_m[0],\
                                             bounds={'amplitud':amp_p[1:3],\
                                                     'shift':shift_p[1:3],\
                                                     'doppler':smooth_m[1:3]})
        
        
        init_modelHierro_Zw = modelHierro_Zw(amp_Zw[0],shift_Zw[0],smooth_m[0],\
                                             bounds={'amplitud':amp_Zw[1:3],\
                                                     'shift':shift_Zw[1:3],\
                                                     'doppler':smooth_m[1:3]})
            
        ##### Constraints
        
        init_modelHierro_f.amplitud.fixed = amp_f[3]
        init_modelHierro_f.shift.fixed = shift_f[3]
        init_modelHierro_f.doppler.fixed = smooth_m[3]
        
        init_modelHierro_g.amplitud.fixed = amp_g[3]
        init_modelHierro_g.shift.fixed = shift_g[3]
        init_modelHierro_g.doppler.fixed = smooth_m[3]
        
        init_modelHierro_s.amplitud.fixed = amp_s[3]
        init_modelHierro_s.shift.fixed = shift_s[3]
        init_modelHierro_s.doppler.fixed = smooth_m[3]
        
        init_modelHierro_p.amplitud.fixed = amp_p[3]
        init_modelHierro_p.shift.fixed = shift_p[3]
        init_modelHierro_p.doppler.fixed = smooth_m[3]
        
        init_modelHierro_Zw.amplitud.fixed = amp_Zw[3]
        init_modelHierro_Zw.shift.fixed = shift_Zw[3]
        init_modelHierro_Zw.doppler.fixed = smooth_m[3]
        
        # Doppler broadening tied for all feii components
        
        def tie_doppler(model):
        
            return model.doppler_8
    
        init_modelHierro_g.doppler.tied = tie_doppler
        init_modelHierro_s.doppler.tied = tie_doppler
        init_modelHierro_p.doppler.tied = tie_doppler
        init_modelHierro_Zw.doppler.tied = tie_doppler
        
        # Full model
        
        model_hierros = init_modelHierro_f + init_modelHierro_g\
            + init_modelHierro_s + init_modelHierro_p + init_modelHierro_Zw
        
        full_model = full_model + model_hierros
            
    
    ### Fitting the model
    
    #Adding continuum fitting
    
    # full_model = full_model + cont_powerlaw
    
    #If needed a window for the fitting can be added
    # add the parameter: window=SpectralRegion(number1*u.AA,number2*u.AA)
    
    
    
    
    
    fitted_model = fit_lines(spec_, full_model,window=fit_window)
    
    print('Finished!')
    
    print(fitted_model)
    
    # Obtained parameters
    
    params = np.transpose(fitted_model.param_sets)[0]
    
    
    
    return fitted_model, params, cont_params
    



