# main.py
from fastapi import FastAPI, HTTPException
from find_ror import find_ror  # Import your script's functionality

from pydantic import BaseModel


app = FastAPI()

# Define a Pydantic model for the response



# Define a Pydantic model for the response
class ROR_response(BaseModel):
    Result: list

@app.post("/api/ror", response_model=ROR_response)
def ror(name: str):
    result = find_ror(name)

    if result is None:
        raise HTTPException(status_code=404, detail="Result not found")

    return {"Result": result}

