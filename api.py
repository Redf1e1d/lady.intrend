from database import SessionLocal, engine, Base
import models_db
from fastapi import FastAPI, Depends, HTTPException
from models_db import User, Product, CartItem, Order
from sqlalchemy.orm import Session

 
app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/telegram-register")
def telegram_register(telegram_id: str, username: str, db:Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(telegram_id = telegram_id, username=username)
        db.add(user)
        db.commit()

    return {"status": "ok"}

@app.get("/products")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.post("/cart/add")
def add_to_cart(telegram_id: str, product_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    item = db.query(CartItem).filter(
        CartItem.user_id == user.id,
        CartItem.product_id == product_id
    ).first()

    if item:
        item.quantity += 1
    else:
        item = CartItem(user_id=user.id, product_id=product_id, quantity=1)
        db.add(item)

    db.commit()

    return {"status": "added"}

@app.get("/cart/{telegram_id}")
def get_cart(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    items = db.query(CartItem).filter(CartItem.user_id == user.id).all()

    return items

@app.post("/order/{telegram_id}")
def create_order(telegram_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total = 0

    for item in items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        total += product.price * item.quantity

    order = Order(user_id=user.id, total_price=total)
    db.add(order)

    # очищаем корзину
    for item in items:
        db.delete(item)

    db.commit()

    return {"order_id": order.id, "total": total}

@app.post("admin/product")
def create_product(
    name: str,
    category: str,
    price: int,
    image_url: str,
    stock: int,
    db: Session = Depends(get_db)
):
    product = Product(
        name = name,
        category = category,
        price = price,
        image_url=image_url,
        stock=stock
    )

    db.add(product)
    db.commit()

    return {"status": "created", "id": product.id}

@app.delete("/admin/product/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()

    return {"status": "deleted"}

@app.get("/admin/orders")
def get_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()
