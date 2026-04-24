from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, IntegerField, PasswordField, SubmitField, TextAreaField, DateField, SelectField, BooleanField, FloatField, HiddenField, FieldList, FormField
from wtforms.validators import DataRequired, Email, EqualTo, Optional, InputRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from app.models import Category, Item, Customer, Sale, Godown, Vendor, Purchase, ItemMovement, User, ExpenseCategory, ExpenseItem, Expense
from app import db
import sqlalchemy as sa
from wtforms.validators import Length
from flask_login import current_user
from wtforms.validators import ValidationError
from datetime import datetime


class CategoryForm(FlaskForm):
	catname = StringField('Category Name', validators=[DataRequired()])
	description = StringField('Description')
	submit = SubmitField('SUBMIT')

class ExpenseCategoryForm(FlaskForm):
    name = StringField('Expense Category', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('SUBMIT')


class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember Me')
	submit = SubmitField('Sign In')


class ResetPasswordRequestForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired()])
	password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Request Password Reset')

def get_items():
    return Item.query.all()

def get_customers():
    return Customer.query.all()

class EstimateItemForm(FlaskForm):
    class Meta:
        csrf = False
    item = QuerySelectField('Item', query_factory=get_items, get_label='itemname')
    quantity = IntegerField('Quantity')
    price = FloatField('Price')
    tax = FloatField('TAX%')

class EstimateForm(FlaskForm):
    customer = QuerySelectField('Customer', query_factory=get_customers, get_label='name')
    date = DateField('Date', default=datetime.utcnow)
    items = FieldList(FormField(EstimateItemForm), min_entries=1)
    submit = SubmitField('Save Estimate')


from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import User  # adjust this import to your project structure
from app import db
import sqlalchemy as sa

class EditCustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    mobile = StringField('Mobile')
    address = StringField('Address')
    

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    aboute_me = TextAreaField('About me', validators=[Length(min=0, max=140)])  # ✅ fixed typo: "aboute_me"
    mobile = StringField('Mobile', validators=[Length(max=20)])
    address = TextAreaField('Address', validators=[Length(max=200)])
    gst = StringField('GST', validators=[Length(max=20)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(User.username == username.data))
            if user is not None:
                raise ValidationError('Please use a different username.')  # ✅ fix logic: raise if user *exists*


class CustomerForm(FlaskForm):
	name = StringField('Customer Name', validators = [DataRequired()])
	mobile =StringField('Mobile #', validators = [DataRequired()])
	email = StringField('Email ID', validators = [DataRequired()])
	gst = StringField('GST #', validators = [Optional()])
	pan = StringField('PAN #', validators = [Optional()])
	address = StringField('Address', validators = [DataRequired()])
	submit = SubmitField('Add Customer')



class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    mobile = IntegerField('Mobile#', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])

    gst = StringField('GST#')
    pas = StringField('PAN#')
    address = TextAreaField('Address')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')



class VendorForm(FlaskForm):
	name = StringField('Vendor / Supplier Name', validators = [DataRequired()])
	mobile = StringField('Mobile #', validators = [DataRequired()])
	email = StringField('Email ID')
	gstin = StringField('GST #')
	pan = StringField('PAN #')
	address = StringField('Address', validators = [DataRequired()])
	submit = SubmitField('Add Customer')



def customer_choice():
	return Customer.query.all()


from flask_wtf import FlaskForm
from wtforms import Form, IntegerField, SubmitField, FieldList, FormField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired
from app.models import Item, Customer

def item_choice():
    return Item.query.filter_by(user_id=current_user.id).all()

def customer_coice():
    return Customer.query.filter_by(user_id=current_user.id).all()

class SaleItemForm(FlaskForm):
    class Meta:
        csrf = False
    itemname = StringField('Item Name', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    rate = FloatField('Rate', validators=[DataRequired()])
    tax = FloatField('TAX %')
    tax_amount = HiddenField('Tax Amount')
    subtotal = FloatField('Sub Total')
    total_amount = HiddenField('Total Amount')

class SaleForm(FlaskForm):
    customername = StringField('Customer Name')
    balance_due = FloatField('Balace Due')
    payment_terms = IntegerField('Payment Terms in Days', default=30, validators=[DataRequired()])
    invoice_number = StringField('Invoice #', render_kw={"readonly": True})
    items = FieldList(FormField(SaleItemForm), min_entries=1)  # Allow dynamic entries
    submit = SubmitField('Submit')



from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, FieldList, FormField, SubmitField, DateField
from wtforms.validators import DataRequired, NumberRange, Optional
from datetime import date

class AmountReceiveForm(FlaskForm):
    class Meta:
        csrf = False
    amount = FloatField("Amount", validators=[DataRequired()])
    payment_mode = SelectField("Payment Mode", choices=[("Cash", "Cash"), ("Card", "Card"), ("Online", "Online")], validators=[DataRequired()])

    payment_date = DateField("Payment Date", format="%m-%d-%Y", default=date.today, validators=[Optional()])


class SaleAmountReceiveForm(FlaskForm):
    customername = QuerySelectField(query_factory=lambda: Customer.query.all(), get_label='name', allow_blank=True)
    payment_terms = StringField("Payment Terms", render_kw={"readonly": True})
    receive_amounts = FieldList(FormField(AmountReceiveForm), min_entries=1)
    balance_due = DecimalField("Balance Due", default=0.00, render_kw={"readonly": True})
    total_amount = DecimalField('Total Due', default=0.00, render_kw={"readonly": True})
    submit = SubmitField("Save Payment")


from wtforms import SelectField, IntegerField, FloatField, FieldList, FormField
from wtforms.validators import DataRequired, NumberRange

from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms import IntegerField, FloatField
from wtforms.validators import DataRequired, NumberRange

class SaleItemEditForm(FlaskForm):
    itemname = QuerySelectField(
        'Item Name', 
        query_factory=item_choice, 
        get_label='itemname', 
        allow_blank=False,
        get_pk=lambda item: item.id  # ✅ Ensures it stores the item ID, not the object
    )
    quantity = IntegerField("Quantity", validators=[DataRequired(), NumberRange(min=1)])
    rate = FloatField("Rate", validators=[DataRequired()])
    tax = FloatField("Tax %", validators=[DataRequired()])
    subtotal = FloatField("Subtotal", validators=[DataRequired()])


def cat_choice():
	return Category.query.all()

class ItemsForm(FlaskForm):
    category = QuerySelectField(query_factory=cat_choice, get_label="catname", allow_blank=True)
    itemname = StringField('Item Name', validators=[DataRequired()])
    item_code = StringField('Item Code')
    hsn_code = StringField('HSN Code')
    purchase_price = FloatField('Purchase Price', default=0.00)
    selling_price = FloatField('Selling Price', default=0.00)
    description = StringField('Description')
    submit = SubmitField('Add Item')

class ExpenseItemsForm(FlaskForm):
    class Meta:
        csrf = False
    itemname = StringField('Item Name')
    quantity = FloatField('Quantity')
    rate = FloatField('Rate')
    amount = FloatField('Amount')
    total_amount = FloatField('Total Amount')

class ExpenseForm(FlaskForm):
    expence_category = QuerySelectField(query_factory=lambda: ExpenseCategory.query.all(), get_label='name', allow_blank=True, blank_text="Select or Add Category", validators=[DataRequired()])
    expense_items = FieldList(FormField(ExpenseItemsForm), min_entries=1)
    payment_type = SelectField('Payment Type', choices=['Cash', 'UPI', 'Cheque', 'Net Banking'])
    submit = SubmitField('SAVE')

def vendor_choice():
	return Vendor.query.all()


class PurchaseItemForm(FlaskForm):
    class Meta:
        csrf = False
        itemname = QuerySelectField("Item", query_factory=..., get_label='itemname', validate_choice=False)

#    itemname = QuerySelectField('Item Name', query_factory=item_choice, get_label='itemname', allow_blank=True)
    quantity = FloatField('Quantity', validators=[DataRequired()])
    rate = FloatField('Rate', validators=[DataRequired()])
    tax = FloatField('TAX %', validators=[Optional()])
    tax_amount = FloatField('Tax Amount')
    subtotal = FloatField('Sub Total')
    total_amount = FloatField('Total Amount')

class PurchaseForm(FlaskForm):
    purchase_id = IntegerField('Purchase ID')  # Make sure this exists
    vendorname = StringField('Vendor Name')
    #QuerySelectField(query_factory=lambda: Vendor.query.all(), get_label='name', allow_blank=True)
    balance_due = FloatField('Balace Due')
    payment_terms = IntegerField('Payment Terms in Days')
    invoice_number = StringField('Invoice #', render_kw={"readonly": True})
    items = FieldList(FormField(PurchaseItemForm), min_entries=1)  # Allow dynamic entries
    submit = SubmitField('Submit')


class PurAmountRecForm(FlaskForm):
    class Meta:
        csrf = False
    amount = FloatField("Amount", validators=[DataRequired()])
    payment_mode = SelectField("Payment Mode", choices=[("Cash", "Cash"), ("Card", "Card"), ("Online", "Online")], validators=[DataRequired()])

    payment_date = DateField("Payment Date", format="%m-%d-%Y", default=date.today, validators=[Optional()])


class PurchaseAmountReceiveForm(FlaskForm):
    vendorname = QuerySelectField(query_factory=lambda: Vendor.query.all(), get_label='name', allow_blank=True)
    payment_terms = StringField("Payment Terms", render_kw={"readonly": True})
    receive_amounts = FieldList(FormField(PurAmountRecForm), min_entries=1)
    balance_due = DecimalField("Balance Due", default=0.00, render_kw={"readonly": True})
    total_amount = DecimalField('Total Due', default=0.00, render_kw={"readonly": True})
    submit = SubmitField("Save Payment")

class GodownForm(FlaskForm):
    locname = StringField('Godown Name', validators=[DataRequired()])
    created_date = HiddenField('Date')
    submit = SubmitField('Add Godown')

def loc_choice():
	return Godown.query.all()

class ItemMovementForm(FlaskForm):
    item = QuerySelectField(query_factory=item_choice, get_label='itemname')
    quantity = IntegerField('Quantity')
    movement_type = SelectField('Movement Type', choices=[("Godown", "Godown")], validators=[DataRequired()])
    from_location = SelectField('From Location', choices=[], validate_choice=False)
    to_location = SelectField('To Location', choices=[], validate_choice=False)

    submit = SubmitField('Move')


class SubscriptionForm(FlaskForm):
    subscription_type = RadioField(
        'Subscription Type', 
        choices=[('monthly', 'Monthly Plan - $10/month'), ('yearly', 'Yearly Plan - $100/year (Save 15%)')],
        validators=[InputRequired()]
    )
    submit = SubmitField('Subscribe')