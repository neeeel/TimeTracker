# Creates a task-bar icon with balloon tip.  Run from Python.exe to see the
# messages printed.
# original version of this demo available at http://www.itamarst.org/software/

import win32api, win32con, win32gui
from win32gui import *
import win32con
import time
from tkinter import messagebox



class Taskbar:
    def __init__(self):
        self.visible = 0
        self.isAlive = False
        self.mainWindowVisible = False
        message_map = {

            win32con.WM_DESTROY: self.onDestroy,
            win32con.WM_USER + 20: self.onTaskbarNotify,
            #win32con.WM_ENDSESSION: self.on_shutdown,
            #win32con.WM_ENDSESSION:self.on_shutdown,
            #win32con.WM_QUERYENDSESSION:self.on_endsession,
        }
        # Register the Window class.
        wc = win32gui.WNDCLASS()
        self.hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "PythoWindowo"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_GRAYTEXT
        wc.lpfnWndProc = message_map  # could also specify a wndproc.
        self.classAtom = win32gui.RegisterClass(wc)
        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(self.classAtom, "Balloon", style, \
                                          0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, \
                                          0, 0, self.hinst, None)
        win32gui.UpdateWindow(self.hwnd)

    def setIcon(self, hicon, tooltip=None):
        self.hicon = hicon
        self.tooltip = tooltip

    def update_tooltip(self,message):
        self.tooltip = message
        if self.isAlive:
            print("modifying")
            message = win32gui.NIM_MODIFY
            nid = (self.hwnd,
                              0,
                              win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                              win32con.WM_USER + 20,
                              self.hicon,
                              self.tooltip)
            win32gui.Shell_NotifyIcon(message, nid)

    def show(self,msg):
        """Display the taskbar icon"""
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE
        if self.tooltip is not None:
            flags |= win32gui.NIF_TIP
            nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, self.hicon, msg)
        else:
            flags |= win32gui.NIF_TIP
            nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, self.hicon,"timeTracker")
        if self.visible:
            self.hide()
        print("adding icon")
        print(msg)
        print(nid)
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        self.visible = 1
        self.mainWindowVisible = False

    def hide(self):
        """Hide the taskbar icon"""
        if self.visible:
            print("destroying icon")
            nid = (self.hwnd, 0)
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        self.visible = 0



    def onDestroy(self, hwnd, msg, wparam, lparam):
        self.hide()
        print("destroying")
        win32gui.PostQuitMessage(0)  # Terminate the app.


    def onTaskbarNotify(self, hwnd, msg, wparam, lparam):
        if lparam!=512:
            print(lparam)
        if lparam==1029:
            print("clicked balloon")
            if self.isAlive:
                print("ya")
                win32gui.PostQuitMessage(0)
                self.hide()
                self.isAlive = False
        if lparam == win32con.WM_LBUTTONUP:
            self.onClick()
        elif lparam == win32con.WM_LBUTTONDBLCLK:
            print("received message")
            self.onDoubleClick()
        elif lparam == win32con.WM_RBUTTONUP:
            self.onRightClick()
        return 1

    def on_endsession(self):
        return True

    def onClick(self):
        """Override in subclassess"""
        pass

    def onDoubleClick(self):
        """Override in subclassess"""
        pass

    def onRightClick(self):
        """Override in subclasses"""
        pass

class WindowForMessages(Taskbar):

    def on_shutdown(self):
        messagebox.showinfo(message="ertoiejreorijy")
        while True:
            pass

    def startMonitoringForMessages(self):
        win32gui.PumpMessages()



class DemoTaskbar(Taskbar):
    def __init__(self):
        Taskbar.__init__(self)

        try:
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(self.hinst, "stopwatch.ico",win32con.IMAGE_ICON, 0, 0, icon_flags)
        except:
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        self.setIcon(hicon)

    def onClick(self):
        print("you clicked")

    def onDoubleClick(self):
        print("you double clicked, bye!")
        win32gui.PostQuitMessage(0)
        print("ha")
        self.mainWindowVisible = True
        #DestroyWindow(self.hwnd)
        #self.classAtom = UnregisterClass(self.classAtom, self.hinst)
        self.isAlive = False
        self.hide()

    def activate(self,msg):
        self.show(msg)
        self.isAlive=True

    def startMonitoringForMessages(self):
        win32gui.PumpMessages()

    def displayBalloon(self,message):
        print("displaying balloon")
        if not self.isAlive:
            self.show("")
        # NIF_INFO flag below enables balloony stuff
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_INFO
        # define the icon properties (see http://msdn.microsoft.com/library/default.asp?url=/library/en-us/shellcc/platform/shell/reference/structures/notifyicondata.asp)
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, self.hicon, "Inactive", message, 10, "TaskTracker")

        # change our already present icon ...
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
        time.sleep(5)
        if not self.isAlive:
            self.hide()
        #DestroyWindow(self.hwnd)
        #self.classAtom = UnregisterClass(self.classAtom,self.hinst)

    def destroy(self):
        print("destroying in sub class")
        self.hide()
        try:
            DestroyWindow(self.hwnd)
        except Exception as e:
            print(e)
        try:
            self.classAtom = UnregisterClass(self.classAtom, self.hinst)
        except Exception as e:
            print(e)
        win32gui.PostQuitMessage(0)

#t = DemoTaskbar()
#t.show()
#t.displayBalloon("werw")
#time.sleep(20)
#t.displayBalloon("second")
#t.hide()
#t.destroy()
#time.sleep(5)
#win32gui.PumpMessages()  # start demo