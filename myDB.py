from tkinter import filedialog,messagebox
import sqlite3
import os
import datetime
import time
import csv
import pandas as pd

def create_Db(fileName):
    ###
    ###Create a new Database
    ###
    ### file is an absolute path specifying where the database file is to be stored
    ###


    ###
    ### TODO :check that the location exists
    ###

    global conn,cur
    conn = sqlite3.connect(fileName, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()

    cur.execute('''CREATE TABLE if NOT EXISTS Project (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    projectNo TEXT,
                    projectName TEXT
                    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS User (
                    ID	INTEGER PRIMARY KEY AUTOINCREMENT,
                    firstName TEXT,
                    surName TEXT,
                    active INTEGER,
                    role TEXT,
                    admin INTEGER,
                    online INTEGER
                )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS Role (
                    ID	INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT
                )''')

    ###
    ### total time worked on project by a user is stored as total seconds.
    ###
    cur.execute('''CREATE TABLE IF NOT EXISTS workedOn (
                    ID	INTEGER PRIMARY KEY AUTOINCREMENT,
                    startDate INTEGER,
                    endDate INTEGER,
                    totalTimeWorked INTEGER,
                    user INTEGER,
                    project INTEGER,
                    taskType TEXT,
                    FOREIGN KEY(user) REFERENCES User(ID),
                    FOREIGN KEY(project) REFERENCES Project(ID)
                )''')
    conn.commit()
    return

def create_user(firstName,surName,role,admin):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute('''SELECT  * from User where firstName = ? and surName = ? ''',(firstName,surName))
    row = result.fetchone()
    if row is not None:
        if messagebox.askyesno(message="This user already exists, do you want to overwrite?\n this will delete all previous work done by this user."):
            try:
                for work in cur.execute('''SELECT * from workedOn where user = ? ''', (row[0],)).fetchall():
                    cur.execute('''DELETE from workedOn where ID = ? ''', (work[0],))
                conn.commit()
            except sqlite3.OperationalError as e:
                messagebox.showinfo(message="Database is locked, couldnt save user\n, please try again later.")
                return False
            return True
        else:
            return True
    try:
        cur.execute("INSERT INTO user (firstName,surName,active,role,admin) VALUES (?,?,?,?,?)",(firstName,surName,0,role,admin))
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        return False

def start_work(userID,projectID,taskType):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    ts = int(datetime.datetime.now() .timestamp())
    result = cur.execute("SELECT * FROM user WHERE ID=? ",(userID,)).fetchone()
    if result is None:
        return True
    ###
    ### is the user currently marked as active?
    ###
    if result[3] != 0:
        currentJob = cur.execute("SELECT * FROM workedOn WHERE ID=? ",(result[3],)).fetchone()
        if not currentJob is None:
            if currentJob[2] == None:
                try:
                    d = int(datetime.datetime.now().timestamp())
                    cur.execute("UPDATE user SET active= 0 WHERE ID = ? ", (userID,))
                    cur.execute("UPDATE workedOn SET endDate= ? WHERE ID = ? ", (d, currentJob[0]))
                    conn.commit()
                except sqlite3.OperationalError as e:
                    print("oh phoo", e)
                    return False
    try:
        cur.execute("INSERT INTO workedOn (startDate,totalTimeWorked,user,project,taskType) VALUES (?,?,?,?,?)",(ts,0,userID,projectID,taskType))
        cur.execute("UPDATE user SET active= ? WHERE ID = ? ",(cur.lastrowid, userID))
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        print("oh phoo",e)
        return False

def stop_work(userID):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    ts = int(datetime.datetime.now().timestamp())
    try:
        result = cur.execute("SELECT * from user WHERE ID = ?",(userID,))
        row = result.fetchone()
        if row is not None:
            cur.execute("UPDATE user SET active= 0 WHERE ID = ?",(userID,))
            cur.execute("UPDATE workedOn SET endDate = ? WHERE ID = ?", (ts,row[3]))
    except sqlite3.OperationalError as e:
        print("database is locked, try again later")
        return False
    conn.commit()
    return True

def get_project_ID(projName):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute('''SELECT  * from project where projectName = ? ''', (projName,))
    row = result.fetchone()
    if row is not None:
        return row[0]
    else:
        try:
            cur.execute("INSERT INTO project (projectNo,projectName) VALUES (?,?)", ("", projName))
            conn.commit()
            return cur.lastrowid
        except sqlite3.OperationalError as e:
            return None

def create_project(projectNo,projectName):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute('''SELECT  * from User where firstName = ? and surName = ? ''', (projectNo,projectName))
    row = result.fetchone()
    if row is not None:
        if messagebox.askyesno(
                message="This project already exists, do you want to overwrite it?\n this will delete all previous work done on this project from the database."):
            try:
                for work in cur.execute('''SELECT * from workedOn where user = ? ''', (row[0],)).fetchall():
                    cur.execute('''DELETE from workedOn where ID = ? ''', (work[0],))
                conn.commit()
            except sqlite3.OperationalError as e:
                print("Database is locked, couldnt save project\n, please try again later.")
                return False
            return True
        else:
            return True
    try:
        cur.execute("INSERT INTO project (projectNo,projectName) VALUES (?,?)", (projectNo,projectName))
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        return False

def create_role(title):
    pass

def get_user_ID(firstName,surName):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute('''SELECT  * from User where firstName = ? and surName = ? ''', (firstName, surName))
    row = result.fetchone()
    if row is not None:
        return (row[0],row[5])
    else:
        return ("",0)

def user_online(ID):
    global databaseFile

    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    try:
        cur.execute("UPDATE user SET online= 1 WHERE ID = ?", (ID,))
        conn.commit()
        cur.close()
        return True
    except sqlite3.OperationalError as e:
        print("oh phoo", e)
        return False

def user_offline(ID):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    try:
        cur.execute("UPDATE user SET online= 0 WHERE ID = ?", (ID,))
        conn.commit()
        cur.close()
        return True
    except sqlite3.OperationalError as e:
        print("oh phoo", e)
        return False

def is_online(ID):
    global databaseFile
    print("checking id",ID," is online")
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    result = cur.execute("SELECT online FROM user WHERE ID = ?",(ID,)).fetchone()
    print(result[0])
    return result[0]


def get_user_list(userID,adminLevel):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    if adminLevel == 0:
        result = cur.execute('''SELECT  * from User  WHERE ID= ?''', (userID,)).fetchall()
    else:
        result = cur.execute('''SELECT  firstName,surName from User  WHERE admin <= ? ORDER BY surname''',(adminLevel,)).fetchall()
    return [user[1] + "," + user[0] for user in result]

def set_file(file):
    global databaseFile
    databaseFile = os.path.abspath(file)

def report_on_user(userID,startDate,endDate):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    conn.execute('pragma foreign_keys=ON')
    cur = conn.cursor()
    startDate = int(datetime.datetime.timestamp(startDate))
    endDate = int(datetime.datetime.timestamp(endDate))
    print(userID,startDate,endDate)
    result = cur.execute("SELECT user.firstname,user.surname,workedOn.startDate,workedOn.endDate,project.projectName,workedOn.taskType "
                         "FROM user JOIN workedOn on user.id = workedon.user JOIN project ON workedon.project = project.ID "
                         "WHERE user.id = ? and workedOn.startDate >= ? and workedOn.endDate <= ? ",(userID,startDate,endDate))
    return result.fetchall()

def check_Db_file():
    global databaseFile
    try:
        conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cur = conn.cursor()
        #result = cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",("User",))
        result = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        result = [item[0] for item in result]
        print(result)
        if len(result) != 5:
            cur.close()
            return False
        if result[0] == "Project"  and result[2] == "User" and result[3] == "Role" and result[4] == "workedOn":
            cur.close()
            return True
        cur.close()
        return False
    except Exception as e:
        return False

def get_current_activity(userList):
    global databaseFile
    conn = sqlite3.connect(databaseFile, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    activity=[]
    for user in userList:
        name = user.split(",")
        id = get_user_ID(name[1],name[0])[0]
        print("id for user",user,"is",id)
        if is_online(id):
            print(user,"is online")
            result = cur.execute("SELECT workedOn.startDate,project.projectName,workedOn.taskType FROM workedOn join project ON workedOn.project = project.ID WHERE user = ? AND endDate is NULL",(id,)).fetchone()
            if result is not None:
                td = datetime.datetime.now()- datetime.datetime.fromtimestamp(result[0])
                td =str(td).split(".")[0]
                activity.append([",".join(name),result[1],result[2], datetime.datetime.strftime(datetime.datetime.fromtimestamp(result[0]),'%d/%m/%Y %H:%M:%S'),td ])
            else:
                activity.append([",".join(name),"None","","",""])
    return activity



file = "S:/SCOTLAND DRIVE 2/Analysis Department/R&D/neil/Other/userDB.sqlite"
file = "C:/Users/NWatson/Desktop/userDB.sqlite"
#databaseFile = os.path.abspath(file)
