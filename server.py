from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import JSONResponse
from handler import LangChainHandler
import uvicorn
import json

app = FastAPI()
langchain_handler = LangChainHandler()

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    content = await file.read()
    file_name = file.filename  # Get the file name
    langchain_handler.store_pdf_metadata( file_name)
    result = langchain_handler.process_pdf(content)
    if result:
        return JSONResponse({"status": "PDF processed successfully"})
    return JSONResponse({"status": "PDF processing failed"}, status_code=400)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        query = json.loads(data).get("query")
        if query:
            response = langchain_handler.generate_response(query)
            await websocket.send_text(json.dumps({"response": response}))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
