Create and Activate virtual environment
    cd backend
    python -m venv venv
    source venv/Scripts/activate

Install required packages
    pip install -r requirements.txt

To run backend 
    uvicorn app.main:app --reload

To run frontend
    cd frontend
    npm run dev