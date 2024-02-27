from fastapi import FastAPI, Response, File, UploadFile,Form
from model import Item, MasterPart
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from pydantic import ValidationError
from io import BytesIO
from itertools import count
from tempfile import NamedTemporaryFile
import json
import pandas as pd
import os

app = FastAPI()

fileData = "data.json"
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=False,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/master-part")
async def getMasterPart():
    with open(fileData, "r") as file:
        data = json.load(file)
        for item in data:
            item["updateDate"] = datetime.strptime(item["updateDate"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M:%S")
    return Response(status_code=200, content=json.dumps(data))

@app.get("/master-part/{id}")
async def getMasterPartDetail(id: int):
    try:
        with open(fileData, "r") as file:
            data = json.load(file)

        item = next((item for item in data if item["id"] == id), None)

        if item is None:
            return Response(status_code=404, content=json.dumps({"message": "Data not found.", "body": {}}))

        return Response(status_code=200, content=json.dumps({"message": "OK", "body": item}))    
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(status_code=500, content=json.dumps({"message": "Internal server error."}))

@app.post("/master-part")
async def createMasterPart(item: Item):
    try:
        current_data = []
        maxId = 1

        if os.path.exists(fileData):
            with open(fileData, "r") as file:
                current_data = json.load(file)
                if current_data:
                    maxId = max(item["id"] for item in current_data) + 1
        else:
            current_data = []
            maxId = 1

        current_data.append({
            "id": maxId,
            "partName": item.partName,
            "partNumber": item.partNumber,
            "updateDate": current_time
        })

        with open(fileData, "w") as file:
            json.dump(current_data, file)
        
        return Response(status_code=200, content=json.dumps({"message": "Create success."}))
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(status_code=500, content=json.dumps({"message": "Internal server error."}))

@app.put("/master-part/{id}")
async def createMasterPart(id: int, item: Item):
    try:
        with open(fileData, "r") as file:
            current_data = json.load(file)

        for data in current_data:
            if data["id"] == id:
                data.update({
                    "partName": item.partName,
                    "partNumber": item.partNumber,
                    "updateDate": current_time  
                })

                with open(fileData, "w") as file:
                    json.dump(current_data, file)
                
                return Response(status_code=200, content=json.dumps({"message": "Update success."}))
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(status_code=500, content=json.dumps({"message": "Internal server error."}))

@app.delete("/master-part/{id}")
async def createMasterPart(id: int):
    try:
        current_data = []

        if os.path.exists(fileData):
            with open(fileData, "r") as file:
                current_data = json.load(file)

            for item in current_data:
                if item["id"] == id:
                    current_data.remove(item)
                    break

            with open(fileData, "w") as file:
                json.dump(current_data, file)

            return Response(status_code=200, content=json.dumps({"message": "Delete success."}))
        else:
            return Response(status_code=404, content=json.dumps({"message": "File not found."}))
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(status_code=500, content=json.dumps({"message": "Internal server error."}))

@app.post("/master-part-import-excel")
async def importExcel(file: UploadFile = File(...)):
    try:
        
        if file.filename.endswith(".xlsx"):
            with NamedTemporaryFile(delete=False) as tmp:
                tmp.write(await file.read())
                tmp.seek(0)
                excel_data = pd.read_excel(tmp.name)
                
            master_part_objects = []
            for _, row in excel_data.iterrows():
                try:

                    id_counter = count()
                    row['id'] = next(id_counter)

                    if pd.isna(row['partNumber']):
                        row['partNumber'] = ''
                    else:
                        row['partNumber'] = str(row['partNumber'])

                    if pd.isna(row['updateDate']):
                        row['updateDate'] = ''  
                    else:
                        try:
                            update_date = pd.to_datetime(row['updateDate'], format='%Y-%m-%d %H:%M:%S', errors='raise')
                            row['updateDate'] = update_date.strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            return Response(status_code=400, content=json.dumps({"message": "Invalid date format."}))

                    master_part_objects.append(MasterPart(**row))
                except ValidationError as e:
                    print(f"Error: {e}")

            json_data = [obj.dict() for obj in master_part_objects]

            with open(fileData, "w") as json_file:
                json.dump(json_data, json_file)

            return Response(status_code=200, content=json.dumps({"message": "import complete."}))
        else:
            return Response(status_code=400, detail="File type not supported. Please import an Excel (.xlsx) file.")
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(status_code=500, content=json.dumps({"message": "Internal server error."}))
    
@app.get("/master-part-export-excel")
async def exportExcel():
    try:
        
        with open(fileData, "r") as json_file:
            json_data = json.load(json_file)

        df = pd.DataFrame(json_data)
        
        excel_buffer = BytesIO()

        df.to_excel(excel_buffer, index=False)

        return Response(
            content=excel_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=masterPart.xlsx"}
        )
    except Exception as e:
        print(f"Error: {str(e)}")
        return Response(status_code=500, content=json.dumps({"message": "Internal server error."}))