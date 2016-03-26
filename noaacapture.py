import time
from time import gmtime, strftime
import pypredict
import subprocess
import os

# Satellite names in TLE plus their frequency
satellites = ['NOAA 18','NOAA 15','NOAA 19']
freqs = [137912500, 137620000, 137100000]
# Dongle gain
dongleGain='50'
#
# Dongle PPM shift, hopefully this will change to reflect different PPM on freq
dongleShift='52'
#
# Dongle index, is there any rtl_fm allowing passing serial of dongle? Unused right now
dongleIndex='0'
#
# Sample rate, width of recorded signal - should include few kHz for doppler shift
sample ='41000'
# Sample rate of the wav file. Shouldn't be changed
wavrate='11025'
#
# Should I remove RAWs?
removeRAW='yes'
# Directories used in this program
# wxtoimg install dir
wxInstallDir='/usr/local/bin'
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
#
# Map file directory
#
mapDir='/opt/wxsat/maps'
# Options for wxtoimg / aptdec
# None actually right now, this will hopefully change in upcoming release
wxAddOverlay='no'
wxEnhHVC='no'
wxEnhHVCT='yes'
wxEnhMSA='no'
wxEnhMCIR='yes'
# Various options
# Should this script create spectrogram : yes/no
createSpectro='yes'
# Use doppler shift for correction, not used right now - leave as is
runDoppler='no'

# Read qth file for station data
stationFileDir=os.path.expanduser('~')
stationFilex=stationFileDir+'/.predict/predict.qth'
stationFile=open(stationFilex, 'r')
stationData=stationFile.readlines()
stationName=str(stationData[0]).rstrip().strip()
stationLat=str(stationData[1]).rstrip().strip()
stationLon=str(stationData[2]).rstrip().strip()
stationAlt=str(stationData[3]).rstrip().strip()
stationFile.close()

stationLonNeg=float(stationLon)*-1


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
		'-E','offset',\
		'-p',dongleShift,\
		recdir+'/'+fname+'.raw' ]

    runForDuration(cmdline, duration)

def transcode(fname):
    print 'Transcoding...'
    cmdline = ['sox','-t','raw','-r',sample,'-es','-b','16','-c','1','-V1',recdir+'/'+fname+'.raw',recdir+'/'+fname+'.wav','rate',wavrate]
    subprocess.call(cmdline)
    if removeRAW in ('yes', 'y', '1'):
	os.remove(recdir+'/'+fname+'.raw')

def doppler(fname,emergeTime):
    cmdline = ['doppler', 
    '-d','',\
    '--tlefile', '~/.predict/predict.tle',\
    '--tlename', xfname,\
    '--location', 'lat='+stationLat+',lon='+stationLon+',alt='+stationAlt,\
    '--freq ', +str(freq),\
    '-i', 'i16',\
    '-s', sample ]
    subprocess.call(cmdline)

def createoverlay(fname,aosTime,satName):
    print 'Creating Map Overlay...'
    cmdline = ['wxmap',
    '-T',satName,\
    '-G',stationFileDir+'/.predict/',\
    '-H','predict.tle',\
    '-M','0',\
    '-L',stationLat+'/'+str(stationLonNeg)+'/'+stationAlt,\
    str(aosTime), mapDir+'/'+str(fname)+'-map.png']
    print cmdline
    subprocess.call(cmdline)

def decode(fname,aosTime,satName):
    satTimestamp = int(fname)
    fileNameC = datetime.datetime.fromtimestamp(satTimestamp).strftime('%Y%m%d-%H%M')
    if wxAddOverlay in ('yes', 'y', '1'):
	print 'Creating basic image with overlay'
	createoverlay(fname,aosTime,satName)
	cmdline = [ wxInstallDir+'/wxtoimg','-A','-m', mapDir+'/'+fname+'-map.png',recdir+'/'+fname+'.wav',imgdir+'/'+satname+'/'+fname+'-normal.jpg']
	print cmdline
	subprocess.call(cmdline)
	if wxEnhHVC in ('yes', 'y', '1'):
	    print 'Creating HVC image'
	    cmdline_hvc = [ wxInstallDir+'/wxtoimg','-A','-e','HVC','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+fname+'.wav', imgdir+'/'+satname+'/'+fname+'-hvc.jpg']
	    subprocess.call(cmdline_hvc)
	if wxEnhHVCT in ('yes', 'y', '1'):
	    print 'Creating HVCT image'
	    cmdline_hvct = [ wxInstallDir+'/wxtoimg','-A','-e','HVCT','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+fname+'.wav',imgdir+'/'+satname+'/'+fname+'-hvct.jpg']
	    subprocess.call(cmdline_hvct)
	if wxEnhMSA in ('yes', 'y', '1'):
	    print 'Creating MSA image'
	    cmdline_msa = [ wxInstallDir+'/wxtoimg','-A','-e','MSA','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+fname+'.wav',imgdir+'/'+satname+'/'+fname+'-msa.jpg']
	    subprocess.call(cmdline_msa)
	if wxEnhMCIR in ('yes', 'y', '1'):
	    print 'Creating MCIR image'
	    cmdline_mcir = [ wxInstallDir+'/wxtoimg','-A','-e','MCIR','-m',mapDir+'/'+fname+'-map.png',recdir+'/'+fname+'.wav',imgdir+'/'+satname+'/'+fname+'-mcir.jpg']
	    subprocess.call(cmdline_mcir)
    else:
	print 'Creating basic image without map'
	cmdline = [ wxInstallDir+'/wxtoimg','-A',recdir+'/'+fname+'.wav', imgdir+'/'+satname+'/'+fileNameC+'-normal.jpg']
	subprocess.call(cmdline)
	if wxEnhHVC in ('yes', 'y', '1'):
	    print 'Creating HVC image'
	    cmdline_hvc = [ wxInstallDir+'/wxtoimg','-A','-e','HVC',recdir+'/'+fname+'.wav', imgdir+'/'+satname+'/'+fileNameC+'-hvc.jpg']
	    subprocess.call(cmdline_hvc)
	if wxEnhHVCT in ('yes', 'y', '1'):
	    print 'Creating HVCT image'
	    cmdline_hvct = [ wxInstallDir+'/wxtoimg','-A','-e','HVCT',recdir+'/'+fname+'.wav', imgdir+'/'+satname+'/'+fileNameC+'-hvct.jpg']
	    subprocess.call(cmdline_hvct)
	if wxEnhMSA in ('yes', 'y', '1'):
	    print 'Creating MSA image'
	    cmdline_msa = [ wxInstallDir+'/wxtoimg','-A','-e','MSA',recdir+'/'+fname+'.wav', imgdir+'/'+satname+'/'+fileNameC+'-msa.jpg']
	    subprocess.call(cmdline_msa)
	if wxEnhMSIR in ('yes', 'y', '1'):
	    print 'Creating MSIR image'
	    cmdline_msir = [ wxInstallDir+'/wxtoimg','-A','-e','MCIR',recdir+'/'+fname+'.wav', imgdir+'/'+satname+'/'+fileNameC+'-msir.jpg']
	    subprocess.call(cmdline_msir)

def recordWAV(freq,fname,duration):
    recordFM(freq,fname,duration,xfname)
    transcode(fname)
    if createSpectro in ('yes', 'y', '1'):
	spectrum(fname)

def spectrum(fname):
    # Changed spectrum generation, now it creates spectrogram from recorded WAV file
    # Optional
    print 'Creating flight spectrum'
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
    print "Beginning pass of "+satName+". Predicted start "+aosTimeCnv+" and end "+losTimeCnv+". Will record for "+str(recordTime).split(".")[0]+" seconds."
    recordWAV(freq,fname,recordTime)
    print "Decoding image"
    decode(fname,aosTime,satName) # make picture
    print "Finished pass of "+satName+" at "+losTimeCnv+". Sleeping for 10 seconds"
    # Is this really needed?
    time.sleep(10.0)

