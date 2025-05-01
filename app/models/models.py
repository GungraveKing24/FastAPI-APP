from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    user_email = Column(String, nullable=False, unique=True)
    user_password = Column(String, nullable=False)
    user_role = Column(String, nullable=False, default="cliente")  # 'admin', 'empleado', 'cliente'
    user_register_date = Column(DateTime, default=datetime.utcnow)
    user_direction = Column(String, default="N/A")
    user_number = Column(String, nullable=False)  # Se debe validar en el esquema que tenga entre 7 y 9 números
    user_url_photo = Column(String, default="N/A")
    user_google_id = Column(String, unique=True, nullable=True)  # Para login con Google
    user_account_state = Column(Boolean, default=True)
    orders = relationship("Order", back_populates="user")

# Tabla de Categorías
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name_cat = Column(String, nullable=False, unique=True)

    arrangements = relationship("Arrangement", back_populates="category")

# Tabla de Productos (Arreglos Florales)
class Arrangement(Base):
    __tablename__ = "arrangements"

    id = Column(Integer, primary_key=True, index=True)
    arr_name = Column(String, nullable=False)
    arr_description = Column(Text, nullable=False)
    arr_price = Column(Float, nullable=False)
    arr_img_url = Column(String, nullable=False)
    arr_availability = Column(Boolean, default=True)
    arr_id_cat = Column(Integer, ForeignKey("categories.id"), nullable=False)
    arr_stock = Column(Integer, default=10)
    arr_discount = Column(Integer, default=0)

    category = relationship("Category", back_populates="arrangements")

# Tabla de Pedidos
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Datos obligatorios para compras sin cuenta
    guest_name = Column(String, nullable=True)  
    guest_email = Column(String, nullable=True)  
    guest_phone = Column(String, nullable=True)  
    guest_address = Column(String, nullable=True)  

    order_state = Column(String, nullable=False, default="carrito")  # Cambiado a "carrito" para estado temporal
    order_date = Column(DateTime, default=datetime.utcnow)
    
    # Eliminar campos de pago de aquí (se moverán a Payment)
    user = relationship("User", back_populates="orders")
    order_details = relationship("OrderDetail", back_populates="order")
    payment = relationship("Payment", uselist=False, back_populates="order")

# Tabla de Detalles del Pedido
class OrderDetail(Base):
    __tablename__ = "orders_details"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    arrangements_id = Column(Integer, ForeignKey("arrangements.id"), nullable=False)
    details_quantity = Column(Integer, nullable=False)  # Validación en esquema: > 0
    details_price = Column(Float, nullable=False)  # Precio unitario del producto
    discount = Column(Float, default=0.0)

    order = relationship("Order", back_populates="order_details")

# Tabla de Pagos
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    pay_method = Column(String, nullable=False)  # 'Tarjeta', 'Efectivo'
    pay_state = Column(String, nullable=False, default="pendiente")
    pay_amount = Column(Float, nullable=False)
    pay_transaction_id = Column(String, unique=True, nullable=True)  # Para pagos en línea
    pay_date = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")

# Tabla de Comentarios
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    comment_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_arrangement_id = Column(Integer, ForeignKey("arrangements.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    comment_rating = Column(Integer, nullable=False, default=0)  # 1 a 5
    comment_date = Column(DateTime, default=datetime.utcnow)

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    product_description = Column(Text)
    product_quantity = Column(Integer, nullable=False, default=0)
    product_price = Column(Float, nullable=False, default=0.00)