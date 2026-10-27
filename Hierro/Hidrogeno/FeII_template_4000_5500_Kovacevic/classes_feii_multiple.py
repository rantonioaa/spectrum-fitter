class modelHierro_f(Fittable1DModel):
            
    #[init,min,max,fixed]
    amp_f = [0.059,0.0,1.0,False]
    shift_f = [-3.91,-20,20,False]
    smooth_m = [1500,700,2800,True] #ONLY CHANGE THE FIRST VALUE/USE SAME VALUE FOR ALL GROUPS
    
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
    smooth_m = [1500,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
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
    smooth_m = [1500,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
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
    smooth_m = [1500,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
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
    smooth_m = [1500,700,2800,True] #ONLY CHANGE THE FIRST VALUE
    
    
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
