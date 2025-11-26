from fastapi import FastAPI, Path, Query, HTTPException
from typing import Optional, Dict, List
from pydantic import BaseModel
from datetime import date
import logging
import sqlite3
from starlette.requests import Request as Requests
from categories import router as categories_router
from passlib.hash import bcrypt

app = FastAPI()


def get_db():
    conn = sqlite3.connect("mydatabase.db")
    conn.row_factory = sqlite3.Row
    return conn


app.include_router(categories_router)

# Pydantic Models


class Expense(BaseModel):
    category: str
    amount: float
    note: Optional[str] = None
    date: Optional[date]
    user_id: int


class UpdateExpense(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None
    date: Optional[date]
    user_id: Optional[int] = None


class Login(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


# Logging Middleware
logging.basicConfig(level=logging.INFO)


@app.middleware("http")
async def log_requests(request: Requests, call_next):
    logging.info(f"{request.method} {request.url}")
    response = await call_next(request)
    return response

# Registration Endpoint


@app.post("/register")
def register(user: UserCreate):
    db = get_db()
    cursor = db.cursor()

    # check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = bcrypt.hash(user.password)

    cursor.execute("""
        INSERT INTO users (name, email, hashed_password)
        VALUES (?, ?, ?)
    """, (user.name, user.email, hashed_password))

    db.commit()
    return {"message": "User registered successfully"}

# login endpoint


@app.post("/login")
def login(user: Login):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    db_user = cursor.fetchone()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt.verify(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {"message": "Login successful", "user_id": db_user["id"]}

# Report Routes Endpoints


@app.get("/reports/monthly/{year}/{month}")
def monthly_report(year: int, month: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    SELECT category, SUM(amount) as total
    FROM expenses
    WHERE strftime('%Y', date) = ?
    AND strftime('%m', date) = ?
    GROUP BY category
    """, (str(year), f"{month:02}"))

    return cursor.fetchall()


@app.get("/reports/yearly/{year}")
def yearly_report(year: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    SELECT category, SUM(amount) as total
    FROM expenses
    WHERE strftime('%Y', date) = ?
    GROUP BY category
    """, (str(year),))

    return cursor.fetchall()

# Root Endpoint


@app.get("/")
def home():
    return {"message": "Welcome to the Expense Tracker API"}

# Path Parameter


@app.get("/expenses/{expense_id}")
def get_expense(expense_id: int = Path(..., gt=0)):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Expense not found")

    return dict(row)

# Filtering and Pagination of Expenses on Endpoint


@app.get("/expenses")
def list_expenses(
    skip: int = 0,
    limit: int = 10,
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
):
    db = get_db()
    cursor = db.cursor()

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date.isoformat())

    if end_date:
        query += " AND date <= ?"
        params.append(end_date.isoformat())

    if min_amount is not None:
        query += " AND amount >= ?"
        params.append(min_amount)

    if max_amount is not None:
        query += " AND amount <= ?"
        params.append(max_amount)

    query += " LIMIT ? OFFSET ?"
    params.extend([limit, skip])

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    return [dict(row) for row in rows]

# Query Parameter for User Expenses


@app.get("/users/{user_id}/expenses")
def get_user_expenses(user_id: int):
    user_expenses = []

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()

    return user_expenses

# Get by Category Endpoint


@app.get("/get-by-category")
def get_category(category: str):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM expenses WHERE category = ?", (category,))
    rows = cursor.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404, detail="There's no existing expense in this category")

    return [dict(row) for row in rows]

# Request Expense Endpoint


@app.post("/expenses")
def create_expense(expense: Expense):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO expenses (amount, date, category, note, user_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        expense.amount,
        expense.date.isoformat() if expense.date else None,
        expense.category,
        expense.note,
        expense.user_id
    ))

    db.commit()

    return {"message": "Expense added"}

# Update Expense Endpoint


@app.put("/expenses/{expense_id}")
@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: UpdateExpense):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Expense not found")

    fields = []
    values = []

    if expense.category is not None:
        fields.append("category = ?")
        values.append(expense.category)

    if expense.amount is not None:
        fields.append("amount = ?")
        values.append(expense.amount)

    if expense.note is not None:
        fields.append("note = ?")
        values.append(expense.note)

    if expense.date is not None:
        fields.append("date = ?")
        values.append(expense.date.isoformat())

    if expense.user_id is not None:
        fields.append("user_id = ?")
        values.append(expense.user_id)

    if not fields:
        raise HTTPException(status_code=400, detail="No data to update")

    query = f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?"
    values.append(expense_id)

    cursor.execute(query, tuple(values))
    db.commit()

    return {"message": "Expense updated"}

# Delete Expense Endpoint


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"message": "Deleted successfully"}
