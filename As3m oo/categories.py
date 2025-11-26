from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3

router = APIRouter(prefix="/categories", tags=["Categories"])


def get_db():
    conn = sqlite3.connect("mydatabase.db")
    conn.row_factory = sqlite3.Row
    return conn


class Category(BaseModel):
    name: str

# Create Category Endpoint


@router.post("/")
def create_category(category: Category):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO categories (name) VALUES (?)",
        (category.name,)
    )

    db.commit()
    db.close()

    return {"message": "Category added successfully"}

# Read Categories Endpoint


@router.get("/")
def get_categories():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    db.close()

    return {"categories": [dict(cat) for cat in categories]}

# Update Category Endpoint


@router.put("/{category_id}")
def update_category(category_id: int, category: Category):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE categories SET name = ? WHERE id = ?",
        (category.name, category_id)
    )

    db.commit()
    db.close()

    return {"message": "Category updated successfully"}

# Delete Category Endpoint


@router.delete("/{category_id}")
def delete_category(category_id: int):
    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))

    db.commit()
    db.close()

    return {"message": "Category deleted successfully"}
