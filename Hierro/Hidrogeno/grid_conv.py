#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 18:21:04 2021

@author: rantonioaa
"""
from astropy.modeling import models
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from astroagn import lctools as lc
import scipy.signal as sig


template = pd.read_csv('FE_OPT_og.dat',delim_whitespace=True,names=['l','flux'])

fwhm_kms = np.arange(700,3100,100)


for i in range(len(fwhm_kms)):
    
    fwhm_angs = lc.kmstoangs(fwhm_kms[i], np.mean(template.l))
    
    g = models.Gaussian1D(amplitude=max(template.flux),\
                          mean=np.mean(template.l),\
                          stddev=lc.fwhmtosigma(fwhm_angs))
        
    gauss = g(template.l.values)
    
    new_temp = np.convolve(template.flux,gauss,mode='same')/sum(gauss)
    
    
    
    df_temp = pd.DataFrame({'l':template.l.values,'flux':new_temp})
    df_temp.to_csv('FE_OPT_'+str(i+1)+'.dat',sep=' ',index=False,header=None)
    
    # plt.plot(template.l,new_temp+fwhm_kms[i]-min(new_temp))
    
    
    



# print(max(template.flux))
# print(max(new_temp))
# plt.yticks(fwhm_kms)
# gaussian_test = sig.windows.gaussian(1001,10)
# print(gaussian_test)
# plt.plot(template.l,gauss)
# plt.plot(template.l,template.flux)
# plt.show()