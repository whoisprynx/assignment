from fastapi import APIRouter
from category import Category
import sqlite3

router = APIRouter(prefix="/categories", tags=["Categories"])

# Create


def get_db():
    conn = sqlite3.connect("mydatabase.db")
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/")
def create_category(category: dict):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO categories(name) VALUES (?)",
                   (category["name"],))
    db.commit()
    return {"message": "Category added"}

# Read


@router.get("/")
def get_categories():
    return {"categories": []}

# Update


@router.put("/{category_id}")
def update_category(category_id: int):
    return {"message": "Updated"}

# Delete


@router.delete("/{category_id}")
def delete_category(category_id: int):
    return {"message": "Deleted"}
