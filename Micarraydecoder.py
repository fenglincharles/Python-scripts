# -*- coding: utf-8 -*
#
#Name: Jabil-AUT Mic array wav file decoder for Enterprise project
#Propouse:
                    #This file is created for decoding Mic array's multi-channel wav file with empty header
                    #Use regression Algorithm makes autotrim-R powerful on reaching best gain value with limited iteration
#
#Required HW:
                               
#Required SW:
                                #Python 2.7
#Required OS:
                                #Windows
#Creadted by: CL
#Last Modify: 20181128
print '**Jabil Product - AUT Mic array wav file decoder for Enterprise project**\n**Working Dir = C:\AUT_Files**'
import sys,os,wave
from numpy import memmap
from matplotlib import pyplot
workingdir=r'C:\AUT_Files'
try:
                    micarrayfile=sys.argv[1]
                    processfile=micarrayfile
except:
                    print 'argv error, use path C:\AUT_Files\testmic.wav'
                    processfile=workingdir+r'\testmic.wav'
#processfile=workingdir+r'\testmic.wav'
channelnum=8
if os.path.exists(workingdir)==False :
                    os.mkdir(workingdir)
if os.path.exists(processfile)==False:
                    raise EOFError,'No process file found'
data0 = memmap(processfile, dtype='int32', mode='readonly')
data=data0
data=data[43:]
#pyplot.figure(1)
#pyplot.subplot(211)
#pyplot.plot(data[::8])
#pyplot.show()
for i in range(channelnum):
                    pcmfile=open(workingdir+r'\tempPCMmic.pcm', 'wb+')
                    data[i::channelnum].tofile(pcmfile)
                    pcmfile.close()
                    pcmfile=open(workingdir+r'\tempPCMmic.pcm', 'rb')
                    pcmdata = pcmfile.read()
                    wavfile=wave.open(workingdir+'\WAVmic'+str(i+1)+'.wav', 'wb')
                    wavfile.setparams((1, 4, 16000, 0, 'NONE', 'NONE'))
                    wavfile.writeframes(pcmdata)
                    wavfile.close()
