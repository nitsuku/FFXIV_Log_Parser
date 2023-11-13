##Version:12

import threading
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
import glob
from shutil import copyfile, copy2, rmtree

status = ""
statuscolor = "white"
working = False
minFrameDuration = 0.02 #animation stuff
rampUpTime = 5 #animation stuff
rampDownTime = 2 #animation stuff
gifTime = 15 #animation stuff
check = False ## was there a checkpoint?
flip = True ## silly logic solver, this is prob a wasted method.
animation = "" ##Do you want a gif or mp4?
fd = True ##First death trigger
phaseClears = [] ##Track the clear time of each phase and calc the averages later.

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
					else:
						dict[startTime] = (duration+phases[0],clear,doorbossdead,firstClear)
				else: #otherwise add normal time counting.
					dict[startTime] = (duration,clear,doorbossdead,firstClear)
				startTime = datetime.datetime(9999,12,31)
				endTime = datetime.datetime(1,1,1)


###########
## Get the current phase of the fight
###########
def getPhase(time):
	for i in range(len(phases)):
		if time < phases[i]:
			return i
	return 0
 
def parseFolder(daynum=None):
	dict = SortedDict() #will store fight data for each pull/event.
	global animation #var checking if you want a gif or mp4
	global flip #shit var that I now need.
	flip = True #ihateyou.gif
	global status, statuscolor
	i = 1
	totalFiles = len(os.listdir(logFolder))
	for filename in os.listdir(logFolder):#Lets parse some loggies!
		status = (f'Parsing %i of {totalFiles} logs. Please wait.' % i)
		statuscolor = "Blue"
		i += 1
		parseLog(logFolder+"\\"+filename,dict)
	plt.switch_backend('agg')
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
	frameDuration = gifTime/len(dict)
	frameStep = 1
	if frameDuration < minFrameDuration:
		frameDuration = minFrameDuration
		rampUpIdx = rampUpTime/frameDuration
		rampDownIdx = rampDownTime/frameDuration
		frameStep = (len(dict) - rampUpIdx - rampDownIdx) / ((gifTime - rampUpTime - rampDownTime) / frameDuration)
	status = "Creating PNG graphs!              "
	#print(f'%s ' % status, end ="\r")		
	status = "Creating PNG graphs!              "
	statuscolor = "White"
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
			if (j > 1618):
				plt.plot(j, dict.peekitem(j)[1][0], color='red', marker='o', markersize=5) ##just blue dots
			else:
				plt.plot(j, dict.peekitem(j)[1][0], color='blue', marker='o', markersize=5) ##just blue dots
		#plt.plot(j, dict.peekitem(j)[1][0], color='blue', marker='o', markersize=5) ##just blue dots
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
			if (((animation.find("g") != -1) or (animation.find("m") != -1)) or (j == len(dict)-1)):
				status = (f'Graphing pull %i of {len(dict)-1} logs. Please wait.' % j)
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
		statuscolor="Blue"
		with imageio.get_writer(gifname, format='GIF-PIL', mode='I', loop = 1, duration=frameDuration, subrectangles=True) as writer:
			for filename in filenames:
				image = imageio.imread(filename)
				writer.append_data(image)
	if (animation.find("m") != -1): ##make mp4
		status = "Assembling MP4. Please wait.      "
		statuscolor="Blue"
		with imageio.get_writer(mp4name, fps=30) as writer2: #30 seems fine, right?
			for filename in filenames:
				image = imageio.imread(filename)
				writer2.append_data(image)
	status = "Cleaning  up files                "
	statuscolor = "White"
	for filename in set(filenames[:-1]):##leave the last image so you have a png too!
		os.remove(filename)
	if daynum:
		os.rename(filenames[len(filenames)-1],("day"+daynum+".png"))
	status = "Graphs complete! Check the folder for results"
	statuscolor = "lightgreen"
	return 

    
def fightSelect(fightName, logLoc) :#, loop) :
    global fightTitle
    fightTitle = fightName
    global logFolder
    logFolder = logLoc
    global fightID
    global phaseColors
    global phases
    global phaseNames
    global transitions
    global working
    global status, statuscolor
    status = "Parsing logs for " + str(fightName)
    statuscolor = "White"
    working = True
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
        phases = [2.9,6.3,8.4,10.8,14.3,17.2,22]
        #phases = [2.74,6,8,10.35,13.1,15.75,20.12]
        phaseNames = ["Adelphel","Thordan","Nidhogg","Eyes","Thordan2","NidhoggHrae","DragonKing"]
        transitions = ["of the archbishop", "Though she emerged victorious", "I would ask one last favor", "you are unharmed?", "Undone by mortal will", "I am become a god eternal", "defeats Dragon-king"]
    elif (fightName == "TOP"):
        fightID = "800375AC"##UPDATE ME
        phaseColors = ['b','r','y','c','m','g']
        phases = [2.17,4.55,7.35,8.3,13.07,17.59]
        phaseNames = ["Omega", "Omega-MF", "Omega-Recon", "Blue Screen", "Dynamis", "Alpha Omega"]
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
    setRegex()
    
def setRegex():
    global wipeRegExp,clearRegExp,startRegExp
    wipeRegExp = re.compile(r"33\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|"+fightID+"\|40000005.*")
    clearRegExp = re.compile(r"33\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|"+fightID+"\|40000003.*")
    startRegExp = re.compile(r"00\|([0-9]*)-([0-9]*)-([0-9]*)T([0-9]*):([0-9]*):([0-9]*).*\|0039\|\|Engage!\|.*")

def update_logs(fp, logcol):
    folder_path = fp
    file_type = '\*log'
    files = glob.glob(folder_path + file_type)
    max_file = os.path.basename(max(files, key=os.path.getctime))
    logfile=folder_path + "\\" + max_file

##Copy to DSR folder
    dest = logcol + "\\" + max_file
    copy2(logfile, dest)


def startApplication():

    from tkinter import Label, Tk, Button, StringVar, IntVar, BooleanVar
    from tkinter import filedialog
    from tkinter import messagebox
    from tkinter.ttk import Combobox
    import customtkinter
    from PIL import Image, ImageTk
    import subprocess
    import asyncio
    from threading import Thread, Event
    import warnings
    import logging
    import difflib

    logging.basicConfig(filename='application.log', level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')

    class BaseGui:
        global fightarray
        fightarray = ["TEA","UWU","UCoB","DSU","TOP"]##to be updated/removed

        def __init__( self, master ):
            self.master = master
            master.title('FFXIV Folder Parser!')
            master.geometry("450x620+10+10")
            master.resizable(width=False, height=False)
            self.thread = None
            self.stop_event = Event()
            self.running = BooleanVar()
            self.running.set(False)
            self.final_status = BooleanVar()
            self.final_status.set(False)
            self.lock = threading.Lock()
            self.logfolder3 = ""
            self.animation = ""
            self.fitename = ""
            self.daynum = ""
            ##Image section
            self.bgimg = Image.open("images/background.png")
            self.bgimg = self.bgimg.resize((450, 350))
            self.render = ImageTk.PhotoImage(self.bgimg)
            self.img = Label(root, image=self.render)
            self.img.image = self.render
            self.img.place(x=0, y=0)

            ##Log folder section
            self.fightLabel = Label(master=root,text="Select the folder your logs are in:")
            self.fightLabel.place(x=20, y=365)
            self.browseButton = customtkinter.CTkButton(root,text="Browse", command=self.browse_button)
            self.browseButton.place(x=300, y=390)
            self.folder_path = StringVar()
            self.folderLabel = customtkinter.CTkLabel(master=root,textvariable=self.folder_path, fg_color="gray",width=250)
            self.folderLabel.place(x=20, y=390)
            ##Fight selection section
            fightSelectLabel = Label(master,text="Choose the fight to parse:")
            fightSelectLabel.place(x=20, y=475)
            self.data=fightarray
            self.fightsCombo=customtkinter.CTkComboBox(root, values=self.data)
            self.fightsCombo.set("TOP") ##DEFAULT APPEARANCE. Change if you are progging just one fight for ease.
            self.fightsCombo.place(x=25, y=500)
            ##Gif an animation section
            self.aniLabel = customtkinter.CTkLabel(master=root,text="Do you want a gif or mp4? Optional.", text_color="black")
            self.aniLabel.place(x=20, y=425)
            self.gifVal = IntVar()
            self.mp4Val = IntVar()
            self.gifCheck = customtkinter.CTkCheckBox(root, text = "GIF", variable = self.gifVal, text_color="black")
            self.mp4Check = customtkinter.CTkCheckBox(root, text = "MP4", variable = self.mp4Val, text_color="black")
            self.gifCheck.place(x=20, y=450)
            self.mp4Check.place(x=90, y=450)
            ##Status updater section
            self.statusTxt = StringVar(value="Awaiting user input. Press START when ready.")
            self.statusClr = ""
            self.statusClr = "white"
            self.statuslabel = customtkinter.CTkLabel(master=root,textvariable=self.statusTxt,fg_color="gray", text_color=self.statusClr, width=350)
            self.statuslabel.place(x=50, y=535)

            ##Start button!
            self.startBTN = customtkinter.CTkButton(root,text="START", command=self.start_parse)
            self.startBTN.place(x=300, y=490)
            
            ##Prog Day section
            self.daylabel = customtkinter.CTkLabel(master=root,text="Day: ", text_color="black",width=35)
            self.daynumBox = customtkinter.CTkEntry(master=root, placeholder_text = "##", width = 50, text_color="white")
            self.daylabel.place(x=350, y=450)
            self.daynumBox.place(x=390, y=450)

            ##ACT file section
            self.fetchActLabel = customtkinter.CTkLabel(master=root,text="Do you want to add the latest log to your logfolder?", text_color="black")
            self.fetchActLabel.place(x=20, y=565)
            self.fetchACT = IntVar()
            self.fetchACTStatus = StringVar(value="No")
            self.fetchACTCb = customtkinter.CTkCheckBox(root, textvariable=self.fetchACTStatus, variable = self.fetchACT, text_color="black", command=self.toggle_act)
            self.fetchACTCb.place(x=20, y=590)

            self.actFolderLabel = Label(master=root,text="Select the folder your ACT writes to:")
            self.actFolderLabel.place(x=20, y=620)
            self.browseACT = customtkinter.CTkButton(root,text="Browse", command=self.browse_act)
            self.browseACT.place(x=300, y=640)

            self.act_folder_path = StringVar(value=str(os.path.expanduser("~"))+"\\AppData\Roaming\Advanced Combat Tracker\FFXIVLogs")
            self.actLabel = customtkinter.CTkLabel(master=root, width=250,textvariable=self.act_folder_path,fg_color="gray",wraplength=250)
            self.actLabel.place(x=20, y=640)
            ##NEW HERE
            # Add a button for update check
            self.update_button = customtkinter.CTkButton(root, text="Check for Updates", command=self.check_for_updates)
            self.update_button.place(x=20, y=590)

            # Add a status line
            self.status_line = customtkinter.CTkLabel(master=root, text="", fg_color="black")
            self.status_line.place(x=20, y=620)
            
            
        def check_for_updates(self):
            repo_url = "https://github.com/nitsuku/FFXIV_Log_Parser.git"
            update_available = self.is_update_available(repo_url)

            if update_available:
                self.update_status_line("Update Available")
            else:
                self.status_line.config(text="")  # Hide the status line if no update available



        def is_update_available(self, repo_url):
            try:
                remote_file_url = f"{repo_url.rstrip('/')}/blob/main/Log_Parser.py"

                # Fetch the first line of the remote file
                remote_first_line = subprocess.run(['curl', '-s', remote_file_url], capture_output=True, text=True).stdout.splitlines()[0]

                # Extract version information using regex
                remote_version_match = re.match(r'##Version:(\d+\.\d+)', remote_first_line)
                if remote_version_match:
                    remote_version = remote_version_match.group(1)
                else:
                    raise RuntimeError("Unable to retrieve remote version information.")

                # Read the first line of the local file
                local_file_path = os.path.realpath(__file__)  # Assuming the script is in the same directory
                with open(local_file_path, 'r', encoding='utf-8') as local_file:
                    local_first_line = local_file.readline()

                # Extract version information from the local file
                local_version_match = re.match(r'##Version:(\d+\.\d+)', local_first_line)
                if local_version_match:
                    local_version = local_version_match.group(1)
                else:
                    raise RuntimeError("Unable to retrieve local version information.")

                # Compare the versions
                return float(remote_version) > float(local_version)

            except Exception as e:
                self.update_status_line(f"An error occurred: {e}")
                return False
                
        def update_status_line(self, message):
            self.status_line.configure(text=f"Status: {message}")
            ##End NEW

        def browse_button(self):
            filename = filedialog.askdirectory()
            temp = filename.replace("/", "\\")
            self.folder_path.set(str(temp))

        def browse_act(self):
            filename = filedialog.askdirectory(initialdir=str(os.path.expanduser("~"))+"\\AppData\Roaming\Advanced Combat Tracker\FFXIVLogs")
            temp = filename.replace("/", "\\")
            self.act_folder_path.set(str(temp))

        def get_animation(self):
            global animation
            animation = "p"
            if self.gifVal.get()==1:
                animation += "g"
            if self.mp4Val.get()==1:
                animation += "m"
            return animation

        def get_fightname(self):
            global fitename
            fitename = ""
            fitename = self.fightsCombo.get()
        
        def get_daynum(self):
            daynum = ""
            daynum = self.daynumBox.get()

        def statusUpdate(self, upd=None):
            self.statusTxt.set(status)
            self.statusClr = str(statuscolor)
            self.statuslabel.configure(text_color=str(self.statusClr)) 
        def start_status_update(self):
            self.statusUpdate()
            self.final_status.set(False)
            self.master.after(500, self.start_status_update)         

        def final_status_update(self):
            self.statusUpdate()
            self.final_status.set(True)
            
        def close(self) :
            logging.debug("Closing the application.")
            self.master.quit()
            
        ##Starts the processing of the log data
        ##Threads the heavy processing section
        def start_parse(self):
            global status,statuscolor
            self.get_animation()
            self.get_fightname()
            self.get_daynum()
            self.statusUpdate(self)
            if self.folder_path.get()=="": 
                status = "Missing LogFolder. Please ensure the log folder is found."
                statuscolor = "red"
                self.statusUpdate()
                return
            elif (self.fightsCombo.get() == ""): 
                status = "Missing Fightname. Please ensure a fight is selected."
                statuscolor = "red"
                self.statusUpdate()
                return
            else: 
                if (self.fetchACTCb.get()):
                    update_logs(str(self.act_folder_path.get()),str(self.folder_path.get()))
                fightSelect(self.fightsCombo.get(), self.folder_path.get())
                self.statusUpdate()
                day = (str(self.daynumBox.get()))
                with self.lock:  # Acquire the lock before modifying the thread and running state
                    if self.thread == None:
                        self.thread = Thread(target=self.begin, args=(day,))
                        self.thread.start()
                        self.running.set(True)
                        self.master.after(100, self.check_thread_completion)
                    else:
                        self.thread = None
                        status = "Please press START when ready."
                        statuscolor = "White"
                return
        def check_thread_completion(self):
            if self.thread and self.thread.is_alive():
                self.master.after(100, self.check_thread_completion)  # Check again after 100ms
            else:
                self.running.set(False)
            
        def thread_completed(self):
            self.statusUpdate()
            self.thread.join()
            #print("Thread completed.")

                
        def begin(self, day):
            self.running.set(True)
            parseFolder(day)
        ##Toggles the ACT section of the gui
        def toggle_act(self):
           if self.fetchACT.get():
                self.actFolderLabel.place(x=20, y=620)
                self.browseACT.place(x=300, y=640)
                self.actLabel.place(x=20, y=640)
                self.fetchACTStatus.set("Yes")
                self.master.geometry("450x680+10+10")
           else: 
                self.actFolderLabel.pack_forget()
                self.browseACT.pack_forget()
                self.actLabel.pack_forget()
                self.fetchACTStatus.set("No")
                self.master.geometry("450x620+10+10") 


    root = Tk() 
    gui = BaseGui(root)
    gui.start_status_update()
    root.protocol( "WM_DELETE_WINDOW", gui.close )
    root.mainloop()
if __name__ == "__main__": 
    try:
        startApplication()
    except Exception as e:
        logging.exception("An error occurred")
        raise
        
