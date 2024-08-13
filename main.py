# -*- coding: utf-8 -*-
import uuid
import sys
import json
import os
import subprocess
from ctypes import windll
import uvicorn
import re
import threading
import shutil

import time
from fastapi import FastAPI, UploadFile, File, Form, HTTPException,Request
from fastapi.responses import JSONResponse
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from mysqlhelper import MySqLHelper

from pydantic import BaseModel


app = FastAPI()
subprocs = {} # 用于保存子进程信息的全局字典
db = MySqLHelper()
fake_db = {
    "testuser": {"password": "testpass", "files": []}
}
origins = [
   '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ItemInsert(BaseModel):
    username: str = None
    password: str = None
@app.post("/data")
async def create_data(file: UploadFile = File(), username: str = Form()):
    print(file.filename)
    print(username)
    return {}

@app.post("/login")
async def login(item: ItemInsert):
    mysql = "select * from user_info where user_id = %s AND user_pwd = %s"
    result = db.selectone(mysql, (item.username,item.password))
    
    if result != None:
        return {"success": True}
    return {"success": False}

@app.post("/upload_one")
async def upload_one_file(file: UploadFile = File(), username: str = Form()): 
    mysql = "insert into model_process (uuid,task_id,user_id,file_name) VALUES(%s,%s,%s,%s)"
    with open("./models/" + file.filename, "wb") as buffer:
        content = await file.read()
        my_id =str( uuid.uuid4())
        print(type(my_id))
        print(my_id)
        os.mkdir('../_output/'+my_id)
        result = db.insertone(mysql,(my_id,my_id, "admin",file.filename))
        buffer.write(content)
        myarg = ["D:\\project\\thee_project\\three-lod-review\\clone_lod\\forgebim\\CloneFolderServer\\api\\models/"+file.filename,"D:\\project\\thee_project\\three-lod-review\\clone_lod\\forgebim\\CloneFolderServer\\_output\\"+my_id,['.pxz', '.fbx', '.glb', '.pdf', '.usdz', '.obj', '.3dxml'],"False"]
        t = threading.Thread(target=executeScenarioProcessor, args=(myarg[0],myarg[1],myarg[2],myarg[3],my_id)) 
        t.start()

        return {"message": "File uploaded"}

@app.post("/files")
async def upload_file(file: UploadFile = File(), username: str = Form()): 
    mysql = "insert into model_process (uuid,task_id,user_id,file_name) VALUES(%s,%s,%s,%s)"
    with open(file.filename, "wb") as buffer:
        content = await file.read()
        my_id =str( uuid.uuid4())
        print(type(my_id))
        print(my_id)
        os.mkdir('../_output/'+my_id)
        result = db.insertone(mysql,(my_id,my_id, "admin",file.filename))
        buffer.write(content)
        temp_inputfile = "D:\\project\\thee_project\\three-lod-review\\clone_lod\\forgebim\\CloneFolderServer\\api/"+file.filename
        myarg = [[temp_inputfile.replace("\\", "\\\\")],"D:\\project\\thee_project\\three-lod-review\\clone_lod\\forgebim\\CloneFolderServer\\_output\\"+my_id,['False'],"False"]
        t = threading.Thread(target=executeScenarioProcessor, args=(myarg[0],myarg[1],myarg[2],myarg[3],my_id)) 
        t.start()

        return {"message": "File uploaded"}
        #executeScenarioProcessor("D:\\project\\thee_project\\three-lod-review\\clone_lod\\forgebim\\CloneFolderServer\\api/"+file.filename,"D:\\project\\thee_project\\three-lod-review\\clone_lod\\forgebim\\CloneFolderServer\\_output",['.pxz', '.fbx', '.glb', '.pdf', '.usdz', '.obj', '.3dxml'],"False",my_id)

    return 0

class ItemGetSelect(BaseModel):
    user_id: str = None

@app.post("/get_files")
async def list_files(item: ItemGetSelect):
    
    mysql = "select * from model_process where user_id = %s"
   
    result = db.selectall(mysql, item.user_id)
    # print(item.user_id)
    # print(result)
  
    # if username not in fake_db:
    #     raise HTTPException(status_code=400, detail="User not found")
    
    # user_files = fake_db[username]["files"]
    # return {"files": user_files}
    
    return result
class ItemDelete(BaseModel):
    uuid: str = None
@app.post("/delete_file")
async def list_files(item: ItemDelete):
    mysql = 'delete from  model_process WHERE uuid=%s'
    ret = db.delete(mysql, str(item.uuid))
    delete_folder('../_output/'+item.uuid)
    print(item.uuid)
    
    return 0

class ItemCancel(BaseModel):
    uuid: str = None
@app.post("/cancel")
async def list_files(item: ItemCancel):
    mysql = "select * from model_process where uuid = %s"

    result = db.selectone(mysql, item.uuid)
    print("subprocessID: " + result["pid"])
    deleteSql = 'delete from  model_process WHERE uuid=%s'
    ret = db.delete(deleteSql, str(item.uuid))
    terminate_process(result["ppid"])
    terminate_process(result["pid"])
    time.sleep(2)
    delete_folder('../_output/'+item.uuid)

    return 0


class ItemNewProject(BaseModel):
    project_name: str = None
    desc: str = None
    user_name: str = None

@app.post("/create_project")
async def createproject(item: ItemNewProject):
    mysql = "insert into project (Pid,project_name,`desc`,user_name) VALUES(%s,%s,%s,%s)"
    my_id =str( uuid.uuid4())
   
    result = db.insertone(mysql,(my_id,item.project_name, item.desc,item.user_name))
  
    return result


class ItemGetSProjects(BaseModel):
    user_name: str = None
    
@app.post("/get_project")
async def getProjects(item: ItemGetSProjects):
    
    mysql = "select * from project where user_name = %s"
   
    result = db.selectall(mysql, item.user_name)

    
    return result


    


class ItemDeleteProject(BaseModel):
    Pid: str = None
@app.post("/delete_project")
async def list_files(item: ItemDeleteProject):
    mysql = 'delete from  project WHERE Pid=%s'
    ret = db.delete(mysql, str(item.Pid))
  
    print(item.Pid)
    
    return 0

class ItemGetProjectModel(BaseModel):
    Pid: str = None

@app.post("/get_project_model")
async def getProjects(item: ItemGetProjectModel):
    print(item.Pid)
    mysql = "select * from project_model where Pid = %s"
   
    result = db.selectall(mysql, item.Pid)

    
    return result

class ItemRemoveModelFromProject(BaseModel):
    uuid: str = None
@app.post("/remove_model_from_project")
async def list_files(item: ItemRemoveModelFromProject):
    mysql = 'delete from  project_model WHERE uuid=%s'
    ret = db.delete(mysql, str(item.uuid))
  
    print(item.uuid)
    
    return 0

class ItemGetModelInfo(BaseModel):
    uuid: str = None
@app.post("/get_model_info")
async def get_model_info(item: ItemGetModelInfo):
    print(item.uuid)
    mysql = "select * from model_process where uuid = %s"
   
    result = db.selectall(mysql, item.uuid)
    # print(item.user_id)
    # print(result)
  
    # if username not in fake_db:
    #     raise HTTPException(status_code=400, detail="User not found")
    
    # user_files = fake_db[username]["files"]
    # return {"files": user_files}
    
    return result

class ItemaddModelToProject(BaseModel):
    Pid: str = None
    uuid: str = None

@app.post("/add_model_to_project")
async def createproject(item: ItemaddModelToProject):
    mysql = "insert into project_model (Pid,uuid) VALUES(%s,%s)"

   
    result = db.insertone(mysql,(item.Pid,item.uuid))
  
    return result

def executeScenarioProcessor(input_file, output_folder, extensions, optimization,uuid):
    args = ['D:\soft\PiXYZScenarioProcessor\PiXYZScenarioProcessor.exe', 'clone', 'clone',  str(input_file) , "\"" + output_folder.replace("\\", "\\\\") + "\"", str(extensions), "\"" + str(optimization) + "\"",str(50)]
    
    count = 0
    print(args)
    p = subprocess.Popen(args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,encoding='utf-8')
    p.pid
    mysql = "UPDATE model_process set ppid = %s where uuid = %s"          
    db_result = db.update(mysql,(p.pid,uuid))

    while p.poll() is None:

        l = str(p.stdout.readline().rstrip()) # This blocks until it receives a newline.

        pid_prog = re.compile(r"PID: (\d+)")
        match = pid_prog.search(l)
        
        if(match):
            mysql = "UPDATE model_process set pid = %s where uuid = %s"            
            db_result = db.update(mysql,(match.group(1),uuid))
            print(match.group(1))
            
        prog = re.compile(r"PROGRESS: (\d+)")
        result = prog.search(l)
        if(result):
            mysql = "UPDATE model_process set progress = %s where uuid = %s"            
            db_result = db.update(mysql,(result.group(1),uuid))
            # print("db_result:", db_result)
            # print("Progress:", result.group(1))
    mysql = "UPDATE model_process set progress = %s where uuid = %s" 
   
    
    print("finish----------------")
    db_result = db.update(mysql,(100,uuid))
    sys.exit() # 子线程自行退出

# 递归删除文件夹及其子文件夹/文件    
def delete_folder(folder):
    # 递归删除文件夹 contents
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            
    # 删除空文件夹本身
    os.rmdir(folder)

def terminate_process(pid):
    try:
        subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True)
        return True
    except subprocess.CalledProcessError:
        return False  


if __name__ == "__main__":  
    uvicorn.run("main:app", host="127.0.0.1", port=8889, reload=True)