import os
import sys,shutil,datetime,time
import numpy as nu
import tkinter as tk
from tkinter import messagebox
print 'Version 20180908 JABIL Data Post Porcessing ...'
time.sleep(3)
date=str(datetime.date.today())
#os.chdir(r'D:\Share-Charles_lin@jabil.com\OneDrive - Jabil\Project\Utah\0830\JABIL QC script - Head Strap acoustic station')
Currentdir=os.getcwd()
os.chdir(Currentdir+r'\\Report')
#fatherpath=os.path.abspath(os.path.join(os.path.dirname('settings.py'),os.path.pardir))
fatherpath=Currentdir

ALL=os.listdir(os.getcwd())
for i in ALL:
    if r'MUTE' in i:
        continue
    if '_' not in i:
        SN=str(i)[:-4]
    else:
        pass
print SN
print ALL
if not os.path.isdir(fatherpath+r'\Log'):
    os.mkdir(fatherpath+r'\Log')
if not os.path.isdir(fatherpath+r'\Log\\'+date):
    os.mkdir(fatherpath+r'\Log\\'+date)
if not os.path.isdir(fatherpath+r'\postprocess'):
    os.mkdir(fatherpath+r'\postprocess')
for i in ALL:
    shutil.copy(i,fatherpath+r'\Log\\'+date)

def tolist(curve):
    curve=[round(i,2) for i in curve.tolist()]
    return curve
ST=''
ET=datetime.datetime.now()
#========Get start time 
if os.path.exists(fatherpath+r'\ST.txt') == True:
    f2=open(fatherpath+r'\ST.txt','r')
    ST=f2.read()
    f2.close()
    ET=datetime.datetime.now()

#=======================================================Result flag
f=open(SN+'.txt','r')
content=f.readlines()
ALL=[filter(None,str(i).strip('\n').split(' ')) for i in content]
LFR_F=ALL[1][1]
LPo_F=ALL[2][1]
LRB_F=ALL[3][1]
LTHD_F=ALL[4][1]
LSen_F=ALL[5][1]
LSen=ALL[5][0].strip('dBSPL').split(':')[1]
RFR_F=ALL[13][1]
RPo_F=ALL[14][1]
RRB_F=ALL[15][1]
RTHD_F=ALL[16][1]
RSen_F=ALL[17][1]
RSen=ALL[17][0].strip('dBSPL').split(':')[1]
Bal_F=ALL[25][1]
LBled_F=ALL[29][1]
RBled_F=ALL[33][1]

ALL_F=[SN]
for i in 1,2,3,4,5,13,14,15,16,17,25,29,33:
    ALL_F.append(ALL[i][1])

#Balance check =========================================
#date.replace(date.split('-')[-1],str(int(date.split('-')[-1])-1).zfill(2))
if os.path.exists(fatherpath+r'\BalanceLimit.txt') == True:
    f2=open(fatherpath+r'\BalanceLimit.txt','r')
    BL=f2.read()
    f2.close()
else:
    f2=open(fatherpath+r'\BalanceLimit.txt','w+')
    f2.write('6')
    BL='6'
    f2.close()    
if abs(float(LSen)-float(RSen))<=float(BL):
    ALL_F[-3]='GOOD'
else:
    ALL_F[-3]='BAD'


ALL_F.append(str(ST))
ALL_F.append(str(ET))
ALL_FN='SN,HA01_Right_FR,HA02_Right_Polarity,HA03_Right_RubBuzz,HA04_Right_THD,HA05_Right_Sensitivity,HA06_Left_FR,HA07_Left_Polarity,HA08_Left_RubBuzz,HA09_Left_THD,HA10_Left_Sensitivity,HA11_Balance,HA12_RightBleed,HA13_LeftBleed,StartTime,EndTime'
f.close()
FRfile=fatherpath+r'\postprocess\\'+'ResultFlagALL.txt'
if os.path.exists(FRfile) == True:
    r=open(FRfile,'a+')
else:
    r=open(FRfile,'a+')
    r.write(ALL_FN+'\n')
r.write(str(ALL_F).strip('[').strip(']').replace('\'','')+'\n')
r.close()


ALL_FN2=[i for i in ALL_FN.split(',')]
Dic_ALL={}
for i in range(len(ALL_FN2)):
    Dic_ALL[ALL_FN2[i]]=ALL_F[i]
    
print Dic_ALL

#========================Sensitivity ==========================
Sen_FN='SN\tSensitivity R\tSensitivity L\tBalance R-L'
FRfile=fatherpath+r'\postprocess\\'+'Sensitivity'+date+r'.txt'
if os.path.exists(FRfile) == True:
    r=open(FRfile,'a+')
else:
    r=open(FRfile,'a+')
    r.write(Sen_FN+'\n')
r.write(SN+'\t'+LSen+'\t'+RSen+'\t'+str(float(LSen)-float(RSen))+'\n')
r.close()


#========================= Name list ==========================
#Testitem={'R FR':'1','L FR':'3','BalanceRL':'5','R Bleed':'7','L Bleed':'9'}
Testitem={'R FR':'1','L FR':'3'}

for t in Testitem:
    #=======================================================L FR,THD,R&B
    f=open(SN+'_'+Testitem.get(t)+'.txt','r')
    content=f.readlines()
    ALL=[filter(None,str(i).strip('\n').split(' ')) for i in content] #SPL
    ALL=nu.array(ALL[1:]).astype(float)
    ALL=ALL.T
    Hz=tolist(ALL[0])
    SPL=tolist(ALL[1])
    print SPL
    #================== Add Name  =================
    NHz=['Hz']
    NSNP=[SN]
    NHz.extend(Hz)
    NSNP.extend(SPL)
    FRfile=fatherpath+r'\postprocess\\'+t+' '+date+r'.txt'
    if os.path.exists(FRfile) == True:
        r=open(FRfile,'a+')
    else:
        r=open(FRfile,'a+')
        r.write(str(NHz).strip('[').strip(']').replace('\'','').replace(',','\t')+'\n')
    #================== Write into file =================
    r.write(str(NSNP).strip('[').strip(']').replace('\'','').replace(',','\t')+'\n')
    r.close()
    if t in ('L FR','R FR'):
        THD=tolist(ALL[3])
        RB=tolist(ALL[4])
        #NHz=['Hz']
        NSNT=[SN]
        NSNR=[SN]
        NSNT.extend(THD)
        NSNR.extend(RB)
        for k in ('THD','RB'):
            if k == 'THD':
                FRfile=fatherpath+r'\postprocess\\'+t+' '+k+' '+date+r'.txt'
                if os.path.exists(FRfile) == True:
                    r=open(FRfile,'a+')
                else:
                    r=open(FRfile,'a+')
                    r.write(str(NHz).strip('[').strip(']').replace('\'','').replace(',','\t')+'\n')        
                r.write(str(NSNT).strip('[').strip(']').replace('\'','').replace(',','\t')+'\n')
            if k == 'RB':
                FRfile=fatherpath+r'\postprocess\\'+t+' '+k+' '+date+r'.txt'
                if os.path.exists(FRfile) == True:
                    r=open(FRfile,'a+')
                else:
                    r=open(FRfile,'a+')
                    r.write(str(NHz).strip('[').strip(']').replace('\'','').replace(',','\t')+'\n')        
                r.write(str(NSNR).strip('[').strip(']').replace('\'','').replace(',','\t')+'\n')           
            r.close()
        #Normalized FR&Correction FR==============================
        if t=='L FR':
            Correctionfile=fatherpath+r'\CorrectioncurveL.txt'
            if os.path.exists(Correctionfile) == True:
                f=open(Correctionfile,'r')
                content=f.readlines()
                Correc=[filter(None,str(i).strip('\n').split('\t')) for i in content] #SPL
                Correc=nu.array(Correc[1:]).astype(float)
                Correc=Correc.T
                #Correc=tolist(Correc[1])
                f.close()
            else:
                Correc=nu.array([0,0])
            CSPL=ALL[1]-Correc[1]            
            CSPL=CSPL-float(RSen)
        if t=='R FR':
            Correctionfile=fatherpath+r'\CorrectioncurveR.txt'
            if os.path.exists(Correctionfile) == True:
                f=open(Correctionfile,'r')
                content=f.readlines()
                Correc=[filter(None,str(i).strip('\n').split('\t')) for i in content] #SPL
                Correc=nu.array(Correc[1:]).astype(float)
                Correc=Correc.T
                #Correc=tolist(Correc[1])
                f.close()
            else:
                Correc=nu.array([0,0])
            CSPL=ALL[1]-Correc[1]                  
            CSPL=CSPL-float(LSen)
        print CSPL
        CSPL=tolist(CSPL)
        NCSPL=[SN]
        NCSPL.append(CSPL) 
        #Write file
        FRfile=fatherpath+r'\postprocess\\'+t+' NormalizedCorrection '+date+r'.txt'
        if os.path.exists(FRfile) == True:
            r=open(FRfile,'a+')
        else:
            r=open(FRfile,'a+')
            r.write(str(NHz).replace('[','').strip(']').replace('\'','').replace(',','\t')+'\n')        
        r.write(str(NCSPL).replace('[','').strip(']').replace('\'','').replace(',','\t')+'\n')        
        
    print NSNP
    f.close()



#=========== For Jabil test=============
FRfile=fatherpath+'\ResultFlag.txt'
r=open(FRfile,'w+')
r.write(ALL_FN+'\n')
r.write(str(ALL_F).strip('[').strip(']').replace('\'','')+'\n')
r.close()


#Show===================================
Result=[]
for i in Dic_ALL:
    if Dic_ALL[i] == 'BAD':
        Result.append(str(i)+':BAD')
if len(Result)==0:
    #tk.messagebox.showinfo(title='test', message=Result)
    w = tk.Tk()
    w.title('Test Result-Good')
    w['width']=600
    w['height']=600
    wT=tk.Text(w,width=600,font=("Helvetica",72))
    wT.configure(background='green')
    wT.place(width=600,height=600)
    wT.insert('0.0',r'     GOOD')
    w.after(8000, lambda: w.destroy()) # Destroy the widget after 30 seconds
    w.mainloop()        
else:
    Result.sort()
    Result='\n'.join(Result)
    w = tk.Tk()
    w.title('Test Result-Failed item')
    w['width']=600
    w['height']=600
    wT=tk.Text(w,width=600,font=("Helvetica",32))
    wT.configure(background='red')
    wT.place(width=600,height=600)
    wT.insert('0.0',Result)
    w.after(8000, lambda: w.destroy()) # Destroy the widget after 30 seconds
    w.mainloop()    
    tk.messagebox.showerror(title='Test Result-Failed item', message=str(Result))



