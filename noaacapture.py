import time
from time import gmtime, strftime
import pypredict
import subprocess

# Satellite names in TLE plus their frequency
satellites = ['NOAA 18','NOAA 19','NOAA 15']
freqs = [137912500, 137100000, 137625000]
# Dongle gain
dongleGain='43'
#
# Dongle PPM shift, hopefully this will change to reflect different PPM on freq
dongleShift='-135'
#
# Dongle index, is there any rtl_fm allowing passing serial of dongle? Unused right now
dongleIndex='0'
#
# Sample rate, width of recorded signal - should include few kHz for doppler shift
sample ='48000'
# Sample rate of the wav file. Shouldn't be changed
wavrate='11025'
#
# Old variable, will be removed soon
location='lon=53.3404,lat=-15.0579,alt=20'
#
# Used in doppler tool, the same values as in predict
# hopefully this will change to import from predict QTH file
stationLon='53.3404'
stationLat='-15.0579'
stationAlt='20'
#
# Directories used in wx
# Recording dir, used for RAW and WAV files
#
recdir='/opt/wxsat/rec'
#
# Spectrogram directory, this would be optional in the future
#
specdir='/opt/wxsat/spectro'
#  
# Output image directory
#
imgdir='/opt/wxsat/img'

# Options for wxtoimg / aptdec
# None actually right now, this will hopefully change in upcoming release

# Various options
# Should this script create spectrogram : yes/no
createSpectro='yes'
# Use doppler shift for correction, not used right now - leave as is
runDoppler='no'


def runForDuration(cmdline, duration):
    try:
        child = subprocess.Popen(cmdline)
        time.sleep(duration)
        child.terminate()
    except OSError as e:
        print "OS Error during command: "+" ".join(cmdline)
        print "OS Error: "+e.strerror

def recordFM(freq, fname, duration, xfname):

    cmdline = ['rtl_fm',\
		'-f',str(freq),\
		'-s',sample,\
		'-g',dongleGain,\
		'-F','9',\
		'-A','fast',\
		'-E','dc',\
		'-p',dongleShift,\
		recdir+'/'+fname+'.raw' ]

    runForDuration(cmdline, duration)

def transcode(fname):
    cmdline = ['sox','-t','raw','-r',sample,'-es','-b','16','-c','1','-V1',recdir+'/'+fname+'.raw',recdir+'/'+fname+'.wav','rate',wavrate]
    subprocess.call(cmdline)

def doppler(fname,emergeTime):
    #cmdline = ['sox','-t','raw','-r',sample,'-es','-b','16','-c','1','-V1',recdir+'/'+fname+'.raw',recdir+'/'+fname+'.wav','rate',wavrate]
    cmdline = ['doppler', 
    '-d','',\
    '--tlefile', '~/.predict/predict.tle',\
    '--tlename', xfname,\
    '--location', 'lat='+stationLat+',lon='+stationLon+',alt='+stationAlt,\
    '--freq ', +str(freq),\
    '-i', 'i16',\
    '-s', sample ]
    subprocess.call(cmdline)

def decode(fname):
    cmdline = ['/usr/local/bin/wxtoimg','-A',recdir+'/'+fname+'.wav', imgdir+'/'+fname+'.jpg']
    subprocess.call(cmdline)

def recordWAV(freq,fname,duration):
    recordFM(freq,fname,duration,xfname)
    transcode(fname)
    if createSpectro in ('yes', 'y', '1'):
	spectrum(fname)

def spectrum(fname):
    # Changed spectrum generation, now it creates spectrogram from recorded WAV file
    # Optional
    cmdline = ['sox',recdir+'/'+fname+'.wav', '-n', 'spectrogram','-o',specdir+'/'+fname+'.png']
    subprocess.call(cmdline)

def findNextPass():
    predictions = [pypredict.aoslos(s) for s in satellites]
    aoses = [p[0] for p in predictions]
    nextIndex = aoses.index(min(aoses))
    return (satellites[nextIndex],\
            freqs[nextIndex],\
            predictions[nextIndex]) 

while True:
    (satName, freq, (aosTime, losTime)) = findNextPass()
    now = time.time()
    towait = aosTime-now
    aosTimeCnv=strftime('%H:%M:%S', time.localtime(aosTime))
    emergeTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(aosTime))
    losTimeCnv=strftime('%H:%M:%S', time.localtime(losTime))
    dimTimeUtc=strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(losTime))
    if towait>0:
        print "waiting "+str(towait).split(".")[0]+" seconds (emerging "+aosTimeCnv+") for "+satName
        time.sleep(towait)
    # If the script broke and sat is passing by - change record time to reflect time change
    if aosTime<now:
	recordTime=losTime-now
    elif aosTime>=now:
	recordTime=losTime-aosTime
    # Go on, for now we'll name recordings and images by Unix timestamp.
    fname=str(aosTime)
    xfname=satName
    print "Beginning pass of "+satname+". Predicted start "+aosTimeCnv+" and end "+losTimeCnv+". Will record for "+str(recordTime).split(".")[0]+" seconds."
    recordWAV(freq,fname,recordTime)
    print "Decoding image"
    decode(fname) # make picture
    # spectrum(fname,losTime-aosTime)
    print "Finished pass of "+satname+" at "+losTimeCnv+". Sleeping for 60 seconds"
    # Is this really needed?
    time.sleep(60.0)

