import re
import datetime
import os
import time
import sys
import threading
from sortedcontainers import SortedDict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import imageio
import warnings

#############
###   To use this script, use powershell and the following commands
###   You will need the following installed:     Python3
###   You will need to install the following packages with the commands included from a powershell window: 
###             pip install re
###             pip install datetime
###             pip install os
###             pip install sys
###             pip install SortedDict
###             pip install matplotlib
###             pip install imageio
###       1) CD to a working directory
###         a) cd C:\Users\user\Desktop\tests\FFXIVLogParser-main
###       2) python .\Log_To_GIF.py "FIGHT_NAME" "LOG_FOLDER_NAME"
###         a) python .\Log_To_GIF.py "UWU" "C:\\Users\\user\\AppData\\Roaming\\Advanced Combat Tracker\\FFXIVLogs"
###         b) python .\Log_To_GIF.py "TEA" "C:\\Users\\user\\Desktop\\tests\\ztea"
###         c) python .\Log_To_GIF.py "TEA" "C:\\Users\\user\\Desktop\\tests\\Tea_group2" "gm"
###         d) python .\Log_To_GIF.py "UCoB" "C:\\Users\\user\\Desktop\\tests\\ucob"
#############
fightlist = "TEA,UWU,UCoB,DSU,P4S,P3S,P2S,P1S,E9S,E10S,E11S,E12S,P5S,P6S,P7S,P8S"
fightarray = ["TEA","UWU","UCoB","DSU","P4S","P3S","P2S","P1S","E9S","E10S","E11S","E12S","P5S","P6S","P7S","P8S"]
minFrameDuration = 0.02 #animation stuff
rampUpTime = 5 #animation stuff
rampDownTime = 2 #animation stuff
gifTime = 15 #animation stuff
status = "" ## user update line.
check = False ## was there a checkpoint?
flip = True ## silly logic solver, this is prob a wasted method.
animation = "" ##Do you want a gif or mp4?
fd = True ##First death trigger
phaseClears = [] ##Track the clear time of each phase and calc the averages later.
wipeRegExp = ""
clearRegExp = "" 
startRegExp = ""
logfolder = ""
###########
## List of all fights that I have supported via the timeline and phases
##     FightID is scraped from logs manually and added here.
##     Fight name/list will need to be updated above as new content is added here.
###########
def fightSelect(fightName, logLoc, loop) :
    global fightTitle
    fightTitle = fightName
    global logFolder
    logFolder = logLoc
    global fightID
    global phaseColors
    global phases
    global phaseNames
    global transitions
    status = "Parsing logs for " + str(fightName)
    loop.run_until_complete(statusUpdate(status, color="white"))##TEST
    print("Parsing logs for " + fightName)
    if (fightName == "TEA"):
        fightID = "80037586"
        phaseColors = ['b','r','y','g']
        phases = [2.20,5.5,11.6,18.83]
        phaseNames = ["LL", "BJCC", "Alex Prime", "Perfect"]
    elif (fightName == "UCoB"):
        fightID = "80037569"
        phaseColors = ['b','r','y','c','g']
        phases = [2.7,6.1,11,13.7,17.5]
        phaseNames = ["Twintania", "Nael", "Bahamut", "Adds", "Golden"]
    elif (fightName == "UWU"):
        fightID = "80037573"
        phaseColors = ['b','r','y','g']
        phases = [2.3,5,7.5,14.5]
        phaseNames = ["Garuda", "Ifrit", "Titan", "Ultima"]
    elif (fightName == "DSU"):
        fightID = "8003759A"##UPDATE ME
        phaseColors = ['b','r','y','c','b','r','gold']
        phases = [2.9,6.3,8.4,10.8,13.8,16.8,21.2]
#        phases = [3.32,6.8,8.3,10.5,13,15.7,19.9]
        phaseNames = ["Adelphel","Thordan","Nidhogg","Eyes","Thordan2","NidhoggHrae","DragonKing"]
        transitions = ["of the archbishop", "defeats King Thordan", "defeats Nidhogg", "undone by mortal", "defeats King Thordan", "defeats y", "\|40000003"]
    elif (fightName == "P4S"):
        fightID = "8003759C"
        phaseColors = ['b','r']
        phases = [7,17]
        phaseNames = ["P1","P2"]
    elif (fightName == "P3S"):
        fightID = "8003759E"
        phaseColors = ['b','r','y','darkorange','gold']
        phases = [2.6,4.3,5.8,7,10.9]
        phaseNames = ["P1","Ads","P3","FoF","End"]
    elif (fightName == "P2S"):
        fightID = "800375A2"
        phaseColors = ['b','r','y']
        phases = [4.3,4.5,10.5]
        phaseNames = ["P1","LC","P3"]
    elif (fightName == "P1S"):
        fightID = "800375A0"
        phaseColors = ['b','r','y','c','gold']
        phases = [2,3,4.6,6.9,10]
        phaseNames = ["Phase1","Cells1","Dart1","Cells2","Dart2"]
    elif (fightName == "E9S"):
        fightID = "800375A0"##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [0.9,3.2,4.55,5.9,7.9]
        phaseNames = ["Phase1","Seed1","PVP1","Seed2","PVP2"]
    elif (fightName == "E10S"):
        fightID = "800375A0"##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [3,4.2,7,8.9,11.3]
        phaseNames = ["Phase1","Orbs1","Phase2","PitchBog1","PitchBog2"]
    elif (fightName == "E11S"):
        fightID = "800375A0"##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [8.15,9]
        phaseNames = ["Phase1","Deception","Cycles"]
    elif (fightName == "E12S"):
        fightID = "800375A0"##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [2,3,4.6,6.9,10]
        phaseNames = ["Phase1","Cells1","Dart1","Cells2","Dart2"]
    elif (fightName == "P5S"):
        fightID = "800375A5"##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [2,3.5,4.5,6.1,10]
        phaseNames = ["Phase1","PartyUp","Devour","PartyUp2","Final"]
    elif (fightName == "P6S"):
        fightID = "800375A9"##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [2.3,4.6,6.9,9.2,10.5]
        phaseNames = ["Phase1","Phase2","Phase3","Phase4","Phase5"]
    elif (fightName == "P7S"):
        fightID = ""##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [2,3,4.6,6.9,10]
        phaseNames = ["Phase1","Cells1","Dart1","Cells2","Dart2"]
    elif (fightName == "P8S"):
        fightID = "800375A0"##UPDATE ME
        phaseColors = ['b','r','y','c','gold']
        phases = [2,3,4.6,6.9,10]
        phaseNames = ["Phase1","Cells1","Dart1","Cells2","Dart2"]
    else:
        print("Invalid fight name entered. Please include the fight name in quotes.")
        print(f"Supported fight names are: {fightlist}")
        sys.exit()


###########
## Parses the log files themselves line by line here
##     Logfile is passed from parseFolder, and dict is an empty collection that is returned.
##     Comments throughout the function for readability since it is long.
###########
def parseLog(logFile, dict):
	with open(logFile, 'r', encoding="utf8") as logSource:
		startTime = datetime.datetime(9999,12,31) #ignore me, bound setting
		endTime = datetime.datetime(1,1,1) #ignore me, bound setting
		clear = False #did you clear the fight?
		doorbossdead = False #did the doorboss get taken down?
		firstClear = True #first clear tracker
		global fd
        ####
        ##  Check each line for a fight start trigger, wipe trigger,
        ##    or clear trigger.
        ####
		for i, line in enumerate(logSource):
			startMatch = startRegExp.match(line)
			if startMatch:
				startTime = datetime.datetime(int(startMatch.group(1)),int(startMatch.group(2)),int(startMatch.group(3)),int(startMatch.group(4)),int(startMatch.group(5)),int(startMatch.group(6)))
				fd = True;
			else:
				wipeMatch = wipeRegExp.match(line)
				if wipeMatch:
					endTime = datetime.datetime(int(wipeMatch.group(1)),int(wipeMatch.group(2)),int(wipeMatch.group(3)),int(wipeMatch.group(4)),int(wipeMatch.group(5)),int(wipeMatch.group(6)))
					clear = False
				else:
					clearMatch = clearRegExp.match(line)
					if clearMatch:
						endTime = datetime.datetime(int(clearMatch.group(1)),int(clearMatch.group(2)),int(clearMatch.group(3)),int(clearMatch.group(4)),int(clearMatch.group(5)),int(clearMatch.group(6)))
						clear = True



            ## Did the door boss die here?
			doorbossdead = doorbossDown(fightID, line)

            ##If doorboss just died, dont scuff the timer since it is through the phase anyway.
			if line.find("In pursuit of the archbishop") != -1:#literally just for DSR. Forgiveness trigger for doorboss kill.
				fd = False
			if check: #If the checkpoint was hit, firstClear flips its value
				firstClear = not firstClear
			else: #room reset, default our firstClear
				firstClear=True
			if endTime > startTime: #If valid log time, fill the dict with data!
				duration = (endTime-startTime).total_seconds()/60
				if(doorbossdead): #if doorboss was defeated, add phase0 time to the counter.
					if (not fd):
						dict[startTime] = (duration+.5,clear,doorbossdead,firstClear) #may need to increase .5 if our dps gets any stronger in this phase or everyone pots.
					#	addToPhaseTracker(getPhase(duration+.5), duration+.5)
					else:
						dict[startTime] = (duration+phases[0],clear,doorbossdead,firstClear)
					#	addToPhaseTracker(getPhase(duration+phases[0]), duration+phases[0])
				else: #otherwise add normal time counting.
					dict[startTime] = (duration,clear,doorbossdead,firstClear)
					#addToPhaseTracker(getPhase(duration), duration)
				startTime = datetime.datetime(9999,12,31)
				endTime = datetime.datetime(1,1,1)

###########
## This will check if the line matches a DSR transition.
##   This data will be used to calculate phase averages.
## Eventually I will finish this
###########
def setPhaseTracker():
	global phaseClears
	for i in range(len(phases)):
		x = []
		phaseClears.append(x)

###########
## This will check if the line matches a DSR transition.
##   This data will be used to calculate phase averages.
## Eventually I will finish this
###########
def addToPhaseTracker(line, duration):
	global phaseClears
	if (fightID == "8003759A"): #dsr
		phaseClears[line].append(duration)
		#for i in range(len(transitions)):
			#print(str(transitions[i]) + "    " + str(duration))
		#	if(str(transitions[i]).lower() in line.lower()):
		#		#print(str(transitions[i]) + "  -  " + str(phases[i]) + "   ---   dur: " + str(duration)) 
		#		phaseClears[i].append(duration)

###########
## Get the current phase of the fight
###########
def getPhase(time):
	for i in range(len(phases)):
		if time < phases[i]:
			return i
	return 0
 

###########
## Called function to check if the arena was just entered or if the
##     fight has a doorboss. If a doorboss is listed (doorquote check)
##     then  returns a value accordingly via check.
###########
def doorbossDown(fightID, line):
	global check
	if (fightID == "8003759C"): #p4s
		doorquote = "Hesperos|Do not believe victory yours... I can yet shed this"
		enterquote = "Asphodelos: The Fourth Circle (Savage) has begun"
		if(doorquote.lower() in line.lower()):
			check = True
		elif(enterquote.lower() in line.lower()):
			check = False
	elif (fightID == "8003759A"): #dsr
		enterquote = "Dragonsong's Reprise (Ultimate) has begun."
		doorquote = "In pursuit of the archbishop, the Warrior of Light journeyed to Azys"
		if(doorquote.lower() in line.lower()):
			check = True
		elif(enterquote.lower() in line.lower()):
			check = False
	elif (fightID == "p12s"): #p12s
		doorquote = "Do not believe victory yours... I can yet shed this"
	elif (fightID == "p8s"):
		doorquote = "Do not believe victory yours... I can yet shed this"
	elif (fightID == "e12s"):
		doorquote = "Do not believe victory yours... I can yet shed this"
	elif (fightID == "idk"):
		doorquote = "Do not believe victory yours... I can yet shed this"
	elif (fightID == "somethingeventually"):
		doorquote = "Do not believe victory yours... I can yet shed this"
	else:
		check = False
	return check

###########
## First off, I'm sorry to whoever, myself included, is reading over the code here.
##   This is the meat of the script, and it has become quite sloppily done.
## Main function of the script. The descriptions will be broken down as we go.
###########
def parseFolder(loop, daynum=None):
	dict = SortedDict() #will store fight data for each pull/event.
	global animation #var checking if you want a gif or mp4
	global flip #shit var that I now need.
	global logfolder
	warnings.filterwarnings("ignore")
	flip = True #ihateyou.gif
	i = 1
	totalFiles = len(os.listdir(logFolder))
	for filename in os.listdir(logFolder):#Lets parse some loggies!
		print(f'File %i of {totalFiles}' % i, end="\r")
		status = "Parsing file " + str(i) + " of " + str(totalFiles) + "."
		loop.run_until_complete(statusUpdate(status, color="white"))##TEST
		i += 1
		parseLog(logFolder+"\\\\"+filename,dict)
		if i == totalFiles+1:
			status = "Creating PNG graphs!"
			loop.run_until_complete(statusUpdate(status, color="white"))##TEST	
	status = "Creating PNG graphs!"
	print(f'%s ' % status, end ="\r")
	loop.run_until_complete(statusUpdate(status, color="white"))##TEST


	plt.xlabel("Pull #")
	plt.ylabel("Duration (min)")
	plt.figure(figsize=(16,9.12))#chart size I use.
	adjustedPhases = [0] + phases
    ##Set the background
	for iPhase in range(len(phases)):
		plt.axhspan(adjustedPhases[iPhase], adjustedPhases[iPhase+1], facecolor=phaseColors[iPhase], alpha=0.1)
	filenames = []
	t = datetime.timedelta()
	a = datetime.timedelta()

	wipecount = []
	wipecount = [0 for i in range(7)]
	## Setting up gif duration bits here.
	rampUpIdx = len(dict)
	rampDownIdx = 0
	try: 
 	   frameDuration = gifTime/len(dict)
	except ZeroDivisionError:
 	   status = "Fight not found in folder"
 	   loop.run_until_complete(statusUpdate(status, color="red"))##TEST
 	   return "0"
	frameStep = 1

	if frameDuration < minFrameDuration:
		frameDuration = minFrameDuration
		rampUpIdx = rampUpTime/frameDuration
		rampDownIdx = rampDownTime/frameDuration
		frameStep = (len(dict) - rampUpIdx - rampDownIdx) / ((gifTime - rampUpTime - rampDownTime) / frameDuration)
		
    ####
    ## This iterates through the entire dict of data and will create a png frame for each pull (wipe or clear)
    ####
	
	for j in range(len(dict)):
		# Dot plotting
		phaseNum = getPhase(dict.peekitem(j)[1][0])
		if dict.peekitem(j)[1][1]: #if the pull is a clear, plot a star on the chart
			if (dict.peekitem(j)[1][2]): #Did the fight have a doorboss already killed?
				plt.plot(j, dict.peekitem(j)[1][0], color='yellow', marker='*', markeredgecolor='gray', markersize=10)
			elif not (dict.peekitem(j)[1][2]):
				plt.plot(j, dict.peekitem(j)[1][0], color='yellow', marker='*', markeredgecolor='gray', markersize=10)
		else: #if the pull was not a clear, mark with a blue dot.
			#plt.plot(j, dict.peekitem(j)[1][0], color=phaseColors[phaseNum], marker='o', markersize=5)##Use phase colors for dots. Not sure if i want to add other color options here.
			plt.plot(j, dict.peekitem(j)[1][0], color='blue', marker='o', markersize=5) ##just blue dots
		if (dict.peekitem(j)[1][2]):
			t += datetime.timedelta(seconds=(int(dict.peekitem(j)[1][0]-int(float(phases[0])))*60)) ## Double check me
		else:
			t += datetime.timedelta(seconds=int(dict.peekitem(j)[1][0]*60))

		a = t/(j+1)
		a = str(a) #average pull time for prog trackin!:D
		if re.search("^[0-9]*:",a) is True :
			a = a[:8]
		else :
			a = a[:7]
		plt.title(f"{fightTitle} prog : {j+1} pulls ({t} combat time)   (Average pull time: {a})")
		
		# Legend
		patches = []
		counted = False
        ## Make the legend for each frame. I'm sorry about the logic here
		for iPatch in range(len(phases)):
			if(flip and not dict.peekitem(j)[1][3]):
				flip = False #If flip is true, firstClear is just triggered. Swap it.
			elif (not flip and dict.peekitem(j)[1][3]):
				flip = True #if firstClear is not triggered, flip needs to be re-enabled.
			if(not flip and not dict.peekitem(j)[1][3]):
				iPatch = iPatch+1 #if flip and firstClear are triggered, you need to add to the next phase.
			if (not counted and dict.peekitem(j)[1][0] < phases[iPatch]): #finally we can do something here
				counted = True #this patch is being processes
				if (dict.peekitem(j)[1][2]): #doorbossdead 
					if (dict.peekitem(j)[1][3]): #firstClear
						wipecount[iPatch] += 1 
					else: #not firstClear
						wipecount[iPatch] += 1
				else: #No doorbossdead, act normal <_<   >_>
					wipecount[iPatch] += 1
			if(not flip and not dict.peekitem(j)[1][3]):
				iPatch = iPatch-1 #undo our modification here so logic flows normal.

			patches += [mpatches.Patch(color=phaseColors[iPatch], label=(phaseNames[iPatch]) + f": {wipecount[iPatch]}")]
		plt.legend(handles=patches, loc="upper left")
		
		# create file name and append it to a list
		if j < rampUpIdx or j > (len(dict) - rampDownIdx) or (j - rampUpIdx)%int(frameStep) == 0:
			filename = f'{j}.png'
			filenames.append(filename)
			# save frame
			plt.savefig(filename)
		
	# build gif
    ##just let this be, it will give you an aspect warning, but every solution I try
    ##  to throw in causes a different one. This way works fine, ignore the warning.
	now = datetime.datetime.now()
	name =" {}-{}".format(now.month, now.day)
	gifname=name+"_summary.gif"
	mp4name=name+"_summary.mp4"
	if (animation.find("g") != -1): ##make gif
		status = "Assembling GIF. Please wait.      "
		print(f'%s ' % status, end ="\r")
		loop.run_until_complete(statusUpdate(status, color="white"))##TEST
		with imageio.get_writer(gifname, format='GIF-PIL', mode='I', loop = 1, duration=frameDuration, subrectangles=True) as writer:
			for filename in filenames:
				image = imageio.imread(filename)
				writer.append_data(image)
	if (animation.find("m") != -1): ##make mp4
		status = "Assembling mp4. Please wait.      "
		print(f'%s ' % status, end ="\r")
		loop.run_until_complete(statusUpdate(status, color="white"))##TEST
		with imageio.get_writer(mp4name, fps=30) as writer2: #30 seems fine, right?
			for filename in filenames:
				image = imageio.imread(filename)
				writer2.append_data(image)
	status = "Cleaning  up files                "
	print(f'%s ' % status, end ="\r")
	loop.run_until_complete(statusUpdate(status, color="white"))##TEST
	for filename in set(filenames[:-1]):##leave the last image so you have a png too!
		os.remove(filename)
	if daynum:
		os.rename(filenames[len(filenames)-1],("day"+daynum+".png"))
	print("Gif, MP4 and PNG complete! All done!")
	status = "Charts Complete! All done!"
	loop.run_until_complete(statusUpdate(status, color="lightgreen"))##TEST
	loop.close()


####
## Typical argument amount checker and input check. 
## Cannot confirm anything about folder path. 
####
def main(fitename, logfolder2, ani, loop, daynum=None):
    global wipeRegExp,clearRegExp,startRegExp
    if fitename not in fightarray:
        print(f"Invalid fight name entered. \n\nSupported fight names are: {fightlist}\n")
        sys.exit()
    elif fitename in fightarray:
        fightSelect(fitename,logfolder2, loop)
    elif fitename in fightarray:
        animation = ani.lower()
    else:
        print("Invalid arguments provided. Please enter fight name and log folder path.")
    
###########
## Regex checks for fight, wipe, and start of combat.
###########    
    wipeRegExp = re.compile(r"33\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|"+fightID+"\|40000005.*")
    clearRegExp = re.compile(r"33\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|"+fightID+"\|40000003.*")
    startRegExp = re.compile(r"00\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|0039\|\|Engage!\|.*")
    setPhaseTracker()
    try:
        import Latest_file_grab
    except ImportError:
        pass
    
    return parseFolder(loop,daynum)
    
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
from tkinter.ttk import Combobox
import customtkinter
from PIL import Image, ImageTk
import subprocess
import asyncio
from threading import Thread

window=Tk()
window.resizable(width=False, height=False)

global logfolder3,ani,fitename,daynum,loop

def browse_button():
    global folder_path, logfolder3, logfolder
    filename = filedialog.askdirectory()
    temp = filename.replace("/", "\\")
    folder_path.set(str(temp))
    logfolder3 = temp

def get_animation():
    global animation
    animation = "p"
    if v2.get()==1:
        animation += "g"
    if v3.get()==1:
        animation += "m"

def get_fightname():
    global fitename
    fitename = ""
    fitename = cb.get()
    
def get_daynum():
    global daynum
    daynum = ""
    daynum = daynumBox.get()

def graceful_end():
    global loop
    #if loop:
    #    loop.close()
    window.destroy()

async def statusUpdate(status, color=None):
    window.update()
    if color:
        tcolor = color
    else:
        color = "white"
    statuslabel.configure(text=status, text_color=color)

def start_parse():
    global logfolder3,fitename,animation,daynum, loop
    get_animation()
    get_fightname()
    get_daynum()
    loop = asyncio.get_event_loop()
    if (logfolder3 == ""): 
        status = "Missing LogFolder. Please ensure the log folder is found."
        loop.run_until_complete(statusUpdate(status, color="red"))##TEST
        return
    if (fitename == ""): 
        status = "Missing Fightname. Please ensure a fight is selected."
        loop.run_until_complete(statusUpdate(status, color="red"))##TEST
        return
    t1 = Thread(target=main, args=(fitename, logfolder3, animation, loop, daynum))
    c = t1.start()
    if c == "0":
        status = "Fight not found in folder."
        loop.run_until_complete(statusUpdate(status, color="red"))##TEST
    else: 
        status = "Job Complete!"
global logfolder3,ani,fitename
logfolder3 = ""
animation = ""
fitename = ""

fightSelectLabel = Label(master=window,text="Choose the fight to parse:")
fightSelectLabel.place(x=20, y=460)

bgimg = Image.open("images/sample.png")
bgimg = bgimg.resize((450, 350))
render = ImageTk.PhotoImage(bgimg)
img = Label(window, image=render)
img.image = render
img.place(x=0, y=0)

data=fightarray
cb=customtkinter.CTkComboBox(window, values=data)
cb.set("DSU")
cb.place(x=25, y=485)

lbl3 = customtkinter.CTkLabel(master=window,text="Do you want a gif or mp4? Optional.", text_color="black")
lbl3.place(x=20, y=415)
v2 = IntVar()
v3 = IntVar()
C2 = customtkinter.CTkCheckBox(window, text = "GIF", variable = v2, text_color="black")
C3 = customtkinter.CTkCheckBox(window, text = "MP4", variable = v3, text_color="black")
C2.place(x=20, y=440)
C3.place(x=90, y=440)

folder_path = StringVar()
lbl3 = customtkinter.CTkLabel(master=window,textvariable=folder_path, fg_color="gray",width=250)
lbl3.place(x=20, y=390)

status = "Awaiting user input. Press START when ready."

statuslabel = customtkinter.CTkLabel(master=window,text=status,fg_color="gray", width=350)
statuslabel.place(x=50, y=525)

lbl1 = Label(master=window,text="Select the folder your logs are in:")
lbl1.place(x=20, y=365)
button2 = customtkinter.CTkButton(window,text="Browse", command=browse_button)
button2.place(x=300, y=390)

startBTN = customtkinter.CTkButton(window,text="START", command=start_parse)
startBTN.place(x=300, y=480)

daylabel = customtkinter.CTkLabel(master=window,text="Day: ", text_color="black",width=35)

daynumBox = customtkinter.CTkEntry(master=window, placeholder_text = "##", width = 50, text_color="white")
daylabel.place(x=350, y=440)
daynumBox.place(x=390, y=440)

window.protocol("WM_DELETE_WINDOW", graceful_end)

window.title('FFXIV Folder Parser!')
window.geometry("450x565+10+10")
window.mainloop()