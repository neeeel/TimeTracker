import tkinter
import re
import myDB
import taskbar
import win32gui
import tkinter.font as font
from tkinter import messagebox,filedialog
from tkinter import ttk
import subprocess
import datetime
import csv
import os
import win32com.client
import sys
import threading

class mainWindow(tkinter.Tk):

    def __init__(self,userDetails, initialState):
        super(mainWindow, self).__init__()
        self.tracsisBlue = "#%02x%02x%02x" % (20, 27, 77)
        self.tracsisGrey = "#%02x%02x%02x" % (99, 102, 106)
        self.settings = userDetails
        self.activityWin = None
        self.initialState = initialState
        self.confirmFunction = None
        self.startFunction = None
        self.stopFunction = None
        self.loadSettingsFunction = None
        self.saveSettingsFunction = None
        self.deferFunction = None
        self.state("zoomed")
        self.firstName = ""
        self.surName = ""
        self.dbFile=""
        self.windowStatus = "Visible"
        self.currentTask = None
        self.currentWindow = 1
        self.taskbar = taskbar.DemoTaskbar()
        #self.messageWindow = taskbar.WindowForMessages()
        #threading.Thread(target = self.messageWindow.startMonitoringForMessages).start()

        self.taskbar.hide()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.protocol("WM_ENDSESSION", self.on_shutdown)
        self.protocol("WM_QUERYENDSESSION", self.on_shutdown)
        self.wm_title("TimeTracker")
        windowsVersion = sys.getwindowsversion().major
        print("windows version is",windowsVersion,type(windowsVersion))

        ###
        ### calculate the screen and window dimensions, adjust the size, and position the window in bottom right of screen
        ###
        f = tkinter.font.Font(family='Courier', size=8)
        frame = tkinter.Frame(self,bg="white")
        frame.pack(expand=1,fill=tkinter.BOTH)
        self.update()
        maximizedBorder =frame.winfo_rooty()
        print("maximised border is",maximizedBorder)
        geom = parsegeometry(self.geometry())
        taskbarHeight = self.winfo_screenheight() - geom[1] - maximizedBorder


        self.width = int(self.winfo_screenwidth() * 1.5/10)
        self.height = int(self.winfo_screenheight()/4)
        self.x =self.winfo_screenwidth() - self.width
        self.y =self.winfo_screenheight() - self.height - taskbarHeight
        print(self.winfo_screenwidth(),self.winfo_screenheight(),self.width, self.height, self.x, self.y,self.winfo_rootx(),self.winfo_rooty())

        self.state("normal")
        self.geometry('%dx%d+%d+%d' % (self.width, self.height, self.x, self.y))
        self.update()
        if windowsVersion == 10:
            x_offset = self.winfo_rootx()- self.winfo_x()
        else:
            x_offset = 0
        normalBorder = frame.winfo_rooty() - self.y

        ###
        ### set up the widgets
        ###
        menuframe = tkinter.Frame(frame, bg="ghost white")
        f = tkinter.font.Font(family='Arial', size=8)
        l = tkinter.Label(master=menuframe, text="Main", font=f, bg="ghost white", fg=self.tracsisBlue)
        l.bind("<Enter>", self.on_label_entry)
        l.bind("<Leave>", self.on_label_exit)
        l.bind("<Button-1>", self.spawn_main_window)
        l.grid(row=0, column=0, sticky="w")

        l = tkinter.Label(master=menuframe, text="Settings", font=f, bg="ghost white", fg=self.tracsisBlue )
        l.bind("<Enter>", self.on_label_entry)
        l.bind("<Leave>", self.on_label_exit)
        l.bind("<Button-1>",self.spawn_settings_window)
        l.grid(row=0,column=1,sticky="w")
        l = tkinter.Label(master=menuframe, text="Report", font=f,bg="ghost white", fg=self.tracsisBlue)
        l.bind("<Enter>", self.on_label_entry)
        l.bind("<Leave>", self.on_label_exit)
        l.bind("<Button-1>", self.spawn_report_window)
        l.grid(row=0, column=2, sticky="w")
        menuframe.pack(fill=tkinter.X,side=tkinter.TOP)

        taskSelectionFrame = tkinter.Frame(frame, bg="white")
        l = tkinter.Label(master=taskSelectionFrame, text="Job No", font=f, bg="white", fg=self.tracsisBlue)
        l.pack(expand=tkinter.YES, fill=tkinter.BOTH,side=tkinter.LEFT,padx=4)
        e = tkinter.Entry(taskSelectionFrame,relief = tkinter.SUNKEN,borderwidth = 2,bg="ghost white", fg=self.tracsisBlue)
        e.pack(expand=tkinter.YES, fill=tkinter.BOTH,side=tkinter.LEFT,padx=4)

        combostyle = ttk.Style()
        combostyle.theme_create('combostyle', parent='alt',
                                settings={'TCombobox':
                                              {'configure':
                                                   {'selectbackground': "ghost white",
                                                    'selectforeground': self.tracsisBlue,
                                                    'fieldbackground': "ghost white",
                                                    'background': "light grey",
                                                    "foreground": self.tracsisBlue

                                                    }}} )
        combostyle.theme_use('combostyle')
        box = ttk.Combobox(taskSelectionFrame, width=11,justify=tkinter.CENTER)
        box["values"] = ("Setup", "Checking", "Reporting", "Queries","Other")
        box.pack(expand=tkinter.YES, fill=tkinter.BOTH,side=tkinter.LEFT,padx = (0,10))
        box["state"] = "readonly"
        box.current(0)
        taskSelectionFrame.pack(fill=tkinter.X,pady=20,padx=(0,25))


        mainframe = tkinter.Frame(frame, bg="white")
        f = tkinter.font.Font(family='Courier', size=8)
        tkinter.Label(master= mainframe, text="Inactive", font=f,bg="white",fg=self.tracsisBlue,height = 2).pack(fill = tkinter.X)
        l = tkinter.Label(master= mainframe, text="Start new task", font=f,bg="white",fg=self.tracsisBlue)
        l.bind("<Enter>",self.on_label_entry)
        l.bind("<Leave>", self.on_label_exit)
        l.bind("<Button-1>",self.on_label_click)
        l.pack()
        l = tkinter.Label(master=mainframe, text="Defer", font=f, bg="white", fg=self.tracsisBlue)
        l.bind("<Enter>", self.on_label_entry)
        l.bind("<Leave>", self.on_label_exit)
        l.bind("<Button-1>", self.on_label_click)
        l.pack()
        mainframe.pack(expand=1,fill=tkinter.BOTH)
        mainframe.bind("<Unmap>", self.onUnMap)
        mainframe.bind("<Map>", self.onMap)
        try:
            self.iconbitmap("stopwatch.ico")
        except Exception as e:
            print(e)
        try:
            self.attributes('-alpha', 0.7)
        except Exception as e:
            print(e)
        self.update()
        self.height = self.winfo_rooty()- self.winfo_y() + 200
        self.y = self.winfo_screenheight() - self.height - taskbarHeight
        self.geometry('%dx%d+%d+%d' % (self.winfo_reqwidth(), self.height,self.winfo_screenwidth() - self.winfo_reqwidth()-(1*x_offset),self.y - normalBorder))
        self.update()
        self.taskbar.hide()
        #self.taskbar.startMonitoringForMessages()

        #self.overrideredirect(True)
        if self.initialState !="Normal":
            self.spawn_settings_window(None)

    def on_label_entry(self,event):
        event.widget.configure(fg=self.tracsisGrey)

    def on_label_exit(self,event):
        event.widget.configure(fg=self.tracsisBlue)

    def on_label_click(self,event):
        text =event.widget.cget("text")
        if text == "Start new task":
            print("clicked to start new task")

            mainFrame = self.nametowidget(self.winfo_children()[0])
            taskFrame = self.nametowidget(mainFrame.winfo_children()[1])
            entry = self.nametowidget(taskFrame.winfo_children()[1])
            box = self.nametowidget(taskFrame.winfo_children()[2])
            print("job details are ",entry.get(),box.get())
            if entry.get() == "":
                messagebox.showinfo(message="Please enter a Job No.")
                return
            event.widget.configure(text="Continue with current Job")
            self.start_task(entry.get().strip(),box.get())
            parent = self.nametowidget(event.widget.winfo_parent())
            f = tkinter.font.Font(family='Courier', size=8)
            self.nametowidget(parent.winfo_children()[2]).configure(text = "Start new task ")
            l = tkinter.Label(master=parent, text="Stop", font=f, bg="white", fg=self.tracsisBlue)
            l.bind("<Enter>", self.on_label_entry)
            l.bind("<Leave>", self.on_label_exit)
            l.bind("<Button-1>", self.on_label_click)
            l.pack()
            l = tkinter.Label(master=parent, text="Defer", font=f, bg="white", fg=self.tracsisBlue)
            l.bind("<Enter>", self.on_label_entry)
            l.bind("<Leave>", self.on_label_exit)
            l.bind("<Button-1>", self.on_label_click)
            l.pack()
        if text == "Start new task ": ### note space at end, to distinguish between the two situations where we want to start a new task
            ### this is when we are currently logging a task, but want to start a new task
            self.stop_task()
            parent = self.nametowidget(event.widget.winfo_parent())
            mainFrame = self.nametowidget(self.winfo_children()[0])
            taskFrame = self.nametowidget(mainFrame.winfo_children()[1])
            entry = self.nametowidget(taskFrame.winfo_children()[1])
            box = self.nametowidget(taskFrame.winfo_children()[2])
            print("job details are ", entry.get(), box.get())
            self.start_task(entry.get().strip(), box.get())
        if text == "Continue with current Job":
            self.confirmFunction()
        if text == "Stop":
            self.stop_task()
            parent = self.nametowidget(event.widget.winfo_parent())
            l = self.nametowidget(parent.winfo_children()[2])
            l.configure(text="Start new task")
            self.nametowidget(parent.winfo_children()[1]).destroy()
            event.widget.destroy()
        if text == "Defer":
            self.deferFunction()

    def spawn_main_window(self,event):
        if self.initialState != "Normal":
            return
        self.currentWindow = 1
        mainframe = self.nametowidget(self.winfo_children()[0])
        for child in mainframe.winfo_children()[1:]:
            child.destroy()


        ###
        ### set up the widgets
        ###

        f = tkinter.font.Font(family='Arial', size=8)
        taskSelectionFrame = tkinter.Frame(mainframe, bg="white")
        tkinter.Label(master=taskSelectionFrame, text="Job No", font=f, bg="white", fg=self.tracsisBlue).pack(
            expand=tkinter.YES, fill=tkinter.BOTH, side=tkinter.LEFT, padx=4)
        e = tkinter.Entry(taskSelectionFrame, relief=tkinter.SUNKEN, borderwidth=2, bg="ghost white",
                          fg=self.tracsisBlue)
        e.pack(expand=tkinter.YES, fill=tkinter.BOTH, side=tkinter.LEFT, padx=4)
        if self.currentTask is not None:
            e.insert(0,self.currentTask)
        style = ttk.Style()
        print("e height is", e.winfo_height())

        combostyle = ttk.Style()
        combostyle.theme_use('combostyle')
        box = ttk.Combobox(taskSelectionFrame, width=11, justify=tkinter.CENTER)
        box["values"] = ("Setup", "Checking", "Reporting", "Queries", "Other")
        box.pack(expand=tkinter.YES, fill=tkinter.BOTH, side=tkinter.LEFT, padx=(0, 10))
        box["state"] = "readonly"
        box.current(0)

        taskSelectionFrame.pack(fill=tkinter.X, pady=20, padx=(0, 25))

        labelFrame = tkinter.Frame(mainframe, bg="white")
        f = tkinter.font.Font(family='Courier', size=8)
        if self.currentTask is None:
            text = "Inactive"
        else:
            text = "Currently working on " + str(self.currentTask)
        tkinter.Label(master=labelFrame, text=text, font=f, bg="white",fg=self.tracsisBlue, height=2).pack(fill=tkinter.X)

        if self.currentTask is None:
            text = "Start new task"
        else:
            text = "Start new task "
            l = tkinter.Label(master=labelFrame, text="Continue with current job", font=f, bg="white", fg=self.tracsisBlue)
            l.bind("<Enter>", self.on_label_entry)
            l.bind("<Leave>", self.on_label_exit)
            l.bind("<Button-1>", self.on_label_click)
            l.pack()

        l = tkinter.Label(master=labelFrame, text=text, font=f, bg="white", fg=self.tracsisBlue)
        l.bind("<Enter>", self.on_label_entry)
        l.bind("<Leave>", self.on_label_exit)
        l.bind("<Button-1>", self.on_label_click)
        l.pack()

        if not self.currentTask is None:
            l = tkinter.Label(master=labelFrame, text="Stop", font=f, bg="white", fg=self.tracsisBlue)
            l.bind("<Enter>", self.on_label_entry)
            l.bind("<Leave>", self.on_label_exit)
            l.bind("<Button-1>", self.on_label_click)
            l.pack()
        l = tkinter.Label(master=labelFrame, text="Defer", font=f, bg="white", fg=self.tracsisBlue)
        l.bind("<Enter>", self.on_label_entry)
        l.bind("<Leave>", self.on_label_exit)
        l.bind("<Button-1>", self.on_label_click)
        l.pack()


        labelFrame.pack(expand=1, fill=tkinter.BOTH)
        labelFrame.bind("<Unmap>", self.onUnMap)
        labelFrame.bind("<Map>", self.onMap)
        self.attributes('-alpha', 0.7)
        self.update()
        # e.configure(height=box.winfo_height())
        self.update()
        print("e height is", e.winfo_height())
        print("box height is", box.winfo_height())
        self.taskbar.hide()
        print("after adding widgets, geometry is", parsegeometry(self.geometry()))
        # self.overrideredirect(True)

    def spawn_report_window(self,event):
        if self.initialState != "Normal":
            return
        self.currentWindow = 3
        mainframe = self.nametowidget(self.winfo_children()[0])
        for child in mainframe.winfo_children()[1:]:
            child.destroy()
        f = tkinter.font.Font(family='Courier', size=8)
        frame = tkinter.Frame(mainframe, bg="white")
        frame.bind("<Unmap>", self.onUnMap)
        frame.bind("<Map>", self.onMap)
        frame.pack()
        box = ttk.Combobox(frame, width=15)
        box["values"] = ("Last Week", "Last Fortnight", "Last Month")
        box.current(0)
        #box.bind("<<ComboboxSelected>>", self.display_option_changed)
        tkinter.Label(frame,text= "Select Period",bg="white").grid(row=0,column= 0,padx=5,pady=(20,5))
        box.grid(row = 0,column=1,padx=5,pady=(20,5))
        if self.settings["admin"] > 0:
            tkinter.Label(frame, text="Select User", bg="white").grid(row=1, column=0,padx=5,pady=5)
            userList = myDB.get_user_list(self.settings["ID"],self.settings["admin"])
            #userList  = [user[2] + "," + user[1] for user in userList]
            userList.insert(0,"All Users")
            box = ttk.Combobox(frame, width=15)
            box["values"] = userList
            box.insert(0,"All Users")
            box.current(0)
            box.grid(row=1,column=1,padx=5,pady=5)
        tkinter.Button(frame, text="Generate", bg="white", command=self.report).grid(row=1 + self.settings["admin"], column=0, columnspan=2,padx=5,pady=15)
        if self.settings["admin"] >=2:
            tkinter.Button(frame, text="View Current Activity", bg="white", command=self.view_current_activity).grid(row=2 + self.settings["admin"],column=0, columnspan=2, padx=5,pady=5)

    def view_current_activity(self):
        if self.activityWin is None:
            self.activityWin = tkinter.Toplevel(self)
            try:
                self.activityWin.iconbitmap("stopwatch.ico")
            except Exception as e:
                print("load of icon failed")
            self.activityWin.protocol("WM_DELETE_WINDOW", self.activity_window_closed)
        for child in self.activityWin.winfo_children():
            child.destroy()
        cols = ["Name","Project","Task Type","Start Time","Duration"]
        ttk.Style().configure("Treeview", background="white",foreground=self.tracsisBlue)
        tree = ttk.Treeview(master=self.activityWin, columns=cols, show="headings", height=8)
        tree.grid(row=0,column=0,sticky = "ew")
        for i in range(5):
            tree.column(i,width = 100,anchor = tkinter.CENTER)
            tree.heading(i,text = cols[i])
        tree.column(3, width=150, anchor=tkinter.CENTER)
        userList = myDB.get_user_list(self.settings["ID"],self.settings["admin"])
        activity = myDB.get_current_activity(userList)
        for act in activity:
            tree.insert("","end",values=act)
        tkinter.Button(self.activityWin, text="Refresh", bg="white",fg=self.tracsisBlue, command=self.view_current_activity).grid(row=2,column=0, padx=5,pady=5)

    def activity_window_closed(self):
        self.activityWin.destroy()
        self.activityWin = None

    def report(self):
        userIDList = []
        mainFrame = self.nametowidget(self.winfo_children()[0])
        reportFrame = self.nametowidget(mainFrame.winfo_children()[1])
        box = self.nametowidget(reportFrame.winfo_children()[0])
        endDate = datetime.datetime.now()
        if box.current()==0:
            startDate = endDate - datetime.timedelta(days=7)
        if box.current()==1:
            startDate = endDate - datetime.timedelta(days=14)
        if box.current()==2:
            startDate = endDate - datetime.timedelta(days=30)


        if self.settings["admin"] ==0:
            userIDList.append(self.settings["ID"])
        else:
            box = self.nametowidget(reportFrame.winfo_children()[3])
            if box.get() == "All Users":
                for item in box["values"][1:]:
                    name = item.split(",")
                    userIDList.append(myDB.get_user_ID(name[1],name[0])[0])
            else:
                name = box.get().split(",")
                print(name)
                userIDList.append(myDB.get_user_ID(name[1], name[0])[0])
        print("userIds are",userIDList)
        result = []
        for ID in userIDList:
            data = myDB.report_on_user(ID,startDate,endDate)
            data = [list(d) for d in data]
            [result.append(d) for d in data]
        print("result is",result)
        for row in result:
            row.append(datetime.datetime.fromtimestamp(row[3]) - datetime.datetime.fromtimestamp(row[2]))
            row[2] = datetime.datetime.fromtimestamp(row[2]).strftime('%d/%m/%Y %H:%M:%S')
            row[3] = datetime.datetime.fromtimestamp(row[3]).strftime('%d/%m/%Y %H:%M:%S')
        result.insert(0,["Name","Surname","Start Date","End Date ","Proj Name  ","Task Type","Duration"])
        print(result)
        try:
            with open("Report.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(result)
        except PermissionError as e:
            pass
        print("basic cwd is",os.getcwd())
        folder = os.path.abspath(os.getcwd())
        print("after abspath, folder is",folder)
        #folder = os.path.abspath(folder)
        #print("after abspath, folder is",folder)
        excelFile = os.path.join(folder,"report.csv")
        print("after join, folder i s",excelFile)
        try:
            xl = win32com.client.Dispatch("Excel.Application")
            xl.Application.Visible = True
            #print("looking for file ",os.path.realpath(folder + "/report.csv"))
            xl.Workbooks.Open(os.path.realpath(excelFile))
        except Exception as e:
            messagebox.showinfo(message="There was a problem with excel, or excel isnt installed on your PC")

    def set_settings_dict(self,dict):
        self.settings = dict

    def on_closing(self):
        print("in on closing, received shutdown meassage")
        self.stop_task()
        self.taskbar.destroy()
        self.destroy()
        myDB.user_offline(self.settings["ID"])
        #messagebox.showinfo(message="caught closing down event")


    def on_shutdown(self):
        print("shutting down")


    def start_task(self,projectName,taskType):
        self.currentTask = projectName
        self.startFunction(projectName,taskType)

    def stop_task(self):
        self.stopFunction()
        self.currentTask = None

    def confirm_task(self):
        self.confirmFunction()

    def display_balloon(self,message):
        self.taskbar.displayBalloon(message)

    def spawn_settings_window(self,event):
        self.currentWindow = 2
        mainframe = self.nametowidget(self.winfo_children()[0])
        for child in mainframe.winfo_children()[1:]:
            child.destroy()
        f = tkinter.font.Font(family='Courier', size=8)
        frame = tkinter.Frame(mainframe, bg="white")
        frame.bind("<Unmap>", self.onUnMap)
        frame.bind("<Map>", self.onMap)
        frame.pack()

        tkinter.Label(frame,text = "Forename",font = f,bg = "white").grid(row=0,column = 0,pady = (10,0))
        tkinter.Label(frame, text="Surname", font=f,bg = "white").grid(row=1, column=0)

        e = tkinter.Entry(frame,width = 10,font = f)
        e.grid( row=0,column=1,padx=5,pady = (10,5),sticky = "w")
        e1 = tkinter.Entry(frame, width=10, font=f)
        e1.grid(row=1, column=1, padx=5, pady=5,sticky = "w")
        e.delete(0, tkinter.END)
        e.insert(0, self.settings["firstName"])
        e1.delete(0, tkinter.END)
        e1.insert(0, self.settings["surName"])

        tkinter.Label(frame,text="Db File",font = f,bg = "white").grid(row=2, column=0)
        l = tkinter.Label(frame,text="None",font = f,justify=tkinter.CENTER,bg = "white")
        l.bind("<Button-3>",self.open_database_file_location )
        l.bind("<Button-1>",self.get_database_file_location)
        l.grid(row=2, column=1,padx=5,pady=5,sticky = "w")
        #tkinter.Button(frame, text="*", font=f, command=lambda: self.get_database_file_location(l)).grid(row=2,column=2,sticky = "w")

        tkinter.Label(frame,text = "Defer for (min)",font = f,bg ="white").grid(row = 3,column=0)
        vcmd = (self.register(self.validate_is_numeric_only), "%d", "%s", "%S")
        e = tkinter.Entry(frame, width=10, font=f,validate="key",validatecommand=vcmd)
        e.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        e.delete(0, tkinter.END)
        e.insert(0, str(self.settings["defer"]))
        if self.settings["file"] != "None":
            l.configure(text=self.settings["file"].split("/")[-1])
        else:
            l.configure(text="None")
        tkinter.Button(frame,text = "Save",font = f,command=self.save_settings, bg="white", fg=self.tracsisBlue).grid(row=4,column=0,padx=10,pady=10,columnspan=2)

    def update_info(self,message):
        print("message is",message)
        if message !="Inactive":
            message = "Working on " + self.currentTask + " for " + message
        if self.currentWindow != 1:
            return
        if self.windowStatus == "Visible":
            frame = self.nametowidget(self.winfo_children()[0])
            mainframe = self.nametowidget(frame.winfo_children()[2])
            label = self.nametowidget(mainframe.winfo_children()[0])
            label.configure(text = message)
            #print("label text is",label.cget("text"),label.winfo_width(),label.winfo_height())
        self.taskbar.update_tooltip(message)

    def destroy__window(self,win):
        self.stopFunction()
        win.destroy()

    def onMap(self,event):
        print("mapping")
        self.windowStatus = "Visible"
        self.wm_deiconify()

    def onUnMap(self,event):
        if len(self.winfo_children()) > 2:
            if type(self.nametowidget(self.winfo_children()[2]))==tkinter.Toplevel:
                self.nametowidget(self.winfo_children()[2]).destroy()
        self.windowStatus = "Hidden"
        frame = self.nametowidget(self.winfo_children()[0])
        mainframe = self.nametowidget(frame.winfo_children()[2])
        label = self.nametowidget(mainframe.winfo_children()[0])
        msg=label.cget("text")
        self.withdraw()
        print("withdrawn")
        self.taskbar.activate(msg)
        win32gui.PumpMessages()
        print("unwithdrawing")
        self.deiconify()
        self.taskbar.hide()

    def load_settings(self):
        f = open("settings.txt", "r")
        try:
            firstname = f.readline().rstrip()
            surname = f.readline().rstrip()
            file = f.readline().rstrip()
            print("here")
        except Exception as e:
            print(e)
            return ["", "", ""]
        myDB.set_file(file)
        #myDB.check_user(firstname,surname)
        print("returning",[firstname,surname, file])
        return [firstname,surname, file]

    def save_settings(self):
        mainFrame = self.nametowidget(self.winfo_children()[0])
        frame = self.nametowidget(mainFrame.winfo_children()[1])
        firstname = self.nametowidget(frame.winfo_children()[2]).get().title()
        surname = self.nametowidget(frame.winfo_children()[3]).get().title()
        file = self.nametowidget(frame.winfo_children()[5]).cget("text")
        defer = self.nametowidget(frame.winfo_children()[7]).get()
        print("name is",firstname,"file is",file)
        if (firstname == "") | (surname == "")| (file == "") | (file == "None"):
            messagebox.showinfo(message="You need to fill out all the fields")
            return
        self.saveSettingsFunction(firstname,surname,self.settings["file"],defer)
        self.initialState = self.loadSettingsFunction()
        print("after loading settings, state is",self.initialState)
        if self.initialState == "Normal":
            self.spawn_main_window(None)
        if self.initialState == "Failed Db":
            messagebox.showinfo(message="You have selected an invalid Database File. Please select a valid database")
            self.nametowidget(frame.winfo_children()[5]).configure(text="None")
            self.settings["file"]="None"
        if self.initialState == "Failed User":
            messagebox.showinfo(message="Username not in Database. Please contact Database Admin")
            self.nametowidget(frame.winfo_children()[2]).configure(text="")
            self.nametowidget(frame.winfo_children()[3]).configure(text="")

    def get_settings(self):
        return[self.firstName,self.surName,self.dbFile]

    def get_database_file_location(self,event):
        ###
        ### prompt the user with a file navigation dialog, to select the location of the job database
        ### display the selected location in a label in the settings window
        ###

        mainFrame = self.nametowidget(self.winfo_children()[0])
        frame = self.nametowidget(mainFrame.winfo_children()[1])
        file = filedialog.askopenfilename()
        if file == "" or ".sqlite" not in file:
            messagebox.showinfo(message="You need to select a database file")
            self.nametowidget(frame.winfo_children()[5]).configure(text="None")
            self.settings["file"] = "None"
            return
        self.settings["file"] = file
        self.nametowidget(frame.winfo_children()[5]).configure(text=self.settings["file"].split("/")[-1])

    def validate_is_numeric_only(self,action,text,char):
        if action == "0":  ### action 0 is delete. We dont mind what they delete
            return True
        return char.isdigit()

    def open_database_file_location(self,event):
        dirName = os.path.dirname(self.settings["file"])
        if os.path.isdir(dirName):
            p = os.path.normpath(dirName)
            subprocess.Popen('explorer "{0}"'.format(p))
        else:
            messagebox.showinfo(message="Database location doesnt exist")

    def ping(self):
        print("PING",self.windowStatus)
        self.after(5000,self.ping)

    def setCallbackFunction(self, text, fun):
        if text == "confirm":
            self.confirmFunction = fun
        if text == "start":
            self.startFunction = fun
        if text == "stop":
            self.stopFunction = fun
        if text == "load_settings":
            self.loadSettingsFunction = fun
        if text == "save settings":
            self.saveSettingsFunction = fun
        if text == "defer":
            self.deferFunction = fun

def parsegeometry(geometry):
    m = re.match("(\d+)x(\d+)([-+]\d+)([-+]\d+)", geometry)
    if not m:
        raise ValueError("failed to parse geometry string")
    return list(map(int, m.groups()))
