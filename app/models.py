from time import time
from datetime import datetime, timezone
#from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_sqlalchemy import SQLAlchemy
import MySQLdb
from collections import defaultdict
from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5
import jwt
from sqlalchemy import JSON
from flask_login import current_user 
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from sqlalchemy import func





@login.user_loader
def load_user(user_id):
    if not user_id:  # ✅ Check if user_id is None or invalid
        return None
    return db.session.get(User, int(user_id))  # ✅ Now safe to query


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    # ✅ Basic fields
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), index=True)
    mobile = db.Column(db.String(15))
    email = db.Column(db.String(120), unique=True)
    gst = db.Column(db.String(15))
    pas = db.Column(db.String(15))  # Not sure what 'pas' is — consider renaming
    address = db.Column(db.String(255))
    password_hash = db.Column(db.String(256))
    aboute_me = db.Column(db.String(255))  # Typo? Should be `about_me`?
    is_admin = db.Column(db.Boolean, default=False)

    # ✅ Account / tracking info
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    default_markup_percent = db.Column(db.Float, default=10.0)
    is_paid = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    payment_expiry = db.Column(db.DateTime)

    # ✅ Business-related
    business_type = db.Column(db.String(50))

    # ✅ Relationships
    subscriptions = db.relationship('Subscription', back_populates='user')
    sales = db.relationship('Sale', back_populates='user')

    # ✅ Methods

    @property
    def is_active(self):
        return not self.blocked

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except Exception:
            return None
        return db.session.get(User, id)

    def has_active_subscription(self):
        sub = Subscription.query.filter_by(user_id=self.id, is_active=True).first()
        return sub and sub.end_date >= datetime.utcnow()

    def sales_count(self):
        return db.session.query(func.count(Sale.id)).filter_by(user_id=self.id).scalar()

    def setup_default_items(self):
        from app.presets import BUSINESS_PRESETS
        from app.models import Category  # import your Category model

        preset_items = BUSINESS_PRESETS.get(self.business_type, [])
        print("✅ Adding items for type:", self.business_type, "→", preset_items)

        for item in preset_items:
            category_name = item.get("category", "General")
            category = Category.query.filter_by(catname=category_name, user_id=self.id).first()
            if not category:
                category = Category(catname=category_name, user_id=self.id)
                db.session.add(category)
                db.session.flush()  # ensures category.id is available
            new_item = Item(
                user_id=self.id,
                itemname=item["itemname"],
                category=category,  # ✅ assign the relationship
                stock_quantity=0)
            db.session.add(new_item)
        db.session.commit()



class Customer(db.Model):
    __tablename__ = 'customers'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(120), index=True, nullable=False)
    mobile = sa.Column(sa.String(15), nullable=False, unique=False)  # ✅ Changed to String for mobile numbers
    email = sa.Column(sa.String(120), unique=True, nullable=True)  # ✅ Corrected email type
    gst = sa.Column(sa.String(15), unique=True, nullable=True)
    pan = sa.Column(sa.String(15), unique=True, nullable=True)
    address = sa.Column(sa.Text)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='customers')  # ✅ Relationship with User

    def __repr__(self):
        return self.name


class Vendor(db.Model):
    __tablename__ = 'vendors'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(120), index=True)
    mobile = db.Column(db.String(15), nullable=True)
    email = sa.Column(sa.String(150), nullable=True)
    gstin = sa.Column(sa.String(12))
    cgst = sa.Column(sa.String(12))
    igst = sa.Column(sa.String(12))
    sgst = sa.Column(sa.String(12))
    pan = sa.Column(sa.String(12))
    address = sa.Column(sa.String(120))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False) 
    user = db.relationship('User', backref='Vendors')  # ✅ Relationship with User

    def __repr__(self):
        return self.name


class Item(db.Model):
    __tablename__ = 'items'
    id = sa.Column(sa.Integer, primary_key=True)
    itemname = sa.Column(sa.String(120), nullable=False)
    hsn_code = sa.Column(sa.String(120))
    item_code = sa.Column(sa.String(120))
    created_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    
    category_id = sa.Column(sa.Integer, sa.ForeignKey('categories.id'))
    category = db.relationship('Category', backref='items')
    unit_price = sa.Column(sa.Float, nullable=True)

    stock_quantity = sa.Column(sa.Integer, default=0)  # ✅ Auto-updated from purchases/sales
    purchase_price = sa.Column(sa.Float, nullable=True)
    selling_price = sa.Column(sa.Float, nullable=True)
    tax_percent = db.Column(db.Float, default=0.0)
    markup_percent = db.Column(db.Float, default=None)
    min_stock = db.Column(db.Float, nullable=False, default=0)

    #purchase_id = sa.Column(sa.Integer, sa.ForeignKey('purchases.id'))  # ✅ Foreign Key added
    purchase_items = db.relationship('PurchaseItem', back_populates='item', lazy=True)  # ✅ Corrected


    sale_items = db.relationship('SaleItem', back_populates='item', lazy=True)
    itemmovement = db.relationship('ItemMovement', back_populates='item', cascade='all, delete-orphan')

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='items')  # ✅ Relationship with User

    low_stock_threshold = db.Column(db.Integer, default=10)


    def __repr__(self):
        return f'{self.itemname}'

    @property
    def profit_margin(self):
        if self.purchase_price and self.selling_price:
            return round(self.selling_price - self.purchase_price, 2)
        return None

    @property
    def profit_percent(self):
        if self.purchase_price and self.selling_price and self.purchase_price != 0:
            return round(((self.selling_price - self.purchase_price) / self.purchase_price) * 100, 2)
        return None





class ItemMovement(db.Model):
    __tablename__ = 'itemmovements'
    movement_id = sa.Column(sa.Integer, primary_key=True)
    item_id = sa.Column(sa.ForeignKey('items.id'))
    
    # Reverse relationship pointing back to Item model
    item = db.relationship('Item', back_populates='itemmovement')  # Changed from 'items' to 'item' to match the 'back_populates' in Item model
    movement_type = sa.Column(sa.String(50), nullable=False)
    
    quantity = sa.Column(sa.Integer)
    from_location_id = sa.Column(sa.ForeignKey('godowns.id'))
    to_location_id = sa.Column(sa.ForeignKey('godowns.id'))
    
    # Relationships to Godown for source and destination locations
    from_location = db.relationship('Godown', foreign_keys=from_location_id)
    to_location = db.relationship('Godown', foreign_keys=to_location_id)
    
    movement_date = sa.Column(sa.DateTime, default=datetime.utcnow)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='itemmovements')  # ✅ Relationship with User

    def __repr__(self):
        return f"<{self.movement_type.capitalize()} - {self.quantity} of {self.item.name}>"

class Category(db.Model):
    __tablename__ = 'categories'
    id = sa.Column(sa.Integer, primary_key=True)
    catname = sa.Column(sa.String(120))
    description = sa.Column(sa.String(200))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='categories')  # ✅ Relationship with User
    def __repr__(self):
        return self.catname


class ExpenseCategory(db.Model):
    __tablename__ = 'expense_category'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(120), nullable=False)
    description = sa.Column(sa.String(220))
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='expense_category')  # ✅ Relationship with User
    def __repr__(self):
        return f"<ExpenseCategory {self.name}>"


class ExpenseItem(db.Model):
    __tablename__ = "expense_item"
    id = sa.Column(sa.Integer, primary_key=True)
    itemname = sa.Column(sa.String(120), nullable=False)
    quantity = sa.Column(sa.Integer, nullable=False)
    rate = sa.Column(sa.Float, nullable=False)
    amount = sa.Column(sa.Float, nullable=False)
    total_amount = sa.Column(sa.Float, nullable=False)
    expense_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    expense_id = sa.Column(sa.Integer, sa.ForeignKey('expenses.id'), nullable=False)
    expense = db.relationship('Expense', back_populates='expense_items')
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='expense_item')  # ✅ Relationship with User


class Expense(db.Model):
    __tablename__ = 'expenses'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='expenses')
    payment_type = sa.Column(sa.String(50), nullable=False)
    expcat_id = sa.Column(sa.Integer, sa.ForeignKey('expense_category.id'), nullable=False)
    expense_category = db.relationship('ExpenseCategory', backref='expenses')
    expense_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    description = sa.Column(sa.String(220))
    expense_items = db.relationship('ExpenseItem', back_populates='expense', lazy=True, cascade="all, delete-orphan")
    total_amount = db.Column(db.Float)

    

class Sale(db.Model):
    __tablename__ = 'sales'
    id = sa.Column(sa.Integer, primary_key=True)
    customer_id = sa.Column(sa.Integer, sa.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer', backref='sales')  # ✅ Fixed customer relation
    invoice_number = sa.Column(sa.String(50), unique=True, nullable=True)  # ✅ Unique invoice number
    invoice_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    payment_terms = sa.Column(sa.Integer, nullable=False, default=30)
    total_amount = sa.Column(sa.Float, nullable=False, default=0.00)
    discount = sa.Column(sa.Float, default=0.00)
    tax_amount = sa.Column(sa.Float, default=0.00)
    total_price = sa.Column(sa.Float, default=0.00, nullable=True)
    recieved_amount = sa.Column(sa.Float, default=0.00)  # ✅ Should be updated from AmountReceive
    balance_due = sa.Column(sa.Float, default=0.00)  # ✅ Auto-update balance
    payment_mode = sa.Column(sa.String(50), nullable=True)
    payment_date = sa.Column(sa.DateTime, nullable=True)
    cgst = sa.Column(sa.String(20), nullable=True)
    sgst = sa.Column(sa.String(20), nullable=True)
    igst = sa.Column(sa.String(20), nullable=True)
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade="all, delete-orphan")
    receive_amounts = db.relationship('AmountReceive', backref='sale', lazy=True, cascade="all, delete-orphan")
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', back_populates='sales')
    def __repr__(self):
        return f"Sale {self.id} - {self.invoice_number}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.balance_due is None and self.total_amount:
            self.balance_due =self.total_amount

    def sales_count(self):
        return Sale.query.filter_by(user_id=self.id).count()

    def add_sale(sale_data, user_id):
        sale = Sale(
                customer_id=sale_data['customer_id'],
                user_id=user_id,  # ✅ Correct usage
                total_price=0
                )
        db.session.add(sale)
        db.session.flush()
        
        total_price = 0
        sale_items = []
        stock_movements = []

        for item_data in sale_data['items']:
            item = Item.query.get(item_data['item_id'])

        if item and item.stock_quantity >= item_data['quantity']:
            sale_item = SaleItem(
                    sale_id=sale.id,
                    item_id=item.id,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['quantity'] * item_data['unit_price'],
                    user_id=user_id  # ✅ Make sure this field is set
                    )
            total_price += sale_item.total_price
            item.stock_quantity -= sale_item.quantity
            sale_items.append(sale_item)

            stock_movements.append(StockMovement(
                item_id=item.id,
                movement_type="sale",
                quantity=-sale_item.quantity,
                user_id=user_id  # ✅ Here too
                ))
        else:
            print(f"❌ Not Enough Stock for {item.name}")
        
        sale.total_price = total_price
        db.session.add_all(sale_items)
        db.session.add_all(stock_movements)
        db.session.commit()
        print(f"✅ Sale {sale.id} Completed by User {user_id}, Total: {sale.total_price}")





class AmountReceive(db.Model):
    __tablename__ = 'amount_receive'
    id = sa.Column(sa.Integer, primary_key=True)
    sale_id = sa.Column(sa.Integer, sa.ForeignKey('sales.id', ondelete="CASCADE"), nullable=False)
    amount = sa.Column(sa.Float, nullable=False)
    payment_mode = sa.Column(sa.String(50), nullable=False)
    payment_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='amount_receive')  # ✅ Relationship with User

    def __repr__(self):
        return f"AmountReceive {self.id} - Rs. {self.amount}"


class PurchaseAmountReceive(db.Model):
    __tablename__ = 'purchase_amount_receive'
    id = sa.Column(sa.Integer, primary_key=True)
    purchase_id = sa.Column(sa.Integer, sa.ForeignKey('purchases.id', ondelete="CASCADE"), nullable=False)
    amount = sa.Column(sa.Float, nullable=False)
    payment_mode = sa.Column(sa.String(50), nullable=False)
    payment_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='purchase_amount_receive')  # ✅ Relationship with User

    def __repr__(self):
        return f"PurchaseAmountReceive {self.id} - Rs. {self.amount}"


class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = sa.Column(sa.Integer, primary_key=True)
    sale_id = sa.Column(sa.Integer, sa.ForeignKey('sales.id', ondelete="CASCADE"), nullable=False)
    item_id = sa.Column(sa.Integer, sa.ForeignKey('items.id', ondelete="CASCADE"), nullable=False)

    quantity = sa.Column(sa.Integer, nullable=False, default=1)
    rate = sa.Column(sa.Float, nullable=False, default=0.0)
    subtotal = sa.Column(sa.Float, nullable=False, default=0.0)
    tax_percent = sa.Column(sa.Float, nullable=False, default=0.0)
    tax_value = sa.Column(sa.Float, nullable=False, default=0.0)
    total_amount = sa.Column(sa.Float, nullable=False, default=0.0)
    total_cost = sa.Column(sa.Float, nullable=True, default=0.0)
    unit_price = sa.Column(sa.Float, default=0.0)

#    item = db.relationship('Item', backref='item_sale_items', lazy='joined')
    item = db.relationship('Item', back_populates='sale_items')


    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='sale_items')  # ✅ Relationship with User

    def __repr__(self):
        return f"<Sold {self.quantity} of {self.item.name}>"

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'
    id = sa.Column(sa.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'), nullable=False)


    item_id = sa.Column(sa.Integer, sa.ForeignKey('items.id', ondelete="CASCADE"), nullable=False)

    quantity = sa.Column(sa.Integer, nullable=False, default=1)
    rate = sa.Column(sa.Float, nullable=False)
    subtotal = sa.Column(sa.Float, nullable=False)
    tax_percent = sa.Column(sa.Float, nullable=False)
    tax_value = sa.Column(sa.Float, nullable=False)
    total_amount = sa.Column(sa.Float, nullable=False)

    unit_price = db.Column(sa.Float, nullable=True)
    total_cost = db.Column(sa.Float, nullable=True)






    item = db.relationship("Item", back_populates="purchase_items")

    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='purchase_items')  # ✅ Relationship with User

    # ❌ REMOVE this line (invalid relationship)
    # receive_amounts = db.relationship('PurchaseAmountReceive', backref='sale', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Purchased {self.quantity} of {self.item.itemname}>"



class Estimate(db.Model):
    __tablename__ = 'estimate'
    id = db.Column(db.Integer, primary_key=True)
    estimate_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='Estimate')  # ✅ 'Estimate' or 'Invoice'

    customer = db.relationship('Customer', backref='estimates')
    items = db.relationship('EstimateItem', backref='estimate', cascade='all, delete-orphan')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref='estimates')




class EstimateItem(db.Model):
    __tablename__ = 'estimate_item'
    id = db.Column(db.Integer, primary_key=True)
    estimate_id = db.Column(db.Integer, db.ForeignKey('estimate.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    tax_percent = db.Column(db.Float, default=0.0)
    tax_value = db.Column(db.Float, default=0.0)

    # ✅ Add this line:
    item = db.relationship('Item', backref='estimate_items')




class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = sa.Column(sa.Integer, primary_key=True)
    vendor_id = sa.Column(sa.Integer, sa.ForeignKey('vendors.id'), nullable=False)
    purchase_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
   # invoice_number = sa.Column(sa.String(50), unique=True, nullable=True)
    invoice_date = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    payment_terms = sa.Column(sa.Integer, nullable=True)
    vendor = db.relationship('Vendor', backref='purchases')  # ✅ Fixed customer relation

    total_amount = sa.Column(sa.Float, nullable=False, default=0.00)
    total_cost = sa.Column(sa.Float, default=0.0, nullable=False)
    discount = sa.Column(sa.Float, default=0.00)
    tax_amount = sa.Column(sa.Float, default=0.00)

    recieved_amount = sa.Column(sa.Float, default=0.00)
    balance_due = sa.Column(sa.Float, default=0.00)

    payment_mode = sa.Column(sa.String(50), nullable=True)
    cgst = sa.Column(sa.String(50), nullable=True)
    igst = sa.Column(sa.String(50), nullable=True)
    sgst = sa.Column(sa.String(50), nullable=True)
    payment_date = sa.Column(sa.DateTime, nullable=True)

    # ✅ This is the correct relationship (inside Purchase, NOT PurchaseItem)
    receive_amounts = db.relationship('PurchaseAmountReceive', backref='purchase', lazy=True, cascade="all, delete-orphan")

    purchase_items = db.relationship('PurchaseItem', backref='purchase_order')


    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='purchases')  # ✅ Relationship with User

    def add_purchase(purchase_data):
        purchase = Purchase(vendor_id=purchase_data['vendor_id'], total_cost=0)
        db.session.add(purchase)
        db.session.flush()  # Get `purchase.id`

        total_cost = 0
        for item_data in purchase_data['items']:
            item = Item.query.get(item_data['item_id'])
            if item:
                purchase_item = PurchaseItem(
                    purchase_id=purchase.id,
                    item_id=item.id,
                    quantity=item_data['quantity'],
                    unit_cost=item_data['unit_cost'],
                    total_cost=item_data['quantity'] * item_data['unit_cost']
                )
                total_cost += purchase_item.total_cost

                # ✅ Update Stock Quantity
                item.stock_quantity += purchase_item.quantity
                db.session.add(purchase_item)

                # ✅ Log Stock Movement
                stock_movement = StockMovement(item_id=item.id, movement_type="purchase", quantity=purchase_item.quantity)
                db.session.add(stock_movement)

        purchase.total_cost = total_cost
        db.session.commit()
        print(f"✅ Purchase {purchase.id} Added Successfully")






class Godown(db.Model):
    __tablename__ = 'godowns'
    id = sa.Column(sa.Integer, primary_key=True)
    locname = sa.Column(sa.String(120))
    created_date = sa.Column(sa.DateTime, default=datetime.utcnow)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='godowns')  # ✅ Relationship with User
    def __str__(self):
        return self.locname


class StockNotification(db.Model):
    __tablename__ = "stock_notification"
    id = sa.Column(sa.Integer, primary_key=True)
    item_id = sa.Column(sa.Integer, sa.ForeignKey('items.id'), nullable=False)
    item = db.relationship('Item', backref='items_notification')
    message = sa.Column(sa.String(255), nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)  # ✅ Added user_id
    user = db.relationship('User', backref='stock_notification')  # ✅ Relationship with User
    threshold = db.Column(db.Float)


class Subscription(db.Model):
    __tablename__ = "subscriptions"
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    plan_type = sa.Column(sa.String(50), nullable=False)  # 'monthly' or 'yearly'
    start_date = sa.Column(sa.DateTime, default=datetime.utcnow)
    end_date = sa.Column(sa.DateTime)

    # Relationship to User
    user = db.relationship('User', back_populates='subscriptions')
    is_active = sa.Column(sa.Boolean, default=True)
    max_entries = db.Column(db.Integer, default=None) 

    def __repr__(self):
        return f"<Subscription(user_id={self.user_id}, plan_type={self.plan_type})>"



