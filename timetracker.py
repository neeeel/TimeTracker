import window
import datetime
import time
import threading
import myDB
import os
import sys
from tkinter import messagebox
from signal import signal, SIGTERM,SIGABRT
from sys import exit
import atexit

def set_exit_handler(func):
    if os.name == "nt":
        try:
            import win32api
            win32api.SetConsoleCtrlHandler(func, True)
        except ImportError:
            version = ".".join(map(str, sys.version_info[:2]))
            raise Exception("pywin32 not installed for Python " + version)
    else:
        import signal
        signal.signal(signal.SIGTERM, func)

def graceful_exit(e):
    print("caught exit signal",e)

def load_settings():
    global userDetails
    userDetails["firstName"] = ""
    userDetails["surName"] = ""
    userDetails["file"] = "None"
    userDetails["ID"] = ""
    userDetails["admin"] = ""
    userDetails["defer"] = 0
    defer = 0
    try:
        f = open("settings.txt", "r")
    except FileNotFoundError as e:
        f = open("settings.txt","w")
        f.close()
        f = open("settings.txt", "r")
    try:
        firstname = f.readline().rstrip()
        userDetails["firstName"] = firstname
        surname = f.readline().rstrip()
        userDetails["surName"] = surname
        file = f.readline().rstrip()
        userDetails["file"] = file
        defer = int(f.readline().rstrip())
    except Exception as e:
        print("failed",e)

    myDB.set_file(file)
    if not myDB.check_Db_file():
        print("check of database file failed")
        userDetails["file"] = "None"
        return "Failed Db"
    else:
        print("check of database file successful")
        userID,admin = myDB.get_user_ID(firstname,surname)
        if userID == "":
            return "Failed User"
        if file == "":
            file = "None"
        userDetails["firstName"] = firstname
        userDetails["surName"] = surname
        userDetails["file"] = file
        userDetails["ID"] = userID
        userDetails["admin"] = admin
        userDetails["defer"] = defer
        flag = False
        while not flag:
            flag = myDB.user_online(userDetails["ID"])
        return "Normal"

def save_settings(firstName,surName,file,defer):
    f = open("settings.txt", "w")
    f.write(firstName + "\n")
    f.write(surName + "\n")
    f.write(file + "\n")
    f.write(defer + "\n")
    myDB.set_file(file)

def start_task(projectName,taskType):
    global taskStartTime, lastMessageTime, running,firstPromptTime, confirmTime
    print("reached start task in timetracker module")
    if taskStartTime is None:
        taskStartTime = datetime.datetime.now()
        confirmTime = datetime.datetime.now()
        print("setting start time to ",taskStartTime)
        flag = False
        while not flag:
            projectID = myDB.get_project_ID(projectName)
            if not projectID is None:
                flag = True ## we have received a project ID from the database

        flag = False
        while not flag:
            flag = myDB.start_work(userDetails["ID"],projectID,taskType)
            firstPromptTime = None

def confirm_task():
    print("confirming task")
    global taskStartTime, confirmTime,firstPromptTime
    confirmTime = datetime.datetime.now()
    firstPromptTime = None

def stop_task():
    global taskStartTime,firstPromptTime, confirmTime, lastMessageTime
    lastMessageTime = datetime.datetime.now()
    if not taskStartTime is None:
        taskStartTime=None
        confirmTime = None
        flag = False
        win.update_info("Inactive")
        while not flag:
            flag = myDB.stop_work(userDetails["ID"])
            firstPromptTime = None

def defer_messages():
    global taskStartTime, lastMessageTime, running, firstPromptTime, confirmTime, win, deferTime
    if userDetails["defer"] != 0:
        deferTime = datetime.datetime.now() + datetime.timedelta(minutes=userDetails["defer"])
        print("setting defer time to",deferTime)
        if lastMessageTime is not None:
            lastMessageTime = lastMessageTime + datetime.timedelta(minutes=userDetails["defer"])
        if firstPromptTime is not None:
            firstPromptTime = firstPromptTime + datetime.timedelta(minutes=userDetails["defer"])
        if confirmTime is not None:
            confirmTime = confirmTime + datetime.timedelta(minutes=userDetails["defer"])

def process():
    global taskStartTime,lastMessageTime,running,firstPromptTime,confirmTime,win, deferTime
    while running:
        if firstPromptTime is not None:
            if deferTime is not None:
                if datetime.datetime.now() > deferTime:
                    deferTime = None
            else:
                ### we have prompted user to confirm task at least once
                td = datetime.datetime.now() - firstPromptTime
                if td.total_seconds() > 300:
                    ### its been 5 minutes since we first prompted for confirm, so stop task
                    td = datetime.datetime.now() - lastMessageTime
                    if td.total_seconds() >= 50:
                        win.display_balloon("No confirmation in last 5 minutes, stopping task")
                        stop_task()
                        firstPromptTime = None
                        lastMessageTime = datetime.datetime.now()
        #print("processing",taskStartTime)
        if taskStartTime is None:
            win.update_info("Inactive")
            if deferTime is not None:
                if datetime.datetime.now() > deferTime:
                    deferTime = None
            else:
                td = datetime.datetime.now() - lastMessageTime
                if td.total_seconds() >= 60:
                    ### one minute since last prompt
                    print("displaying no task started message",datetime.datetime.now())
                    win.display_balloon("No task started")
                    lastMessageTime = datetime.datetime.now()
        else:
            td = datetime.datetime.now() - confirmTime
            text = str(datetime.datetime.now() - taskStartTime).split(".")[0]
            win.update_info(text)
            if deferTime is not None:
                if datetime.datetime.now() > deferTime:
                    deferTime = None
            else:
                if td.total_seconds() >= 3600:
                    td = datetime.datetime.now() - lastMessageTime
                    if td.total_seconds() >= 60:
                        win.display_balloon("Please confirm current task")
                        lastMessageTime = datetime.datetime.now()
                        if firstPromptTime is None:
                            firstPromptTime = datetime.datetime.now()

        time.sleep(5)

settings = []
userDetails = {}
initialState = load_settings()
print(userDetails)
running = True
#atexit.register(graceful_exit,3)

# Normal exit when killed
#signal(SIGTERM, lambda signum, stack_frame: lambda:graceful_exit(1))
#signal(SIGABRT, lambda:graceful_exit(0))
taskStartTime = None
firstPromptTime = None
confirmTime = None
deferTime = None
lastMessageTime = datetime.datetime.now()

win =window.mainWindow(userDetails,initialState)
win.setCallbackFunction("confirm",confirm_task)
win.setCallbackFunction("start",start_task)
win.setCallbackFunction("stop",stop_task)
win.setCallbackFunction("load_settings",load_settings)
win.setCallbackFunction("save settings",save_settings)
win.setCallbackFunction("defer",defer_messages)
win.update_info("Inactive")
thread = threading.Thread(target=process)
thread.start()
win.mainloop()
running = False
stop_task()
flag = False
if userDetails["ID"] != "":
    while not flag:
        flag = myDB.user_offline(userDetails["ID"])
