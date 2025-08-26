from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from datetime import date, timedelta, datetime
from jose import JWTError, jwt
from passlib.context import CryptContext
import db_helper

app = FastAPI()

# Security configs
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# Pydantic Models
# -----------------------------
class Expense(BaseModel):
    amount: float
    category: str
    notes: str

class DateRange(BaseModel):
    start_date: date
    end_date: date

class UserCreate(BaseModel):
    username: str
    password: str
    role: str  # "admin" or "user"

# -----------------------------
# Auth Helpers
# -----------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user = db_helper.get_user_by_username(username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_admin_user(user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# -----------------------------
# Routes
# -----------------------------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db_helper.get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user["username"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}

@app.post("/admin/create_user")
def create_user(new_user: UserCreate, admin: dict = Depends(get_admin_user)):
    db_helper.create_user(new_user.username, new_user.password, new_user.role)
    return {"message": f"{new_user.role.capitalize()} '{new_user.username}' created."}

@app.get("/admin/all_users")
def get_all_users(admin: dict = Depends(get_admin_user)):
    return db_helper.get_all_users()

@app.get("/admin/user_expenses/{username}/{expense_date}")
def get_user_expenses_by_admin(username: str, expense_date: date, admin: dict = Depends(get_admin_user)):
    user = db_helper.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_helper.fetch_expenses_for_user_date(user["id"], expense_date)

@app.get("/expenses/{expense_date}")
def get_expenses(expense_date: date, user=Depends(get_current_user)):
    try:
        if user["role"] == "admin":
            raise HTTPException(status_code=403, detail="Admins should view user data from dashboard.")
        return db_helper.fetch_expenses_for_user_date(user["id"], expense_date)
    except Exception as e:
        return {"error": str(e)}

@app.post("/expenses/{expense_date}")
def add_or_update_expenses(expense_date: date, expenses: List[Expense], user=Depends(get_current_user)):
    try:
        if user["role"] == "admin":
            raise HTTPException(status_code=403, detail="Admins cannot modify their own expenses.")
        db_helper.delete_expenses_for_user_date(user["id"], expense_date)
        for expense in expenses:
            db_helper.insert_expense_with_user(user["id"], expense_date, expense.amount, expense.category, expense.notes)
        return {"message": "Expenses saved."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/analytics/")
def get_analytics(date_range: DateRange, user=Depends(get_current_user)):
    try:
        data = db_helper.fetch_expense_summary_for_user(user["id"], date_range.start_date, date_range.end_date)
        if not data:
            return {}
        total = sum(row['total'] for row in data)
        breakdown = {
            row['category']: {
                "total": row['total'],
                "percentage": (row['total'] / total * 100) if total != 0 else 0
            } for row in data
        }
        return breakdown
    except Exception as e:
        return {"error": str(e)}
