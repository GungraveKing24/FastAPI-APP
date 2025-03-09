from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String, nullable=False)
    user_email = Column(String, unique=True, nullable=False)
    user_password = Column(String, nullable=False)
    user_role = Column(String, nullable=False, default="cliente")
    user_register_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    comments = relationship("Comment", back_populates="user")

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_name = Column(String, nullable=False)
    product_description = Column(Text)
    product_quantity = Column(Integer, nullable=False, default=0)
    product_price = Column(Float, nullable=False, default=0.00)

class Arrangement(Base):
    __tablename__ = "arrangements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    arr_name = Column(String, nullable=False)
    arr_description = Column(Text, nullable=False)
    arr_price = Column(Float, nullable=False)
    arr_img_url = Column(String, nullable=False)
    arr_availability = Column(Boolean, nullable=False, default=True)

    comments = relationship("Comment", back_populates="arrangement")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_state = Column(String, nullable=False, default="pendiente")
    order_pay_type = Column(String, nullable=False)
    order_total = Column(Float, nullable=False)
    order_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")
    details = relationship("OrderDetail", back_populates="order")
    payment = relationship("Payment", back_populates="order")

class OrderDetail(Base):
    __tablename__ = "orders_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    arrangements_id = Column(Integer, ForeignKey("arrangements.id"), nullable=False)
    details_quantity = Column(Integer, nullable=False)
    details_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="details")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    pay_method = Column(String, nullable=False)
    pay_state = Column(String, nullable=False, default="pendiente")
    pay_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    order = relationship("Order", back_populates="payment")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comment_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment_arrangement_id = Column(Integer, ForeignKey("arrangements.id"), nullable=False)
    comment_text = Column(Text, nullable=False)
    comment_rating = Column(Integer, nullable=False, default=0)
    comment_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="comments")
    arrangement = relationship("Arrangement", back_populates="comments")
