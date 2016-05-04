import subprocess
import sys
import time
import subprocess
import re
import numpy

#A version of this module which can seek a set minimum elevation of a pass 
#Heavily modified by kols - original by HanYangZhao/dr. Paul Brewer

#First, let's set the minimum elevation
min_elev = 45 

class missingSatellitePredictionError(Exception):
    def __init__(self):
        self.description = "predict did not return data for the satellite"

    def __str__(self):
        return self.description

format = "%Y-%m-%d %H:%M:%S"
def time_converter(time_in):
  epoch = time.mktime(time.strptime(time_in,format)) 
  return epoch


def aoslos(satname):
    time_now = time.strftime(format) 
    epoch_now = time_converter(time_now)  
    epoch_future = epoch_now 

    print "Seeking passes with minimum elevetation of %s..." % min_elev
    while True:
      try:
        epoch_future += 5 #seeking 5 seconds into the future

        cmd = "predict -p '%s' %d" % (satname, epoch_future)
        #print cmd
        lines = subprocess.check_output([cmd], shell=True).split("\n")
        passes = []
        for i in range(len(lines)-1):
          line = re.split("\s", lines[i])
          if line[6]: #This part
            elevation = int(line[6])
            time_prediction = line[0]
          if line[7]: #and this part is due to silly formatting from predict
            elevation = int(line[7])
            time_prediction = line[0]
          passes.append([elevation, time_prediction])

        if max(passes)[0] < min_elev:
          pass
        else:
          aosTime = int(passes[0][1])
          max_elev = max(passes) #Not important here, but is max of group
          losTime = int(passes[len(passes)-1][1])
          #some debuggers...
          #print aosTime
          #print max_elev
          #print losTime
          #for i in lines:
          #  print i
          break
      except Exception:
        raise missingSatellitePredictionError()

    return (aosTime, losTime)
