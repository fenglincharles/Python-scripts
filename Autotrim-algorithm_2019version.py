# -*- coding: utf-8 -*
#
#
# Test mode,for RS to develop sub function, not connect to algorithm
#
# python2.7
# 0217version
# 0325fix ANC6bug => dont use ANC6, L3R3 bug
#20190919 for loop, put 0 to -0.5
#0920 fix dataL -> dataR
import os
import sys
#import datetime
#import time
import json
from numpy import dot, transpose
import numpy as nu
from numpy.linalg import pinv
gui = 1
#import logging
#import matplotlib.pyplot as plt
#date = datetime.date.today()
AutotrimLogpath = 'C\\rsdebug'
print "version 0923"


def inputcheck(dataA):
    #data={k: v for k, v in data.items() if v is not None}
    dataA['X']
    dataA['Target ANC']
    dataA['L1']
    dataA['R1']
    dataL = {}
    dataR = {}
    for k, v in dataA.items():
        if v == None:
            del dataA[k]

    for k, v in dataA.items():
        if k[-1] == 'L':
            dataL[k[:-1]] = v
        if k[-1] == 'R':
            dataR[k[:-1]] = v

    if len(dataL)-len(dataR) <> 0:
        raise Exception, 'Error,on ANC curve'
    else:
        itr = len(dataL)
    print itr
    lgain = Autorim_regression_algorithm('L', itr, dataL)
    rgain = Autorim_regression_algorithm('R', itr, dataR)
    if itr == 1:
        if lgain == 'NO' or rgain == 'NO':
            return 'NO'
        else:
            return 'YES'
    output = {"L": lgain, "R": rgain}
    return str(output)


def Autorim_regression_algorithm(LorR, itr, data):
    #global FB_L,FF_L,FB_R,FF_R,gain1
    if LorR == 'L':
        gain1 = dataA['L1']
    if LorR == 'R':
        gain1 = dataA['R1']
    xg = gain1[0]  # FB 1st
    yg = gain1[1]  # FF 1st
    x = []
    y = []
    SdD = []  # acutal measurement
    DN = []  # acutal measurement curve
    L = []  # limit check
    # f=[50,63,80,100,125,160,200,250,315,400,500,630,800,1000]
    f = [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000]
    f = dataA['X']
    Dg = nu.array(dataA['Target ANC'])
    SumdDt = 68  # Target distance 1dB=17, 2dB=68, 3dB=153
    # 1st
    x.append(xg)  # default FB gain
    y.append(yg)  # default FF gain
    c = nu.array(data['ANC1'])
    SumdD = sum((c-Dg)**2)
    SdD.append(SumdD)  # default actual measurement
    DN.append(c)
    # L.append(mea[2])
    if itr == 1:
        if SumdD < dataA['Distance']:
            return 'OK'
        else:
            return 'NO'
    # 2nd
    x.append(x[0]-0.5)
    y.append(y[0]-0.5)
    # mea=Autotrim_measure(LorR,Tr,x[1],y[1])
    c = nu.array(data['ANC2'])
    SumdD = sum((c-Dg)**2)
    SdD.append(SumdD)  # 2nd actual measurement
    DN.append(c)
    # L.append(mea[2])
    AC = dot(pinv([[x[0], 1], [x[1], 1]]), nu.vstack(
        (DN[0], DN[1])))  # regress equation D=Ax+C
    SumdD3 = 20000  # Regressing prediction for x, y    at
    # SumdD3=2000 #Regressing prediction for x, y    at
    #print AC
    pl = []
    x.append(x[0]-0.5)  # First x2 (3rd time)
    for xi in nu.arange(-3, -0.5, 3):
        Di = AC[0, :]*xi+AC[1, :]
        SumdDi = sum((Di-Dg)**2)
        if SumdDi < SumdD3:   # minus 2000 stop
            x[2] = xi
            SumdD3 = SumdDi
        else:
            # print 'not found'
            pass
        pl.append(SumdD3)
    print min(pl)
    y.append(y[1])  # y2 (3rd time)

    if itr == 2:
        return [x[-1], y[-1]]
    c = nu.array(data['ANC3'])
    SumdD = sum((c-Dg)**2)
    SdD.append(SumdD)  # default actual measurement
    DN.append(c)
    print 'AC', x, y, SdD

    # 3nd use 3 actual measurement to create PolynomialFeatures
    ABC = dot(pinv([[x[0], y[0], 1], [x[1], y[1], 1], [x[2], y[2], 1]]), nu.vstack(
        (DN[0], DN[1], DN[2])))  # regress equation D=Ax+By+C
    SumdD4 = 10000
    # SumdD4=2000
    pl = []
    x.append(x[2]-0.5)  # First x3(4rd time)
    y.append(y[2]-0.5)  # First x3
    for xi in nu.arange(-2.5, -0.5, 2.5):
        for yi in nu.arange(-2.5, -0.5, 0.5):
            Di = ABC[0, :]*xi+ABC[1, :]*yi+ABC[2, :]
            SumdDi = sum((Di-Dg)**2)
            if SumdDi < SumdD4:
                x[3] = xi
                y[3] = yi
                SumdD4 = SumdDi
            pl.append(SumdD4)
    if itr == 3:
        return [x[-1], y[-1]]
    print x, y

    c = nu.array(data['ANC4'])
    SumdD = sum((c-Dg)**2)
    SdD.append(SumdD)  # default actual measurement
    DN.append(c)
    # 4nd use 4 actual measurement to create PolynomialFeatures
    # ABCD=pinv([x1,y1,1,x1*y1;x2,y2,1,x2*y2;x3,y3,1,x3*y3;x4,y4,1,x4*y4])*[D1;D2;D3;D4];
    ABCD = dot(pinv([[x[0], y[0], 1, x[0]*y[0]], [x[1], y[1], 1, x[1]*y[1]], [x[2], y[2], 1, x[2]*y[2]],
                     [x[3], y[3], 1, x[3]*y[3]]]), nu.vstack((DN[0], DN[1], DN[2], DN[3])))  # regress equation D=Ax+By+C+Dxy
    SumdD5 = 5000
    # SumdD5=100
    pl = []
    x.append(x[3]-0.5)  # First x4
    y.append(y[3]-0.5)  # First x4

    for xi in nu.arange(-2.5, -0.5, 2.5):
        for yi in nu.arange(-2.5, -0.5, 2.5):
            # Di=ABCD(1,:).*xi+ABCD(2,:).*yi+ABCD(3,:)+ABCD(4,:).*xi.*yi;W
            Di = ABCD[0, :]*xi+ABCD[1, :]*yi+ABCD[2, :]+ABCD[3, :]*xi*yi
            SumdDi = sum((Di-Dg)**2)
            if SumdDi < SumdD5:
                x[4] = xi
                y[4] = yi
                SumdD5 = SumdDi
            else:
                # print 'not found'
                pass
            pl.append(SumdD5)
    print pl
    if itr == 4:
        return [x[-1], y[-1]]
    px = []
    pl = []
    c = nu.array(data['ANC5'])
    SumdD = sum((c-Dg)**2)
    SdD.append(SumdD)  # default actual measurement
    DN.append(c)
    print SdD
    print DN
    x_opt = x[SdD.index(min(SdD))]
    y_opt = y[SdD.index(min(SdD))]
    # 5rd-9rd iteration
    SdD.append(SdD[4])
    DN.append(DN[4])
    # L.append(L[4])
    x.append(x[4])  # First x5
    y.append(y[4])  # First x5
    for i in [0]:
        # if min(SdD)<=min(SumdD3,SumdD4,SumdD5):
        if min(SdD) <= 10:
            break
        else:
            Mvalue = max(SdD)
            Mindex = SdD.index(Mvalue)
            x[SdD.index(max(SdD))] = x_opt
            y[SdD.index(max(SdD))] = y_opt
            # DN[Mindex]=DN[5]
            # SdD[Mindex]=SdD[5]
            ABCD = dot(pinv([[x[0], y[0], 1, x[0]*y[0]], [x[1], y[1], 1, x[1]*y[1]], [x[2], y[2], 1, x[2]*y[2]], [
                       x[-1], y[-1], 1, x[-1]*y[-1]]]), nu.vstack((DN[0], DN[-1], DN[2], DN[-1])))  # regress equation D=Ax+By+C+Dxy
            for xi in nu.arange(-2.5, -0.5, 0.5):
                for yi in nu.arange(-2.5, -0.5, 0.5):
                    # Di=ABCD(1,:).*xi+ABCD(2,:).*yi+ABCD(3,:)+ABCD(4,:).*xi.*yi;W
                    Di = ABCD[0, :]*xi+ABCD[1, :] * \
                        yi+ABCD[2, :]+ABCD[3, :]*xi*yi
                    SumdDi = sum((Di-Dg)**2)
                    if SumdDi < SumdD5:
                        x_opt = xi
                        y_opt = yi
                        SumdD5 = SumdDi
                    else:
                        print 'not found'
                        print x_opt, y_opt
                    pl.append(SumdD5)
            #px = nu.linspace(1, 10, (i+1)*(len(nu.arange(-6, 0, 0.5),)**2))
            if itr == 5:
                # return [x[-1],y[-1]]
                break
            c = nu.array(data['ANC6'])
            SumdD = sum((c-Dg)**2)
            SdD.append(SumdD)
            DN.append(c)
            x[Mindex] = x_opt   #
            y[Mindex] = y_opt   #
    if min(SdD) > 100000:
        #logging.info('All regression results failed on limit! go back default value')
        x_opt = xg
        y_opt = yg
    else:
        x_opt = x[SdD.index(min(SdD))]
        y_opt = y[SdD.index(min(SdD))]
    label = ['FB', 'FF']
    if gui == 1:
        #plt.savefig(AutotrimLogpath+'\\'+'-'+str(date)+' '+str(LorR)+' Curve Dynamic.png')
        # plt.show()
        pass

    # =================================================================================================================
    return [x_opt, y_opt]


if __name__ == '__main__':
    # starttime=datetime.datetime.now()
    try:
        #raw=sys.argv[1].replace('~', '"')
        if os.path.exists(os.getcwd()+u'\\autotrimgui.txt'):
            raw = open(os.getcwd()+u'\\autotrimgui.txt', 'r')
            AutotrimLogpath = raw.read()
            gui = 1
            raw.close()
        inputfile = os.getcwd()+u'\input.txt'
        if os.path.exists(inputfile):
            raw = open(inputfile, 'r')
        else:
            raw = open(os.getcwd()+u'\output.txt', 'w+')
            raw.write('ERROR on input file')
            raw.close()
            raise Exception
        dataA = json.loads(raw.read())
        raw.close()
        # print data
        output = inputcheck(dataA)
        raw = open(os.getcwd()+u'\output.txt', 'w+')
        raw.write(output)
        raw.close()
        # logging.info('Autotrim-R')
        # OP=Autorim_regression_algorithm()
    except Exception:
        syserr = sys.exc_info()
        print syserr
        raw = open(os.getcwd()+u'\output.txt', 'w+')
        raw.write(str(syserr))
        raw.close()
        #logging.info('Err Exception'+str(syserr))
    except:
        syserr = sys.exc_info()
        print syserr
    finally:
        pass
