import sys
import time
import logging
import hashlib

from tkinter import *
from tkinter import filedialog
from watchdog.observers import Observer

from watchdog.events import LoggingEventHandler
from enum import Enum, auto
from datetime import datetime

from os import listdir
from os.path import isfile, join, getsize, exists

import controllers


class OpType(Enum):
    CREATE = auto()
    DELETE = auto()
    MOVE = auto()
    MODIFY = auto()


class infoRecord:
    def __init__(self, opType, src_path, time_stamp, dest_path=0):
        self.opType = opType  # Тип операции
        self.src_path = src_path  # Исходный путь
        self.dest_path = dest_path  # Конечный путь (если применимо)
        self.time_stamp = time_stamp  # Временная отметка изменения
        if opType != OpType.DELETE:
            self.size = getsize(src_path)
            self.hash = self.calcHash(src_path)
        else:
            self.size = None
            self.hash = None

    def calcHash(self, path):
        hasher = hashlib.md5()
        with open(path, 'rb') as file:
            buf = file.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def fileSizeStr(self, size):
        if size is None:
            return
        for unit in ['', 'К', 'М', 'Г']:
            if abs(size) < 1024.0:
                return "%3.1f%s%s" % (size, unit, "Б")
            size /= 1024.0
        return "Слишком большой файл"

    def __str__(self):
        string = "%s | %s | %s | %s | %s |" % (
            self.time_stamp, OpType(self.opType),
            self.fileSizeStr(self.size), str(self.hash), self.src_path)
        if self.dest_path != 0:
            string += " | " + self.dest_path
        return string


def update(record):
    print(record)
    if record.src_path not in historyList:
        historyList[record.src_path] = []
    if record.opType == OpType.CREATE:
        historyList[record.src_path] = [str(record)]
    if record.opType == OpType.DELETE:
        print("TEST")
        historyList.pop(record.src_path)
        deletedFiles.append(record.src_path)
    if record.opType == OpType.MODIFY:
        historyList[record.src_path].append(str(record))
    if record.opType == OpType.MOVE:
        historyList[record.dest_path] = historyList.pop(
            record.src_path)
        historyList[record.dest_path].append(str(record))

    lbox3.delete(0, "end")
    for idx, item in enumerate(deletedFiles):
        lbox3.insert(idx, item)

    global currentKey
    loadHistory(currentKey)
    refreshDirList(currentPath)


class monitorHandler(LoggingEventHandler):
    def on_moved(self, event):
        super(monitorHandler, self).on_moved(event)

        time_stamp = datetime.now().time()

        update(infoRecord(OpType.MOVE, event.src_path, time_stamp,
                          event.dest_path))

    def on_created(self, event):
        super(monitorHandler, self).on_created(event)

        time_stamp = datetime.now().time()

        update(infoRecord(OpType.CREATE, event.src_path, time_stamp))

    def on_deleted(self, event):
        super(monitorHandler, self).on_deleted(event)

        time_stamp = datetime.now().time()

        update(infoRecord(OpType.DELETE, event.src_path, time_stamp))

    def on_modified(self, event):
        super(monitorHandler, self).on_modified(event)

        time_stamp = datetime.now().time()

        update(infoRecord(OpType.MODIFY, event.src_path, time_stamp))


historyList = dict()
deletedFiles = []
currentPath = "None"
currentKey = "None"


def loadHistory(key):
    lbox2.delete(0, "end")
    path = currentPath + "\\" + key
    print("------------------", path)
    if path in historyList:
        for idx, item in enumerate(historyList[path]):
            lbox2.insert(idx, item)


class observerManager():
    observer = None

    def changePath(self, path):

        if self.observer is not None:
            self.observer.stop()
        event_handler = monitorHandler()
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()


def askFileDirectory(event):
    directory = filedialog.askdirectory()
    entry1.delete(0, END)
    entry1.insert(0, directory)
    observerManager().changePath(directory)
    refreshDirList(directory)
    global currentPath
    currentPath = directory
    return


def refreshDirList(directory):
    lbox1.delete(0, "end")
    for idx, path in enumerate(listdir(directory)):
        lbox1.insert(idx, path)


def onItemSelect(event):
    global key
    key = lbox1.get(lbox1.curselection())
    loadHistory(key)
    currentKey = key


root = Tk()
root.title("Мониторинг файлов")
root.geometry("500x750")
frame = Frame(root)
Grid.rowconfigure(root, 0, weight=1)
Grid.columnconfigure(root, 0, weight=1)
grid = Frame(frame)
grid.grid(sticky=N+S+E+W, column=0, row=5, columnspan=2)

label1 = Label(text="Обзор директории")
entry1 = Entry()
lbox1 = Listbox(selectmode=SINGLE)
label2 = Label(text="История")
lbox2 = Listbox(selectmode=SINGLE)
label3 = Label(text="Удалённые файлы")
lbox3 = Listbox(selectmode=SINGLE)

label1.grid(row=0, column=0, sticky=N)
entry1.grid(row=1, column=0, sticky=E+W, columnspan=2)
lbox1.grid(row=2, column=0, sticky=N+S+E+W, columnspan=2)
label2.grid(row=3, column=0, sticky=N+S+E+W, columnspan=2)
lbox2.grid(row=4, column=0, sticky=N+S+E+W, columnspan=2)
label3.grid(row=5, column=0, sticky=N+S+E+W, columnspan=2)
lbox3.grid(row=6, column=0, sticky=N+S+E+W, columnspan=2)

entry1.bind("<Button-1>", askFileDirectory)
entry1.bind("<Key>", lambda e: "break")  # Запретить ввод в окно
lbox1.bind("<Button-1>", onItemSelect)

root.mainloop()
