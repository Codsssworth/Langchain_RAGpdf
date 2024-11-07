import streamlit as st
import asyncio
import websockets
import json
import requests 

async def send_query(query, websocket):
    await websocket.send(json.dumps({"query": query}))

def upload_pdf(pdf_file):
    try:
        # Send the file as a multipart/form-data request to the FastAPI server
        response = requests.post("http://localhost:8000/upload-pdf/", files={"file": pdf_file})
        response.raise_for_status()  # Check if the request was successful
        return response.json()  # Return JSON response if successful
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the server: {e}")
        return None

async def receive_response(websocket):
    response = await websocket.recv()
    return json.loads(response).get("response")

def main():
    st.set_page_config(page_title="Real-Time PDF Query Chat")
    st.header("Ask questions from your PDF in real-time 💬")

    # File upload
    pdf_file = st.file_uploader("Upload your PDF", type="pdf")
    if pdf_file:
        upload_response = upload_pdf(pdf_file)
        # Check if upload_response is valid and contains "status"
        if upload_response and upload_response.get("status") == "PDF processed successfully":
            st.write("PDF uploaded and processed successfully. Ready for questions!")
        else:
            st.write("Failed to process PDF. Please try again.")

    # WebSocket connection
    websocket_url = "ws://localhost:8000/ws"
    user_question = st.text_input("Ask a question about your PDF:")
    if st.button("Send"):
        if user_question and pdf_file:
            async def interact_with_server():
                async with websockets.connect(websocket_url) as websocket:
                    # Send query
                    await send_query(user_question, websocket)
                    # Receive response
                    response = await receive_response(websocket)
                    st.write("Response:", response)

            asyncio.run(interact_with_server())

if __name__ == "__main__":
    main()
