# runtimeInfo.py: a demo showing some use-cases for class core.RuntimeInfo() and core.msPerFrame()

# these are used in the demo, in the way you might in your experiment:
__author__ = 'Jeremy "R." Gray' # double-quotes will be silently removed
__version__ = "v1.0 a' " # single quotes are left alone, eg, O'Connor 

from psychopy import core, visual

# when creating an experiment, define your window (& monitor):
myWin = visual.Window((200,200), fullscr=1, monitor='testMonitor',allowGUI=False)
    # fullscr=True gives better timing (100x smaller SD in some cases)

# then gather run-time info, and save in a dict-like object. All parameters are optional:
info = core.RuntimeInfo(
        author=__author__+'; <-- your name goes here (plus whatever else, e.g., email)',
        version=__version__+"; <-- your experiment version info",
        verbose=True, # True means report on everything
        win=myWin,    # a psychopy.visual.Window() instance
        progressBar=True # some eye-candy to avoid a blank screen
        ) 

print """
System and other run-time configuration is now saved in "info", a dict-like object. You have to decide
what to do with it--probably print some or all of it, likely into a data file or other log file.

"print info" will give you the same as "print str(info)". This format is intended to be useful 
for writing to a data file in a human readable form:
"""
print info
print """If that's more detail than you want in every data file, try verbose = False."""

print """
Here's the same info in python syntax. To get this, use "print repr(info)". You could write this format into 
a data file, and its fairly readable, only slightly less than the str(info) version. But because its 
python syntax you could later simply import your data file into python to reconstruct the dict:
"""
print "info = %s" % repr(info)

print """
Because info is a dict, you can extract single items using their keys, e.g.:
  psychopy_version = %s""" % info['psychopy_version']
print "  msPerFrameAvg (average all samples, at least 50) = %s" % info["msPerFrameAvg"]
print "  msPerFrameMd6 (average of 6 samples taken at the median) = %s" % info["msPerFrameMd6"]
print "  msPerFrameSD (standard deviation of all samples, at least 50) = %s" % info["msPerFrameSD"],

# in key: value pairs, most values are strings: type(info["win__isFullScr"]) == type('abc')
# but you can eval() them:
if eval(info["win__isFullScr"]): print "(full-screen)"
else: print "(NOT full-screen)"

# some keys are only conditionally present, depending on what RuntimeInfo you ask for
# sometimes you need to check if a key exists before using it:
try: 
    print "  monitor = %s" % info["win_monitor.name"]
except:
    pass
    