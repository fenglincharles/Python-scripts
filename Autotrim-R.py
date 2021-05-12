# -*- coding: utf-8 -*
#
#Name: AMS 3435 ANC chip TrimBox Automation control validation
#Propouse:
                    #This script is creaded for setting up Automation OTP control for AMS 3435 chip through TrimBox
                    #Use regression Algorithm makes autotrim-R powerful on reaching best gain value with limited iteration
#
#Required HW:
                                #TrimBoxAS350X
                                #DUT with AMS3435 chip
                                #Acoustic Test fixtures( Ref Mic & Ref SPK & Acoustic Enviroment)
#Required SW:
                                #Soundcheck V12
                                #Python 2.7
#Required OS:
                                #Windows
#Creadted by: CL
#20180421 add "COM1" as param of TRIMUART for ANCtuningstat settup
#20180428 issue discovered: if set time.sleep 0.5 in trimbox run(line182), it will cause last two config loaded failed when run locadconfig. set 0.3 is ok. DUT is JBL
#20180512 Add main for Anc tuning station. fix 'e'command bug. about to use sys,argv
#20180522 Range(20) -> Rnage(16,21)
#20180604 adjust global variable and dataframe type
#0614 save as Autotrim.py
#0626update writecommand, update minusloop,update config-FFquickcheckdelta, update autotrimSN.txt at Soundchecklog
#0628update reverse action as iterationtime=0, fix getflag trivial, add333-342 to fix mic error
#0705remove activeburn flag on firsttime burn
#0717 change from Autotrim to Autotrim-R
#0720 Release formal version of regression autotrim program
#V0721 Startflag added for Jabil test
#V0722 open message for burn-bt
#V0722 default gain from 20 16.5 to D4FB D4FF
#0724 update curve plot to folder
#0724 update target goal to A-2Z, stimulas from 50Hz to 80hz
#0725 add FAflag 
#0802 add sleep on no-burn, fix typo  of regression limit check
#0803 add loadconfig at FAflag process, firstcheck go 20 16.5，update default value message
#0804 edit burnflag_L and R from "or" to "and"
#0808 edit d4 gain as the same as config
#0809 Add TypeError to check burn process
#0810 Update repeat command when gets error, off the following "i" command after burn
#0811 Dubug
#0826 Version 0826 Edit:\n 1,Slot L and R check \n2, SC folder \n3, LS argv function \n4,Jabiltest trimflag
#0911 version
#1224 add check file and check value every dump
Version='Version 0912 Edit:\n1,Slot L and R check \n2,SC folder \n3,LS argv function \n4,Jabiltest trimflag \n5,takeoff repeat on burn \n6,seperate LR burn\n7,Break down flag ANC On\n Version1227 Add default value check function'
import configparser
import pkgutil
import serial
from serial.serialutil import SerialBase, SerialException, to_bytes, portNotOpenError, writeTimeoutError
import time, datetime
#import socket
import os, sys
start = time.clock() #record processing time
date=datetime.date.today()
import xml.dom.minidom as xml
import datetime
import win32com.client
import logging
#import pandas as pd
from argparse import ArgumentParser
#===== Regression
from numpy import dot,transpose
from numpy.linalg import pinv
import numpy as nu
import matplotlib.pyplot as plt
#===== Regression end
print date
print Version
print '====================Jabil PD=========================== \n Autotrim-R is a python based software creaded for \n setting up Automation OTP control for AMS 3435 chip through TrimBox'
global ANCONcount,FB_L,FF_L,FB_R,FF_R,SideOKflag,port,Burnflag,Burnflag_L,Burnflag_R,processflag,Slotcount,G_D,FAflag,JabiltestN,JabiltestV
starttime=datetime.datetime.now()
G_D=[]
processflag=[]
port='COM3'
baudrate=38400
Burningbuffer=3
device='2' #Dual mode, two devices
path = r'C:\ANCFiles'
setiterationtime=5+1
stepunitgain=1
reverbuffergain=-1
activateburn='NO'
#Read ini doc
cf=configparser.ConfigParser()
os.chdir(r'C:\ANCFiles')
if os.getcwd()+r'\AutotrimMessage_and_Config\ANCautotrimconfig.ini':
    cf.read(os.getcwd()+r'\AutotrimMessage_and_Config\ANCautotrimconfig.ini')
    path=cf.get('Autotrim', 'ANCFilepath')
    SNfile=cf.get('Autotrim', 'SNfile')
    Autotrimflagfilepath=cf.get('Autotrim', 'Autotrimflagfilepath')
    AutotrimLogpath=cf.get('Autotrim', 'AutotrimLogpath')
    AutotrimMessagepath=path+r'\AutotrimMessage_and_Config'
    port=cf.get('Autotrim', 'TrimBoxPort')
    setiterationtime=int(cf.get('Autotrim', 'Setiterationtime'))
    testgain=float(cf.get('Autotrim', 'Testgain'))
    stepunitgain=float(cf.get('Autotrim', 'Stepunitgain'))
    reverbuffergain=float(cf.get('Autotrim', 'Reverbuffergain'))
    activateburn=cf.get('Autotrim', 'ActivateBurn')
    ActivateDefaultCheckBurn=cf.get('Autotrim', 'ActivateDefaultCheckBurn')
    FFquickcheckdelta=cf.get('Autotrim', 'FFquickcheckdelta')
    Tp=[int(i) for i in list(str(cf.get('Autotrim-R', 'TargetCurvepoint')).split(','))]
    setregressiontime=int(cf.get('Autotrim-R', 'Setregressiontimetime'))
    setG_D_L=int(cf.get('Autotrim-R', 'Firstpassdistance_L'))
    setG_D_R=int(cf.get('Autotrim-R', 'Firstpassdistance_R'))
    FAflag=cf.get('Autotrim-R','FAflag')


#Start flag for Jabiltest
f=open(Autotrimflagfilepath+'Startflag.txt','w')
f.write('Start'+'\n')
f.close()
raw_input('======= Auotrim-R is ready for the test process =======\n Press "Enter" to continue ....')
f=open(Autotrimflagfilepath+'Startflag.txt','w')
f.write('Go'+'\n')
f.close()

#Check the version : Retail or LS
if os.path.exists(Autotrimflagfilepath+'Modelflag.txt') == True:
    f5=open(Autotrimflagfilepath+'Modelflag.txt','r')
    Model=f5.read()
    f5.close()
else:
    raw_input( 'No product Config ! please check, click “ENTER" to use Retail version')
    Model='Retail'
if Model == 'Retail':
    SC_MSG_START=AutotrimMessagepath+r'\Autotrim-Message-Start.sqc'
    SC_MSG_BURN=AutotrimMessagepath+r'\Autotrim-Message-Burn.sqc'
    SC_MSG_NOBURN=AutotrimMessagepath+r'\Autotrim-Message-NoBurn.sqc'
    SC_MSG_BURN_BT=AutotrimMessagepath+r'\Autotrim-Message-Burn-BT.sqc'
    SC_MSG_NOBURN_BT=AutotrimMessagepath+r'\Autotrim-Message-NoBurn-BT.sqc'
    Trimbixconfigfile=AutotrimMessagepath+r'\config16dB20dBfromcustomerBranden.xoams'  
    trimboxvaluecheckfile=cf.get('Autotrim', 'Trimboxvaluecheckfile_Retail')
    print ' ================ Retail config mode ====================== '
elif Model == 'LS':
    SC_MSG_START=AutotrimMessagepath+r'\LS-Autotrim-Message-Start.sqc'
    SC_MSG_BURN=AutotrimMessagepath+r'\LS-Autotrim-Message-Burn.sqc'
    SC_MSG_NOBURN=AutotrimMessagepath+r'\LS-Autotrim-Message-NoBurn.sqc'
    SC_MSG_BURN_BT=AutotrimMessagepath+r'\LS-Autotrim-Message-Burn-BT.sqc'
    SC_MSG_NOBURN_BT=AutotrimMessagepath+r'\LS-Autotrim-Message-NoBurn-BT.sqc'
    Trimbixconfigfile=AutotrimMessagepath+r'\LS-config16dB20dBfromcustomerBranden.xoams'
    trimboxvaluecheckfile=cf.get('Autotrim', 'Trimboxvaluecheckfile_LS')
    print ' ================ LS config mode ====================== '
else:
    raw_input('Modelflag contains unrecognized text , click “ENTER" to use Retail version')
    SC_MSG_START=AutotrimMessagepath+r'\Autotrim-Message-Start.sqc'
    SC_MSG_BURN=AutotrimMessagepath+r'\Autotrim-Message-Burn.sqc'
    SC_MSG_NOBURN=AutotrimMessagepath+r'\Autotrim-Message-NoBurn.sqc'
    SC_MSG_BURN_BT=AutotrimMessagepath+r'\Autotrim-Message-Burn-BT.sqc'
    SC_MSG_NOBURN_BT=AutotrimMessagepath+r'\Autotrim-Message-NoBurn-BT.sqc'
    Trimbixconfigfile=AutotrimMessagepath+r'\config16dB20dBfromcustomerBranden.xoams'  
    trimboxvaluecheckfile=cf.get('Autotrim', 'Trimboxvaluecheckfile_Retail')
#os.remove(Autotrimflagfilepath+'Modelflag.txt')
#check value file
fc=open(trimboxvaluecheckfile)
checkvalue=fc.read()
checkvalue=checkvalue.replace('\r','').replace('\n','').replace('OTP register dump:','').replace(': ',':').split(' ')

fc.close()
#script
SC1=path+r'\SC1.sqc'
SC2=path+r'\SC2-LR.sqc'
SC3=path+r'\SC_clear_sn.sqc'
SC_LR=path+r'\Autotrim-LR.sqc'
SC_L=path+r'\Autotrim-L.sqc'
SC_R=path+r'\Autotrim-R.sqc'
#SC_BT=path+r'\Autotrim-BT+Limit.sqc'
SC_BT=path+r'\Autotrim-BT+Limit.sqc'
SC_PNI=path+r'\Autotrim-PNI.sqc'
SC_FANC=path+r'\Autotrim-FANC.sqc'
SC_LINE=path+r'\Autotrim-LINE.sqc'
#flag
#SC_CheckmicFlag=path+r'\AutotrimFlag-CheckmicFlag.txt'
SC_SideOkflag=path+r'\AutotrimFlag-SideOKflag.txt'
SC_Lmicflag=path+r'\AutotrimFlag-L.txt'
SC_Rmicflag=path+r'\AutotrimFlag-R.txt'
SC_DCurveflag=path+r'\AutotrimFlag-SideCurve.txt'
SC_Checkflag=path+r'\AutotrimFlag-Check.txt'
SC_TEMP=path+r'\temp.txt'
ANCONcount=1
Burnflag = 'NO'
Burnflag_L = 'NO'
Burnflag_R = 'NO'

#Read SN file
if os.path.exists(SNfile) == True:
    f2=open(SNfile,'r')
    SN=f2.read()
    f2.close()
    processflag.append(SN)
else:
    print 'SN file not exist'
    SN='NoneSN'
#Check folder
if not os.path.isdir(path):
    os.mkdir(path)
if not os.path.isdir(AutotrimLogpath):
    os.mkdir(AutotrimLogpath)
#set log
logger = logging.getLogger()  # 不加名称设置root logger
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
# 使用FileHandler输出到文件
fh = logging.FileHandler(AutotrimLogpath+'\\'+str(SN)+'-'+str(date)+'-'+'log.txt', mode='a')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
# 使用StreamHandler输出到屏幕
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
# 添加两个Handler
logger.addHandler(ch)
logger.addHandler(fh)

JabiltestN=['Intialize Trimbox','Burn Remain Times L','Burn Remain Times R',
            'Burn L','Burn R','ANC On','Default Performance L',
            'Default Performance R']
JabiltestV=['None' for i in range(8)]
def autotrim():
    global stepunitgain,Checkflag
    try: 
        #check SC and inform OP to power on ANC chip and plug in 3.5mm jack
        logging.info('autotrim-> This Mode is :'+str(Model))
        logging.info('autotrim -> Checking init ...')
        logging.info('autotrim -> '+ checkinit())       
        #Open Trimbox
        logging.info('autotrim -> Opening Trimbox ...')
        JabiltestV[JabiltestN.index('Intialize Trimbox')]='PASS'
        Tr=TRIMBOXuart(port)
        #Load config and define slotcount
        logging.info(Trimboxdefaultprocess(Tr))
        #Run PNI curve
        logging.info('autotrim -> openseqSC_PNI')
        openseq(SC_PNI)
        Passflag=autotrimpni(Tr)
        #Run ANC autotrim
        logging.info('autotrim -> openseqSC_LR')
        openseq(SC_LR)
        #Regression
        Autotrim_regression_process(Tr)
        logging.info('autotrim -> Runing limit ...')
        openseqflag=openseq(SC_BT)
        runflag=run()
        #logging.info('autotrim -> ANC station process complted')
        autotrimflag('Doneflag')
    except ValueError: #trimbox run err
        syserr=sys.exc_info()
        logging.info('Trim box run with ERR return'+str(syserr))
        autotrimflag('Doneflag',u'Trimbox run报错 ANC 無法連接 ,请确认产品与灰色音频音频线是否正确连结,并重新测试'+str(syserr))    
    except TypeError:
        syserr=sys.exc_info()
        logging.info('Trim box run with ERR return after burn process'+str(syserr))
        autotrimflag('Doneflag',u'Trimbox run Err '+str(syserr))            
    except SerialException:
        syserr=sys.exc_info()
        logging.info(r'COM port Err, plesae reset COM port.COM Port'+str(syserr))
        JabiltestV[JabiltestN.index('Intialize Trimbox')]='FAIL'
        autotrimflag('Doneflag',u'COM port 错误,请重新测试.如重复出现请告知现场TE做COM port检验,開GUI的UART setting做重置'+str(syserr))
    except SystemExit:  
        syserr=sys.exc_info()
        logging.info(r'ANC default performance not good, please check FF mic or FB mic solder'+str(syserr))
        autotrimflag('Doneflag',u'ANC default 表现失常 左:'+Checkflag[0]+u' 右:'+Checkflag[1]+u',请快速检验FF麦克风,如麦克风没问题则重新测试且确保产品放置正确') 
    except SyntaxError:
        syserr=sys.exc_info()
        logging.info(r'Trimbox與DUT 初始连结报错.'+str(syserr))
        autotrimflag('Doneflag',u'Trimbox與DUT 初始连结报错.'+str(syserr))         
    except:
        syserr=sys.exc_info()
        logging.info(r'ERR occur on autotrim process, Please check DUT! or Soundcheck software.'+str(syserr))
        autotrimflag('Doneflag',u'Autotrim 报错,请确认产品与灰色音频音频线是否正确连结,并重新测试'+str(syserr))
    finally:
        #SC3openseqflag=openseq(SC3)
        #SC3runflag=run()        
        logging.info(r'Trimbox close')
        Tr.close()
def autotrimpni(Tr):
    for i in (1,2):
        for j in ('30','31'):
            logging.info(Tr.run('w '+str(j)+r' 80 '+str(i)))
    runflag=run()
    logging.info(Tr.run('l 1'))
    logging.info(Tr.run('l 2'))
    return 0    
def Trimboxdefaultprocess(Tr):
    global ANCONcount,FB_L,FF_L,FB_R,FF_R,SideOKflag,SlotcountR,SlotcountL,processflag,JabiltestN,JabiltestV
    
    logging.info('Trimboxdefaultprocess -> loadconfig..')
    logging.info(Tr.run('d 1'))
    logging.info(Tr.run('d 2'))
    logging.info(Tr.run('l 1'))
    logging.info(Tr.run('l 2'))
    SlotcountL=int(Tr.run('s 1'))
    SlotcountR=int(Tr.run('s 2'))
    JabiltestV[JabiltestN.index('Burn Remain Times L')]=str(SlotcountL)
    JabiltestV[JabiltestN.index('Burn Remain Times R')]=str(SlotcountR)
    processflag.append(str(SlotcountL))
    processflag.append(str(SlotcountR))
    Ft=0
    if int(SlotcountL) == 3 :#and int(SlotcountR) == 3:
        logging.info('Trimboxdefaultprocess -> SlotcountL :'+str(SlotcountL))
        logging.info('Trimboxdefaultprocess -> SlotcountR :'+str(SlotcountR))
        logging.info(Tr.Loadconfig('1'))
        logging.info(Tr.Loadconfig('2'))
        logging.info('Trimboxdefaultprocess -> Start default burn L and R')
        logging.info(Tr.run('d 1'))
        logging.info(Tr.run('d 2'))
        logging.info(Tr.run('b 1',2))
        JabiltestV[JabiltestN.index('Burn L')]='PASS'
        time.sleep(0.5)
        if int(SlotcountR) <> 0:
            logging.info(Tr.run('b 2',2))
            JabiltestV[JabiltestN.index('Burn R')]='PASS'
            time.sleep(0.5)
        else:
            logging.info('Pass Burn R')
            JabiltestV[JabiltestN.index('Burn R')]='Ignore'
        logging.info(Tr.run('i',2))
        time.sleep(0.5)
        logging.info(Tr.run('i'))
        JabiltestV[JabiltestN.index('ANC On')]='FAIL'
        logging.info(openseq(SC_MSG_BURN))
        runflag=run()
        logging.info(Tr.run('x'))
        JabiltestV[JabiltestN.index('ANC On')]='PASS'
        time.sleep(0.5)
        logging.info(Tr.run('d 1'))
        logging.info(Tr.run('d 2'))
	Ft=1
    elif int(SlotcountR) == 3:
        logging.info('Trimboxdefaultprocess -> SlotcountL :'+str(SlotcountL))
        logging.info('Trimboxdefaultprocess -> SlotcountR :'+str(SlotcountR))
        logging.info(Tr.Loadconfig('2'))
        logging.info(Tr.Loadconfig('1'))
        logging.info('Trimboxdefaultprocess -> Start default burn R and L')
        logging.info(Tr.run('d 1'))
        logging.info(Tr.run('d 2'))
        logging.info(Tr.run('b 2',2))
        JabiltestV[JabiltestN.index('Burn R')]='PASS'
        time.sleep(0.5)
        if int(SlotcountL) <> 0:
            logging.info(Tr.run('b 1',2))
            JabiltestV[JabiltestN.index('Burn L')]='PASS'
            time.sleep(0.5)
        else:
            logging.info('Pass Burn L')
            JabiltestV[JabiltestN.index('Burn L')]='Ignore'
        logging.info(Tr.run('i',2))
        time.sleep(0.5)
        logging.info(Tr.run('i'))
        JabiltestV[JabiltestN.index('ANC On')]='FAIL'
        logging.info(openseq(SC_MSG_BURN))
        runflag=run()
        logging.info(Tr.run('x'))
        JabiltestV[JabiltestN.index('ANC On')]='PASS'
        time.sleep(0.5)
        logging.info(Tr.run('d 1'))
        logging.info(Tr.run('d 2'))
	Ft=1
    logging.info('Trimboxdefaultprocess -> SlotcountL :'+str(SlotcountL))
    logging.info('Trimboxdefaultprocess -> SlotcountR :'+str(SlotcountR))
    #State register check
    for i in (1,2):
        RecordRead=Tr.run('d '+str(i))
        logging.info('RecordRead on '+str(i)+' is :\n'+str(RecordRead))
        RecordRead=RecordRead.replace('\r','').replace('\n','').replace('d '+str(i),'').replace('OTP register dump:','').replace(': ',':').split(' ')
        for k in (2,3,4,5,10,11,12,13):
            valuetest=cmp(RecordRead[k], checkvalue[k])
            logging.debug('register check--> Current Device value : Default value')
            logging.debug('register check'+str(RecordRead[k])+':'+str(checkvalue[k]))
            if valuetest <> 0:
                logging.info('Error on Register Check!! value --> Current Device value : '+str(RecordRead[k])+' , Default value : '+str(checkvalue[k]))
                if i == 1:
                    JabiltestV[JabiltestN.index('Burn L')]='RegisterError'
                elif i == 2:
                    JabiltestV[JabiltestN.index('Burn R')]='RegisterError'
                raise TypeError, 'Register check Err on '+str(RecordRead[k])
    dgainerrcheck=1
    while (dgainerrcheck<>0):
        logging.debug('gain value check')
        #Gain check start
        dgainerrcheck=0
        for i in (1,2):
            Slotcount=int(Tr.run('s '+str(i)))
            if Slotcount == 2:
                registergaincheck=(0,1)
            if Slotcount == 1:
                registergaincheck=(6,7)
            if Slotcount == 0:
                registergaincheck=(8,9)
            print registergaincheck
            RecordRead=Tr.run('d '+str(i))
            logging.info('RecordRead on '+str(i)+' is :\n'+str(RecordRead))
            RecordRead=RecordRead.replace('\r','').replace('\n','').replace('d '+str(i),'').replace('OTP register dump:','').replace(': ',':').split(' ')        
            for k in registergaincheck:
                gai=(int(RecordRead[k].split(':')[1],16)-128)*0.5-0.5
                logging.info('gain value on [1=Right,2=Left]: '+str(i)+'[(0or1):Slotcount=2,(6or7):Slotcount=1,(8or9):Slotcount=0]: '+str(k)+' = '+str(gai))
                if gai<15 or gai>24 :
                    logging.debug('gain set out of range 15-23, reburn!')
                    dgainerrcheck=1
                else:
                    pass
        #Gain check End
        #dgainerrcheck=1
        if dgainerrcheck==1:
            #SlotcountL=0
            if int(SlotcountL) == 0 or int(SlotcountR) == 0:
                logging.debug('One side SLot = 0 , Stop burn')
                JabiltestV[JabiltestN.index('Burn L')]='RegisterError'
                JabiltestV[JabiltestN.index('Burn R')]='RegisterError'
                raise TypeError,'Register check Err with slot = 0'
            else:
                if ActivateDefaultCheckBurn=='YES':
                    JabiltestV[JabiltestN.index('Burn L')]='REBURN'
                    JabiltestV[JabiltestN.index('Burn R')]='REBURN'
                    logging.info('Reburn default gain setting due to fail default gain check')
                    #logging.info(Tr.Loadconfig('1'))
                    #logging.info(Tr.Loadconfig('2'))
                    logging.info('Trimboxdefaultprocess -> Start Reburn L and R')
                    
                    logging.info(Tr.run('w 0x30 '+hex(int(2*20+128+1))+' '+str(1)))
                    logging.info(Tr.run('w 0x31 '+hex(int(2*16.5+128+1))+' '+str(1)))
                    
                    logging.info(Tr.run('w 0x30 '+hex(int(2*20+128+1))+' '+str(2)))
                    logging.info(Tr.run('w 0x31 '+hex(int(2*16.5+128+1))+' '+str(2)))
                    time.sleep(0.5)
                    logging.info(Tr.run('d 1'))
                    logging.info(Tr.run('d 2'))                    
                    logging.info(Tr.run('b 1',2))
                    JabiltestV[JabiltestN.index('Burn L')]='PASS'
                    time.sleep(0.5)
                    logging.info(Tr.run('b 2',2))
                    JabiltestV[JabiltestN.index('Burn R')]='PASS'                  
                else:
                    logging.info('Pass Burn L/R')
                    JabiltestV[JabiltestN.index('Burn L')]='Ignore'
                    JabiltestV[JabiltestN.index('Burn R')]='Ignore'
                logging.info(Tr.run('i',2))
                time.sleep(0.5)
                logging.info(Tr.run('i'))
                JabiltestV[JabiltestN.index('ANC On')]='FAIL'
                if ActivateDefaultCheckBurn=='YES':
                    logging.info(openseq(SC_MSG_BURN))
                    runflag=run()
                logging.info(Tr.run('x'))
                JabiltestV[JabiltestN.index('ANC On')]='PASS'
                time.sleep(0.5)
                logging.info(Tr.run('d 1'))
                logging.info(Tr.run('d 2'))
                SlotcountL=int(Tr.run('s 1'))
                SlotcountR=int(Tr.run('s 2'))
                logging.info('Burn remains time update , SlotL = '+str(SlotcountL)+', Slot R = '+ str(SlotcountR)  )
                JabiltestV[JabiltestN.index('Burn Remain Times L')]=str(SlotcountL)
                JabiltestV[JabiltestN.index('Burn Remain Times R')]=str(SlotcountR)                  
        else:
	    if Ft==1:
		logging.info('Trimboxdefaultprocess -> first time burn completed witout register err')
		pass
	    else:
		JabiltestV[JabiltestN.index('Burn L')]='Ignore'
		JabiltestV[JabiltestN.index('Burn R')]='Ignore' 
		logging.info(Tr.Loadconfig('1','NO'))
		logging.info(Tr.Loadconfig('2','NO'))
		JabiltestV[JabiltestN.index('ANC On')]='FAIL'
		logging.info(openseq(SC_MSG_NOBURN))
		runflag=run()
		JabiltestV[JabiltestN.index('ANC On')]='PASS'       
      
    FB_L = D4FB_L
    FB_R = D4FB_R
    FF_L = D4FF_L
    FF_R = D4FF_R
    return FB_L,FF_L,FB_R,FF_R
def autotrimSN(LorR,FB,FF):
    if LorR == 'L':
        f=open(Autotrimflagfilepath+r'autotrimSN.txt','w+')
        f.write(SN[8:]+'FB'+str(FB)+'FF'+str(FF))
        f.close()
    if LorR == 'R':
        f=open(Autotrimflagfilepath+r'autotrimSN.txt','w+')
        f.write(SN[8:]+'FB'+str(FB)+'FF'+str(FF))
        f.close()
def autotrimvaluelog():
    L_FBL,L_FFL,L_L90,L_L300,L_FBR,L_FFR,L_R90,L_R300,SN
    if os.path.exists(path+r'\logANCvalue.txt') == True:
        s=['L_FBL','L_FFL','L_L90','L_L300','L_FBR','L_FFR','L_R90','L_R300'];number=0
        f=open(path+r'\logANCvalue.txt','a+')
        for i in L_FBL,L_FFL,L_L90,L_L300,L_FBR,L_FFR,L_R90,L_R300:
            j=[str(k) for k in i]
            f.write(str(date)+' '+SN[8:]+' '+str(s[number])[2:]+' '+' '.join(j)+'\n')
            number=number+1
        f.close()
    else:
        f=open(path+r'\logANCvalue.txt','w+')
        for i in L_FBL,L_FFL,L_L90,L_L300,L_FBR,L_FFR,L_R90,L_R300:
            j=[str(k) for k in i]
            f.write(str(date)+' '+SN[8:]+' '+str(i)[2:]+' '+' '.join(j)+'\n')
        f.close()    
def autotrimflag(Flag,msg='Success'):
    global processflag
    print datetime.date.today()
    processflag=[str(i) for i in processflag]
    f=open(Autotrimflagfilepath+str(Flag)+'.txt','wb')
    #f2=open(SNfile,'r')
    #f.write('SN='+f2.read()+'\n')
    f.write(msg.encode('utf-8')+'\n')
    #f2.close()
    f.close()
    endtime=datetime.datetime.now()
    processflag.append(str(endtime-starttime))
    if os.path.exists(path+r'\logANCSuccessflag.txt') == True:
        f=open(path+r'\logANCSuccessflag.txt','a+')
        f.write(str(date)+' '+str(SN)+' '+msg.encode('utf-8')+'\n')
        f.close()
    else:
        f=open(path+r'\logANCSuccessflag.txt','w+')
        f.write(str(date)+' '+str(SN)+' '+msg.encode('utf-8')+'\n')
        f.close()
    if os.path.exists(path+r'\logANCautoloopflag.txt') == True:
        f=open(path+r'\logANCautoloopflag.txt','a+')
        f.write(' '.join(processflag)+'\n')
        f.close()
    else:
        f=open(path+r'\logANCautoloopflag.txt','w+')
        #f.write('SN SideOKflag Burnflag_L Burnflag_R SideOKflag \n')
        f.write('SN SlotL SlotR FirstcheckL FirstcheckR D_L D_R G_D_L G_D_R x_optL y_optL x_optR y_optR BurnflagL BurnflagR\n')
        f.write(' '.join(processflag)+'\n')
        f.close()
    #===========For Jabil test trimtest breaks down==============================
    f=open(Autotrimflagfilepath+r'AutotrimJabiltestResult.txt','w+')
    for i in range(len(JabiltestN)):
        f.write(JabiltestN[i]+'\t'+JabiltestV[i]+'\n')
    f.close()
def ANCdoc(ANCinfo):
    if os.path.exists(path+r'\logANC.txt') == True:
        f=open(path+r'\logANC.txt','a+')
        f.write(str(date)+' '+str(SN)+' '+ANCinfo+'\n')
        f.close()
    else:
        f=open(path+r'\logANC.txt','w+')
        f.write(str(date)+' '+str(SN)+' '+'FB_L FF_L FB_R FF_R'+'\n')
        f.write(str(date)+' '+str(SN)+' '+ANCinfo+'\n')
        f.close()    
def checkinit():
    if os.path.exists(SC_LINE) == True:
        openseq(SC_LINE)
        Checkflag=run()
        if Checkflag[0] == False:
            raise Exception
    openseq(SC_MSG_START)
    Checkflag=run()
    time.sleep(1)
    if Checkflag[0] == False:
        raise Exception
    else:
        return 'checkinit : OK'
def vi_return():
    return vi.getcontrolvalue('Success?')
def openseq(seq_path):
    paramValues_openseq = ['open ' + seq_path, False, False, '0.0', "", "Null", "Null", "Null"]
    vi.call(paramNames, paramValues_openseq)
    return vi_return()
def run():
    paramValues_run = ["run", False, False, '0.0', "", "Null", "Null", "Null"]
    vi.call(paramNames, paramValues_run)
    #raw_input('test case build')
    return vi_return(),vi.getcontrolvalue('Pass?')
    #vi.getcontrolvalue('Success?')
def Autotrim_getdistance(LorR):
    Dg=Tp
    if LorR=='C2':
        f=open(SC_Checkflag)
        content=f.readlines()
        Check_L=content[0].split('\t')[-3]
        f.seek(0)
        Check_R=content[1].split('\t')[-3] 
        f.close()
        return Check_L,Check_R    #Check curve with limit
    if LorR=='C':
        f=open(SC_Checkflag)
        content=f.readlines()
        f.close()
        return content[0].split('\t')[-3]#Check curve with limit
    if LorR=='B':
        f2=open(SC_DCurveflag)
        content=f2.readlines()
        cL=[float(i) for i in content[1].strip('\n').split('\t')[2:13]] #catch value starts from 1000
        cL=nu.array(cL)
        f2.seek(0)
        cR=[float(i) for i in content[3].strip('\n').split('\t')[2:13]] #catch value starts from 1000
        cR=nu.array(cR)
        SumdD_L=sum((cL-Dg)**2)
        SumdD_R=sum((cR-Dg)**2)
        f2.close()
        return SumdD_L,SumdD_R
    if LorR=='L' or LorR=='R':
        L=Autotrim_getdistance('C')
        f2=open(SC_DCurveflag)
        content=f2.readlines()
        c=[float(i) for i in content[1].strip('\n').split('\t')[2:13]] #catch value starts from 1000
        c=nu.array(c)
        SumdD=sum((c-Dg)**2)
        f2.close()
        return SumdD,c,L
def Autotrim_regression_process(Tr):
    global G_D,Burnflag_L,Burnflag_R,processflag,FB_L,FF_L,FB_R,FF_R,gain1,FAflag,Checkflag,JabiltestN,JabiltestV
    if SlotcountL==0 or SlotcountR==0 or FAflag=='YES':
        logging.info('Slot number is 0, or FAflag = YES, skip Autotrim_regression_process')
        JabiltestV[JabiltestN.index('Default Performance L')]='Ignore'
        JabiltestV[JabiltestN.index('Default Performance R')]='Ignore'        
        pass
    else:  
        Burnflag_L='NO'
        Burnflag_R='NO'
        #PNI has been measured
        ANClog='ANC=FB_L,FF_L:'+str(FB_L)+','+str(FF_L)+',FB_R,FF_R:'+str(FB_R)+','+str(FF_R)
        logging.info(ANClog)
        runflag=run()    
        #First Check mic====================================
        #processflag.append(str(FB_L))
        #processflag.append(str(FF_L))
        #processflag.append(str(FB_R))
        #processflag.append(str(FF_R))
        logging.info(Tr.run('w 0x30 '+hex(int(2*20+128+1))+' '+str(1)))
        logging.info(Tr.run('w 0x31 '+hex(int(2*16.5+128+1))+' '+str(1)))
        logging.info(Tr.run('w 0x30 '+hex(int(2*20+128+1))+' '+str(2)))
        logging.info(Tr.run('w 0x31 '+hex(int(2*16.5+128+1))+' '+str(2)))        
        Checkflag=Autotrim_getdistance('C2')
        processflag.append(str(Checkflag[0]))
        processflag.append(str(Checkflag[1]))
        JabiltestV[JabiltestN.index('Default Performance L')]=str(Checkflag[0])
        JabiltestV[JabiltestN.index('Default Performance R')]=str(Checkflag[1])     
        logging.info('First check Mic function by limit : Lside and Rside:'+str(Checkflag))
        if Checkflag[0]=='FAIL' or Checkflag[1]=='FAIL':
            logging.info(Tr.run('i'))
            logging.info(Tr.run('i'))
            logging.info(Tr.run('x'))
            time.sleep(0.5)
            logging.info(Tr.run('d 1'))
            time.sleep(0.5)
            logging.info(Tr.run('d 2'))      
            logging.info(Tr.run('l 1'))
            time.sleep(0.5)
            logging.info(Tr.run('l 2'))
            time.sleep(0.5)
            logging.info(Tr.run('i'))
            logging.info(Tr.run('i'))
            logging.info(Tr.run('x'))
            time.sleep(0.5)
            logging.info(Tr.run('d 1'))
            time.sleep(0.5)
            logging.info(Tr.run('d 2'))    
            time.sleep(0.5)
            logging.info(Tr.run('i'))
            logging.info(Tr.run('i'))            
            sys.exit(0)
            raise SystemExit
        #Check First pass if needs to go autotrim======================================
        D4_D=Autotrim_getdistance('B')
        processflag.append(D4_D[0])
        processflag.append(D4_D[1])
        G_D=[setG_D_L,setG_D_R]
        processflag.append(G_D[0])
        processflag.append(G_D[1])        
        logging.info('D4_D:'+str(D4_D))
        #D4_D=[100,100]
        if D4_D[0]>G_D[0]:
            openseqflag=openseq(SC_L)
            OptL=Autorim_regression_algorithm(Tr,'L')
            #Check process
            Checkflag=Autotrim_getdistance('C')
            Compareflag=Autotrim_compare(OptL,gain1)
            logging.info('Check limit : '+ str(Checkflag)+',Compare Ori-gain value : '+str(Compareflag))
            if Checkflag=='PASS' and Compareflag=='Newgain':
                Burnflag_L='YES'
            else:
                Burnflag_L='NO'
                #load back
                logging.info('Loading back previous gain..')
                #logging.info(Tr.run('l1'))
                logging.info('Write L FB, FF = '+str(FB_L)+','+str(FF_L))
                logging.info(Tr.run('w 0x30 '+hex(int(2*FB_L+128+1))+' '+str(1)))
                logging.info(Tr.run('w 0x31 '+hex(int(2*FF_L+128+1))+' '+str(1)))
        else:
            OptL=[20,16.5]
        processflag.append(str(OptL[0]))
        processflag.append(str(OptL[1]))
        if D4_D[1]>G_D[1]:
            openseqflag=openseq(SC_R)
            OptR=Autorim_regression_algorithm(Tr,'R')
            #Check process
            Checkflag=Autotrim_getdistance('C')
            Compareflag=Autotrim_compare(OptR,gain1)
            logging.info('Check limit : '+ str(Checkflag)+',Compare Ori-gain value : '+str(Compareflag))
            if Checkflag=='PASS' and Compareflag=='Newgain':
                Burnflag_R='YES'
            else:
                Burnflag_R='NO'
                #load back
                logging.info('Loading back previous gain..')
                #logging.info(Tr.run('l2'))F_R
                logging.info('Write R FB, FF = '+str(FB_R)+','+str(FF_R))
                logging.info(Tr.run('w 0x30 '+hex(int(2*FB_R+128+1))+' '+str(2)))
                logging.info(Tr.run('w 0x31 '+hex(int(2*FF_R+128+1))+' '+str(2)))
        else:
            OptR=[20,16.5]
        processflag.append(str(OptR[0]))
        processflag.append(str(OptR[1]))        
        logging.info('Burnflag_L,Burnflag_R : '+str(Burnflag_L)+','+str(Burnflag_R))
        logging.info('Autotrim_regression_process is done : OptL OptR :'+str(OptL)+','+str(OptR))
    #processflag[1]=SideOKflag
    #Fianl run
    openseqflag=openseq(SC_FANC)
    run()
    #Burn process============================================================
    processflag.append(Burnflag_L)
    processflag.append(Burnflag_R)
    if int(SlotcountL)==0:
        logging.info('Slot number is 0, skip burn')
    else:
        if Burnflag_L=='YES' and Burnflag_R=='YES':
            if activateburn=='YES' and float(SlotcountL)<>0 and float(SlotcountR)<>0:
                #Burnprocess
                logging.info('Autotrim_regression_process -> activateburn = '+str(activateburn)+',SlotcountL,SlotcountL='
                             +str(SlotcountL)+','+str(SlotcountR)+', Start burn process')
                logging.info(Tr.run('b 1'))                
                logging.info(Tr.run('b 2',2))
                time.sleep(0.5)
                logging.info(Tr.run('i',2))
                #time.sleep(0.5)
                #logging.info(Tr.run('i',2))
                openseq(SC_MSG_BURN_BT)
                runflag=run()
                return 0
            else:
                logging.info('Autotrim_regression_process -> activateburn = '+str(activateburn)+',SlotcountL,SlotcountL='
                             +str(SlotcountL)+','+str(SlotcountR)+',skip burn process')            
        else:
            logging.info('Autotrim_regression_process -> Burnflag=No,no burn process')
        #openseq(SC_MSG_NOBURN_BT)
    logging.info(Tr.run('i'))
    logging.info(Tr.run('i'))
    logging.info(Tr.run('x'))
    time.sleep(0.5)
    logging.info(Tr.run('d 1'))
    time.sleep(0.5)
    logging.info(Tr.run('d 2'))
    logging.info(Tr.run('l 1'))
    time.sleep(0.5)
    logging.info(Tr.run('l 2'))
    time.sleep(0.5)
    logging.info(Tr.run('i'))
    logging.info(Tr.run('i'))
    logging.info(Tr.run('x'))
    time.sleep(0.5)
    logging.info(Tr.run('d 1'))
    time.sleep(0.5)
    logging.info(Tr.run('d 2'))
    time.sleep(0.5)
    logging.info(Tr.run('i'))
    logging.info(Tr.run('i'))
    return 0
    #Show limit==============================================================      
def Autotrim_compare(gain,gainin):
    if gain[0]==gainin[0] and gain[1]==gainin[1]:
        return 'Same'
    else:
        return 'Newgain'
def Autotrim_measure(LorR,Tr,FB,FF):
    #Write
    if LorR=='L':
        logging.info('Write L FB, FF = '+str(FB)+','+str(FF))
        logging.info(Tr.run('w 0x30 '+hex(int(2*FB+128+1))+' '+str(1)))
        logging.info(Tr.run('w 0x31 '+hex(int(2*FF+128+1))+' '+str(1)))
        #Measure
        autotrimSN(LorR,str(FB),str(FF))
        run()
        mea=Autotrim_getdistance(LorR)
    if LorR=='R':
        logging.info('Write R FB, FF = '+str(FB)+','+str(FF))
        logging.info(Tr.run('w 0x30 '+hex(int(2*FB+128+1))+' '+str(2)))
        logging.info(Tr.run('w 0x31 '+hex(int(2*FF+128+1))+' '+str(2)))
        #Measure
        autotrimSN(LorR,str(FB),str(FF))
        run()
        mea=Autotrim_getdistance(LorR)        
    return mea
def Autorim_regression_algorithm(Tr,LorR):
    global FB_L,FF_L,FB_R,FF_R,gain1
    if LorR=='L':
        gain1=[FB_L,FF_L]
    if LorR=='R':
        gain1=[FB_R,FF_R]
    xg=gain1[0] #FB 1st
    yg=gain1[1] #FF 1st
    x=[]
    y=[]
    SdD=[] #acutal measurement
    DN=[] #acutal measurement curve
    L=[] #limit check
    #f=[50,63,80,100,125,160,200,250,315,400,500,630,800,1000]
    f=[100,125,160,200,250,315,400,500,630,800,1000]
    #f=[50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000]
    #Dg=HeadsetAMS(xg,yg) #Golden Curve
    #Dg=[-16,-10,-19.5,-22,-29.3,-26.6,-22.2,-17.3,-13.3,-8.4,-8.1,-9.9,-8.2,-0.6,9.3,8.7,5.7]
    #Dg=[-30,-30,-30,-30,-30,-30,-30,-30,-30,-30,-30,-30,-30,0] #50-1000 1/3 Otc
    #Dg=[Tp,Tp,Tp,Tp,Tp,Tp,Tp,Tp,Tp,Tp,0]
    Dg=Tp
    logging.info('Dg='+str(Dg))
    #plt.plot(f,Dg)
    #plt.savefig(LorR+r'targetcurve.png')
    #plt.show()
    SumdDt=68 #Target distance 1dB=17, 2dB=68, 3dB=153
    #1st
    x.append(xg) #default FB gain
    y.append(yg) #default FF gain
    mea=Autotrim_measure(LorR,Tr,x[0],y[0])
    SdD.append(mea[0])# default actual measurement
    DN.append(mea[1])
    L.append(mea[2])
    #2nd
    x.append(x[0]+0.5)
    y.append(y[0]+0.5)
    mea=Autotrim_measure(LorR,Tr,x[1],y[1])
    SdD.append(mea[0])# 2nd actual measurement
    DN.append(mea[1])
    L.append(mea[2])
    AC=dot(pinv([[x[0],1],[x[1],1]]),nu.vstack((DN[0],DN[1]))) #regress equation D=Ax+C
    SumdD3=20000 #Regressing prediction for x, y    at 
    #SumdD3=2000 #Regressing prediction for x, y    at 
    print AC
    pl=[]
    x.append(x[0]+0.5)#First x2 (3rd time)
    for xi in nu.arange(15,23,0.5):
        Di=AC[0,:]*xi+AC[1,:]
        SumdDi=sum((Di-Dg)**2)
        if SumdDi<SumdD3:   # minus 2000 stop
            x[2]=xi
            SumdD3=SumdDi
        else:
            #print 'not found'
            pass    
        pl.append(SumdD3)
    print min(pl)
    y.append(y[1])#y2 (3rd time)
    #draw
    px=nu.linspace(1,10,len(nu.arange(15,23,0.5),))
    plt.figure()
    plt.subplot(4,3,7)
    plt.plot(px,pl,'b')
    plt.title('D=Ax+C',fontsize=7,loc ='left',verticalalignment='baseline')
    plt.xticks(fontsize=7)
    
    #plt.savefig(str(LorR)+r' AxC.png')
    #plt.show()
    mea=Autotrim_measure(LorR,Tr,x[2],y[2])#use predict 3rd time to do actural measurement
    SdD.append(mea[0]) # 3nd actual measurement
    DN.append(mea[1])
    L.append(mea[2]) 
    print 'AC',x,y,SdD
    
    #3nd use 3 actual measurement to create PolynomialFeatures
    ABC=dot(pinv([[x[0],y[0],1],[x[1],y[1],1],[x[2],y[2],1]]),nu.vstack((DN[0],DN[1],DN[2]))) #regress equation D=Ax+By+C
    SumdD4=10000   
    #SumdD4=2000   
    pl=[]
    x.append(x[2]+0.5)   #First x3(4rd time)
    y.append(y[2]+0.5)   #First x3
    for xi in nu.arange(15,23,0.5):
        for yi in nu.arange(15,23,0.5):
            Di=ABC[0,:]*xi+ABC[1,:]*yi+ABC[2,:]
            SumdDi=sum((Di-Dg)**2)
            if SumdDi<SumdD4:
                x[3]=xi
                y[3]=yi
                SumdD4=SumdDi
            pl.append(SumdD4)
    print min(pl)
    px=nu.linspace(1,10,len(nu.arange(15,23,0.5),)**2)
    #plt.figure()
    plt.subplot(4,3,8)
    plt.plot(px,pl,'b')
    plt.title('D=Ax+By+C',fontsize=7,loc ='left',verticalalignment='baseline')
    plt.xticks(fontsize=7)
    #plt.savefig(str(LorR)+r' AxByC.png')
    #plt.show()
    print x,y
    mea=Autotrim_measure(LorR,Tr,x[3],y[3])#use predict 4rd time to do actural measurement
    SdD.append(mea[0]) # 4nd actual measurement
    DN.append(mea[1])
    L.append(mea[2])

    #4nd use 4 actual measurement to create PolynomialFeatures
    #ABCD=pinv([x1,y1,1,x1*y1;x2,y2,1,x2*y2;x3,y3,1,x3*y3;x4,y4,1,x4*y4])*[D1;D2;D3;D4];
    ABCD=dot(pinv([[x[0],y[0],1,x[0]*y[0]],[x[1],y[1],1,x[1]*y[1]],[x[2],y[2],1,x[2]*y[2]],[x[3],y[3],1,x[3]*y[3]]])
             ,nu.vstack((DN[0],DN[1],DN[2],DN[3]))) #regress equation D=Ax+By+C+Dxy
    SumdD5=5000  
    #SumdD5=100  
    pl=[]
    x.append(x[3]+0.5)   #First x4
    y.append(y[3]+0.5)   #First x4
  
    for xi in nu.arange(15,23,0.5):
        for yi in nu.arange(15,23,0.5):
            #Di=ABCD(1,:).*xi+ABCD(2,:).*yi+ABCD(3,:)+ABCD(4,:).*xi.*yi;W
            Di=ABCD[0,:]*xi+ABCD[1,:]*yi+ABCD[2,:]+ABCD[3,:]*xi*yi
            SumdDi=sum((Di-Dg)**2)
            if SumdDi<SumdD5:
                x[4]=xi
                y[4]=yi
                SumdD5=SumdDi
            else:
                #print 'not found'
                pass                
            pl.append(SumdD5)
    print pl
    px=nu.linspace(1,10,len(nu.arange(15,23,0.5),)**2)
    #plt.figure()
    plt.subplot(4,3,9)
    plt.plot(px,pl,'b')
    plt.title('D=Ax+By+C+Dxy',fontsize=7,loc ='left',verticalalignment='baseline')
    plt.xticks(fontsize=7)
    #plt.savefig(str(LorR)+r' AxByCDxy.png')
    #plt.show()
    px=[]
    pl=[]
    mea=Autotrim_measure(LorR,Tr,x[4],y[4])#use predict 5rd time to do actural measurement
    SdD.append(mea[0])# 5nd actual measurement
    DN.append(mea[1])
    L.append(mea[2])
    print SdD
    print DN
    x_opt=x[SdD.index(min(SdD))]
    y_opt=y[SdD.index(min(SdD))]
    #5rd-9rd iteration
    SdD.append(SdD[4])
    DN.append(DN[4])
    L.append(L[4])
    x.append(x[4])   #First x5
    y.append(y[4])   #First x5
    logging.info('x(FB):'+str(x))
    logging.info('y(FF):'+str(y))
    logging.info('SdD:'+str(SdD))
    logging.info('DN:'+str(DN))    
    for i in range(0,setregressiontime):
        if min(SdD)<=min(SumdD3,SumdD4,SumdD5):
            break
        else:
            Mvalue=max(SdD)
            Mindex=SdD.index(Mvalue)
            x[SdD.index(max(SdD))]=x_opt
            y[SdD.index(max(SdD))]=y_opt
            #DN[Mindex]=DN[5]
            #SdD[Mindex]=SdD[5]
            ABCD=dot(pinv([[x[0],y[0],1,x[0]*y[0]],[x[1],y[1],1,x[1]*y[1]],[x[2],y[2],1,x[2]*y[2]],[x[-1],y[-1],1,x[-1]*y[-1]]])
                     ,nu.vstack((DN[0],DN[-1],DN[2],DN[-1]))) #regress equation D=Ax+By+C+Dxy            
            for xi in nu.arange(15,23,0.5):
                for yi in nu.arange(15,23,0.5):
                    #Di=ABCD(1,:).*xi+ABCD(2,:).*yi+ABCD(3,:)+ABCD(4,:).*xi.*yi;W
                    Di=ABCD[0,:]*xi+ABCD[1,:]*yi+ABCD[2,:]+ABCD[3,:]*xi*yi
                    SumdDi=sum((Di-Dg)**2)
                    if SumdDi<SumdD5:
                        x_opt=xi
                        y_opt=yi
                        SumdD5=SumdDi
                    else:
                        print 'not found'
                        print x_opt,y_opt                        
                    pl.append(SumdD5)
            px=nu.linspace(1,10,(i+1)*(len(nu.arange(15,23,0.5),)**2))      
            #D5=HeadsetAMS(x_opt,y_opt); % 4+i th measurement
            #SumdD6=sum((D6-Dg).^2);
            #Err=[Err,SumdD5];
            #Xr=[Xr,x_opt];Yr=[Yr,y_opt];Dr=[Dr;D6];       
            mea=Autotrim_measure(LorR,Tr,x_opt,y_opt)#use predict 5rd time to do actural measurement
            #SumdD5=mea[0] # 5nd actual measurement
            SdD[Mindex]=mea[0]   
            DN[Mindex]=mea[1]
            L[Mindex]=mea[2]
            #DN.append(mea[1])
            x[Mindex]=x_opt   #
            y[Mindex]=y_opt   # 
            logging.info('x(FB):'+str(x))
            logging.info('y(FF):'+str(y))
            logging.info('SdD:'+str(SdD))
            logging.info('DN:'+str(DN))
            logging.info('L:'+str(L))
    #Post-process for check flag, add 10000 to one failed on limit check
    logging.info('Post-process for check flag, add 100000 to one failed on limit check..')
    L=[1 if i=='PASS' else 100000 for i in L]
    logging.debug('post Limit :'+str(LorR)+' '+str(L))
    L=nu.array(L)
    SdD=L*SdD
    SdD=SdD.tolist()
    logging.info('post SdD:'+str(SdD))
    #Opt final
    if min(SdD)>100000:
        logging.info('All regression results failed on limit! go back default value')
        x_opt=xg
        y_opt=yg
    else:
        x_opt=x[SdD.index(min(SdD))]
        y_opt=y[SdD.index(min(SdD))]
    logging.info('x_opt:'+str(x_opt)+',y_opt:'+str(y_opt))
    #plt.cla()
    plt.subplot(4,3,10)
    plt.plot(px,pl,'b')
    plt.title('D=Ax+By+C+Dxy',fontsize=4,loc ='left',verticalalignment='baseline')
    plt.xticks(fontsize=7)
    plt.subplot(4,3,11)
    #plt.show()
    plt.plot(range(1,len(x)+1),x)
    plt.title('FB and FF',fontsize=7 ,loc ='left',verticalalignment='baseline')
    plt.plot(range(1,len(y)+1),y)
    label=['FB','FF']
    plt.legend(label,fontsize=7 ,loc='upper left')    
    plt.subplot(4,3,12)    
    #plt.show()
    plt.plot(x,y)
    plt.title('x=FB,y=FF',fontsize=7,loc ='left',verticalalignment='baseline')
    plt.subplot(2,1,1)
    plt.plot(f,Dg,linestyle="--")    
    plt.plot(f,DN[0],'b')
    plt.plot(f,DN[1])
    plt.plot(f,DN[2])
    plt.plot(f,DN[3])
    plt.plot(f,DN[4])
    plt.plot(f,DN[5],'r',marker="*")
    label=['Target curve',
        str(x[0])+','+str(y[0]),
           str(x[1])+','+str(y[1]),
           str(x[2])+','+str(y[2]),
           str(x[3])+','+str(y[3]),
           str(x[4])+','+str(y[4]),
           str(x[5])+','+str(y[5])]
    plt.title(str(LorR)+' Curve Dynamic',fontsize=10)
    plt.legend(label,fontsize=7,loc='upper left')
    plt.subplots_adjust(wspace =0.4, hspace =0.4)
    plt.savefig(AutotrimLogpath+'\\'+str(SN)+'-'+str(date)+' '+str(LorR)+' Curve Dynamic.png')
    #plt.show()
    
    #=================================================================================================================
    return x_opt,y_opt
    
class TRIMBOXuart:
    def __init__(self, port='COM3', baudrate='38400'):
        self.port = port 
        self.baudrate = baudrate
        self.serial = serial.Serial(port=self.port, baudrate=self.baudrate, 
                                   bytesize=serial.EIGHTBITS, 
                                   parity=serial.PARITY_NONE, 
                                   stopbits=serial.STOPBITS_ONE, 
                                   timeout=0.5, #Important, defind how many time a read() could last.
                                   xonxoff=False, 
                                   rtscts=False, 
                                   write_timeout=1, 
                                   dsrdtr=False, 
                                   inter_byte_timeout=1, 
                                   exclusive=None)
        self.serial.flushInput()
        self.serial.flushOutput()
        time.sleep(0.1)  
        self.run('v')
        #logging.info(self.run('y'))    single mode
        self.run('e')
        self.run('x',1)
        time.sleep(0.5)
    def run(self, cmd,  phasecheck=0, repeatcheck=0, valueuncheck=0):
        #send and recv
        cmd_ba = bytearray('%s\r' % cmd)
        if 'w' in cmd:
            #self.serial.write('w 20 09\r\n')
            #self.serial.write('w 0x3f 0x02\r')
            time.sleep(0.015)
            pass
        self.serial.write(cmd_ba)
        if 'b' in cmd: #set buffer for AMS to process the burning
            time.sleep(Burningbuffer)
        else:
            pass
        time.sleep(0.15)
        bytetoread=self.serial.inWaiting() #how many byte waiting to be readed
        #RecordRead=ser.read(bytetoread).splitlines()
        #RecordRead='None'
        RecordRead=self.serial.read(bytetoread)

        if cmd == 'e':
            if 'x ' in RecordRead:
                pass
            else:
                self.run('e')
        if 's' in cmd:
            Slotcount=RecordRead[int(RecordRead.find(':'))+2]
            logging.info('Slotnumber is : cmd= '+str(cmd)+', slotcount='+str(Slotcount))
            return Slotcount        
        if 'ERR' in RecordRead:
            #return 2/0
            #self.run('i')
            #return 'ERRRRRRRR occurs'
            if 'b ' in cmd:
                logging.info('ERR return with burn command: cmd='+cmd)     
                raise TypeError,'burn with ERR return,Record='+RecordRead
            if repeatcheck==0:
                logging.info('ERR return 1st time, start repeat command '+cmd)
                time.sleep(0.5)
                Record=self.run(cmd, phasecheck, 1)
                return Record
            elif repeatcheck==1:
                logging.info('ERR return 2rd time, start repeat command '+cmd)
                time.sleep(0.5)                
                Record2=self.run(cmd, phasecheck, 2)
                return Record2
            elif repeatcheck==2:
                logging.info('ERR return 3nd time, start repeat command '+cmd)              
                if phasecheck==1:
                    raise SyntaxError,'First time connection Error : cmd ='+cmd+',Record='+RecordRead
                elif phasecheck==2:
                    raise TypeError,'repeatcheck with error return, : cmd ='+cmd+',Record='+RecordRead
                raise ValueError,'ERR Return from Trimbox: cmd ='+cmd+',Record='+RecordRead

        else:
            return RecordRead
            # save
        #self.save(bytetoread, Trimbixdatafile)
    def close(self):
        self.run('i')
        self.serial.close()
        return 'OK'
    def ListToDict(self, datafile = None):
        #List -> Dict [RecordReadDict]
        tx = datafile
        for i in tx:
            if ':' in i:
                pass
            else:
                #tx.insert(tx.index(i), i+':')
                tx[tx.index(i)] = tx[tx.index(i)]+':'
            RecordReadDict = dict((i.split(':') for i in tx))  
    def Loadconfig(self, devi, writeflag='YES'):
        #Make write OTP mode enable 20180429
        #logging.info(self.run('w 20 09 '+devi))
        logging.info(self.run('w 3f 02 '+devi))
        time.sleep(0.05)
        DOMtree = xml.parse(Trimbixconfigfile)
        Data = DOMtree.documentElement 
        reglist = Data.getElementsByTagName("reg")
        for i in reglist:
            addr = i.getAttribute("addr")
            val = i.getAttribute("val")
            #addr = i.getAttribute("addr")[2:]
            #val = i.getAttribute("val")[2
            #addr.encode('utf8'),val.encode('utf8'),'device='+devi
            if writeflag == 'YES':
                logging.info('w '+addr.encode('utf8')+' '+val.encode('utf8')+' '+devi)            
                self.run('w '+addr.encode('utf8')+' '+val.encode('utf8')+' '+devi)      
            if devi == '1':
                if addr == '0x30':
                    global D4FB_L
                    D4FB_L = (int(val.encode('utf8'),16)-128)*0.5-0.5
                    self.run('w '+addr.encode('utf8')+' '+val.encode('utf8')+' '+devi)
                    print D4FB_L
                elif addr == '0x31':
                    global D4FF_L
                    D4FF_L = (int(val.encode('utf8'),16)-128)*0.5-0.5
                    self.run('w '+addr.encode('utf8')+' '+val.encode('utf8')+' '+devi)
                    print D4FF_L
            elif devi == '2':
                if addr == '0x30':
                    global D4FB_R
                    D4FB_R = (int(val.encode('utf8'),16)-128)*0.5-0.5
                    self.run('w '+addr.encode('utf8')+' '+val.encode('utf8')+' '+devi)
                elif addr == '0x31':
                    global D4FF_R
                    D4FF_R = (int(val.encode('utf8'),16)-128)*0.5-0.5
                    self.run('w '+addr.encode('utf8')+' '+val.encode('utf8')+' '+devi)
if __name__ == '__main__':
    #starttime=datetime.datetime.now()
    try:
        SCApp = win32com.client.Dispatch("Soundcheck120.Application")
        vi = SCApp.GetVIReference("ControlSC.vi", "", False, 0)
        vi._FlagAsMethod("call")
        paramNames = ["Command", "Success?", "Pass?", "Margin", "Table", "Xdatapoints", "Ydatapoints", "Zdatapoints"]
        #sys.argv[0] is the script name
        logging.info('Autotrim-R')
        logging.info(port)
        OP=autotrim()
    except Exception:
        syserr=sys.exc_info()
        logging.info('Err Exception'+str(syserr))
    except :
        syserr=sys.exc_info()
        logging.info('Please check if hardware key is up, or the connection of Trimbox'+str(syserr))
        autotrimflag(r'Doneflag',u'SC open Err or Trimbox connection Err.')
        #raw_input()
    finally:
        endtime=datetime.datetime.now()
        Costtime=endtime-starttime
        logging.info('Take times: '+str(Costtime))
