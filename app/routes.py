from flask import render_template, flash, redirect, url_for, send_file, session, make_response, g, Blueprint
from app import db
from app.forms import CategoryForm, ItemsForm, CustomerForm, SaleForm, GodownForm, VendorForm, PurchaseForm, ItemMovementForm, LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm, SaleItemEditForm, SaleAmountReceiveForm, AmountReceiveForm, PurchaseItemForm,  PurchaseAmountReceiveForm, ExpenseCategoryForm, ExpenseItemsForm, ExpenseForm, SubscriptionForm, EstimateForm
from app.models import User, Customer, Item, Category, Sale, Godown, Vendor, Purchase, ItemMovement, SaleItem, AmountReceive, PurchaseItem, PurchaseAmountReceive, ExpenseCategory, Expense, ExpenseItem, StockNotification, Subscription, Estimate, EstimateItem
import sqlalchemy as sa
from flask_login import current_user, login_user, logout_user, login_required
from flask import request
from urllib.parse import urlsplit
from datetime import datetime, timezone, timedelta
from app.email import send_password_reset_email
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from flask import request, jsonify
from sqlalchemy import func, case
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask_babel import _
from app.locale_utils import get_current_locale

from flask import render_template
from flask_babel import get_locale
from app.locale_utils import get_translation_dict
from language_utils import get_locale, get_translation_dict


bp = Blueprint('main', __name__)

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@bp.route('/admin/customers')
@login_required
@admin_required
def admin_customers():
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('admin/customers.html', customers=customers)

@bp.route('/admin/vendors')
@login_required
@admin_required
def admin_vendors():
    vendors = Vendor.query.order_by(Vendor.name).all()
    return render_template('admin/vendors.html', vendors=vendors)

@bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=users)


@bp.route('/admin/sales')
@login_required
@admin_required
def admin_sales():
    sales = (
        db.session.query(Sale)
        .join(Sale.user)
        .options(joinedload(Sale.user))
        .order_by(User.username)
        .all()
    )
    return render_template('admin/sales.html', sales=sales)

@bp.route('/admin/purchases')
@login_required
@admin_required
def admin_purchases():
    purchases = (
        db.session.query(Purchase)
        .join(Purchase.user)
        .options(joinedload(Purchase.user))
        .order_by(User.username)
        .all()
    )
    return render_template('admin/purchases.html', purchases=purchases)

@bp.route('/admin/expenses')
@login_required
@admin_required
def admin_expenses():
    expenses = (
        db.session.query(Expense)
        .join(Expense.user)
        .options(joinedload(Expense.user))
        .order_by(User.username)
        .all()
    )
    return render_template('admin/expenses.html', expenses=expenses)

@bp.route('/admin/estimates')
@login_required
@admin_required
def admin_estimates():
    estimates = (
        db.session.query(Estimate)
        .join(Estimate.user)
        .options(joinedload(Estimate.user))
        .order_by(User.username)
        .all()
    )
    return render_template('admin/estimates.html', estimates=estimates)


from sqlalchemy.orm import joinedload

@bp.route('/admin/items')
@login_required
@admin_required
def admin_items():
    items = (
        db.session.query(Item)
        .join(Item.user)
        .options(joinedload(Item.user))  # optional: avoids extra queries in template
        .order_by(User.username)
        .all()
    )
    return render_template('admin/items.html', items=items)


@bp.route('/admin/block/<int:user_id>')
@login_required
@admin_required
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.blocked = True   # ✅ Set the real column
    db.session.commit()
    flash(f"User {user.username} has been blocked.", "warning")
    return redirect(url_for('main.admin_users'))

@bp.route('/admin/unblock/<int:user_id>')
@login_required
@admin_required
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.blocked = False  # ✅ Unblock by changing the actual DB column
    db.session.commit()
    flash(f"User {user.username} has been unblocked.", "success")
    return redirect(url_for('main.admin_users'))

@bp.route('/admin/export_users_csv')
@login_required
@admin_required
def admin_export_users_csv():
    users = User.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Username', 'Mobile', 'Address', 'Email', 'GST', 'PAN', 'Admin', 'Last Seen', 'Paid', 'Expiry'])

    for u in users:
        writer.writerow([u.username, u.mobile, u.address, u.email, u.gst, u.pas, u.is_admin, u.last_seen, u.is_paid, u.payment_expiry])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=users.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@bp.route('/admin/export_items_csv')
def admin_export_items_csv():
    from flask import Response
    import csv
    from io import StringIO

    items = Item.query.all()
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Item Name', 'HSN Code', 'Item Code', 'Created Date', 'Stock', 'Purchase Price', 'Selling Price', 'Username'])

    for i in items:
        writer.writerow([
            i.itemname, i.hsn_code, i.item_code, i.created_date,
            i.stock_quantity, i.purchase_price, i.selling_price,
            i.user.username if i.user else ''
        ])

    output.seek(0)
    return Response(output, mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=items.csv'})

import csv
from flask import make_response
from io import StringIO
from .models import Customer  # Adjust this import based on your project

@bp.route('/admin/export_customers_csv')
@login_required
@admin_required
def admin_export_customers_csv():
    customers = Customer.query.all()

    output = StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow(['ID', 'Name', 'Mobile', 'Address', 'Email', 'GST', 'PAN', 'User'])

    # Write data rows
    for c in customers:
        writer.writerow([
            c.id,
            c.name,
            c.mobile,
            c.address,
            c.email,
            c.gst or '',
            c.pan or '',
            c.user.username if c.user else ''
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=customers.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


from flask import Response
import csv
from io import StringIO
from sqlalchemy.orm import joinedload

@bp.route('/admin/export_purchases_csv')
@login_required
@admin_required
def admin_export_purchases_csv():
    purchases = (
        db.session.query(Purchase)
        .options(joinedload(Purchase.Vendor), joinedload(Purchase.user))
        .order_by(Purchase.invoice_date.desc())
        .all()
    )

    def generate():
        data = StringIO()
        writer = csv.writer(data)

        # Header row
        writer.writerow(['Invoice ID', 'Date', 'Vendor', 'Total Amount', 'User', 'Due Balance'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # Data rows
        for p in purchases:
            writer.writerow([
                p.id,
                p.invoice_date.strftime("%Y-%m-%d") if p.invoice_date else '',
                p.Vendor.name if p.Vendor else '',
                p.total_amount,
                p.user.username if p.user else '',
                p.balance_due
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    headers = {
        'Content-Disposition': 'attachment; filename=purchases.csv',
        'Content-Type': 'text/csv',
    }

    return Response(generate(), headers=headers)


@bp.route('/admin/export_estimates_csv')
@login_required
@admin_required
def admin_export_estimates_csv():
    import csv
    from io import StringIO
    from flask import Response
    from sqlalchemy.orm import joinedload
    from app.models import Estimate  # Make sure Estimate is imported

    estimates = (
        Estimate.query
        .options(joinedload(Estimate.customer), joinedload(Estimate.user))
        .order_by(Estimate.id.desc())
        .all()
    )

    def generate():
        data = StringIO()
        writer = csv.writer(data)
        # Write header
        writer.writerow(['ID', 'Date', 'Customer', 'Total Amount', 'Status', 'User'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # Write rows
        for est in estimates:
            writer.writerow([
                est.id,
                est.date.strftime('%Y-%m-%d') if est.date else '',
                est.customer.name if est.customer else '',
                est.total_amount or 0,
                est.status or 'Pending',
                est.user.username if est.user else ''
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    return Response(generate(), mimetype='text/csv', headers={
        "Content-Disposition": "attachment;filename=estimates.csv"
    })


from flask import Response
import csv
from io import StringIO
from sqlalchemy.orm import joinedload
from app.models import Expense
from app.routes import bp  # your Blueprint
from flask_login import login_required


@bp.route('/admin/export_expenses_csv')
@login_required
@admin_required
def admin_export_expenses_csv():
    # Fetch expenses with related user and category to avoid DetachedInstanceError
    expenses = Expense.query.options(
        joinedload(Expense.user),
        joinedload(Expense.expense_category)
    ).all()

    # Prepare CSV in-memory
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Date", "Category", "Payment Type", "Total Amount", "Description", "Username"])

    for e in expenses:
        cw.writerow([
            e.id,
            e.expense_date.strftime('%Y-%m-%d %H:%M'),
            e.expense_category.name if e.expense_category else '',
            e.payment_type,
            f"{e.total_amount:.2f}",
            e.description or '',
            e.user.username if e.user else ''
        ])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"}
    )


from sqlalchemy.orm import joinedload

@bp.route('/admin/export_sales_csv')
@login_required
@admin_required
def admin_export_sales_csv():
    sales = (
        db.session.query(Sale)
        .options(joinedload(Sale.customer), joinedload(Sale.user))  # 👈 eager load
        .order_by(Sale.id)
        .all()
    )

    def generate():
        data = StringIO()
        writer = csv.writer(data)

        writer.writerow([
            'Invoice ID',
            'Date',
            'Customer Name',
            'Total Amount',
            'Due Balance',
            'Created By'
        ])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        for s in sales:
            writer.writerow([
                s.id,
                s.invoice_date,
                s.customer.name if s.customer else '',
                s.total_amount,
                s.balance_due,
                s.user.username if s.user else ''
            ])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=sales_export.csv"}
    )

def check_active_subscription():
    active_subscription = Subscription.query.filter_by(user_id=current_user.id, is_active=True).first()
    
    if not active_subscription:
        return False

    # Count total entries (Sales + Purchases + Expenses)
    sale_count = Sale.query.filter_by(user_id=current_user.id).count()
    purchase_count = Purchase.query.filter_by(user_id=current_user.id).count()
    expense_count = Expense.query.filter_by(user_id=current_user.id).count()

    total_entries = sale_count + purchase_count + expense_count

    # Check for nearing limit
    if active_subscription.plan_type == 'free' and total_entries >= 900:
        flash(f"⚠️ You have used {total_entries}/1000 free entries. Upgrade soon to avoid disruption.", "warning")

    # Optional: enforce limit if exceeded
    if active_subscription.plan_type == 'free' and total_entries >= 1000:
        flash("❌ You’ve reached the 1000 free entries limit. Please subscribe to continue.", "danger")
        return False

    return True

    
@bp.context_processor
def inject_subscription_status():
    status = None
    if current_user.is_authenticated:
        sub = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.end_date.desc()).first()
        if sub and sub.end_date >= datetime.utcnow():
            status = "Active"
        else:
            status = "Expired"
    return dict(subscription_status=status)

@bp.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)



def currency_format(value):
    return f"₹{value:,.2f}"

bp.add_app_template_filter(currency_format, name='currency')


@bp.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.now(timezone.utc)
		db.session.commit()



from flask import g
from sqlalchemy import func, case

@bp.context_processor
def inject_stock_alerts():
    if current_user.is_authenticated:
        alerts = StockNotification.query.join(Item).filter(
            StockNotification.user_id == current_user.id
        ).order_by(StockNotification.created_at.desc()).limit(5).all()
        return dict(low_stock_alerts=alerts)
    return dict(low_stock_alerts=[])


@bp.before_request
def load_stock_notifications():
    from app.models import Item, PurchaseItem, SaleItem
    from flask_login import current_user
    from sqlalchemy import func
    from datetime import datetime

    if current_user.is_authenticated:
        items = db.session.query(Item).filter_by(user_id=current_user.id).all()
        stock_notifications = []

        for item in items:
            purchased = db.session.query(func.sum(PurchaseItem.quantity)).filter_by(item_id=item.id).scalar() or 0
            sold = db.session.query(func.sum(SaleItem.quantity)).filter_by(item_id=item.id).scalar() or 0
            current_stock = purchased - sold

            if current_stock < item.min_stock:
                stock_notifications.append({
                    "itemname": item.itemname,
                    "message": f"Only {current_stock} left in stock.",
                    "time": datetime.utcnow().strftime('%b %d, %H:%M')
                })

        g.stock_notifications = stock_notifications
        g.stock_notif_count = len(stock_notifications)
    else:
        g.stock_notifications = []
        g.stock_notif_count = 0

from flask_login import login_required, current_user
from sqlalchemy import or_, func, case




@bp.route('/')
@bp.route('/index')
@login_required
def index():
    print(f"current_user: {current_user}")
    print(f"Is authenticated? {current_user.is_authenticated}")
    print(f"User ID: {current_user.get_id()}")
    lang = get_locale()
    translations = get_translation_dict(lang)
    print(get_locale())
    search_query = request.args.get('search', '').strip()
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    # Filtered queries
    sales_query = db.session.query(Sale.id, Customer.name, Sale.invoice_date, Sale.total_amount) \
        .join(Customer, Customer.id == Sale.customer_id) \
        .filter(Sale.user_id == current_user.id)

    purchases_query = db.session.query(Purchase.id, Vendor.name, Purchase.invoice_date, Purchase.total_amount) \
        .join(Vendor, Vendor.id == Purchase.vendor_id) \
        .filter(Purchase.user_id == current_user.id)

    payments_in_query = db.session.query(AmountReceive.amount, Customer.name, AmountReceive.payment_date) \
        .join(Sale, Sale.id == AmountReceive.sale_id) \
        .join(Customer, Customer.id == Sale.customer_id) \
        .filter(AmountReceive.user_id == current_user.id)

    payments_out_query = db.session.query(PurchaseAmountReceive.amount, Vendor.name, PurchaseAmountReceive.payment_date) \
        .join(Purchase, Purchase.id == PurchaseAmountReceive.purchase_id) \
        .join(Vendor, Vendor.id == Purchase.vendor_id) \
        .filter(PurchaseAmountReceive.user_id == current_user.id)

    expenses_query = db.session.query(Expense.expense_date, ExpenseCategory.name, sa.func.sum(ExpenseItem.amount)) \
        .join(ExpenseCategory, ExpenseCategory.id == Expense.expcat_id) \
        .join(ExpenseItem, ExpenseItem.expense_id == Expense.id) \
        .filter(Expense.user_id == current_user.id) \
        .group_by(Expense.id)

    stock_data = (
        db.session.query(
            Item.id, Item.itemname,
            (func.sum(case((ItemMovement.movement_type == "Purchase", ItemMovement.quantity), else_=0)) -
             func.sum(case((ItemMovement.movement_type == "Sale", ItemMovement.quantity), else_=0))
            ).label('remaining_stock')
        )
        .join(ItemMovement, Item.id == ItemMovement.item_id)
        .filter(ItemMovement.user_id == current_user.id)
        .group_by(Item.id)
        .all()
    )
    stock_list = [{"item_name": row[1], "remaining_stock": row[2]} for row in stock_data]

    # Filters
    if from_date and to_date:
        sales_query = sales_query.filter(Sale.invoice_date.between(from_date, to_date))
        purchases_query = purchases_query.filter(Purchase.invoice_date.between(from_date, to_date))
        payments_in_query = payments_in_query.filter(AmountReceive.payment_date.between(from_date, to_date))
        payments_out_query = payments_out_query.filter(PurchaseAmountReceive.payment_date.between(from_date, to_date))
        expenses_query = expenses_query.filter(Expense.expense_date.between(from_date, to_date))

    if search_query:
        sales_query = sales_query.filter(Customer.name.ilike(f"%{search_query}%"))
        purchases_query = purchases_query.filter(Vendor.name.ilike(f"%{search_query}%"))
        payments_in_query = payments_in_query.filter(Customer.name.ilike(f"%{search_query}%"))
        payments_out_query = payments_out_query.filter(Vendor.name.ilike(f"%{search_query}%"))
        expenses_query = expenses_query.filter(ExpenseCategory.name.ilike(f"%{search_query}%"))

    # Fetch and format
    sales_data = [{"type": "Sale", "party": s.name, "date": s.invoice_date, "amount": s.total_amount} for s in sales_query.all()]
    purchases_data = [{"type": "Purchase", "party": p.name, "date": p.invoice_date, "amount": -p.total_amount} for p in purchases_query.all()]
    payments_in_data = [{"party": p.name, "date": p.payment_date, "amount": p.amount} for p in payments_in_query.all()]
    payments_out_data = [{"party": p.name, "date": p.payment_date, "amount": -p.amount} for p in payments_out_query.all()]
    expenses_data = [{"category_name": e[1], "expense_date": e[0], "total_amount": e[2]} for e in expenses_query.all()]

    return render_template('index.html', t=translations, user=current_user, sales=sales_data, purchases=purchases_data, payments_in=payments_in_data, payments_out=payments_out_data, expenses=expenses_data, stock=stock_list)


@bp.route('/api/index')
@login_required
def api_index():
    search_query = request.args.get('search', '').strip()
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    # Same queries as your normal index
    sales_query = db.session.query(Sale.id, Customer.name, Sale.invoice_date, Sale.total_amount) \
        .join(Customer, Customer.id == Sale.customer_id) \
        .filter(Sale.user_id == current_user.id)

    purchases_query = db.session.query(Purchase.id, Vendor.name, Purchase.invoice_date, Purchase.total_amount) \
        .join(Vendor, Vendor.id == Purchase.vendor_id) \
        .filter(Purchase.user_id == current_user.id)

    payments_in_query = db.session.query(AmountReceive.amount, Customer.name, AmountReceive.payment_date) \
        .join(Sale, Sale.id == AmountReceive.sale_id) \
        .join(Customer, Customer.id == Sale.customer_id) \
        .filter(AmountReceive.user_id == current_user.id)

    payments_out_query = db.session.query(PurchaseAmountReceive.amount, Vendor.name, PurchaseAmountReceive.payment_date) \
        .join(Purchase, Purchase.id == PurchaseAmountReceive.purchase_id) \
        .join(Vendor, Vendor.id == Purchase.vendor_id) \
        .filter(PurchaseAmountReceive.user_id == current_user.id)

    expenses_query = db.session.query(Expense.expense_date, ExpenseCategory.name, sa.func.sum(ExpenseItem.amount)) \
        .join(ExpenseCategory, ExpenseCategory.id == Expense.expcat_id) \
        .join(ExpenseItem, ExpenseItem.expense_id == Expense.id) \
        .filter(Expense.user_id == current_user.id) \
        .group_by(Expense.id)

    stock_data = (
        db.session.query(
            Item.id, Item.itemname,
            (func.sum(case((ItemMovement.movement_type == "Purchase", ItemMovement.quantity), else_=0)) -
             func.sum(case((ItemMovement.movement_type == "Sale", ItemMovement.quantity), else_=0))
            ).label('remaining_stock')
        )
        .join(ItemMovement, Item.id == ItemMovement.item_id)
        .filter(ItemMovement.user_id == current_user.id)
        .group_by(Item.id)
        .all()
    )

    if from_date and to_date:
        sales_query = sales_query.filter(Sale.invoice_date.between(from_date, to_date))
        purchases_query = purchases_query.filter(Purchase.invoice_date.between(from_date, to_date))
        payments_in_query = payments_in_query.filter(AmountReceive.payment_date.between(from_date, to_date))
        payments_out_query = payments_out_query.filter(PurchaseAmountReceive.payment_date.between(from_date, to_date))
        expenses_query = expenses_query.filter(Expense.expense_date.between(from_date, to_date))

    if search_query:
        sales_query = sales_query.filter(Customer.name.ilike(f"%{search_query}%"))
        purchases_query = purchases_query.filter(Vendor.name.ilike(f"%{search_query}%"))
        payments_in_query = payments_in_query.filter(Customer.name.ilike(f"%{search_query}%"))
        payments_out_query = payments_out_query.filter(Vendor.name.ilike(f"%{search_query}%"))
        expenses_query = expenses_query.filter(ExpenseCategory.name.ilike(f"%{search_query}%"))

    # Fetch data
    sales_data = [{"type": "Sale", "party": s.name, "date": s.invoice_date.strftime('%Y-%m-%d'), "amount": s.total_amount} for s in sales_query.all()]
    purchases_data = [{"type": "Purchase", "party": p.name, "date": p.invoice_date.strftime('%Y-%m-%d'), "amount": -p.total_amount} for p in purchases_query.all()]
    payments_in_data = [{"party": p.name, "date": p.payment_date.strftime('%Y-%m-%d'), "amount": p.amount} for p in payments_in_query.all()]
    payments_out_data = [{"party": p.name, "date": p.payment_date.strftime('%Y-%m-%d'), "amount": -p.amount} for p in payments_out_query.all()]
    expenses_data = [{"category_name": e[1], "expense_date": e[0].strftime('%Y-%m-%d'), "total_amount": e[2]} for e in expenses_query.all()]
    stock_list = [{"item_name": row[1], "remaining_stock": row[2]} for row in stock_data]

    return jsonify({
        "sales": sales_data,
        "purchases": purchases_data,
        "payments_in": payments_in_data,
        "payments_out": payments_out_data,
        "expenses": expenses_data,
        "stock": stock_list
    })




@bp.route('/stock_alerts')
@login_required
def stock_alerts():
    lang = get_locale()
    translations = get_translation_dict(lang)
    from sqlalchemy import func
    from flask_login import current_user

    user_id = current_user.id

    # Get purchase and sale totals
    purchases = (
        db.session.query(ItemMovement.item_id, func.sum(ItemMovement.quantity).label('total_purchased'))
        .filter(ItemMovement.movement_type == "Purchase", ItemMovement.user_id == user_id)
        .group_by(ItemMovement.item_id)
        .all()
    )
    sales = (db.session.query(ItemMovement.item_id, func.sum(ItemMovement.quantity).label('total_sold'))
        .filter(ItemMovement.movement_type.in_(["Sale", "sale", "SOLD", "Out"]), ItemMovement.user_id == user_id)
        .group_by(ItemMovement.item_id)
        .all()
        )

    purchase_dict = {item_id: total_purchased for item_id, total_purchased in purchases}
    sale_dict = {item_id: total_sold for item_id, total_sold in sales}

    stock_data = []

    # ✅ Loop through ALL items, not just purchased ones
    all_items = Item.query.filter_by(user_id=user_id).all()

    for item in all_items:
        item_id = item.id
        total_purchased = purchase_dict.get(item_id, 0)
        total_sold = sale_dict.get(item_id, 0)
        remaining_stock = total_purchased + total_sold

        # ✅ Get threshold from StockNotification if available
        stock_notification = StockNotification.query.filter_by(item_id=item_id, user_id=user_id).first()
        threshold = stock_notification.threshold if stock_notification else None

        stock_data.append({
            "item_name": item.itemname,
            "remaining_stock": remaining_stock,
            "threshold": threshold
        })
    

    return render_template('stock_alerts.html', stock_data=stock_data, t=translations)


import csv
from io import StringIO
from flask import Response, jsonify

@bp.route('/export_stock_alerts_csv')
@login_required
def export_stock_alerts_csv():
    lang = get_locale()
    translations = get_translation_dict(lang)
    from sqlalchemy import func
    from flask_login import current_user

    user_id = current_user.id

    # Get purchase and sale totals
    purchases = (
        db.session.query(ItemMovement.item_id, func.sum(ItemMovement.quantity).label('total_purchased'))
        .filter(ItemMovement.movement_type == "Purchase", ItemMovement.user_id == user_id)
        .group_by(ItemMovement.item_id)
        .all()
    )
    sales = (db.session.query(ItemMovement.item_id, func.sum(ItemMovement.quantity).label('total_sold'))
        .filter(ItemMovement.movement_type.in_(["Sale", "sale", "SOLD", "Out"]), ItemMovement.user_id == user_id)
        .group_by(ItemMovement.item_id)
        .all()
        )

    purchase_dict = {item_id: total_purchased for item_id, total_purchased in purchases}
    sale_dict = {item_id: total_sold for item_id, total_sold in sales}

    stock_data = []

    # Loop through ALL items, not just purchased ones
    all_items = Item.query.filter_by(user_id=user_id).all()

    for item in all_items:
        item_id = item.id
        total_purchased = purchase_dict.get(item_id, 0)
        total_sold = sale_dict.get(item_id, 0)
        remaining_stock = total_purchased + total_sold

        # Get threshold from StockNotification if available
        stock_notification = StockNotification.query.filter_by(item_id=item_id, user_id=user_id).first()
        threshold = stock_notification.threshold if stock_notification else None

        stock_data.append({
            "item_name": item.itemname,
            "remaining_stock": remaining_stock,
            "threshold": threshold
        })

    # Generate the CSV file in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write the header
    writer.writerow(['Item Name', 'Remaining Stock', 'Threshold'])
    
    # Write data rows
    for data in stock_data:
        writer.writerow([data["item_name"], data["remaining_stock"], data["threshold"]])

    # Set the response to return the CSV as an attachment
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=stock_alerts.csv"})



@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print(f"User {current_user.username} is already logged in")
        return redirect(url_for('main.select_mode'))  # Redirect to mode selector if already logged in

    form = LoginForm()

    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('main.login'))

        # 🔒 Blocked user check
        if hasattr(user, 'is_active') and not user.is_active:
            flash('Your account has been blocked. Please contact support.', 'danger')
            return redirect(url_for('main.login'))

        login_user(user, remember=form.remember_me.data)

        # 🛑 Ensure session gets saved
        session['_user_id'] = str(user.id)
        session.modified = True
        print(f"Logged in user ID: {session.get('_user_id')}")

        # 🔁 Redirect to mode selection page
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('main.select_mode')

        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)




@bp.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Missing JSON data'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = db.session.scalar(sa.select(User).where(User.username == username))

    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    login_user(user)  # If you need session login; or skip if just token-based
    session['_user_id'] = str(user.id)
    session.modified = True

    return jsonify({
        'message': 'Login successful',
        'user_id': user.id,
        'username': user.username
    }), 200



@bp.route('/user/<username>')
@login_required
def user(username):
	user = db.first_or_404(sa.select(User).where(User.username == username))
	return render_template('user.html', user=user)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(original_username=current_user.username, obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.aboute_me = form.aboute_me.data
        current_user.mobile = form.mobile.data
        current_user.address = form.address.data
        current_user.gst = form.gst.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.index', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.aboute_me.data = current_user.aboute_me
        form.mobile.data = current_user.mobile
        form.address.data = current_user.address
        form.gst.data = current_user.gst
    return render_template('edit_profile.html', user=current_user, title='Edit Profile', form=form)


@bp.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('main.login'))



from flask_login import login_user

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()

    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            mobile=form.mobile.data,
            address=form.address.data
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.flush()

        trial_sub = Subscription(
            user_id=new_user.id,
            plan_type='trial',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),
            is_active=True,
            max_entries=1000
        )
        db.session.add(trial_sub)

        db.session.commit()

        login_user(new_user)
        flash("🎉 Registration successful! Let's get started.", "success")
        return redirect(url_for('main.onboarding'))

    return render_template('register.html', form=form)


from app.presets import BUSINESS_PRESETS

@bp.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding():
    if request.method == 'POST':
        selected_type = request.form.get('business_type')

        if not selected_type:
            flash("Please select your business type", "warning")
            return redirect(url_for('main.onboarding'))

        current_user.business_type = selected_type
        db.session.add(current_user)
        db.session.flush()

        try:
            current_user.setup_default_items()
            db.session.commit()
            flash("✅ Default items added for your business.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Error adding items: {e}", "danger")

        return redirect(url_for('main.index'))

    return render_template("onboarding.html", business_presets=BUSINESS_PRESETS)




@bp.route('/api/register', methods=['POST'])
def api_register():
    if current_user.is_authenticated:
        return jsonify({"message": "User already logged in"}), 200

    data = request.get_json()

    # Validate the incoming request data
    if not data:
        return jsonify({"error": "No data provided"}), 400

    username = data.get('username')
    mobile = data.get('mobile')
    email = data.get('email')
    gst = data.get('gst')
    pas = data.get('pas')
    address = data.get('address')
    password = data.get('password')

    if not username or not mobile or not email or not gst or not pas or not address or not password:
        return jsonify({"error": "All fields are required"}), 400

    # Check if the username or email already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already taken"}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "Email already registered"}), 400

    # Create the new user
    user = User(
        username=username,
        mobile=mobile,
        email=email,
        gst=gst,
        pas=pas,
        address=address
    )
    user.set_password(password)

    # Add user to the database
    db.session.add(user)
    db.session.commit()

    # Respond with success message
    return jsonify({"message": "Registration successful! Please log in."}), 201



@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	form = ResetPasswordRequestForm()
	if form.validate_on_submit():
		user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
		if user:
			send_password_reset_email(user)
		flash('Check your email for the instructions to reset your password')
		return redirect(url_for('main.login'))
	return render_template('reset_password_request.html', title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))
	user = User.verify_reset_password_token(token)
	if not user:
		return redirect(url_for('main.index'))
	form = ResetPasswordForm()
	if form.validate_on_submit():
		user.set_password(form.password.data)
		db.session.commit()
		flash('Your password has been reset.')
		return redirect(url_for('main.login'))
	return render_template('reset_password.html', form=form)

@bp.route('/category', methods=['GET', 'POST'])
@login_required
def category():
    lang = get_locale()
    translations = get_translation_dict(lang)
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    view_category = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('viewcategory.html', title='Category', view_category=view_category, t=translations)

@bp.route('/viewexpcategory', methods=['GET', 'POST'])
@login_required
def viewexpcategory():
    lang = get_locale()
    translations = get_translation_dict(lang)
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    view_expcategory = ExpenseCategory.query.filter_by(user_id=current_user.id).all()
    return render_template('viewexpcategory.html', title='Exp Catgory', view_expcategory=view_expcategory, t=translations)


@bp.route('/viewcustomer', methods=['GET', 'POST'])
@login_required
def viewcustomer():
    lang = get_locale()
    translations = get_translation_dict(lang)
    
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    view_customer = Customer.query.filter_by(user_id=current_user.id).all()
    return render_template('viewcustomer.html', title='Customer', view_customer=view_customer, t=translations)

@bp.route('/export_customers_csv')
@login_required
def export_customers_csv():
    customers = Customer.query.filter_by(user_id=current_user.id).all()

    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Mobile', 'Email', 'Address', 'GST Number', 'PAN Number'])

    for c in customers:
        writer.writerow([
            c.name or '',
            c.mobile or '',
            c.email or '',
            c.address or '',
            c.gst or '',
            c.pan or ''
        ])

    # Create a response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=customers.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@bp.route('/viewvendor', methods=['GET', 'POST'])
@login_required
def viewvendor():
    lang = get_locale()
    translations = get_translation_dict(lang)
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    view_vendor = Vendor.query.filter_by(user_id=current_user.id).all()
    return render_template('viewvendor.html', title='Vendor', view_vendor=view_vendor, t=translations)


@bp.route('/export_vendors_csv')
@login_required
def export_vendors_csv():
    vendors = Vendor.query.filter_by(user_id=current_user.id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow(['Name', 'Mobile', 'Email', 'Address', 'GST Number', 'PAN Number'])

    # Data rows
    for v in vendors:
        writer.writerow([
            v.name or '',
            v.mobile or '',
            v.email or '',
            v.address or '',
            v.gstin or '',
            v.pan or ''
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=vendors.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


@bp.route('/viewitems', methods=['GET', 'POST'])
@login_required
def viewitems():
    lang = get_locale()
    translations = get_translation_dict(lang)
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    view_items = Item.query.filter_by(user_id=current_user.id).all()
    return render_template('viewitems.html', title='Items', view_items=view_items, t=translations)

from flask import Response
import csv
from io import StringIO
from flask_login import login_required, current_user

@bp.route('/export_csv_items')
@login_required
def export_csv_items():
    # Fetch only items for the logged-in user
    items = Item.query.filter_by(user_id=current_user.id).all()

    # Use StringIO to build CSV in memory
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Item Name", "Item ID", "Category"])

    for item in items:
        writer.writerow([item.itemname, item.id, item.category])

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=items.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )



@bp.route('/viewsale', methods=['GET', 'POST'])
@login_required
def viewsale():
    lang = get_locale()
    translations = get_translation_dict(lang)
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    amount_status =  AmountReceive.query.filter_by(user_id=current_user.id).all()
    view_sale = Sale.query.filter_by(user_id=current_user.id).all()
    
    return render_template('viewsale.html', title='Sale', view_sale = view_sale, amount_status=amount_status, t=translations)



from io import StringIO
import csv
from flask import make_response
from app.models import Sale, AmountReceive

@bp.route('/export_csv_sales', methods=['GET'])
@login_required
def export_csv_sales():
    # Get sales data for the current user
    sales_data = Sale.query.filter_by(user_id=current_user.id).all()
    amount_status = AmountReceive.query.filter_by(user_id=current_user.id).all()

    # Create CSV in-memory file
    si = StringIO()
    writer = csv.writer(si)
    
    # Write headers for the CSV file
    writer.writerow(['Customer', 'Invoice #', 'Invoice Date', 'Items', 'Total Amount', 'Received Amount', 'Payment Date', 'Payment Mode', 'Due Balance'])

    for sale in sales_data:
        # Get the customer name
        customer_name = sale.customer.name if sale.customer else 'N/A'

        # Get the items
        items = ", ".join([item.item.itemname for item in sale.items])

        # Get the received amount, payment date, and payment mode (if any)
        received_amount = 0
        payment_date = ""
        payment_mode = ""
        for as_payment in amount_status:
            if as_payment.sale_id == sale.id:
                received_amount += as_payment.amount
                payment_date = as_payment.payment_date
                payment_mode = as_payment.payment_mode

        # Write the data for this sale
        writer.writerow([
            customer_name,
            sale.id,
            sale.invoice_date.strftime('%Y-%m-%d %H:%M:%S'),
            items,
            sale.total_amount,
            received_amount,
            payment_date.strftime('%Y-%m-%d %H:%M:%S') if payment_date else '',
            payment_mode,
            sale.balance_due
        ])

    # Generate response to download the CSV file
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=sales_report.csv"
    output.headers["Content-type"] = "text/csv"
    
    return output


from sqlalchemy.orm import joinedload

@bp.route('/viewpurchase', methods=['GET', 'POST'])
@login_required
def viewpurchase():
    lang = get_locale()
    translations = get_translation_dict(lang)

    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))

    purchase_amount_status = PurchaseAmountReceive.query.filter_by(user_id=current_user.id).all()

    view_purchase = Purchase.query.options(
        joinedload(Purchase.purchase_items).joinedload(PurchaseItem.item)
    ).filter_by(user_id=current_user.id).all()

    return render_template('viewpurchase.html', title='Purchase', view_purchase=view_purchase, purchase_amount_status=purchase_amount_status, t=translations)


import csv
from flask import Response
from io import StringIO

@bp.route('/export_purchases_csv')
def export_purchases_csv():
    # Fetch purchases data from your database
    view_purchase = Purchase.query.all()  # Adjust this query based on your actual data
    purchase_amount_status = PurchaseAmountReceive.query.all()  # Adjust accordingly
    
    # Create a StringIO stream to write CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers for the CSV file
    writer.writerow(['Vendor', 'Purchase ID', 'Purchase Date', 'Total Amount', 'Items', 'Paid Amount', 'Payment Date', 'Payment Mode', 'Due Balance'])
    
    # Iterate through each purchase and write data
    for purchase in view_purchase:
        items = ', '.join([item.item.itemname for item in purchase.purchase_items])
        
        # Find matching payment data
        paid_amount = 0
        payment_date = ''
        payment_mode = ''
        for ps in purchase_amount_status:
            if ps.purchase_id == purchase.id:
                paid_amount = ps.amount
                payment_date = ps.payment_date
                payment_mode = ps.payment_mode
                break
        
        # Calculate the due balance
        due_balance = purchase.balance_due
        
        # Write purchase data to CSV
        writer.writerow([
            purchase.Vendor,
            purchase.id,
            purchase.purchase_date.strftime('%Y-%m-%d'),  # Adjust format as needed
            purchase.total_amount,
            items,
            paid_amount,
            payment_date.strftime('%Y-%m-%d') if payment_date else '',
            payment_mode,
            due_balance
        ])
    
    # Set the response headers to indicate it's a CSV file
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=purchases.csv"})



@bp.route('/viewexpense', methods=['GET', 'POST'])
@login_required
def viewexpense():
    lang = get_locale()
    translations = get_translation_dict(lang)
    # Get user ID
    user_id = current_user.id

    # Get all expenses for the current user
    expense = ExpenseItem.query.filter_by(user_id=user_id).all()

    # Calculate total expense for this user
    total_expense = (
        db.session.query(func.sum(ExpenseItem.total_amount))
        .filter_by(user_id=user_id)
        .scalar()
    ) or 0.0  # Avoid None

    return render_template(
        'viewexpense.html',
        expense=expense,
        total_expense=total_expense, t=translations,
        user=current_user  # Optional, for using in template
    )


from io import StringIO
import csv
from flask import Response
from flask_login import current_user

@bp.route('/export_expenses_csv')
@login_required
def export_expenses_csv():
    # Fetch expense data for the logged-in user
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    # Prepare the CSV data
    output = StringIO()
    writer = csv.writer(output)

    # Write the header row with plain English
    writer.writerow(['Name', 'Quantity', 'Rate', 'Total', 'Expense Level'])

    # Write the expense data
    for expense in expenses:
        # Loop through each related ExpenseItem (expense_items)
        for expense_item in expense.expense_items:
            # Get the amount for this expense item
            expense_amount_value = expense_item.amount

            # Determine the expense level
            expense_level = ''
            if expense_amount_value > 1000:
                expense_level = 'High Expense'
            elif expense_amount_value > 500:
                expense_level = 'Medium Expense'
            else:
                expense_level = 'Low Expense'

            # Write the item data to the CSV
            writer.writerow([expense_item.itemname, expense_item.quantity, expense_item.rate, expense_item.total_amount, expense_level])

    # Set the response to return the CSV as an attachment
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=expenses.csv"})

@bp.route('/viewlocation', methods=['GET', 'POST'])
@login_required
def viewlocation():
    lang = get_locale()
    translations = get_translation_dict(lang)
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))

    view_location = Godown.query.filter_by(user_id=current_user.id).all()
    return render_template('viewlocation.html', title='Godown', view_location=view_location, t=translations)

@bp.route('/viewitemmovement', methods = ['GET', 'POST'])
@login_required
def viewitemmovement():
    lang = get_locale()
    translations = get_translation_dict(lang)
    if not current_user.is_authenticated:
        return redirect(url_for('main.login'))
    view_itemmovements = ItemMovement.query.filter_by(user_id=current_user.id).all()
    return render_template('viewitemmovement.html', title='Item Movement', view_itemmovements = view_itemmovements, t=translations)


@bp.route('/addcategory', methods=['GET', 'POST'])
@login_required
def addcategory():
    lang = get_locale()
    translations = get_translation_dict(lang)
    form = CategoryForm(request.form)
    if request.method == 'POST' and form.validate():
        catname = request.form.getlist('catname')
        description = request.form.getlist('description')
        for catname, description in zip(catname, description):
            print(catname, description)
            categories = Category(catname=catname, description=description, user_id=current_user.id)
            db.session.add(categories)
        db.session.commit()
        flash('You have successfully added a new category')
        return redirect(url_for('main.category'))
    return render_template('addcategory.html', title='Category', form=form, t=translations)

@bp.route('/addexpcategory', methods=['GET', 'POST'])
@login_required
def addexpcategory():
    lang = get_locale()
    translations = get_translation_dict(lang)
    form = ExpenseCategoryForm(request.form)
    if request.method == 'POST' and form.validate():
        name = request.form.get('name')
        description = request.form.get('description')
        user_id = current_user.id

        expcats = ExpenseCategory(name=name, description=description, user_id=current_user.id)
        db.session.add(expcats)
        db.session.commit()
        return redirect(url_for('main.viewexpcategory'))
    return render_template('addexpcategory.html', title='Expense Category', form=form, t=translations)

@bp.route('/addlocationajax', methods=['POST'])
@login_required
def add_location_ajax():
    locname = request.form.get('location_name')
    if not locname:
        return jsonify(success=False, message="Location name is required.")

    # Check for existing location
    existing = Godown.query.filter_by(locname=locname, user_id=current_user.id).first()
    if existing:
        return jsonify(success=False, message="Location already exists.")

    new_loc = Godown(locname=locname, user_id=current_user.id)
    db.session.add(new_loc)
    db.session.commit()

    return jsonify(success=True, id=new_loc.id, name=new_loc.locname)

@bp.route('/addcategoryajax', methods=['POST'])
@login_required  # ✅ Ensure user is logged in
def add_category_ajax():
    category_name = request.form.get('category_name')

    if category_name:
        # ✅ Save category with user_id
        new_category = Category(catname=category_name, user_id=current_user.id)
        db.session.add(new_category)
        db.session.commit()

        return jsonify({
            'success': True,
            'category_name': new_category.catname,
            'category_id': new_category.id,
            'user_id': new_category.user_id  # ✅ Return user ID in response
        })

    return jsonify({'success': False})


@bp.route('/additems', methods=['GET', 'POST'])
@login_required
def additems():
    form = ItemsForm(request.form)
    if request.method=='POST' and form.validate():
        itemname = request.form.get('itemname')
        hsn_code = request.form.get('hsn_code')
        item_code = request.form.get('item_code')
        description = request.form.get('description')
        selling_price = request.form.get('selling_price')
        purchase_price = request.form.get('purchase_price')
        
        items = Item(category=form.category.data, itemname=itemname, hsn_code=hsn_code, item_code=item_code, selling_price=selling_price, purchase_price=purchase_price, description=description, user_id=current_user.id)
        db.session.add(items)
        db.session.commit()
        flash('You have successfully added a new item.')
        return redirect(url_for('main.viewitems'))
    return render_template('additems.html', title='Add Items', form=form)

@bp.route('/additemmovement', methods=['GET', 'POST'])
@login_required
def additemmovement():
    form = ItemMovementForm()

    locations = Godown.query.filter_by(user_id=current_user.id).all()
    location_choices = [(str(loc.id), loc.locname) for loc in locations]
    form.from_location.choices = location_choices
    form.to_location.choices = location_choices

    if request.method == 'POST':
        from_location_id = request.form.get('from_location')
        to_location_id = request.form.get('to_location')

        imove = ItemMovement(
            item_id=form.item.data.id if hasattr(form.item.data, 'id') else form.item.data,
            quantity=form.quantity.data,
            movement_type=form.movement_type.data,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            movement_date=datetime.utcnow(),
            user_id=current_user.id
        )
        db.session.add(imove)
        db.session.commit()
        flash('✅ Item movement recorded successfully.')
        return redirect(url_for('main.viewitemmovement'))

    return render_template('additemmovement.html', form=form)




@bp.route('/addexpense', methods=['GET', 'POST'])
@login_required
def addexpense():
    if not check_active_subscription():
        return redirect(url_for('main.subscription'))
    form = ExpenseForm()

    if request.method == 'POST':
        print("📩 Received Form Data:", request.form)

        if form.validate_on_submit():
            selected_category = form.expence_category.data

            if not selected_category:
                flash("❌ Error: No valid expense category selected!", "danger")
                return render_template('addexpense.html', form=form)

            # ✅ Create and save Expense record
            expense = Expense(
                user_id=current_user.id,
                expcat_id=selected_category.id,
                payment_type=form.payment_type.data,
                total_amount=0.0  # Temporary, will update after calculating
            )
            db.session.add(expense)
            db.session.flush()  # Make sure expense.id is available

            total_expense_amount = 0.0

            for item_form in form.expense_items:
                itemname = item_form.itemname.data
                quantity = item_form.quantity.data or 0
                rate = item_form.rate.data or 0

                if not itemname:
                    print("⚠️ Skipping empty item")
                    continue

                amount = quantity * rate

                expense_item = ExpenseItem(
                    expense_id=expense.id,
                    user_id=current_user.id,  # ✅ Associate item with user
                    itemname=itemname,
                    quantity=quantity,
                    rate=rate,
                    amount=amount,
                    total_amount=amount,
                    expense_date=datetime.utcnow()  # ✅ Optional: You can use form field too
                )

                total_expense_amount += amount
                db.session.add(expense_item)

            expense.total_amount = total_expense_amount  # ✅ Update total
            db.session.commit()

            flash("✅ Expense added successfully!", "success")
            return redirect(url_for('main.viewexpense'))

        else:
            flash(f"❌ Form Validation Failed! {form.errors}", "danger")

    return render_template('addexpense.html', form=form)

import time

LOW_STOCK_THRESHOLD = 10  # Customize as needed




def model_to_dict(obj, exclude_fields=None):
    """Convert SQLAlchemy model to a dict for JSON serialization"""
    if exclude_fields is None:
        exclude_fields = []
    return {
        column.name: getattr(obj, column.name)
        for column in obj.__table__.columns
        if column.name not in exclude_fields
    }



@bp.route('/get_item_price/<int:item_id>')
@login_required
def get_item_price(item_id):
    item = Item.query.filter_by(id=item_id, user_id=current_user.id).first()
    if item:
        return jsonify(price=item.selling_price or 0.0)
    return jsonify(price=0.0)


@bp.route('/addsale', methods=['GET', 'POST'])
@login_required
def addsale():
    if not check_active_subscription():
        flash("You need an active subscription to add sales.", "warning")
        return redirect(url_for('main.subscription'))

    user_id = current_user.id
    form = SaleForm()
    form.customername.query_factory = lambda: Customer.query.filter_by(user_id=user_id).all()

    # Get item list for JS or prefill
    item_objs = Item.query.filter_by(user_id=user_id).all()
    item_list = [model_to_dict(i, exclude_fields=["user_id"]) for i in item_objs]

    # Optional: Handle prefill from converted invoice
    invoice_id = request.args.get('invoice_id', type=int)
    if invoice_id and request.method == 'GET':
        invoice = Estimate.query.filter_by(id=invoice_id, user_id=user_id, status='Invoice').first()
        if invoice:
            form.customername.data = invoice.customer
            form.items.entries = []  # Clear default
            for est_item in invoice.items:
                item_form = SaleItemForm()
                item_form.itemname.data = est_item.item
                item_form.quantity.data = est_item.quantity
                item_form.rate.data = est_item.price
                item_form.tax.data = est_item.item.tax_percent if est_item.item else 0
                form.items.append_entry(item_form)

    if request.method == 'POST':
        customer_id = request.form.get('customername')
        customer_name = customer_id

        # Get or create customer
        customer = None
        if customer_id and customer_id.isdigit():
            customer = Customer.query.filter_by(id=int(customer_id), user_id=user_id).first()
        elif customer_name:
            customer = Customer.query.filter_by(name=customer_name.strip(), user_id=user_id).first()
        if not customer:
            customer = Customer(name=customer_name.strip(), user_id=user_id, mobile='NA')
            db.session.add(customer)
            db.session.commit()

        if form.validate():
            total_sale_amount = 0.0
            sale = Sale(
                customer_id=customer.id,
                payment_terms=form.payment_terms.data,
                total_amount=0.0,
                balance_due=0.0,
                invoice_date=datetime.utcnow(),
                user_id=user_id
            )
            db.session.add(sale)
            db.session.flush()

            sale_items = []

            for i, item_form in enumerate(form.items.entries):
                item_id_raw = request.form.get(f'items-{i}-itemname', '').strip()
                quantity = item_form.quantity.data or 0
                rate = item_form.rate.data or 0

                item = None
                if item_id_raw.isdigit():
                    item = Item.query.filter_by(id=int(item_id_raw), user_id=user_id).first()
                else:
                    item = Item.query.filter_by(itemname=item_id_raw, user_id=user_id).first()

                if not item:
                    item = Item(
                        itemname=item_id_raw,
                        unit_price=rate,
                        stock_quantity=0,
                        user_id=user_id,
                        created_date=datetime.utcnow()
                    )
                    db.session.add(item)
                    db.session.flush()

                tax = item_form.tax.data or item.tax_percent or 0
                subtotal = quantity * rate
                tax_amount = subtotal * (tax / 100)
                item_total = subtotal + tax_amount
                total_sale_amount += item_total

                item.stock_quantity -= quantity
                db.session.add(item)

                db.session.add(ItemMovement(
                    item_id=item.id,
                    movement_type="Sale",
                    quantity=-quantity,
                    movement_date=datetime.utcnow(),
                    user_id=user_id
                ))

                if item.stock_quantity < item.low_stock_threshold:
                    db.session.add(StockNotification(
                        item_id=item.id,
                        message=f"Only {item.stock_quantity} left.",
                        created_at=datetime.utcnow(),
                        user_id=user_id
                    ))
                    flash(f"⚠️ {item.itemname} stock is low: {item.stock_quantity}", "warning")

                sale_items.append(SaleItem(
                    sale_id=sale.id,
                    item_id=item.id,
                    quantity=quantity,
                    rate=rate,
                    subtotal=subtotal,
                    tax_percent=tax,
                    tax_value=tax_amount,
                    total_amount=item_total,
                    user_id=user_id
                ))

            sale.total_amount = round(total_sale_amount, 2)
            sale.balance_due = round(total_sale_amount, 2)
            db.session.add_all(sale_items)
            db.session.commit()

            flash("Sale added successfully!", "success")
            return redirect(url_for('main.viewsale'))
        else:
            flash("Form validation failed", "danger")
            print("Form errors:", form.errors)

    # Show form (GET or failed POST)
    customer_objs = Customer.query.filter_by(user_id=user_id).all()
    customer_list = [model_to_dict(c, exclude_fields=["user_id"]) for c in customer_objs]
    return render_template("addsale.html", form=form, item_list=item_list, customer_list=customer_list)








@bp.route('/api/addsale', methods=['POST'])
@login_required
def api_addsale():
    user_id = current_user.id
    data = request.get_json()  # Get data from the request body (expects JSON)

    if not data:
        return jsonify({"error": "No data provided"}), 400

    customer_name = data.get('customername')
    customer_id = data.get('customer_id')
    items = data.get('items', [])
    payment_terms = data.get('payment_terms')

    # Handle customer logic (either find existing or create new customer)
    customer = None
    if customer_id:
        customer = Customer.query.filter_by(id=customer_id, user_id=user_id).first()

    if not customer and customer_name:
        customer = Customer.query.filter_by(name=customer_name.strip(), user_id=user_id).first()

    if not customer and customer_name:
        customer = Customer(name=customer_name.strip(), user_id=user_id, mobile='NA')
        db.session.add(customer)
        db.session.commit()

    if not customer:
        return jsonify({"error": "Customer not found or created"}), 400

    # Create sale
    total_sale_amount = 0.0
    sale = Sale(
        customer_id=customer.id,
        payment_terms=payment_terms,
        total_amount=0.0,
        balance_due=0.0,
        invoice_date=datetime.utcnow(),
        user_id=user_id
    )
    db.session.add(sale)
    db.session.flush()

    # Process items
    sale_items = []
    for item_data in items:
        item_id = item_data.get('item_id')
        item_name = item_data.get('item_name')
        quantity = item_data.get('quantity', 0)
        rate = item_data.get('rate', 0.0)
        tax = item_data.get('tax', 0.0)

        # Find or create item
        item = None
        if item_id:
            item = Item.query.filter_by(id=item_id, user_id=user_id).first()
        
        if not item and item_name:
            item = Item.query.filter_by(itemname=item_name, user_id=user_id).first()

        if not item:
            item = Item(
                itemname=item_name,
                unit_price=rate,
                stock_quantity=0,
                user_id=user_id,
                created_date=datetime.utcnow()
            )
            db.session.add(item)
            db.session.flush()

        # Calculate totals
        subtotal = rate * quantity
        tax_amount = (tax / 100) * subtotal
        item_total = subtotal + tax_amount
        total_sale_amount += item_total

        # Update stock and record item movement
        item.stock_quantity -= quantity
        db.session.add(item)

        # Add item movement
        db.session.add(ItemMovement(
            item_id=item.id,
            movement_type="Sale",
            quantity=-quantity,
            movement_date=datetime.utcnow(),
            user_id=user_id
        ))

        sale_items.append(SaleItem(
            sale_id=sale.id,
            item_id=item.id,
            quantity=quantity,
            rate=rate,
            subtotal=subtotal,
            tax_percent=tax,
            tax_value=tax_amount,
            total_amount=item_total,
            user_id=user_id
        ))

    sale.total_amount = round(total_sale_amount, 2)
    sale.balance_due = round(total_sale_amount, 2)
    db.session.add_all(sale_items)
    db.session.commit()

    return jsonify({
        "message": "Sale added successfully!",
        "sale_id": sale.id,
        "total_amount": total_sale_amount,
        "items": [model_to_dict(item, exclude_fields=["user_id"]) for item in sale_items]
    }), 201




from flask_login import current_user, login_required

from flask import make_response

@bp.route('/download_invoice/<int:sale_id>')
@login_required
def download_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    customer = Customer.query.get(sale.customer_id)

    if not customer:
        flash(_("Customer not found for this sale."), "error")
        return redirect(url_for('main.viewsale'))

    sale_items = SaleItem.query.options(joinedload(SaleItem.item)).filter_by(sale_id=sale.id).all()

    pdf_response = generate_invoice(sale, customer, sale_items, current_user)

    if pdf_response:
        # Ensure the response is of PDF type
        response = make_response(pdf_response)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=invoice.pdf'
        return response

    flash(_("Invoice could not be generated."), "error")
    return redirect(url_for('main.viewsale'))



from flask import send_file, session, current_app
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import rl_config
from markupsafe import escape
from datetime import datetime
import os

from app.models import User, AmountReceive  # ✅ Ensure these are imported correctly
from flask_babel import _


import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_noto_fonts():
    # 🔁 Absolute path to font folder (DO NOT use relative 'static/fonts')
    font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts'))

    fonts = {
        "NotoSans": "NotoSans-Regular.ttf",
        "NotoSansDevanagari": "NotoSansDevanagari.ttf",
        "NotoSansKannada": "NotoSansKannada.ttf",
        "NotoSansTamil": "NotoSansTamil.ttf",
        "NotoSansTelugu": "NotoSansTelugu.ttf",
        "NotoSansMalayalam": "NotoSansMalayalam.ttf",
        "NotoSansBengali": "NotoSansBengali.ttf"
    }

    for name, filename in fonts.items():
        full_path = os.path.join(font_dir, filename)

        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"❌ Font file missing: {full_path}")

        print(f"✅ Registering {name} from {full_path}")
        pdfmetrics.registerFont(TTFont(name, full_path))


from io import BytesIO
from flask import send_file, session
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from markupsafe import escape
from app.models import User, AmountReceive  # Adjust path as needed
from app.utils.fonts import register_fonts
from flask_babel import _


def generate_invoice(sale, customer, sale_items, current_user):
    try:
        register_fonts()
        user = User.query.get(current_user.id)
        if not user:
            raise ValueError("User not found")

        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer, pagesize=A4, leftMargin=30, rightMargin=30, topMargin=40, bottomMargin=30
        )
        elements = []

        lang = session.get("lang", "en")
        font_name = {
            "hi": "NotoSansDevanagari",
            "kn": "NotoSansKannada",
            "ta": "NotoSansTamil",
            "te": "NotoSansTelugu",
            "ml": "NotoSansMalayalam",
            "bn": "NotoSansBengali"
        }.get(lang, "NotoSans")

        styles = getSampleStyleSheet()
        normal = ParagraphStyle('Normal', fontName=font_name, fontSize=10, leading=13)
        bold = ParagraphStyle('Bold', fontName=font_name, fontSize=12, leading=14, spaceAfter=6)

        # ✅ Header
        header_data = [
            [Paragraph(f"<b>{user.username}</b><br/>{user.email or ''}<br/>{user.mobile or ''}<br/>{user.address or ''}", normal),
             Paragraph(f"<b>{_('Customer:')}</b> {customer.name}<br/>"
                       f"<b>{_('Mobile:')}</b> {customer.mobile}<br/>"
                       f"<b>{_('Invoice#:')}</b> {sale.id}<br/>"
                       f"<b>{_('Date:')}</b> {sale.invoice_date.strftime('%Y-%m-%d')}", normal)]
        ]
        header_table = Table(header_data, colWidths=[270, 270])
        header_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 15))

        # 🛒 Sale Items Table
        item_data = [[
            _('Item Name'), _('Quantity'), _('Rate (Rs)'), _('Subtotal (Rs)'), _('Tax %'), _('Total (Rs)')
        ]]
        grand_total = 0.0
        for item in sale_items:
            total = item.total_amount
            grand_total += total
            item_data.append([
                escape(item.item.itemname),
                str(item.quantity),
                f"Rs {float(item.rate):.2f}",
                f"Rs {float(item.subtotal):.2f}",
                f"{item.tax_percent}%",
                f"Rs {float(total):.2f}"
            ])
        item_data.append(["", "", "", "", _('Grand Total:'), f"Rs {float(grand_total):.2f}"])

        item_table = Table(item_data, colWidths=[150, 50, 70, 80, 50, 90])
        item_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (-2, -1), (-1, -1), colors.HexColor("#F9E79F")),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 15))

        # 💸 Payment Summary
        received_payments = AmountReceive.query.filter_by(sale_id=sale.id).all()
        total_received = sum(p.amount for p in received_payments)
        balance_due = sale.total_amount - total_received

        payment_data = [[_('Received Amount (Rs)'), _('Payment Mode'), _('Payment Date')]]
        for p in received_payments:
            payment_data.append([
                f"Rs {float(p.amount):.2f}",
                escape(p.payment_mode),
                p.payment_date.strftime('%Y-%m-%d')
            ])
        payment_data.append(["", "", ""])
        payment_data.append([_('Total Received:'), f"Rs {float(total_received):.2f}", ""])
        payment_data.append([_('Balance Due:'), f"Rs {float(balance_due):.2f}", ""])

        pay_table = Table(payment_data, colWidths=[150, 150, 150])
        pay_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D6EAF8")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
        ]))
        elements.append(pay_table)
        elements.append(Spacer(1, 12))

        # ✅ Final Status Caption
        if balance_due <= 0:
            elements.append(Paragraph(f'<font color="green"><b>✔️ {_("This invoice is fully paid.")}</b></font>', bold))
        else:
            elements.append(Paragraph(f'<font color="red"><b>❌ {_("Payment Due: Rs ")}{balance_due:.2f}</b></font>', bold))

        pdf.title = f"Invoice_{sale.id}"
        pdf.author = user.username or "Business"
        pdf.build(elements)
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name=f"invoice_{sale.id}.pdf", mimetype="application/pdf")

    except Exception as e:
        print("❌ PDF Generation Error:", str(e))
        return None


@bp.route('/print_invoice/<int:sale_id>')
@login_required
def print_invoice(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    customer = Customer.query.get_or_404(sale.customer_id)
    sale_items = SaleItem.query.options(joinedload(SaleItem.item)).filter_by(sale_id=sale.id).all()
    received_payments = AmountReceive.query.filter_by(sale_id=sale.id).all()

    return render_template(
        "print_invoice.html", user=current_user,
        sale=sale,
        customer=customer,
        sale_items=sale_items,
        received_payments=received_payments,
        t=get_translation_dict(session.get('lang', 'en')),
        lang=session.get('lang', 'en')
    )


import imgkit
from flask import send_file

@bp.route('/invoice_image/<int:sale_id>')
@login_required
def invoice_image(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    customer = Customer.query.get_or_404(sale.customer_id)
    sale_items = SaleItem.query.options(joinedload(SaleItem.item)).filter_by(sale_id=sale.id).all()
    received_payments = AmountReceive.query.filter_by(sale_id=sale.id).all()

    html = render_template(
        "print_invoice.html",  # Make sure it's printable and standalone
        user=current_user,
        sale=sale,
        customer=customer,
        sale_items=sale_items,
        received_payments=received_payments,
        t=get_translation_dict(session.get('lang', 'en')),
        lang=session.get('lang', 'en')
    )

    path_to_wkhtmltoimage = '/usr/bin/wkhtmltoimage'  # adjust if needed
    config = imgkit.config(wkhtmltoimage=path_to_wkhtmltoimage)

    options = {
        'format': 'png',
        'quality': '100',
        'encoding': "UTF-8"
    }

    image_file = f'/tmp/invoice_{sale.id}.png'
    imgkit.from_string(html, image_file, config=config, options=options)

    return send_file(image_file, mimetype='image/png', as_attachment=True, download_name=f'invoice_{sale.id}.png')



@bp.route('/purchase_invoice_image/<int:purchase_id>')
@login_required
def purchase_invoice_image(purchase_id):
    import imgkit
    from datetime import datetime
    from flask import current_app

    # ✅ Load purchase with vendor relationship
    purchase = Purchase.query.get_or_404(purchase_id)
    vendor = purchase.vendor  # ✅ Use model relationship

    # ✅ Load related data
    purchase_items = PurchaseItem.query.options(joinedload(PurchaseItem.item)).filter_by(purchase_id=purchase.id).all()
    received_payments = PurchaseAmountReceive.query.filter_by(purchase_id=purchase.id).all()

    # ✅ Render HTML
    html = render_template(
        "print_purchase.html",
        user=current_user,
        purchase=purchase,
        vendor=vendor,  # ✅ Will work because of correct field `vendor.name`
        purchase_items=purchase_items,
        received_payments=received_payments,
        t=get_translation_dict(session.get('lang', 'en')),
        lang=session.get('lang', 'en'),
        now=datetime.now
    )

    # ✅ Save temp HTML for debugging (optional)
    debug_html_path = f"/tmp/debug_purchase_invoice_{purchase.id}.html"
    with open(debug_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    # ✅ Convert HTML to Image
    config = imgkit.config(wkhtmltoimage="/usr/bin/wkhtmltoimage")  # adjust if needed
    output_path = f"/tmp/purchase_invoice_{purchase.id}.png"

    imgkit.from_string(html, output_path, config=config, options={
        'format': 'png',
        'quality': '100',
        'encoding': "UTF-8"
    })

    return send_file(output_path, mimetype='image/png', as_attachment=True,
                     download_name=f'purchase_invoice_{purchase.id}.png')




@bp.route('/print_purchase/<int:purchase_id>')
@login_required
def print_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    vendor = Vendor.query.get_or_404(purchase.vendor_id)
    purchase_items = PurchaseItem.query.options(joinedload(PurchaseItem.item)).filter_by(purchase_id=purchase.id).all()
    received_payments = PurchaseAmountReceive.query.filter_by(purchase_id=purchase.id).all()

    return render_template(
        "print_purchase.html",
        user=current_user,
        purchase=purchase,
        vendor=vendor,
        purchase_items=purchase_items,
        received_payments=received_payments,
        t=get_translation_dict(session.get('lang', 'en')),
        lang=session.get('lang', 'en')
    )



@bp.route('/addpurchase', methods=['GET', 'POST'])
@login_required
def addpurchase():
    if not check_active_subscription():
        flash("You need an active subscription to add purchases.", "warning")
        return redirect(url_for('main.subscription'))

    user_id = current_user.id
    form = PurchaseForm()
    form.vendorname.query_factory = lambda: Vendor.query.filter_by(user_id=user_id).all()

    item_objs = Item.query.filter_by(user_id=user_id).all()
    item_list = [model_to_dict(i, exclude_fields=["user_id"]) for i in item_objs]

    if request.method == 'POST':
        vendor_id = request.form.get('vendorname')
        vendor_name = request.form.get('vendorname')
        vendor = None

        # Vendor handling
        if vendor_id and vendor_id.isdigit():
            vendor = Vendor.query.filter_by(id=int(vendor_id), user_id=user_id).first()
        if not vendor and vendor_name:
            vendor = Vendor.query.filter_by(name=vendor_name.strip(), user_id=user_id).first()
        if not vendor and vendor_name:
            vendor = Vendor(name=vendor_name.strip(), user_id=user_id, mobile='NA')
            db.session.add(vendor)
            db.session.commit()

        if form.validate():
            total_purchase_amount = 0.0
            purchase = Purchase(
                vendor_id=vendor.id,
                payment_terms=form.payment_terms.data,
                total_amount=0.0,
                balance_due=0.0,
                invoice_date=datetime.utcnow(),
                user_id=user_id
            )
            db.session.add(purchase)
            db.session.flush()

            purchase_items = []

            for i, item_form in enumerate(form.items.entries):
                item_id_raw = request.form.get(f'items-{i}-itemname', '').strip()
                rate = item_form.rate.data or 0.0
                quantity = item_form.quantity.data or 0

                # Get existing item if exists
                if item_id_raw.isdigit():
                    item = Item.query.filter_by(id=int(item_id_raw), user_id=user_id).first()
                else:
                    item = Item.query.filter_by(itemname=item_id_raw, user_id=user_id).first()

                # Tax: pull from form, else from existing item
                tax = item_form.tax.data or (item.tax_percent if item and item.tax_percent else 0)

                # Markup from input field
                markup_raw = request.form.get(f'items-{i}-markup', '').strip()
                if markup_raw.replace('.', '', 1).isdigit():
                    markup = float(markup_raw)
                elif item and item.markup_percent is not None:
                    markup = item.markup_percent
                elif current_user.default_markup_percent is not None:
                    markup = current_user.default_markup_percent
                else:
                    markup = 10.0  # default fallback

                subtotal = quantity * rate
                tax_amount = subtotal * (tax / 100)
                item_total = subtotal + tax_amount
                total_purchase_amount += item_total

                # Create or update item
                if not item:
                    item = Item(
                        itemname=item_id_raw,
                        purchase_price=rate,
                        selling_price=round(rate * (1 + markup / 100), 2),
                        stock_quantity=quantity,
                        user_id=user_id,
                        created_date=datetime.utcnow(),
                        markup_percent=markup,
                        tax_percent=tax
                    )
                    db.session.add(item)
                    db.session.flush()
                else:
                    item.purchase_price = rate
                    item.selling_price = round(rate * (1 + markup / 100), 2)
                    item.markup_percent = markup
                    item.tax_percent = tax
                    item.stock_quantity += quantity
                    db.session.add(item)

                # Log item movement
                db.session.add(ItemMovement(
                    item_id=item.id,
                    movement_type="Purchase",
                    quantity=quantity,
                    movement_date=datetime.utcnow(),
                    user_id=user_id
                ))

                if item.stock_quantity < LOW_STOCK_THRESHOLD:
                    db.session.add(StockNotification(
                        item_id=item.id,
                        message=f"Only {item.stock_quantity} left.",
                        created_at=datetime.utcnow(),
                        user_id=user_id
                    ))
                    flash(f"⚠️ {item.itemname} stock is low: {item.stock_quantity}", "warning")

                # Add purchase item
                purchase_items.append(PurchaseItem(
                    purchase_id=purchase.id,
                    item_id=item.id,
                    quantity=quantity,
                    rate=rate,
                    subtotal=subtotal,
                    tax_percent=tax,
                    tax_value=tax_amount,
                    total_amount=item_total,
                    user_id=user_id
                ))

            purchase.total_amount = round(total_purchase_amount, 2)
            purchase.balance_due = round(total_purchase_amount, 2)
            db.session.add_all(purchase_items)
            db.session.commit()

            flash("Purchase added successfully!", "success")
            return redirect(url_for('main.viewpurchase'))
        else:
            flash("Form validation failed", "danger")
            print("Form errors:", form.errors)

    vendor_objs = Vendor.query.filter_by(user_id=user_id).all()
    vendor_list = [model_to_dict(v, exclude_fields=["user_id"]) for v in vendor_objs]
    return render_template("addpurchase.html", form=form, item_list=item_list, vendor_list=vendor_list)




from reportlab.lib.styles import ParagraphStyle


@bp.route('/download_purchase_invoice/<int:purchase_id>')
@login_required
def download_purchase_invoice(purchase_id):
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from app.utils.fonts import register_fonts
    from app.models import Purchase, PurchaseItem, PurchaseAmountReceive, Vendor
    from sqlalchemy.orm import joinedload

    # ✅ Register multilingual fonts
    register_fonts()

    # ✅ Get purchase data
    purchase = Purchase.query.get_or_404(purchase_id)
    vendor = Vendor.query.get_or_404(purchase.vendor_id)
    items = PurchaseItem.query.options(joinedload(PurchaseItem.item)).filter_by(purchase_id=purchase.id).all()
    payments = PurchaseAmountReceive.query.filter_by(purchase_id=purchase_id).all()

    lang = session.get('lang', 'en')
    font_name = {
        'hi': 'NotoSansDevanagari',
        'kn': 'NotoSansKannada',
        'ta': 'NotoSansTamil',
        'te': 'NotoSansTelugu',
        'ml': 'NotoSansMalayalam',
        'bn': 'NotoSansBengali'
    }.get(lang, 'NotoSans')

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # ✅ Styles
    style_normal = ParagraphStyle(name='Normal', fontName=font_name, fontSize=10, leading=13)
    style_title = ParagraphStyle(name='Title', fontName=font_name, fontSize=14, leading=18)

    # ✅ Header Table
    header_data = [
        [
            Paragraph(f"<b>Generated By:</b><br/>{current_user.username}", style_normal),
            Paragraph(f"<b>Vendor:</b><br/>{vendor.name}", style_normal)
        ],
        [
            Paragraph(f"<b>Mobile:</b><br/>{current_user.mobile or '-'}", style_normal),
            Paragraph(f"<b>Mobile:</b><br/>{vendor.mobile or '-'}", style_normal)
        ],
        [
            Paragraph(f"<b>Address:</b><br/>{current_user.address or '-'}", style_normal),
            Paragraph(
                f"<b>Invoice #:</b><br/>{purchase.id}<br/><b>Date:</b><br/>{purchase.purchase_date.strftime('%Y-%m-%d')}",
                style_normal
            )
        ]
    ]

    header_table = Table(header_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # ✅ Items Table
    table_data = [[
        Paragraph("<b>Item</b>", style_normal),
        Paragraph("<b>Qty</b>", style_normal),
        Paragraph("<b>Rate</b>", style_normal),
        Paragraph("<b>Subtotal</b>", style_normal),
        Paragraph("<b>Tax%</b>", style_normal),
        Paragraph("<b>Total</b>", style_normal)
    ]]

    grand_total = 0
    for item in items:
        total = item.total_amount
        grand_total += total
        table_data.append([
            Paragraph(item.item.itemname, style_normal),
            str(item.quantity),
            f"₹{item.rate}",
            f"₹{item.subtotal}",
            f"{item.tax_percent}%",
            f"₹{total:.2f}"
        ])

    table_data.append([
        "", "", "", "", Paragraph("<b>Grand Total</b>", style_normal),
        Paragraph(f"₹{grand_total:.2f}", style_normal)
    ])

    item_table = Table(table_data, colWidths=[150, 50, 60, 70, 50, 90])
    item_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d3d3d3')),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('BACKGROUND', (-2, -1), (-1, -1), colors.lightyellow)
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 15))

    # ✅ Payments Table
    total_received = sum(p.amount for p in payments)
    balance_due = purchase.total_amount - total_received

    pay_data = [[
        Paragraph("<b>Received</b>", style_normal),
        Paragraph("<b>Mode</b>", style_normal),
        Paragraph("<b>Date</b>", style_normal)
    ]]
    for p in payments:
        pay_data.append([
            f"₹{p.amount}",
            p.payment_mode,
            p.payment_date.strftime('%Y-%m-%d')
        ])
    pay_data.append(["", "", ""])
    pay_data.append([
        Paragraph("<b>Total Received:</b>", style_normal),
        Paragraph(f"₹{total_received:.2f}", style_normal),
        ""
    ])
    pay_data.append([
        Paragraph("<b>Balance Due:</b>", style_normal),
        Paragraph(f"₹{balance_due:.2f}", style_normal),
        ""
    ])

    pay_table = Table(pay_data, colWidths=[150, 150, 150])
    pay_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c0c0c0')),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(pay_table)
    elements.append(Spacer(1, 12))

    # ✅ Payment Status Caption
    if balance_due <= 0:
        elements.append(Paragraph('<font color="green"><b>✔ Fully Paid</b></font>', style_title))
    else:
        elements.append(Paragraph(f'<font color="red"><b>❌ Balance Due: ₹{balance_due:.2f}</b></font>', style_title))

    # ✅ Generate PDF
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"invoice_{purchase.id}.pdf", mimetype='application/pdf')




from flask import send_file, session, redirect, url_for, flash

@bp.route('/editpurchase/<int:purchase_id>', methods=['GET', 'POST'])
def edit_purchase(purchase_id):
    # Process form and update sale...

    pdf_response = generate_purchase_invoice(purchase, vendor, purchase_items)
    if pdf_response:
        # ✅ Store the download URL in session before redirecting
        session['invoice_download_url'] = url_for('main.download_invoice', purchase_id=purchase.id)
        return redirect(url_for('main.viewpurchase'))

    flash('Failed to generate invoice.', 'error')
    return redirect(url_for('main.viewpurchase'))




def generate_estimate_number():
    from sqlalchemy import func
    today_str = datetime.now().strftime('%Y%m%d')
    prefix = f"EST-{today_str}-"

    latest = (
        db.session.query(Estimate.estimate_number)
        .filter(Estimate.estimate_number.like(f"{prefix}%"))
        .order_by(Estimate.estimate_number.desc())
        .first()
    )

    if latest:
        last_number = int(latest[0].split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{prefix}{next_number:03d}"


def generate_invoice_number():
    from sqlalchemy import func
    today_str = datetime.utcnow().strftime('%Y%m%d')
    prefix = f"INV-{today_str}-"

    latest = (
        db.session.query(Estimate.estimate_number)
        .filter(Estimate.status == 'Invoice')
        .filter(Estimate.estimate_number.like(f"{prefix}%"))
        .order_by(Estimate.estimate_number.desc())
        .first()
    )

    if latest:
        last_number = int(latest[0].split("-")[-1])
        next_number = last_number + 1
    else:
        next_number = 1

    return f"{prefix}{next_number:03d}"



from flask import send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from io import BytesIO
from datetime import datetime
#import weasyprint


from flask import render_template, request, redirect, url_for, flash

@bp.route('/add_estimate', methods=['GET', 'POST'])
@login_required
def add_estimate():
    user_id = current_user.id
    form = EstimateForm()
    form.customer.query_factory = lambda: Customer.query.filter_by(user_id=user_id).all()

    item_objs = Item.query.filter_by(user_id=user_id).all()
    item_list = [model_to_dict(i, exclude_fields=["user_id"]) for i in item_objs]

    if request.method == 'POST':
        customer_id = request.form.get('customer')
        customer_name = customer_id

        # Get or create customer
        customer = None
        if customer_id and customer_id.isdigit():
            customer = Customer.query.filter_by(id=int(customer_id), user_id=user_id).first()
        if not customer and customer_name:
            customer = Customer.query.filter_by(name=customer_name.strip(), user_id=user_id).first()
        if not customer:
            customer = Customer(name=customer_name.strip(), user_id=user_id, mobile='NA')
            db.session.add(customer)
            db.session.commit()

        if form.validate():
            estimate = Estimate(
                estimate_number=generate_estimate_number(),
                customer_id=customer.id,
                date=form.date.data or datetime.utcnow(),
                status='Estimate',
                user_id=user_id
            )
            db.session.add(estimate)
            db.session.flush()

            total = 0.0
            for i, item_form in enumerate(form.items.entries):
                item_id_raw = request.form.get(f'items-{i}-item', '').strip()
                quantity = item_form.quantity.data or 0
                rate = item_form.price.data or 0

                item = None
                if item_id_raw.isdigit():
                    item = Item.query.filter_by(id=int(item_id_raw), user_id=user_id).first()
                else:
                    item = Item.query.filter_by(itemname=item_id_raw, user_id=user_id).first()

                if not item:
                    item = Item(
                        itemname=item_id_raw,
                        unit_price=rate,
                        stock_quantity=0,
                        user_id=user_id,
                        created_date=datetime.utcnow()
                    )
                    db.session.add(item)
                    db.session.flush()

                # Get tax
                tax = item_form.tax.data or item.tax_percent or 0
                subtotal = quantity * rate
                tax_amount = subtotal * (tax / 100)
                total_amount = subtotal + tax_amount
                total += total_amount

                db.session.add(EstimateItem(
                    estimate_id=estimate.id,
                    item_id=item.id,
                    quantity=quantity,
                    price=rate,
                    subtotal=subtotal,
                    tax_percent=tax,
                    tax_value=tax_amount
                ))

            estimate.total_amount = round(total, 2)
            db.session.commit()
            flash("✅ Estimate created successfully!", "success")
            return redirect(url_for('main.estimate_list'))
        else:
            flash("❌ Form validation failed", "danger")
            print("Form errors:", form.errors)

    customer_objs = Customer.query.filter_by(user_id=user_id).all()
    customer_list = [model_to_dict(c, exclude_fields=["user_id"]) for c in customer_objs]

    return render_template(
        "add_estimate.html",
        form=form,
        item_list=item_list,
        customer_list=customer_list
    )


@bp.route('/estimates')
@login_required
def estimate_list():
    estimates = Estimate.query.filter_by(status='Estimate').order_by(Estimate.date.desc()).all()
    return render_template('estimate_list.html', estimates=estimates)


@bp.route('/invoices')
@login_required
def invoice_list():
    invoices = Estimate.query.filter_by(status='Invoice').order_by(Estimate.date.desc()).all()
    return render_template('invoice_list.html', invoices=invoices)


@bp.route('/delete_invoice/<int:estimate_id>', methods=['POST'])
@login_required
def delete_invoice(estimate_id):
    invoice = Estimate.query.filter_by(id=estimate_id, user_id=current_user.id, status='Invoice').first_or_404()
    db.session.delete(invoice)
    db.session.commit()
    flash("🗑️ Invoice deleted successfully!", "success")
    return redirect(url_for('main.invoice_list'))



@bp.route('/estimate/<int:estimate_id>')
@login_required
def estimate_detail(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    return render_template('estimate_detail.html', estimate=estimate)


@bp.route('/download_estimate/<int:estimate_id>')
@login_required
def download_estimate(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)
    html = render_template('estimate_pdf.html', estimate=estimate)
    pdf = weasyprint.HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=estimate_{estimate.id}.pdf'
    return response


@bp.route('/convert_estimate/<int:estimate_id>')
@login_required
def convert_estimate(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)

    if estimate.status == 'Invoice':
        flash('This estimate is already converted to an invoice.', 'info')
        return redirect(url_for('main.invoice_list'))

    # Convert to Invoice
    estimate.status = 'Invoice'
    estimate.estimate_number = generate_invoice_number()
    estimate.date = datetime.utcnow()

    db.session.commit()

    flash('Estimate converted to Invoice successfully!', 'success')
    return redirect(url_for('main.invoice_list'))







@bp.route('/get_customers')
def get_customers():
    customers = Customer.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in customers])


@bp.route("/get_items", methods=["GET"])
def get_items():
    items = Item.query.all()
    item_list = [{"id": item.id, "itemname": item.itemname} for item in items]

    if not item_list:
        return jsonify([])  # ✅ Return empty array instead of `None`

    return jsonify(item_list)  # ✅ Always return valid JSON


@bp.route('/get_categories')
def get_categories():
    categories = ExpenseCategory.query.all()
    cat_list = [{"id": cat.id, "name": cat.name} for cat in categories]
    return jsonify(cat_list)

@bp.route('/get_vendors')
def get_vendors():
    vendors = Vendor.query.all()  # Replace with your actual DB model
    vendor_list = [{"id": v.id, "name": v.name} for v in vendors]  # Ensure correct format
    return jsonify(vendor_list)


@bp.route('/addcustomer', methods=['GET', 'POST'])
@login_required
def addcustomer():
    form = CustomerForm(request.form)
    if request.method == 'POST' and form.validate():
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')
        gst = request.form.get('gst')
        pan = request.form.get('pan')
        address = request.form.get('address', '')
        customers = Customer(name=name, mobile=mobile, email=email, gst=gst, pan=pan, address=address, user_id=current_user.id)
        db.session.add(customers)
        db.session.commit()

    if request.method == 'POST':
        print("Form Data:", request.form)  # Print all submitted form data
        print("Errors:", form.errors)  # Print validation errors

        flash('You have successfully added a new customer.')
        return redirect(url_for('main.viewcustomer'))
    return render_template('addcustomer.html', title='Customer', form=form)



@bp.route('/addcustomerajax', methods=['POST'])
@login_required
def add_customer_ajax():
    name = request.form.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    existing_customer = Customer.query.filter_by(name=name.strip(), user_id=current_user.id).first()
    if existing_customer:
        return jsonify({'id': existing_customer.id, 'name': existing_customer.name})

    new_customer = Customer(name=name.strip(), user_id=current_user.id, mobile='NA')
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({'id': new_customer.id, 'name': new_customer.name})




@bp.route("/additemajax", methods=["POST"])
@login_required
def additemajax():
    user_id = current_user.id
    itemname = request.form.get("itemname", "").strip()

    if not itemname:
        return jsonify({"error": "Item name is required"}), 400

    item = Item.query.filter_by(itemname=itemname, user_id=user_id).first()
    if not item:
        item = Item(
            itemname=itemname,
            user_id=user_id,
            unit_price=0,
            stock_quantity=0,
            created_date=datetime.utcnow()
        )
        db.session.add(item)
        db.session.commit()

    return jsonify({"id": item.id, "itemname": item.itemname})


from flask_login import current_user

@bp.route('/addexpcategoryajax', methods=['POST'])
@login_required
def addexpcategoryajax():
    category_name = request.form.get('category_name')
    
    if category_name:
        existing = ExpenseCategory.query.filter_by(name=category_name, user_id=current_user.id).first()
        if not existing:
            new_cat = ExpenseCategory(name=category_name, user_id=current_user.id)  # ✅ Add user_id here
            db.session.add(new_cat)
            db.session.commit()
            return jsonify({
                'success': True,
                'category_id': new_cat.id,
                'category_name': new_cat.name
            })
        else:
            return jsonify({
                'success': True,
                'category_id': existing.id,
                'category_name': existing.name
            })

    return jsonify({'success': False})


@bp.route("/submit_expense", methods=["POST"])
def submit_expense():
    data = request.get_json()
    category_id = data.get("expence_category")
    category = ExpenseCategory.query.get(id)
    if not category:
        return jsonify({"success": False, "message": "Invalid category selection"}), 400
    new_expense = Expense(category_id=category.id)
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({"success": True, "message": "Expense added!"})

@bp.route('/addvendorajax', methods=['POST'])
def add_vendor_ajax():
    try:
        data = request.json
        vendor_name = data.get("vendorName")
        vendor_mobile = data.get("vendorMobile")

        if not vendor_name:
            return jsonify({"success": False, "message": "Vendor Name is required!"}), 400

        new_vendor = Vendor(name=vendor_name, mobile=vendor_mobile)
        db.session.add(new_vendor)
        db.session.commit()

        return jsonify({
            "success": True,
            "vendorId": new_vendor.id,  # ✅ Ensure ID is returned
            "vendorName": new_vendor.name
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@bp.route('/addvendor', methods=['GET', 'POST'])
@login_required
def addvendor():
	form = VendorForm()
	if form.validate_on_submit():
		vendors = Vendor(name=form.name.data, mobile=form.mobile.data, email=form.email.data, gstin=form.gstin.data, pan=form.pan.data, address=form.address.data, user_id=current_user.id)
		db.session.add(vendors)
		db.session.commit()
		flash('You have successfully added a new vendor.')
		return redirect(url_for('main.viewvendor'))
	return render_template('addvendor.html', title='Vendor', form=form)



@bp.route('/addlocation', methods=['GET', 'POST'])
@login_required
def addlocation():
    form = GodownForm()
    if form.validate_on_submit():
        addlocation = Godown(locname=form.locname.data, user_id=current_user.id)
        db.session.add(addlocation)
        db.session.commit()
        return redirect(url_for('main.viewlocation'))
    return render_template('addlocation.html', title='Add Godown', form=form)


@bp.route('/addsale_from_invoice/<int:estimate_id>', methods=['GET', 'POST'])
@login_required
def addsale_from_invoice(estimate_id):
    estimate = Estimate.query.get_or_404(estimate_id)

    # Create new Sale based on Estimate
    sale = Sale(
        customer_id=estimate.customer_id,
        invoice_number=generate_invoice_number(),  # Optional: if needed
        total_amount=estimate.total_amount,
        balance_due=estimate.total_amount,
        invoice_date=datetime.utcnow(),
        payment_terms=30,  # ✅ Fixed: default value to avoid NULL error
        user_id=current_user.id
    )
    db.session.add(sale)
    db.session.flush()  # Get sale.id

    for est_item in estimate.items:
        # Optional: fetch Item for stock and tax info
        item = Item.query.get(est_item.item_id)
        if item:
            item.stock_quantity -= est_item.quantity
            db.session.add(item)

        db.session.add(SaleItem(
            sale_id=sale.id,
            item_id=est_item.item_id,
            quantity=est_item.quantity,
            rate=est_item.price,
            subtotal=est_item.subtotal,
            tax_percent=0,  # You can auto-fetch from item.tax_percent if needed
            tax_value=0,
            total_amount=est_item.subtotal,
            user_id=current_user.id
        ))

    # Optional: mark estimate as converted
    estimate.status = "Invoice"

    db.session.commit()
    flash("✅ Estimate converted to sale successfully!", "success")
    return redirect(url_for('main.viewsale'))


@bp.route('/editcategory/<int:id>', methods=['GET', 'POST'])
@login_required
def editcategory(id):
    lang = get_locale()
    translations = get_translation_dict(lang)
    view_category = Category.query.filter_by(id=id, user_id=current_user.id).first()
    if not view_category:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.category'))

    form = CategoryForm(obj=view_category)
    if form.validate_on_submit():
        view_category.catname = form.catname.data
        view_category.description = form.description.data
        db.session.commit()
        flash('You have edited the category.')
        return redirect(url_for('main.category'))
    form.catname.data = view_category.catname
    form.description.data = view_category.description
    return render_template('addcategory.html', action="Edit", form=form, view_category=view_category, t=translations)

@bp.route('/editexpcategory/<int:id>', methods=['GET', 'POST'])
@login_required
def editexpcategory(id):
    view_expcategory = ExpenseCategory.query.get_or_404(id)
    form = ExpenseCategoryForm(obj=view_expcategory)
    if form.validate_on_submit():
        view_expcategory.name=form.name.data
        view_expcategory.description=form.description.data
        db.session.commit()
        flash('You have edited the Category.')
        return redirect(url_for('main.viewexpcategory'))
    form.name.data = view_expcategory.name
    form.description.data = view_expcategory.description
    return render_template('addexpcategory.html', form=form, action='Edit', view_expcategory=view_expcategory)


@bp.route('/editlocation/<int:id>', methods=['GET', 'POST'])
@login_required
def editlocation(id):
    view_location = Godown.query.filter_by(id=id, user_id=current_user.id).first()
    if not view_location:
        flash("Unauthorized access", "danger")
        return redirect(url_for('main.viewlocation'))

    form = GodownForm(obj=view_location)
    if form.validate_on_submit():
        view_location.locname = form.locname.data
        db.session.commit()
        flash('You have edited the location.')
        return redirect(url_for('main.viewlocation'))
    form.locname.data = view_location.locname
    return render_template('addlocation.html', action="Edit", form=form, view_location=view_location)


@bp.route('/edititemmovement/<int:movement_id>', methods=['GET', 'POST'])
@login_required
def edititemmovement(movement_id):
	view_itemmovement = ItemMovement.query.get_or_404(movement_id)
	form = ItemMovementForm(obj=view_itemmovement)
	if form.validate_on_submit():
		view_itemmovement.movement_type = form.movement_type.data
		view_itemmovement.quantity = form.quantity.data
		view_itemmovement.from_location = form.from_location.data
		view_itemmovement.to_location = form.to_location.data
		db.session.commit()
		flash('You have edited the movement.')
		return redirect(url_for('main.viewitemmovement'))
	form.movement_type.data = view_itemmovement.movement_type
	form.quantity.data = view_itemmovement.quantity
	form.from_location.data = view_itemmovement.from_location
	form.to_location.data = view_itemmovement.to_location
	return render_template('additemmovement.html', action="Edit", form=form, view_itemmovement = view_itemmovement)



@bp.route('/receiveamount/<int:id>', methods=['GET', 'POST'])
@login_required
def receiveamount(id):
    view_sale = Sale.query.get_or_404(id)
    customer = Customer.query.get(view_sale.customer_id)

    if not customer:
        flash("Customer details not found!", "error")
        return redirect(url_for('main.viewsale'))

    previous_payments = AmountReceive.query.filter_by(sale_id=id).all()
    form = SaleAmountReceiveForm(obj=view_sale)

    if form.validate_on_submit():
        for received_form in form.receive_amounts:
            new_payment = AmountReceive(
                sale_id=id,
                amount=received_form.amount.data,
                payment_mode=received_form.payment_mode.data,
                payment_date=received_form.payment_date.data,
                user_id=current_user.id  # 👈 Save user info if needed
            )
            db.session.add(new_payment)

        total_received = sum(p.amount for p in previous_payments) + sum(f.amount.data for f in form.receive_amounts)
        view_sale.balance_due = view_sale.total_amount - total_received

        db.session.commit()
        flash('Payment received successfully!', 'success')
        return redirect(url_for('main.viewsale'))

    return render_template(
        'receiveamount.html',
        form=form,
        view_sale=view_sale,
        previous_payments=previous_payments,
        customer=customer,
        user=current_user  # 👈 If you need to use it in the template
    )


from flask_login import current_user

@bp.route('/receivepurchaseamount/<int:id>', methods=['GET', 'POST'])
@login_required
def receivepurchaseamount(id):
    view_purchase = Purchase.query.get_or_404(id)
    vendor = Vendor.query.get(view_purchase.vendor_id)

    if not vendor:
        flash("Vendor details not found!", "error")
        return redirect(url_for('main.viewpurchase'))

    previous_payments = PurchaseAmountReceive.query.filter_by(purchase_id=id).all()
    form = PurchaseAmountReceiveForm(obj=view_purchase)

    if form.validate_on_submit():
        print(f"🟢 Form Validated by: {current_user.username}")  # 👈 See who's submitting

        for received_form in form.receive_amounts:
            new_payment = PurchaseAmountReceive(
                purchase_id=id,
                amount=received_form.amount.data,
                payment_mode=received_form.payment_mode.data,
                payment_date=received_form.payment_date.data,
                user_id=current_user.id
            )
            db.session.add(new_payment)

        total_received = sum(p.amount for p in previous_payments) + sum(f.amount.data for f in form.receive_amounts)
        view_purchase.balance_due = view_purchase.total_amount - total_received

        db.session.commit()
        flash('Payment received successfully!', 'success')

        return redirect(url_for('main.viewpurchase'))

    return render_template(
        'receivepurchaseamount.html',
        form=form,
        view_purchase=view_purchase,
        previous_payments=previous_payments,
        vendor=vendor,
        user=current_user  # Optional: if you want to use it in template
    )


@bp.route('/editpurchase/<int:id>', methods=['GET', 'POST'])
@login_required
def editpurchase(id):
	view_purchase = Purchase.query.get_or_404(id)
	form = PurchaseForm(obj=view_purchase)
	if form.validate_on_submit():
		view_purchase.vendorname = form.vendorname.data
		view_purchase.peyment_terms = form.payment_terms.data
		view_purchase.item_name = form.item_name.data
		view_purchase.amount = form.amount.data
		db.session.commit()
		flash('You have edited the purchase invoice')
		return redirect(url_for('main.viewpurchase'))
	return render_template('addpurchase.html', action="Edit", form=form, view_purchase=view_purchase)


@bp.route('/admin/editcustomer/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_editcustomer(id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    customer = Customer.query.get_or_404(id)

    if request.method == 'POST':
        customer.name = request.form['name']
        customer.mobile = request.form['mobile']
        customer.address = request.form['address']
        db.session.commit()
        flash('Customer updated successfully.', 'success')
        return redirect(url_for('main.admin_customers'))

    return render_template('admin/edit_customer.html', customer=customer)


@bp.route('/admin/editvendor/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_editvendor(id):
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    vendor = Vendor.query.get_or_404(id)

    if request.method == 'POST':
        vendor.name = request.form['name']
        vendor.mobile = request.form['mobile']
        vendor.address = request.form['address']
        db.session.commit()
        flash('Vendor updated successfully.', 'success')
        return redirect(url_for('main.admin_vendors'))

    return render_template('admin/edit_vendor.html', vendor=vendor)

@bp.route('/admin/export_vendors_csv')
@login_required
@admin_required
def admin_export_vendors_csv():
    import csv
    from io import StringIO
    from flask import Response

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Mobile', 'Address', 'Email', 'GST', 'PAN', 'User'])

    vendors = Vendor.query.all()
    for v in vendors:
        writer.writerow([
            v.name, v.mobile, v.address, v.email or '',
            v.gstin or '', v.pan or '', v.user.username
        ])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=vendors.csv"})


@bp.route('/editcustomer/<int:id>', methods=['GET', 'POST'])
@login_required
def editcustomer(id):
    view_customer = Customer.query.filter_by(id=id, user_id=current_user.id).first()

    if not view_customer:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.viewcustomer'))
    
    form = CustomerForm(obj=view_customer)

    if request.method == 'POST' and form.validate_on_submit():
        # Only update DB if POST
        view_customer.name = form.name.data
        view_customer.mobile = form.mobile.data
        view_customer.email = form.email.data
        view_customer.gst = form.gst.data
        view_customer.pan = form.pan.data
        view_customer.address = form.address.data
        db.session.commit()
        flash('You have edited the Customer.')
        return redirect(url_for('main.viewcustomer'))
    
    elif request.method == 'GET':
        # Only populate form fields if it's a GET request
        form.name.data = view_customer.name
        form.mobile.data = view_customer.mobile
        form.email.data = view_customer.email
        form.gst.data = view_customer.gst
        form.pan.data = view_customer.pan
        form.address.data = view_customer.address

    if form.errors:
        print(form.errors)


    return render_template('addcustomer.html', action="Edit", form=form, view_customer=view_customer)


@bp.route('/editvendor/<int:id>', methods=['GET', 'POST'])
@login_required
def editvendor(id):
    view_vendor = Vendor.query.filter_by(id=id, user_id=current_user.id).first()
    if not view_vendor:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('main.viewvendor'))

    form = VendorForm(obj=view_vendor)
    if form.validate_on_submit():
        view_vendor.name = form.name.data
        view_vendor.mobile = form.mobile.data
        view_vendor.email = form.email.data
        view_vendor.gstin = form.gstin.data
        view_vendor.pan = form.pan.data
        view_vendor.address = form.address.data
        db.session.commit()
        flash('You have edited the Vendor.')
        return redirect(url_for('main.viewvendor'))
    form.name.data = view_vendor.name
    form.mobile.data = view_vendor.mobile
    form.email.data = view_vendor.email
    form.gstin.data = view_vendor.gstin
    form.pan.data = view_vendor.pan
    form.address.data = view_vendor.address
    return render_template('addvendor.html', action="Edit", form=form, view_vendor=view_vendor)


@bp.route('/edititems/<int:id>', methods=['GET', 'POST'])
@login_required
def edititems(id):
    view_items = Item.query.filter_by(id=id, user_id=current_user.id).first()
    if not view_items:
        flash("Unauthorized access", "danger")
        return redirect(url_for(main.viewitems))
    form = ItemsForm()
    if form.validate_on_submit():
        view_items.itemname = form.itemname.data
        view_items.hsn_code = form.hsn_code.data
        view_items.item_code = form.item_code.data
        view_items.description = form.description.data
        view_items.view_category = form.category.data
        db.session.commit()
        flash('You have edite the Item.')
        return redirect(url_for('main.viewitems'))
    form.itemname.data = view_items.itemname
    form.hsn_code.data = view_items.hsn_code
    form.item_code.data = view_items.item_code
    form.description.data = view_items.description
    form.category.data = view_items.category
    return render_template('additems.html', action="Edit", form=form, view_items = view_items)

	
@bp.route('/deletecategory/<int:id>', methods=['GET', 'POST'])
@login_required
def deletecategory(id):
    del_categ = Category.query.filter_by(id=id, user_id=current_user.id).first()
    if not del_categ:
        flash("Unauthorized access", "danger")
        redirect(url_for(main.category))

    db.session.delete(del_categ)
    db.session.commit()
    flash('You have deleted the category.')
    return redirect(url_for('main.category'))

@bp.route('/deleteexpense/<int:id>', methods=['GET', 'POST'])
@login_required
def deleteexpense(id):
    del_exp = ExpenseItem.query.get_or_404(id)
    db.session.delete(del_exp)
    db.session.commit()
    flash('You have deleted the Expense.')
    return redirect(url_for('main.viewexpense'))

@bp.route('/deleteexpcategory/<int:id>', methods=['GET', 'POST'])
@login_required
def deleteexpcategory(id):
    del_cat = ExpenseCategory.query.filter_by(id=id, user_id=current_user.id).first()
    if not del_cat:
        flash("Unauthorized access", "danger")
    db.session.delete(del_cat)
    db.session.commit()
    flash('You have deleted the Category')
    return redirect(url_for('main.viewexpcategory'))

@bp.route('/deleteitemmovement/<int:movement_id>', methods=['GET', 'POST'])
@login_required
def deleteitemmovement(movement_id):
	del_move = ItemMovement.query.get_or_404(movement_id)
	db.session.delete(del_move)
	db.session.commit()
	flash('You have delete the record.')
	return redirect(url_for('main.viewitemmovement'))

@bp.route('/deletepurchase/<int:id>', methods=['GET', 'POST'])
@login_required
def deletepurchase(id):
	del_pur = Purchase.query.get_or_404(id)
	db.session.delete(del_pur)
	db.session.commit()
	flash('You have deleted the purchase.')
	return redirect(url_for('main.viewpurchase'))

@bp.route('/deletelocation/<int:id>', methods=['GET', 'POST'])
@login_required
def deletelocation(id):
	del_loc = Godown.query.get_or_404(id)
	db.session.delete(del_loc)
	db.session.commit()
	flash('You have delete the Godown.')
	return redirect(url_for('main.viewlocation'))


@bp.route('/deletecustomer/<int:id>', methods=['GET', 'POST'])
@login_required
def deletecustomer(id):
	del_cust = Customer.query.get_or_404(id)
	db.session.delete(del_cust)
	db.session.commit()
	flash('You have deleted the Customer.')
	return redirect(url_for('main.viewcustomer'))

@bp.route('/deletevendor/<int:id>', methods = ['GET', 'POST'])
@login_required
def deletevendor(id):
	del_ven = Vendor.query.get_or_404(id)
	db.session.delete(del_ven)
	db.session.commit()
	flash('You have delete the Vendor.')
	return redirect(url_for('main.viewvendor'))

@bp.route('/deletesale/<int:id>', methods=['GET', 'POST'])
@login_required
def deletesale(id):
	del_sale = Sale.query.get_or_404(id)
	db.session.delete(del_sale)
	db.session.commit()
	flash('you have deleted the Sale Invoice.')
	return redirect(url_for('main.viewsale'))


@bp.route('/deleteitems/<int:id>', methods=['GET', 'POST'])
@login_required
def deleteitems(id):
	del_item = Item.query.get_or_404(id)
	db.session.delete(del_item)
	db.session.commit()
	flash('You have delete the item.')
	return redirect(url_for('main.viewitems'))

def get_sales_by_date(date_str, user=None):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    query = Sale.query.filter(db.func.date(Sale.invoice_date) == date.date())
    if user:
        query = query.filter(Sale.user_id == user.id)
    return query.all()

import io
from io import StringIO
@bp.route('/sales_report', methods=['GET'])
@login_required
def sales_report():
    lang = get_locale()
    translations = get_translation_dict(lang)
    search_query = request.args.get('search', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    sales_query = Sale.query.filter(Sale.user_id == current_user.id)

    if search_query:
        sales_query = sales_query.join(Customer).filter(Customer.name.ilike(f"%{search_query}%"))

    if from_date and to_date:
        sales_query = sales_query.filter(Sale.invoice_date.between(from_date, to_date))

    sales = sales_query.order_by(Sale.invoice_date.desc()).all()

    # ✅ Return partial if AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('partials/sales_results.html', sales=sales, t=translations)

    return render_template('sales_report.html', sales=sales, t=translations)

@bp.route('/export_sales_csv', methods=['GET'])
@login_required
def export_sales_csv():
    search_query = request.args.get('search', '')
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    sales_query = Sale.query.filter(Sale.user_id == current_user.id)

    if search_query:
        sales_query = sales_query.join(Customer).filter(Customer.name.ilike(f"%{search_query}%"))

    if from_date and to_date:
        sales_query = sales_query.filter(Sale.invoice_date.between(from_date, to_date))

    sales = sales_query.order_by(Sale.invoice_date.desc()).all()

    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(["Invoice #", "Customer", "Date", "Total Amount"])

    for sale in sales:
        csv_writer.writerow([sale.id, sale.customer.name, sale.invoice_date.strftime('%Y-%m-%d'), sale.total_amount])

    response = Response(csv_data.getvalue(), content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=sales_report.csv"
    return response


from sqlalchemy.orm import joinedload
from sqlalchemy import func

@bp.route('/daybook', methods=['GET'])
@login_required
def daybook_report():
    lang = get_locale()
    translations = get_translation_dict(lang)
    date_filter = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    # Sales
    sales = Sale.query.filter(
        Sale.user_id == current_user.id,
        func.date(Sale.invoice_date) == date_filter
    ).all()

    # Purchases
    purchases = Purchase.query.filter(
        Purchase.user_id == current_user.id,
        func.date(Purchase.purchase_date) == date_filter
    ).all()

    # Expenses (with related ExpenseItems)
    expenses = Expense.query.options(joinedload(Expense.expense_items)).filter(
        Expense.user_id == current_user.id,
        func.date(Expense.expense_date) == date_filter
    ).all()

    # Totals
    total_sales = sum(sale.total_amount for sale in sales)
    total_purchases = sum(purchase.total_cost for purchase in purchases)
    total_expenses = sum(
        item.amount for exp in expenses for item in exp.expense_items
    )

    net_profit = total_sales - (total_purchases + total_expenses)

    return render_template(
        'daybook.html',
        user=current_user,
        t=translations,
        sales=sales,
        purchases=purchases,
        expenses=expenses,
        total_sales=total_sales,
        total_purchases=total_purchases,
        total_expenses=total_expenses,
        net_profit=net_profit,
        date_filter=date_filter
    )


from flask import Response
from io import StringIO
import csv
from datetime import datetime
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import Sale, Purchase, ExpenseItem, Expense

@bp.route('/export_daybook_csv', methods=['GET'])
@login_required
def export_daybook_csv():
    date_filter = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))

    # Fetch user-specific entries
    sales = Sale.query.filter(
        Sale.user_id == current_user.id,
        func.date(Sale.invoice_date) == date_filter
    ).all()

    purchases = Purchase.query.filter(
        Purchase.user_id == current_user.id,
        func.date(Purchase.purchase_date) == date_filter
    ).all()

    expenses = ExpenseItem.query.filter(
        ExpenseItem.user_id == current_user.id,
        func.date(ExpenseItem.expense_date) == date_filter
    ).all()

    # Prepare CSV data
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerow(["Transaction Type", "ID", "Name / Item", "Amount"])

    for sale in sales:
        csv_writer.writerow(["Sale", sale.id, sale.customer.name, "%.2f" % sale.total_amount])

    for purchase in purchases:
        csv_writer.writerow(["Purchase", purchase.id, purchase.Vendor.name, "%.2f" % purchase.total_cost])

    for item in expenses:
        csv_writer.writerow(["Expense", item.expense_id, item.itemname, "%.2f" % item.total_amount])

    # Return CSV file
    response = Response(csv_data.getvalue(), content_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=daybook_{date_filter}.csv"
    return response



##### Purchase Report ##

def get_filtered_purchases(start_date=None, end_date=None, vendor_id=None, customer_id=None, item_id=None):
    query = Purchase.query.join(PurchaseItem).join(Item).join(Vendor)

    if start_date and end_date:
        query = query.filter(Purchase.purchase_date.between(start_date, end_date))

    if vendor_id:
        query = query.filter(Purchase.vendor_id == vendor_id)

    if customer_id:
        query = query.filter(Purchase.customer_id == customer_id)  # Only if relevant

    if item_id:
        query = query.filter(PurchaseItem.item_id == item_id)

    return query.all()


@bp.route('/purchase_report', methods=['GET'])
@login_required
def purchase_report():
    lang = get_locale()
    translations = get_translation_dict(lang)
    
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    search_query = request.args.get('search', '')

    # ✅ Filter by current user's purchases
    query = Purchase.query.join(Vendor).filter(
        Vendor.name.ilike(f"%{search_query}%"),
        Purchase.user_id == current_user.id  # 👈 Assuming Purchase has user_id
    )

    if from_date and to_date:
        query = query.filter(Purchase.invoice_date.between(from_date, to_date))

    purchases = query.order_by(Purchase.invoice_date.desc()).all()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('partials/purchase_results.html', purchases=purchases)

    return render_template('purchase_report.html', purchases=purchases, t=translations)



@bp.route('/export_purchase_csv')
@login_required
def export_purchase_csv():
    purchases = get_filtered_purchases()

    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    writer.writerow(["Purchase ID", "Vendor", "Date", "Total Amount"])

    for purchase in purchases:
        writer.writerow([purchase.id, purchase.Vendor.name, purchase.purchase_date.strftime('%Y-%m-%d'), purchase.total_amount])

    response = make_response(csv_output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=purchase_report.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@bp.route('/transactions_report')
@login_required
def transactions_report():
    from datetime import datetime, timedelta
    from sqlalchemy import func
    lang = get_locale()
    translations = get_translation_dict(lang)

    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')

    try:
        if not from_date_str or not to_date_str:
            to_date = datetime.today().date()
            from_date = to_date - timedelta(days=30)
        else:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect(url_for('main.transactions_report'))

    search_query = request.args.get('search', '').lower()

    # ✅ Sales
    sales_query = (
        db.session.query(Sale.id, Customer.name, Sale.invoice_date, Sale.total_amount)
        .join(Customer, Customer.id == Sale.customer_id)
        .filter(Sale.user_id == current_user.id)
        .filter(Sale.invoice_date.between(from_date, to_date))
    )
    if search_query:
        sales_query = sales_query.filter(sa.func.lower(Customer.name).like(f"%{search_query}%"))
    sales_data = [{"type": "Sale", "party": s.name, "date": s.invoice_date, "amount": s.total_amount} for s in sales_query.all()]

    # ✅ Payments In
    payments_in_query = (
        db.session.query(AmountReceive.amount, Customer.name, AmountReceive.payment_date)
        .join(Sale, Sale.id == AmountReceive.sale_id)
        .join(Customer, Customer.id == Sale.customer_id)
        .filter(Sale.user_id == current_user.id)
        .filter(AmountReceive.payment_date.between(from_date, to_date))
    )
    if search_query:
        payments_in_query = payments_in_query.filter(sa.func.lower(Customer.name).like(f"%{search_query}%"))
    payments_in_data = [{"type": "Payment In", "party": p.name, "date": p.payment_date, "amount": p.amount} for p in payments_in_query.all()]

    # ✅ Purchases
    purchases_query = (
        db.session.query(Purchase.id, Vendor.name, Purchase.invoice_date, Purchase.total_amount)
        .join(Vendor, Vendor.id == Purchase.vendor_id)
        .filter(Purchase.user_id == current_user.id)
        .filter(Purchase.invoice_date.between(from_date, to_date))
    )
    if search_query:
        purchases_query = purchases_query.filter(sa.func.lower(Vendor.name).like(f"%{search_query}%"))
    purchases_data = [{"type": "Purchase", "party": p.name, "date": p.invoice_date, "amount": -p.total_amount} for p in purchases_query.all()]

    # ✅ Payments Out
    payments_out_query = (
        db.session.query(PurchaseAmountReceive.amount, Vendor.name, PurchaseAmountReceive.payment_date)
        .join(Purchase, Purchase.id == PurchaseAmountReceive.purchase_id)
        .join(Vendor, Vendor.id == Purchase.vendor_id)
        .filter(Purchase.user_id == current_user.id)
        .filter(PurchaseAmountReceive.payment_date.between(from_date, to_date))
    )
    if search_query:
        payments_out_query = payments_out_query.filter(sa.func.lower(Vendor.name).like(f"%{search_query}%"))
    payments_out_data = [{"type": "Payment Out", "party": p.name, "date": p.payment_date, "amount": -p.amount} for p in payments_out_query.all()]

    # ✅ Expenses
    expenses_query = (
        db.session.query(
            func.date(ExpenseItem.expense_date),
            ExpenseCategory.name,
            sa.func.sum(ExpenseItem.amount)
        )
        .join(Expense, Expense.id == ExpenseItem.expense_id)
        .join(ExpenseCategory, ExpenseCategory.id == Expense.expcat_id)
        .filter(ExpenseItem.user_id == current_user.id)
        .filter(func.date(ExpenseItem.expense_date).between(from_date, to_date))
        .group_by(func.date(ExpenseItem.expense_date), ExpenseCategory.name)
    )
    if search_query:
        expenses_query = expenses_query.filter(sa.func.lower(ExpenseCategory.name).like(f"%{search_query}%"))
    expenses_data = [{"type": "Expense", "party": e[1], "date": e[0], "amount": -e[2]} for e in expenses_query.all()]

    # ✅ Combine all
    all_transactions = sales_data + payments_in_data + purchases_data + payments_out_data + expenses_data

    # 🔧 Normalize all date types to `datetime.date`
    for txn in all_transactions:
        if isinstance(txn["date"], datetime):
            txn["date"] = txn["date"].date()

    # ✅ Sort by date (latest first)
    all_transactions.sort(key=lambda x: x["date"], reverse=True)

    # ✅ Return HTML
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render_template("partials/transactions_list.html", transactions=all_transactions, t=translations)

    return render_template("transactions_report.html",
                           transactions=all_transactions,
                           from_date=from_date,
                           to_date=to_date,
                           t=translations)


from flask_login import current_user, login_required
import csv
from datetime import datetime, timedelta
from flask import Response, request
from flask_login import login_required, current_user

@bp.route('/export_transactions_csv')
@login_required
def export_transactions_csv():
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')
    search_query = request.args.get('search', '')

    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    default_from_date = datetime.today() - timedelta(days=30)
    default_to_date = datetime.today()

    from_date = validate_date(from_date_str, default_from_date).date()
    to_date = validate_date(to_date_str, default_to_date).date()

    # ✅ Sales
    sales = (
        db.session.query(Sale.id, Customer.name, Sale.invoice_date, Sale.total_amount)
        .join(Customer, Customer.id == Sale.customer_id)
        .filter(Sale.user_id == current_user.id)
        .filter(func.date(Sale.invoice_date).between(from_date, to_date))
        .filter(Customer.name.ilike(f"%{search_query}%"))
        .all()
    )
    sales_data = [{"type": "Sale", "party": s.name, "date": s.invoice_date, "amount": s.total_amount} for s in sales]

    # ✅ Payments In
    payments_in = (
        db.session.query(AmountReceive.amount, Customer.name, AmountReceive.payment_date)
        .join(Sale, Sale.id == AmountReceive.sale_id)
        .join(Customer, Customer.id == Sale.customer_id)
        .filter(Sale.user_id == current_user.id)
        .filter(func.date(AmountReceive.payment_date).between(from_date, to_date))
        .filter(Customer.name.ilike(f"%{search_query}%"))
        .all()
    )
    payments_in_data = [{"type": "Payment In", "party": p.name, "date": p.payment_date, "amount": p.amount} for p in payments_in]

    # ✅ Purchases
    purchases = (
        db.session.query(Purchase.id, Vendor.name, Purchase.invoice_date, Purchase.total_amount)
        .join(Vendor, Vendor.id == Purchase.vendor_id)
        .filter(Purchase.user_id == current_user.id)
        .filter(func.date(Purchase.invoice_date).between(from_date, to_date))
        .filter(Vendor.name.ilike(f"%{search_query}%"))
        .all()
    )
    purchases_data = [{"type": "Purchase", "party": p.name, "date": p.invoice_date, "amount": -p.total_amount} for p in purchases]

    # ✅ Payments Out
    payments_out = (
        db.session.query(PurchaseAmountReceive.amount, Vendor.name, PurchaseAmountReceive.payment_date)
        .join(Purchase, Purchase.id == PurchaseAmountReceive.purchase_id)
        .join(Vendor, Vendor.id == Purchase.vendor_id)
        .filter(Purchase.user_id == current_user.id)
        .filter(func.date(PurchaseAmountReceive.payment_date).between(from_date, to_date))
        .filter(Vendor.name.ilike(f"%{search_query}%"))
        .all()
    )
    payments_out_data = [{"type": "Payment Out", "party": p.name, "date": p.payment_date, "amount": -p.amount} for p in payments_out]

    # ✅ Expenses (fixed)
    expenses = (
        db.session.query(
            func.date(ExpenseItem.expense_date),
            ExpenseCategory.name,
            sa.func.sum(ExpenseItem.amount)
        )
        .join(Expense, Expense.id == ExpenseItem.expense_id)
        .join(ExpenseCategory, ExpenseCategory.id == Expense.expcat_id)
        .filter(ExpenseItem.user_id == current_user.id)
        .filter(func.date(ExpenseItem.expense_date).between(from_date, to_date))
        .group_by(func.date(ExpenseItem.expense_date), ExpenseCategory.name)
        .all()
    )
    expenses_data = [{"type": "Expense", "party": e[1], "date": e[0], "amount": -e[2]} for e in expenses]

    # ✅ Combine all
    transactions = sales_data + payments_in_data + purchases_data + payments_out_data + expenses_data

    # ✅ Generate CSV
    def generate_csv():
        data = [["Transaction Type", "Party", "Date", "Amount"]]
        for txn in transactions:
            data.append([txn["type"], txn["party"], txn["date"].strftime('%Y-%m-%d'), txn["amount"]])
        output = csv.StringIO()
        writer = csv.writer(output)
        writer.writerows(data)
        return output.getvalue()

    response = Response(generate_csv(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=transactions_report.csv"
    return response





from flask_login import login_required, current_user

from datetime import datetime, date

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or date(2000, 1, 1)  # Default to a very early date
    to_date = parse_date_safe(raw_to) or date.today()  # Default to today
    return from_date, to_date



@bp.route('/profit_loss_report')
@login_required
def profit_loss_report():
    # Get safe date range
    from_date, to_date = get_safe_date_range()

    # ✅ Total Sales Revenue (for current user)
    sales = db.session.query(sa.func.sum(Sale.total_amount))\
        .filter(Sale.user_id == current_user.id)\
        .filter(Sale.invoice_date.between(from_date, to_date))\
        .scalar() or 0.0

    # ✅ Total Purchases (COGS)
    purchases = db.session.query(sa.func.sum(Purchase.total_amount))\
        .filter(Purchase.user_id == current_user.id)\
        .filter(Purchase.invoice_date.between(from_date, to_date))\
        .scalar() or 0.0

    gross_profit = sales - purchases

    # ✅ Total Expenses
    total_expenses = db.session.query(sa.func.sum(ExpenseItem.amount))\
        .join(Expense, Expense.id == ExpenseItem.expense_id)\
        .filter(Expense.user_id == current_user.id)\
        .filter(Expense.expense_date.between(from_date, to_date))\
        .scalar() or 0.0

    net_profit = gross_profit - total_expenses

    # Return rendered template with the calculated data
    return render_template(
        'profit_loss_report.html',
        sales=sales,
        purchases=purchases,
        gross_profit=gross_profit,
        total_expenses=total_expenses,
        net_profit=net_profit
    )



import csv
from datetime import datetime
from flask import Response, request
from flask_login import login_required, current_user

@bp.route('/export_profit_loss_csv')
@login_required
def export_profit_loss_csv():
    # Get date range from query params, validate and set defaults if missing
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Default date range (last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # Total Sales
    sales = db.session.query(sa.func.sum(Sale.total_amount))\
        .filter(Sale.user_id == current_user.id)\
        .filter(Sale.invoice_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Total Purchases (COGS)
    purchases = db.session.query(sa.func.sum(Purchase.total_amount))\
        .filter(Purchase.user_id == current_user.id)\
        .filter(Purchase.invoice_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Gross Profit Calculation
    gross_profit = sales - purchases

    # Total Expenses
    total_expenses = db.session.query(sa.func.sum(ExpenseItem.amount))\
        .join(Expense, Expense.id == ExpenseItem.expense_id)\
        .filter(Expense.user_id == current_user.id)\
        .filter(Expense.expense_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Net Profit Calculation
    net_profit = gross_profit - total_expenses

    # Prepare the CSV data
    output = [["Metric", "Amount"]]
    output += [
        ["Total Sales", f"{sales:.2f}"],
        ["Total Purchases (COGS)", f"{purchases:.2f}"],
        ["Gross Profit", f"{gross_profit:.2f}"],
        ["Total Expenses", f"{total_expenses:.2f}"],
        ["Net Profit", f"{net_profit:.2f}"]
    ]

    # Create the CSV response
    response = Response()
    response.status_code = 200
    response.headers["Content-Disposition"] = "attachment; filename=profit_loss_report.csv"
    response.headers["Content-Type"] = "text/csv"
    writer = csv.writer(response.stream)
    writer.writerows(output)
    return response


from flask_login import login_required, current_user

from datetime import datetime, date

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or date(2000, 1, 1)  # Default to a very early date
    to_date = parse_date_safe(raw_to) or date.today()  # Default to today
    return from_date, to_date




@bp.route('/cash_flow_report')
@login_required
def cash_flow_report():
    # Get safe date range
    from_date, to_date = get_safe_date_range()

    # ✅ Cash Inflows (received from customers)
    sales_inflows = db.session.query(sa.func.sum(AmountReceive.amount))\
        .join(Sale, Sale.id == AmountReceive.sale_id)\
        .filter(Sale.user_id == current_user.id)\
        .filter(AmountReceive.payment_date.between(from_date, to_date))\
        .scalar() or 0.0

    other_income = 0.0  # Add any other user-specific income if applicable

    # ✅ Purchases (COGS)
    purchase_outflows = db.session.query(sa.func.sum(Purchase.total_amount))\
        .filter(Purchase.user_id == current_user.id)\
        .filter(Purchase.invoice_date.between(from_date, to_date))\
        .scalar() or 0.0

    # ✅ Vendor Payments
    vendor_payments = db.session.query(sa.func.sum(PurchaseAmountReceive.amount))\
        .join(Purchase, Purchase.id == PurchaseAmountReceive.purchase_id)\
        .filter(Purchase.user_id == current_user.id)\
        .filter(PurchaseAmountReceive.payment_date.between(from_date, to_date))\
        .scalar() or 0.0

    # ✅ Expenses
    expenses_outflows = db.session.query(sa.func.sum(ExpenseItem.total_amount))\
        .join(Expense, Expense.id == ExpenseItem.expense_id)\
        .filter(Expense.user_id == current_user.id)\
        .filter(Expense.expense_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Total calculations
    total_inflows = sales_inflows + other_income
    total_outflows = purchase_outflows + vendor_payments + expenses_outflows
    net_cash_flow = total_inflows - total_outflows

    # Return the rendered report template with calculated values
    return render_template(
        'cash_flow_report.html',
        sales_inflows=sales_inflows,
        other_income=other_income,
        purchase_outflows=purchase_outflows,
        vendor_payments=vendor_payments,
        expenses_outflows=expenses_outflows,
        total_inflows=total_inflows,
        total_outflows=total_outflows,
        net_cash_flow=net_cash_flow
    )


import csv
import io
from datetime import datetime, timedelta
from flask import Response, request, make_response
from flask_login import login_required, current_user

@bp.route('/export_cash_flow_csv')
@login_required
def export_cash_flow_csv():
    # Get date range from query params, validate and set defaults if missing
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Default date range (last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # Cash inflows (Sales Receivables)
    sales_inflows = db.session.query(sa.func.sum(AmountReceive.amount))\
        .join(Sale, Sale.id == AmountReceive.sale_id)\
        .filter(Sale.user_id == current_user.id)\
        .filter(AmountReceive.payment_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Placeholder for Other Income (can be updated if needed)
    other_income = 0.0  # You can modify this to fetch other income data if applicable

    # Cash outflows (Purchases)
    purchase_outflows = db.session.query(sa.func.sum(Purchase.total_amount))\
        .filter(Purchase.user_id == current_user.id)\
        .filter(Purchase.invoice_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Vendor Payments (Payments to Vendors)
    vendor_payments = db.session.query(sa.func.sum(PurchaseAmountReceive.amount))\
        .join(Purchase, Purchase.id == PurchaseAmountReceive.purchase_id)\
        .filter(Purchase.user_id == current_user.id)\
        .filter(PurchaseAmountReceive.payment_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Expenses outflows
    expenses_outflows = db.session.query(sa.func.sum(ExpenseItem.total_amount))\
        .join(Expense, Expense.id == ExpenseItem.expense_id)\
        .filter(Expense.user_id == current_user.id)\
        .filter(Expense.expense_date.between(from_date, to_date))\
        .scalar() or 0.0

    # Total Inflows and Outflows Calculation
    total_inflows = sales_inflows + other_income
    total_outflows = purchase_outflows + vendor_payments + expenses_outflows
    net_cash_flow = total_inflows - total_outflows

    # Prepare CSV response
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Category", "Amount"])
    writer.writerow(["Total Cash Inflows", f"{sales_inflows:.2f}"])
    writer.writerow(["Other Income", f"{other_income:.2f}"])
    writer.writerow(["Total Cash Outflows", f"{total_outflows:.2f}"])
    writer.writerow(["Purchases (COGS)", f"{purchase_outflows:.2f}"])
    writer.writerow(["Vendor Payments", f"{vendor_payments:.2f}"])
    writer.writerow(["Expenses", f"{expenses_outflows:.2f}"])
    writer.writerow(["Net Cash Flow", f"{net_cash_flow:.2f}"])

    # Return CSV file as response
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=cash_flow_report.csv"
    return response




from flask import render_template
from flask_login import login_required, current_user
import sqlalchemy as sa
from app import db
from app.models import Sale, Purchase, ExpenseItem, Expense, Item, AmountReceive, PurchaseAmountReceive


# Helper functions with user_id
def get_cash_available(user_id):
    cash_in = db.session.query(sa.func.sum(AmountReceive.amount))\
        .filter(AmountReceive.user_id == user_id).scalar() or 0.0
    cash_out = db.session.query(sa.func.sum(PurchaseAmountReceive.amount))\
        .filter(PurchaseAmountReceive.user_id == user_id).scalar() or 0.0
    return cash_in - cash_out


def get_accounts_receivable(user_id):
    return (
        db.session.query(sa.func.sum(Sale.total_amount - sa.func.coalesce(AmountReceive.amount, 0)))
        .outerjoin(AmountReceive, Sale.id == AmountReceive.sale_id)
        .filter(Sale.user_id == user_id)
        .filter(Sale.total_amount > sa.func.coalesce(AmountReceive.amount, 0))
        .scalar() or 0.0
    )


def get_inventory_value(user_id):
    return (
        db.session.query(sa.func.sum(Item.stock_quantity * Item.unit_price))
        .filter(Item.user_id == user_id)
        .scalar() or 0.0
    )


def get_accounts_payable(user_id):
    return (
        db.session.query(sa.func.sum(Purchase.total_amount - sa.func.coalesce(PurchaseAmountReceive.amount, 0)))
        .outerjoin(PurchaseAmountReceive, Purchase.id == PurchaseAmountReceive.purchase_id)
        .filter(Purchase.user_id == user_id)
        .filter(Purchase.total_amount > sa.func.coalesce(PurchaseAmountReceive.amount, 0))
        .scalar() or 0.0
    )


def get_net_profit(user_id):
    sales_total = db.session.query(sa.func.sum(Sale.total_amount)).filter(Sale.user_id == user_id).scalar() or 0.0
    purchases_total = db.session.query(sa.func.sum(Purchase.total_amount)).filter(Purchase.user_id == user_id).scalar() or 0.0
    expenses_total = db.session.query(sa.func.sum(ExpenseItem.amount))\
        .join(Expense, Expense.id == ExpenseItem.expense_id)\
        .filter(Expense.user_id == user_id).scalar() or 0.0
    return sales_total - purchases_total - expenses_total


# 📘 Balance Sheet Route
@bp.route('/balance_sheet')
@login_required
def balance_sheet():
    user_id = current_user.id  # ✅ Get user ID from login

    cash_available = get_cash_available(user_id)
    accounts_receivable = get_accounts_receivable(user_id)
    inventory_value = get_inventory_value(user_id)
    accounts_payable = get_accounts_payable(user_id)
    loans_payable = 0.0  # You can add this later if you track loans
    net_profit = get_net_profit(user_id)
    owners_equity = 0.0  # Adjust if you have investment data

    total_assets = cash_available + accounts_receivable + inventory_value
    total_liabilities = accounts_payable + loans_payable
    total_equity = net_profit + owners_equity

    return render_template(
        'balance_sheet.html',
        cash_available=cash_available,
        accounts_receivable=accounts_receivable,
        inventory_value=inventory_value,
        accounts_payable=accounts_payable,
        loans_payable=loans_payable,
        net_profit=net_profit,
        owners_equity=owners_equity,
        total_assets=total_assets,
        total_liabilities=total_liabilities,
        total_equity=total_equity
    )


@bp.route('/export_balance_sheet_csv')
@login_required
def export_balance_sheet_csv():
    user_id = current_user.id

    cash_available = get_cash_available(user_id)
    accounts_receivable = get_accounts_receivable(user_id)
    inventory_value = get_inventory_value(user_id)
    accounts_payable = get_accounts_payable(user_id)
    loans_payable = 0.0
    net_profit = get_net_profit(user_id)
    owners_equity = 0.0

    total_assets = cash_available + accounts_receivable + inventory_value
    total_liabilities = accounts_payable + loans_payable
    total_equity = net_profit + owners_equity

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Category", "Amount"])
    writer.writerow(["💰 Cash Available", f"{cash_available:.2f}"])
    writer.writerow(["📄 Accounts Receivable", f"{accounts_receivable:.2f}"])
    writer.writerow(["📦 Inventory Value", f"{inventory_value:.2f}"])
    writer.writerow(["📉 Accounts Payable", f"{accounts_payable:.2f}"])
    writer.writerow(["🏦 Loans Payable", f"{loans_payable:.2f}"])
    writer.writerow(["📊 Net Profit", f"{net_profit:.2f}"])
    writer.writerow(["🧑‍💼 Owner’s Equity", f"{owners_equity:.2f}"])
    writer.writerow(["Total Assets", f"{total_assets:.2f}"])
    writer.writerow(["Total Liabilities", f"{total_liabilities:.2f}"])
    writer.writerow(["Total Equity", f"{total_equity:.2f}"])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=balance_sheet.csv"
    return response


from datetime import datetime, timedelta
from flask import request, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
import sqlalchemy as sa
from app.models import db, Sale, Purchase, Item, Expense, ExpenseItem, AmountReceive, PurchaseAmountReceive

@bp.route('/trial_balance_report')
@login_required
def trial_balance_report():
    user_id = current_user.id
    from_date_str = request.args.get('from_date', '')
    to_date_str = request.args.get('to_date', '')

    # ✅ Handle missing or invalid dates by defaulting to last 30 days
    try:
        if not from_date_str or not to_date_str:
            to_date = datetime.today().date()
            from_date = to_date - timedelta(days=30)
        else:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash("Invalid date format provided.", "danger")
        return redirect(url_for('main.trial_balance_report'))

    # ✅ Cash Balance (Cash In - Cash Out)
    cash_balance = (
        (db.session.query(sa.func.coalesce(sa.func.sum(AmountReceive.amount), 0))
            .filter(AmountReceive.user_id == user_id)
            .scalar() or 0.0)
        -
        (db.session.query(sa.func.coalesce(sa.func.sum(PurchaseAmountReceive.amount), 0))
            .filter(PurchaseAmountReceive.user_id == user_id)
            .scalar() or 0.0)
    )

    # ✅ Accounts Receivable
    accounts_receivable = (
        db.session.query(
            sa.func.coalesce(sa.func.sum(Sale.total_amount), 0) - 
            sa.func.coalesce(sa.func.sum(AmountReceive.amount), 0)
        )
        .outerjoin(AmountReceive, Sale.id == AmountReceive.sale_id)
        .filter(Sale.user_id == user_id)
        .filter(Sale.invoice_date.between(from_date, to_date))
        .scalar() or 0.0
    )

    # ✅ Inventory Value
    inventory_value = (
        db.session.query(
            sa.func.sum(Item.stock_quantity * Item.unit_price)
        )
        .filter(Item.user_id == user_id)
        .scalar() or 0.0
    )

    # ✅ Accounts Payable
    accounts_payable = (
        db.session.query(
            sa.func.coalesce(sa.func.sum(Purchase.total_amount), 0) -
            sa.func.coalesce(sa.func.sum(PurchaseAmountReceive.amount), 0)
        )
        .outerjoin(PurchaseAmountReceive, Purchase.id == PurchaseAmountReceive.purchase_id)
        .filter(Purchase.user_id == user_id)
        .filter(Purchase.invoice_date.between(from_date, to_date))
        .scalar() or 0.0
    )

    # ✅ Sales Revenue
    total_sales = (
        db.session.query(sa.func.coalesce(sa.func.sum(Sale.total_amount), 0))
        .filter(Sale.user_id == user_id)
        .filter(Sale.invoice_date.between(from_date, to_date))
        .scalar() or 0.0
    )

    # ✅ Purchases
    total_purchases = (
        db.session.query(sa.func.coalesce(sa.func.sum(Purchase.total_amount), 0))
        .filter(Purchase.user_id == user_id)
        .filter(Purchase.invoice_date.between(from_date, to_date))
        .scalar() or 0.0
    )

    # ✅ Expenses
    total_expenses = (
        db.session.query(sa.func.coalesce(sa.func.sum(ExpenseItem.amount), 0))
        .join(Expense)
        .filter(Expense.user_id == user_id)
        .filter(Expense.expense_date.between(from_date, to_date))
        .scalar() or 0.0
    )

    # ✅ Net Profit
    net_profit = total_sales - total_purchases - total_expenses

    trial_balance_data = [
        {"account": "Cash", "debit": cash_balance, "credit": 0},
        {"account": "Accounts Receivable", "debit": accounts_receivable, "credit": 0},
        {"account": "Inventory", "debit": inventory_value, "credit": 0},
        {"account": "Accounts Payable", "debit": 0, "credit": accounts_payable},
        {"account": "Sales Revenue", "debit": 0, "credit": total_sales},
        {"account": "Cost of Goods Sold (COGS)", "debit": total_purchases, "credit": 0},
        {"account": "Expenses", "debit": total_expenses, "credit": 0},
        {
            "account": "Net Profit",
            "debit": 0 if net_profit > 0 else abs(net_profit),
            "credit": net_profit if net_profit > 0 else 0
        },
    ]

    return render_template(
        'trial_balance_report.html',
        trial_balance_data=trial_balance_data,
        total_debits=sum(entry["debit"] for entry in trial_balance_data),
        total_credits=sum(entry["credit"] for entry in trial_balance_data),
        from_date=from_date,
        to_date=to_date
    )


import csv
import io
from datetime import datetime, timedelta
from flask import Response, request, make_response
from flask_login import login_required, current_user

@bp.route('/export_trial_balance_csv')
@login_required
def export_trial_balance_csv():
    user_id = current_user.id
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set default date range (last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Account", "Debit", "Credit"])

    # Cash
    cash_balance = (
        db.session.query(sa.func.sum(AmountReceive.amount) - sa.func.sum(PurchaseAmountReceive.amount))
        .filter(AmountReceive.user_id == user_id)
        .filter(PurchaseAmountReceive.user_id == user_id)
        .scalar() or 0.0
    )
    writer.writerow(["Cash", cash_balance, 0])

    # Sales Revenue
    total_sales = db.session.query(sa.func.sum(Sale.total_amount)).filter(Sale.user_id == user_id).filter(Sale.invoice_date.between(from_date, to_date)).scalar() or 0.0
    writer.writerow(["Sales Revenue", 0, total_sales])

    # Purchases (COGS)
    total_purchases = db.session.query(sa.func.sum(Purchase.total_amount)).filter(Purchase.user_id == user_id).filter(Purchase.invoice_date.between(from_date, to_date)).scalar() or 0.0
    writer.writerow(["Purchases (COGS)", total_purchases, 0])

    # Total Expenses
    total_expenses = db.session.query(sa.func.sum(ExpenseItem.amount)).join(Expense).filter(Expense.user_id == user_id).filter(Expense.expense_date.between(from_date, to_date)).scalar() or 0.0
    writer.writerow(["Total Expenses", total_expenses, 0])

    # Vendor Payments
    vendor_payments = db.session.query(sa.func.sum(PurchaseAmountReceive.amount)).filter(PurchaseAmountReceive.user_id == user_id).filter(PurchaseAmountReceive.payment_date.between(from_date, to_date)).scalar() or 0.0
    writer.writerow(["Vendor Payments", vendor_payments, 0])

    # Customer Payments
    customer_payments = db.session.query(sa.func.sum(AmountReceive.amount)).filter(AmountReceive.user_id == user_id).filter(AmountReceive.payment_date.between(from_date, to_date)).scalar() or 0.0
    writer.writerow(["Customer Payments", 0, customer_payments])

    # Generate CSV response
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=trial_balance.csv"
    response.headers["Content-type"] = "text/csv"
    return response


from datetime import datetime

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or date(2000, 1, 1)  # Default to a very early date
    to_date = parse_date_safe(raw_to) or date.today()  # Default to today
    return from_date, to_date

@bp.route('/vendor_report')
def vendor_report():
    # Get safe date range and search query
    from_date, to_date = get_safe_date_range()
    search_query = request.args.get('search', '')
    user = current_user

    # ✅ Base vendor query for total purchases
    vendor_query = db.session.query(Vendor.name, sa.func.sum(Purchase.total_amount).label("total_purchases")) \
        .join(Purchase, Vendor.id == Purchase.vendor_id) \
        .filter(Purchase.invoice_date.between(from_date, to_date)) \
        .filter(Purchase.user_id == user.id)

    if search_query:
        vendor_query = vendor_query.filter(Vendor.name.ilike(f"%{search_query}%"))

    vendor_purchases = vendor_query.group_by(Vendor.id).all()

    # ✅ Vendor Payments query
    vendor_payment_query = db.session.query(Vendor.name, sa.func.sum(PurchaseAmountReceive.amount).label("total_payments")) \
        .join(Purchase, Vendor.id == Purchase.vendor_id) \
        .join(PurchaseAmountReceive, Purchase.id == PurchaseAmountReceive.purchase_id) \
        .filter(PurchaseAmountReceive.payment_date.between(from_date, to_date)) \
        .filter(Purchase.user_id == user.id)

    if search_query:
        vendor_payment_query = vendor_payment_query.filter(Vendor.name.ilike(f"%{search_query}%"))

    vendor_payments = vendor_payment_query.group_by(Vendor.id).all()

    # ✅ Merge Data (Vendor Purchases and Payments)
    vendor_data = {}
    for vendor, total_purchases in vendor_purchases:
        vendor_data[vendor] = {"total_purchases": total_purchases, "total_payments": 0.0}

    for vendor, total_payments in vendor_payments:
        if vendor in vendor_data:
            vendor_data[vendor]["total_payments"] = total_payments
        else:
            vendor_data[vendor] = {"total_purchases": 0.0, "total_payments": total_payments}

    # ✅ Prepare vendor report
    vendor_report = []
    for vendor, data in vendor_data.items():
        balance_due = data["total_purchases"] - data["total_payments"]
        vendor_report.append({
            "vendor": vendor,
            "total_purchases": data["total_purchases"],
            "total_payments": data["total_payments"],
            "balance_due": balance_due
        })

    return render_template('vendor_report.html', vendor_report=vendor_report, search_query=search_query)


import csv
import io
from datetime import datetime, timedelta
from flask import Response, request, make_response
from flask_login import login_required, current_user

@bp.route('/export_vendor_csv')
@login_required
def export_vendor_csv():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    user = current_user

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set default date range (last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # ✅ Fetch Vendor Purchases
    vendor_purchases = (
        db.session.query(Vendor.name, sa.func.sum(Purchase.total_amount).label("total_purchases"))
        .join(Purchase, Vendor.id == Purchase.vendor_id)
        .filter(Purchase.invoice_date.between(from_date, to_date))
        .filter(Purchase.user_id == user.id)
        .group_by(Vendor.id)
        .all()
    )

    # ✅ Fetch Payments to Vendors
    vendor_payments = (
        db.session.query(Vendor.name, sa.func.sum(PurchaseAmountReceive.amount).label("total_payments"))
        .join(Purchase, Vendor.id == Purchase.vendor_id)
        .join(PurchaseAmountReceive, Purchase.id == PurchaseAmountReceive.purchase_id)
        .filter(PurchaseAmountReceive.payment_date.between(from_date, to_date))
        .filter(Purchase.user_id == user.id)
        .group_by(Vendor.id)
        .all()
    )

    # ✅ Merge and Calculate
    vendor_data = {}
    for vendor_name, total_purchases in vendor_purchases:
        vendor_data[vendor_name] = {"total_purchases": total_purchases, "total_payments": 0.0}

    for vendor_name, total_payments in vendor_payments:
        if vendor_name in vendor_data:
            vendor_data[vendor_name]["total_payments"] = total_payments
        else:
            vendor_data[vendor_name] = {"total_purchases": 0.0, "total_payments": total_payments}

    vendor_report_data = []
    for vendor_name, data in vendor_data.items():
        balance_due = data["total_purchases"] - data["total_payments"]
        vendor_report_data.append([vendor_name, data["total_purchases"], data["total_payments"], balance_due])

    # ✅ Create CSV response
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Vendor", "Total Purchases", "Total Payments", "Balance Due"])
    writer.writerows(vendor_report_data)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=vendor_report.csv"
    response.headers["Content-type"] = "text/csv"
    return response


from flask_login import current_user

from datetime import datetime

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or date(2000, 1, 1)  # Default to a very early date
    to_date = parse_date_safe(raw_to) or date.today()  # Default to today
    return from_date, to_date

@bp.route('/customer_report')
def customer_report():
    # Get safe date range
    from_date, to_date = get_safe_date_range()
    user = current_user

    # ✅ Fetch Customer Sales for the logged-in user
    customer_sales = (
        db.session.query(Customer.id, Customer.name, sa.func.sum(Sale.total_amount).label("total_sales"))
        .join(Sale, Customer.id == Sale.customer_id)
        .filter(Sale.invoice_date.between(from_date, to_date))
        .filter(Sale.user_id == user.id)
        .group_by(Customer.id)
        .all()
    )

    # ✅ Fetch Payments Received for the logged-in user
    customer_payments = (
        db.session.query(Customer.id, sa.func.sum(AmountReceive.amount).label("total_payments"))
        .join(Sale, Customer.id == Sale.customer_id)
        .join(AmountReceive, Sale.id == AmountReceive.sale_id)
        .filter(AmountReceive.payment_date.between(from_date, to_date))
        .filter(Sale.user_id == user.id)
        .group_by(Customer.id)
        .all()
    )

    # ✅ Merge Data (Customer Sales and Payments)
    customer_data = {}
    for customer_id, customer_name, total_sales in customer_sales:
        customer_data[customer_id] = {"name": customer_name, "total_sales": total_sales, "total_payments": 0.0}

    for customer_id, total_payments in customer_payments:
        if customer_id in customer_data:
            customer_data[customer_id]["total_payments"] = total_payments
        else:
            customer_data[customer_id] = {"name": "", "total_sales": 0.0, "total_payments": total_payments}

    # ✅ Prepare customer report data
    customer_report_data = []
    for customer_id, data in customer_data.items():
        balance_due = data["total_sales"] - data["total_payments"]
        customer_report_data.append({
            "customer": data["name"],
            "total_sales": data["total_sales"],
            "total_payments": data["total_payments"],
            "balance_due": balance_due
        })

    return render_template('customer_report.html', customer_report=customer_report_data)



from flask_login import current_user

from datetime import datetime, timedelta
import csv
from flask import Response, request
from flask_login import login_required, current_user

@bp.route('/export_customer_csv')
@login_required
def export_customer_csv():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    user = current_user

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set default date range (last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # ✅ Fetch Customer Sales
    customer_sales = (
        db.session.query(Customer.id, Customer.name, sa.func.sum(Sale.total_amount).label("total_sales"))
        .join(Sale, Customer.id == Sale.customer_id)
        .filter(Sale.invoice_date.between(from_date, to_date))
        .filter(Sale.user_id == user.id)
        .group_by(Customer.id)
        .all()
    )

    # ✅ Fetch Payments Received
    customer_payments = (
        db.session.query(Customer.id, sa.func.sum(AmountReceive.amount).label("total_payments"))
        .join(Sale, Customer.id == Sale.customer_id)
        .join(AmountReceive, Sale.id == AmountReceive.sale_id)
        .filter(AmountReceive.payment_date.between(from_date, to_date))
        .filter(Sale.user_id == user.id)
        .group_by(Customer.id)
        .all()
    )

    # ✅ Merge Data
    customer_data = {}
    for customer_id, customer_name, total_sales in customer_sales:
        customer_data[customer_id] = {"name": customer_name, "total_sales": total_sales, "total_payments": 0.0}

    for customer_id, total_payments in customer_payments:
        if customer_id in customer_data:
            customer_data[customer_id]["total_payments"] = total_payments
        else:
            customer_data[customer_id] = {"name": "", "total_sales": 0.0, "total_payments": total_payments}

    # ✅ Build CSV data
    customer_report_data = []
    for customer_id, data in customer_data.items():
        balance_due = data["total_sales"] - data["total_payments"]
        customer_report_data.append([data["name"], data["total_sales"], data["total_payments"], balance_due])

    # ✅ Create CSV response
    response = Response(content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=customer_report.csv"
    csv_writer = csv.writer(response.stream)
    csv_writer.writerow(["Customer", "Total Sales", "Total Payments", "Balance Due"])
    for row in customer_report_data:
        csv_writer.writerow(row)

    return response





from flask_login import current_user

from datetime import datetime

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or date(2000, 1, 1)  # Default to a very early date
    to_date = parse_date_safe(raw_to) or date.today()  # Default to today
    return from_date, to_date

@bp.route('/stock_summary_report')
def stock_summary_report():
    # Get safe date range
    from_date, to_date = get_safe_date_range()
    user = current_user

    # ✅ Opening Stock - Only items for current user
    opening_stock = db.session.query(
        Item.id, Item.itemname, Item.stock_quantity
    ).filter(Item.user_id == user.id).all()

    # ✅ Purchases (Stock In)
    purchases = db.session.query(
        PurchaseItem.item_id, sa.func.sum(PurchaseItem.quantity).label("total_purchased")
    ).join(Purchase).filter(
        Purchase.invoice_date.between(from_date, to_date),
        Purchase.user_id == user.id
    ).group_by(PurchaseItem.item_id).all()

    # ✅ Sales (Stock Out)
    sales = db.session.query(
        SaleItem.item_id, sa.func.sum(SaleItem.quantity).label("total_sold")
    ).join(Sale).filter(
        Sale.invoice_date.between(from_date, to_date),
        Sale.user_id == user.id
    ).group_by(SaleItem.item_id).all()

    # Prepare purchase and sales data dictionaries
    purchase_data = {p.item_id: p.total_purchased for p in purchases}
    sales_data = {s.item_id: s.total_sold for s in sales}

    # Prepare stock summary
    stock_summary = []
    for item in opening_stock:
        purchased_qty = purchase_data.get(item.id, 0)
        sold_qty = sales_data.get(item.id, 0)
        closing_stock = item.stock_quantity + purchased_qty - sold_qty

        stock_summary.append({
            "Item": item.itemname,
            "Opening Stock": item.stock_quantity,
            "Purchased": purchased_qty,
            "Sold": sold_qty,
            "Closing Stock": closing_stock
        })

    return render_template('stock_summary_report.html', stock_summary=stock_summary)



from flask_login import current_user

from datetime import datetime, timedelta
import io
import csv
from flask import Response, request
from flask_login import login_required, current_user

@bp.route('/export_stock_summary_csv')
@login_required
def export_stock_summary_csv():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')
    user = current_user

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set a default date range if no valid dates are provided (e.g., last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # ✅ Opening Stock
    opening_stock = db.session.query(
        Item.id, Item.itemname, Item.stock_quantity
    ).filter(Item.user_id == user.id).all()

    # ✅ Purchases
    purchases = db.session.query(
        PurchaseItem.item_id, sa.func.sum(PurchaseItem.quantity).label("total_purchased")
    ).join(Purchase).filter(
        Purchase.invoice_date.between(from_date, to_date),
        Purchase.user_id == user.id
    ).group_by(PurchaseItem.item_id).all()

    # ✅ Sales
    sales = db.session.query(
        SaleItem.item_id, sa.func.sum(SaleItem.quantity).label("total_sold")
    ).join(Sale).filter(
        Sale.invoice_date.between(from_date, to_date),
        Sale.user_id == user.id
    ).group_by(SaleItem.item_id).all()

    # Creating dictionaries for purchased and sold quantities
    purchase_data = {p.item_id: p.total_purchased for p in purchases}
    sales_data = {s.item_id: s.total_sold for s in sales}

    # ✅ Prepare stock summary data
    stock_summary = []
    for item in opening_stock:
        purchased_qty = purchase_data.get(item.id, 0)
        sold_qty = sales_data.get(item.id, 0)
        closing_stock = item.stock_quantity + purchased_qty - sold_qty

        stock_summary.append([
            item.itemname,
            item.stock_quantity,
            purchased_qty,
            sold_qty,
            closing_stock
        ])

    # ✅ Prepare CSV Response
    response = Response(content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=stock_summary.csv"

    # Writing CSV content
    csv_writer = csv.writer(response.stream)
    csv_writer.writerow(["Item", "Opening Stock", "Purchased", "Sold", "Closing Stock"])
    csv_writer.writerows(stock_summary)

    return response



from datetime import datetime

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or datetime(2000, 1, 1).date()  # Default to a very early date
    to_date = parse_date_safe(raw_to) or datetime.today().date()  # Default to today
    return from_date, to_date

@bp.route('/item_wise_profit_loss')
@login_required
def item_wise_profit_loss():
    user = current_user  # ✅ Get current logged-in user

    # Get safe date range
    from_date, to_date = get_safe_date_range()

    # ✅ Fetch Sales Data
    sales = db.session.query(
        Item.id,
        Item.itemname,
        sa.func.sum(SaleItem.quantity).label("total_sold"),
        sa.func.sum(SaleItem.quantity * SaleItem.rate).label("total_revenue")
    ).join(SaleItem, SaleItem.item_id == Item.id) \
    .join(Sale, Sale.id == SaleItem.sale_id) \
    .filter(Sale.invoice_date.between(from_date, to_date)) \
    .group_by(Item.id, Item.itemname) \
    .all()

    # ✅ Fetch COGS Data
    cogs_data = db.session.query(
        PurchaseItem.item_id,
        sa.func.sum(PurchaseItem.quantity * PurchaseItem.unit_price).label("total_cogs")
    ).join(Purchase, Purchase.id == PurchaseItem.purchase_id) \
    .filter(Purchase.invoice_date.between(from_date, to_date)) \
    .group_by(PurchaseItem.item_id) \
    .all()

    # ✅ Convert COGS to dict
    cogs_dict = {c.item_id: c.total_cogs or 0 for c in cogs_data}

    # ✅ Prepare Final Data
    profit_loss_data = []
    for sale in sales:
        item_id = sale.id
        cogs = cogs_dict.get(item_id, 0)  # Default to 0 if no COGS found for item
        total_revenue = sale.total_revenue or 0
        total_sold = sale.total_sold or 0
        profit_loss = total_revenue - cogs

        profit_loss_data.append({
            "item": sale.itemname,
            "sold_quantity": total_sold,
            "total_revenue": total_revenue,
            "cogs": cogs,
            "profit_loss": profit_loss
        })

    return render_template(
        'item_wise_profit_loss.html',
        profit_loss_data=profit_loss_data,
        user=user,
        from_date=from_date,
        to_date=to_date
    )


from datetime import datetime
import io
import csv
from flask import Response, request
from flask_login import login_required

@bp.route('/export_item_profit_loss_csv')
@login_required
def export_item_profit_loss_csv():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set a default date range if no valid dates are provided (e.g., last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # ✅ Fetch Sales Data
    sales = db.session.query(
        Item.id,
        Item.itemname,
        sa.func.sum(SaleItem.quantity).label("total_sold"),
        sa.func.sum(SaleItem.quantity * SaleItem.rate).label("total_revenue")
    ).join(SaleItem, SaleItem.item_id == Item.id) \
    .join(Sale, Sale.id == SaleItem.sale_id) \
    .filter(Sale.invoice_date.between(from_date, to_date)) \
    .group_by(Item.id, Item.itemname) \
    .all()

    # ✅ Fetch COGS Data
    cogs_data = db.session.query(
        PurchaseItem.item_id,
        sa.func.sum(PurchaseItem.quantity * PurchaseItem.unit_price).label("total_cogs")
    ).join(Purchase, Purchase.id == PurchaseItem.purchase_id) \
    .filter(Purchase.invoice_date.between(from_date, to_date)) \
    .group_by(PurchaseItem.item_id) \
    .all()

    # ✅ Convert to dict for COGS data
    cogs_dict = {c.item_id: c.total_cogs or 0 for c in cogs_data}

    # ✅ Prepare CSV Output
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Item", "Sold Quantity", "Total Revenue", "COGS", "Profit/Loss"])

    for sale in sales:
        item_id = sale.id
        total_sold = sale.total_sold or 0
        total_revenue = sale.total_revenue or 0
        cogs = cogs_dict.get(item_id, 0)
        profit_loss = total_revenue - cogs

        writer.writerow([sale.itemname, total_sold, total_revenue, cogs, profit_loss])

    # ✅ Return CSV response
    response = Response(output.getvalue(), content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=item_profit_loss.csv"

    return response


from flask import render_template, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app import  db
from app.models import Sale, Customer
import sqlalchemy as sa

@bp.route('/gstr1_report')
@login_required
def gstr1_report():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    # Default date range: Last 30 days
    if not from_date or not to_date:
        to_date = datetime.today().strftime('%Y-%m-%d')
        from_date = (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d')

    from_date_parsed = datetime.strptime(from_date, '%Y-%m-%d')
    to_date_parsed = datetime.strptime(to_date, '%Y-%m-%d')

    # B2B Sales
    b2b_sales = db.session.query(
        Sale.id, Customer.gst, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter(
        Customer.gst != "",
        Sale.invoice_date.between(from_date_parsed, to_date_parsed)
    ).all()

    # B2C Large Sales (> 2.5 lakh)
    b2c_large_sales = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter(
        (Customer.gst == "") & (Sale.total_amount > 250000),
        Sale.invoice_date.between(from_date_parsed, to_date_parsed)
    ).all()

    # B2C Small Sales (<= 2.5 lakh)
    b2c_small_sales = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter(
        (Customer.gst == "") & (Sale.total_amount <= 250000),
        Sale.invoice_date.between(from_date_parsed, to_date_parsed)
    ).all()

    # Export Sales
    exports = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter(
        Customer.gst.startswith("EXP"),
        Sale.invoice_date.between(from_date_parsed, to_date_parsed)
    ).all()

    # Nil Rated/Exempted Sales
    nil_rated_sales = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount
    ).filter(
        Sale.tax_amount == 0,
        Sale.invoice_date.between(from_date_parsed, to_date_parsed)
    ).all()

    # Tax Summary
    tax_summary = db.session.query(
        sa.func.sum(Sale.cgst),
        sa.func.sum(Sale.sgst),
        sa.func.sum(Sale.igst)
    ).filter(
        Sale.invoice_date.between(from_date_parsed, to_date_parsed)
    ).first()

    return render_template(
        'gstr1_report.html',
        b2b_sales=b2b_sales,
        b2c_large_sales=b2c_large_sales,
        b2c_small_sales=b2c_small_sales,
        exports=exports,
        nil_rated_sales=nil_rated_sales,
        tax_summary=tax_summary,
        date_filter=f"{from_date} to {to_date}",
        user=current_user
    )


from datetime import datetime
import io
import csv
from flask import Response, request
from flask_login import login_required, current_user

@bp.route('/export_gstr1_csv')
@login_required
def export_gstr1_csv():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set a default date range if no valid dates are provided (e.g., last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # ✅ Fetching data
    b2b_sales = db.session.query(
        Sale.id, Customer.gst, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter(Customer.gst != "", Sale.invoice_date.between(from_date, to_date)).all()

    b2c_large_sales = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter((Customer.gst == "") & (Sale.total_amount > 250000), Sale.invoice_date.between(from_date, to_date)).all()

    b2c_small_sales = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter((Customer.gst == "") & (Sale.total_amount <= 250000), Sale.invoice_date.between(from_date, to_date)).all()

    exports = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount, Sale.tax_amount
    ).join(Customer).filter(Customer.gst.startswith("EXP"), Sale.invoice_date.between(from_date, to_date)).all()

    nil_rated_sales = db.session.query(
        Sale.id, Sale.invoice_date, Sale.total_amount
    ).filter(Sale.tax_amount == 0, Sale.invoice_date.between(from_date, to_date)).all()

    # ✅ Create CSV in Memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers for CSV
    writer.writerow(["Invoice Number", "GSTIN", "Invoice Date", "Total Amount", "Tax Amount"])

    # Write B2B Sales
    for sale in b2b_sales:
        writer.writerow([
            sale.id, 
            sale.gstin if sale.gstin else "N/A", 
            sale.invoice_date.strftime("%Y-%m-%d"),  # Safely format invoice_date
            f"{sale.total_amount:.2f}",
            f"{sale.tax_amount or 0:.2f}"
        ])

    # Write B2C Large Sales
    for sale in b2c_large_sales:
        writer.writerow([
            "", "", sale.invoice_date.strftime("%Y-%m-%d"),  # Safely format invoice_date
            f"{sale.total_amount:.2f}",
            f"{sale.tax_amount or 0:.2f}"
        ])

    # Write B2C Small Sales
    for sale in b2c_small_sales:
        writer.writerow([
            "", "", sale.invoice_date.strftime("%Y-%m-%d"),  # Safely format invoice_date
            f"{sale.total_amount:.2f}",
            f"{sale.tax_amount or 0:.2f}"
        ])

    # Write Exports
    for sale in exports:
        writer.writerow([
            "", "Export", sale.invoice_date.strftime("%Y-%m-%d"),  # Safely format invoice_date
            f"{sale.total_amount:.2f}",
            f"{sale.tax_amount or 0:.2f}"
        ])

    # Write Nil Rated Sales
    for sale in nil_rated_sales:
        writer.writerow([
            sale.id, "", sale.invoice_date.strftime("%Y-%m-%d"),  # Safely format invoice_date
            f"{sale.total_amount:.2f}",
            "0.00"  # Nil-rated sales have 0 tax amount
        ])

    # ✅ Send CSV Response
    response = Response(output.getvalue(), content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=gstr1_report.csv"
    return response


from flask import render_template, request
from flask_login import current_user  # ✅ import if using Flask-Login

from datetime import datetime

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or datetime(2000, 1, 1).date()  # Default to a very early date
    to_date = parse_date_safe(raw_to) or datetime.today().date()  # Default to today
    return from_date, to_date

@bp.route('/gstr2_report')
def gstr2_report():
    from_date, to_date = get_safe_date_range()  # Get safe date range
    user = current_user  # ✅ Get the logged-in user

    # ✅ Filter purchases by user if needed (example assumes `Purchase.user_id`)
    purchases = db.session.query(
        Purchase.id, Vendor.gstin, Purchase.invoice_date,
        Purchase.total_amount, Purchase.tax_amount, Purchase.cgst, Purchase.sgst, Purchase.igst
    ).join(Vendor).filter(
        Purchase.invoice_date.between(from_date, to_date),
        Purchase.user_id == user.id  # ✅ Filter by user if applicable
    ).all()

    # Check if no purchases are found and handle it accordingly
    if not purchases:
        flash('No purchases found for the selected date range.', 'info')

    return render_template('gstr2_report.html', purchases=purchases, user=user, from_date=from_date, to_date=to_date)


from flask import Response
from flask_login import current_user

from datetime import datetime
import io
import csv
from flask import Response, request

from flask_login import current_user

@bp.route('/export_gstr2_csv')
def export_gstr2_csv():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    user = current_user  # ✅

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set a default date range if no valid dates are provided (e.g., last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # ✅ Fetch GSTR2 Data (Purchases)
    gstr2_data = db.session.query(
        Purchase.id, Vendor.gstin, Purchase.invoice_date,
        Purchase.total_amount, Purchase.tax_amount, Purchase.cgst, Purchase.sgst, Purchase.igst
    ).join(Vendor).filter(
        Purchase.invoice_date.between(from_date, to_date),
        Purchase.user_id == user.id  # ✅ user-specific filter
    ).all()

    # ✅ Create CSV in Memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Invoice Number", "Vendor GSTIN", "Invoice Date", "Total Amount", "Tax Amount", "CGST", "SGST", "IGST"])

    for purchase in gstr2_data:
        writer.writerow([
            purchase.id,
            purchase.gstin if purchase.gstin else "N/A",
            purchase.invoice_date.strftime("%Y-%m-%d"),  # ✅ Safely format the date
            f"{purchase.total_amount:.2f}",
            f"{purchase.tax_amount or 0:.2f}",
            f"{purchase.cgst or 0:.2f}",
            f"{purchase.sgst or 0:.2f}",
            f"{purchase.igst or 0:.2f}"
        ])

    # ✅ Send CSV Response
    response = Response(output.getvalue(), content_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=gstr2_report.csv"
    return response



from flask import Flask, render_template, request, Response
import csv
import io

from flask_login import current_user

from datetime import datetime
from flask import flash

# Function to safely parse dates from request
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

# Function to return safe from_date and to_date
def get_safe_date_range():
    raw_from = request.args.get('from_date')
    raw_to = request.args.get('to_date')
    from_date = parse_date_safe(raw_from) or datetime(2000, 1, 1).date()  # Default to a very early date
    to_date = parse_date_safe(raw_to) or datetime.today().date()  # Default to today
    return from_date, to_date

@bp.route('/gstr3b_report')
def gstr3b_report():
    from_date, to_date = get_safe_date_range()  # Get safe date range
    
    # ✅ Fetch Sales Data
    sales_data = db.session.query(
        sa.func.sum(Sale.total_amount).label("total_sales"),
        sa.func.sum(Sale.tax_amount).label("output_gst")
    ).filter(Sale.invoice_date.between(from_date, to_date)).first()

    total_sales = sales_data.total_sales or 0.0
    output_gst = sales_data.output_gst or 0.0

    # ✅ Fetch Purchases Data
    purchase_data = db.session.query(
        sa.func.sum(Purchase.total_amount).label("total_purchases"),
        sa.func.sum(Purchase.tax_amount).label("input_gst")
    ).filter(Purchase.invoice_date.between(from_date, to_date)).first()

    total_purchases = purchase_data.total_purchases or 0.0
    input_gst = purchase_data.input_gst or 0.0

    # ✅ Net GST Payable
    gst_payable = output_gst - input_gst

    # Check if data is found and show flash message if no data found
    if total_sales == 0.0 and total_purchases == 0.0:
        flash('No data found for the selected date range.', 'info')

    return render_template(
        'gstr3b_report.html',
        total_sales=total_sales,
        output_gst=output_gst,
        total_purchases=total_purchases,
        input_gst=input_gst,
        gst_payable=gst_payable,
        user=current_user  # ✅ pass user
    )


from datetime import datetime, timedelta
import io
import csv
from flask import Response, request
from sqlalchemy import func

from flask_login import current_user

@bp.route('/gstr3b_report_csv')
def gstr3b_report_csv():
    from_date = request.args.get('from_date', '')
    to_date = request.args.get('to_date', '')

    # ✅ Validate and set default date range if empty or invalid
    def validate_date(date_str, default_date=None):
        try:
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
            return default_date
        except ValueError:
            return default_date

    # Set a default date range if no valid dates are provided (e.g., last 30 days)
    default_from_date = (datetime.now() - timedelta(days=30))
    default_to_date = datetime.now()

    from_date = validate_date(from_date, default_from_date)
    to_date = validate_date(to_date, default_to_date)

    # ✅ Fetch Sales Data (Output GST)
    sales_data = db.session.query(
        func.sum(Sale.total_amount).label("total_sales"),
        func.sum(Sale.tax_amount).label("output_gst")
    ).filter(Sale.invoice_date.between(from_date, to_date)).first()

    total_sales = sales_data.total_sales or 0.0
    output_gst = sales_data.output_gst or 0.0

    # ✅ Fetch Purchases Data (Input GST)
    purchase_data = db.session.query(
        func.sum(Purchase.total_amount).label("total_purchases"),
        func.sum(Purchase.tax_amount).label("input_gst")
    ).filter(Purchase.invoice_date.between(from_date, to_date)).first()

    total_purchases = purchase_data.total_purchases or 0.0
    input_gst = purchase_data.input_gst or 0.0

    # ✅ Net GST Payable
    gst_payable = output_gst - input_gst

    # ✅ CSV Creation
    output = io.StringIO()
    writer = csv.writer(output)

    # ✅ Write Metadata
    writer.writerow(["GSTR-3B Report"])
    writer.writerow(["From", from_date.strftime('%Y-%m-%d'), "To", to_date.strftime('%Y-%m-%d')])
    writer.writerow(["Generated by", current_user.username])  # ✅ Update with correct field
    writer.writerow([])

    # ✅ Write Data Header
    writer.writerow(["Total Sales", "Output GST", "Total Purchases", "Input GST", "Net GST Payable"])

    # ✅ Write Report Data
    writer.writerow([
        f"{total_sales:.2f}",
        f"{output_gst:.2f}",
        f"{total_purchases:.2f}",
        f"{input_gst:.2f}",
        f"{gst_payable:.2f}"
    ])

    # ✅ Send CSV Response
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=gstr3b_report.csv"
    return response



from functools import wraps
from flask import redirect, url_for, flash
from datetime import datetime

def payment_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main.login'))
        if not current_user.is_paid or (current_user.payment_expiry and current_user.payment_expiry < datetime.utcnow()):
            flash("Your subscription has expired. Please renew to access this feature.", "warning")
            return redirect(url_for('main.pricing'))  # your pricing page
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/premium-feature')
@login_required
@payment_required
def premium_feature():
    return render_template('premium.html')

import razorpay
from flask import current_app

@bp.route('/create_order', methods=['GET'])
@login_required
def create_order():
    client = razorpay.Client(auth=(current_app.config['RAZORPAY_KEY_ID'], current_app.config['RAZORPAY_KEY_SECRET']))

    # Create a Razorpay order
    payment = client.order.create({
        "amount": 10000,  # ₹100.00 in paise
        "currency": "INR",
        "receipt": f"order_rcptid_{current_user.id}",
        "notes": {"user_id": str(current_user.id)}
    })

    return render_template('pay.html', key_id=current_app.config['RAZORPAY_KEY_ID'], order=payment)

import hmac
import hashlib

@bp.route('/razorpay_webhook', methods=['POST'])
def razorpay_webhook():
    secret = current_app.config['RAZORPAY_KEY_SECRET']
    payload = request.data
    received_signature = request.headers.get('X-Razorpay-Signature')

    generated_signature = hmac.new(
        bytes(secret, 'utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(received_signature, generated_signature):
        data = request.get_json()
        user_id = data['payload']['payment']['entity']['notes']['user_id']
        user = User.query.get(int(user_id))
        user.is_paid = True
        user.payment_expiry = datetime.utcnow() + timedelta(days=30)
        db.session.commit()
        return jsonify({'status': 'success'}), 200

    return jsonify({'status': 'invalid signature'}), 400


@bp.route('/subscription', methods=['GET', 'POST'])
@login_required
def subscription():
    form = SubscriptionForm()  # Define the form

    if request.method == 'POST' and form.validate_on_submit():
        # Get the subscription type from the form
        subscription_type = form.subscription_type.data

        # Handle the subscription logic
        if subscription_type == 'monthly':
            current_user.subscription_type = 'monthly'
            current_user.subscription_active = True
            # Set up any other subscription logic like billing, etc.
        elif subscription_type == 'yearly':
            current_user.subscription_type = 'yearly'
            current_user.subscription_active = True
            # Set up yearly subscription logic

        db.session.commit()  # Commit the changes to the database

        flash("You have successfully subscribed!", "success")
        return redirect(url_for('main.index'))  # Redirect to another page (e.g., dashboard)

    # Render the subscription page with the form
    return render_template('subscription.html', form=form)

@bp.route('/terms')
def terms():
    return render_template('terms_and_conditions.html')


import razorpay
from flask import current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models import Subscription, db  # Replace with your actual import path

@bp.route('/subscribe', methods=['GET', 'POST'])
@login_required
def subscribe():
    if request.method == 'POST':
        plan = request.form.get('subscription_type')

        if not plan:
            flash("Please select a subscription plan.", "warning")
            return redirect(url_for('main.subscribe'))

        # Set plan pricing
        if plan == "monthly":
            amount_rupees = 150  # ₹150/month
            duration_days = 30
        elif plan == "yearly":
            amount_rupees = 1600  # ₹1600/year
            duration_days = 365
        else:
            flash("Invalid plan selected.", "danger")
            return redirect(url_for('main.subscribe'))

        # Create Razorpay order
        client = razorpay.Client(auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"]
        ))

        amount_paise = amount_rupees * 100  # Convert to paise
        payment = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })

        return render_template("checkout.html", 
            plan=plan, 
            amount=amount_rupees, 
            razorpay_key=current_app.config["RAZORPAY_KEY_ID"],
            order_id=payment['id']
        )

    return render_template("subscription.html")




import razorpay

@bp.route('/pay', methods=['GET'])
@login_required
def pay():
    client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY_ID", "YOUR_RAZORPAY_SECRET"))

    # Create Razorpay Order
    payment = client.order.create({
        "amount": 50000,  # ₹500.00 in paise
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template("checkout.html", 
                           order_id=payment['id'],
                           amount=50000,
                           key_id="YOUR_RAZORPAY_KEY_ID",
                           user=current_user)


import razorpay
from flask import request, redirect, url_for, flash
from datetime import datetime, timedelta

RAZORPAY_KEY_ID = "rzp_test_7bPWI4nWcRtQ0S"
RAZORPAY_SECRET = "hYKeEuVwpXXxAw1Vktyx14gT"

@bp.route('/subscription_success', methods=['POST', 'GET'])
@login_required
def subscription_success():
    if request.method == 'POST':
        try:
            # Get payment details from the POST request
            payment_id = request.form.get('razorpay_payment_id')
            order_id = request.form.get('razorpay_order_id')
            signature = request.form.get('razorpay_signature')

            # Verify the payment signature
            client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            client.utility.verify_payment_signature(params_dict)  # ✅ Raises error if invalid

            # ✅ Signature verified, activate subscription
            start = datetime.utcnow()
            end = start + timedelta(days=30)  # or 365 for yearly

            # Mark previous subscriptions inactive
            Subscription.query.filter_by(user_id=current_user.id).update({'is_active': False})

            # Create new subscription
            subscription = Subscription(
                user_id=current_user.id,
                plan_type='monthly',
                start_date=start,
                end_date=end,
                is_active=True
            )
            db.session.add(subscription)
            db.session.commit()

            flash("✅ Subscription activated successfully!", "success")
            return redirect(url_for('main.index'))

        except razorpay.errors.SignatureVerificationError:
            flash("❌ Payment verification failed!", "danger")
            return redirect(url_for('main.subscription'))

        except Exception as e:
            print("❌ Error:", e)
            flash("❌ Something went wrong during payment processing.", "danger")
            return redirect(url_for('main.subscription'))

    # Direct access without POST
    return redirect(url_for('main.subscription'))

@bp.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    plan = request.form.get('plan')
    order_id = request.form.get('razorpay_order_id')
    payment_id = request.form.get('razorpay_payment_id')
    signature = request.form.get('razorpay_signature')

    start = datetime.utcnow()
    end = start + timedelta(days=30 if plan == "monthly" else 365)

    # Mark old subscriptions inactive
    Subscription.query.filter_by(user_id=current_user.id).update({'is_active': False})

    new_subscription = Subscription(
        user_id=current_user.id,
        plan_type=plan,
        start_date=start,
        end_date=end,
        is_active=True
    )

    db.session.add(new_subscription)
    db.session.commit()

    flash("🎉 Subscription successful!", "success")
    return redirect(url_for('main.index'))


@bp.route('/terms_and_conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')


@bp.route('/contact')
def contact():
    return render_template('contact.html')


@bp.route('/cancellation_refund_policy')
def cancellation_refund_policy():
    return render_template('cancellation_refund_policy.html')


@bp.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')


@bp.route('/shipping_delivery')
def shipping_delivery():
    return render_template('shipping_delivery.html')


from flask import Blueprint, Response
import csv
import io


#### VOICE FILES / ROUTES are GOES HERE.....


@bp.route('/voice_add_item_ui')
@login_required
def voice_add_item_ui():
    lang = get_locale()  # or session.get('lang')
    t = get_translation_dict(lang)
    return render_template('voice/voice_add_item.html', t=t)


@bp.route('/voice_add_item', methods=['POST'])
@login_required
def voice_add_item():
    data = request.get_json()
    itemname = data.get('itemname')
    selling_price = data.get('selling_price')
    purchase_price = data.get('purchase_price')

    if itemname and selling_price:
        item = Item(
            itemname=itemname,
            selling_price=float(selling_price),
            purchase_price=float(purchase_price or 0),
            description='(added by voice)',
            hsn_code='',
            item_code='',
            category=None,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({'message': f"Item '{itemname}' added successfully."})

    return jsonify({'message': 'Item name and selling price are required.'}), 400


@bp.route('/voice_add_customer_ui')
@login_required
def voice_add_customer_ui():
    return render_template('voice/voice_add_customer.html')


@bp.route('/voice_add_customer', methods=['POST'])
@login_required
def voice_add_customer():
    data = request.get_json()
    name = data.get('customername', '').strip()
    mobile = data.get('mobile', '').replace(' ', '')[:10]  # 🔥 Strip spaces, limit to 10 digits
    email = data.get('email', '').strip()
    address = data.get('address', '').strip()

    if not name or not mobile:
        return jsonify({'message': 'Customer name and mobile are required.'}), 400

    new_customer = Customer(
        name=name,
        mobile=mobile,
        email=email,
        address=address,
        user_id=current_user.id
    )
    db.session.add(new_customer)
    db.session.commit()
    return jsonify({'message': f"Customer '{name}' added successfully."})



@bp.route('/voice_add_vendor_ui')
@login_required
def voice_add_vendor_ui():
    return render_template('voice/voice_add_vendor.html')


@bp.route('/voice_add_vendor', methods=['POST'])
@login_required
def voice_add_vendor():
    data = request.get_json()
    name = data.get('vendorname', '').strip()
    mobile = data.get('mobile', '').replace(' ', '')[:10]
    email = data.get('email', '').strip()
    address = data.get('address', '').strip()

    if not name or not mobile:
        return jsonify({'message': 'Vendor name and mobile are required.'}), 400

    new_vendor = Vendor(
        name=name,
        mobile=mobile,
        email=email,
        address=address,
        user_id=current_user.id
    )
    db.session.add(new_vendor)
    db.session.commit()
    return jsonify({'message': f"Vendor '{name}' added successfully."})


@bp.route('/voice_add_sale_ui')
@login_required
def voice_add_sale_ui():
    return render_template('voice/voice_add_sale.html')


@bp.route('/voice_add_sale', methods=['POST'])
@login_required
def voice_add_sale():
    data = request.get_json()
    print("Received JSON:", data)

    customername = data.get('customername')
    items = data.get('items', [])

    if not customername or not items:
        return jsonify({'message': 'Customer and at least one item are required.'}), 400

    user_id = current_user.id

    # Get or create customer
    customer = Customer.query.filter_by(name=customername, user_id=user_id).first()
    if not customer:
        customer = Customer(name=customername, user_id=user_id, mobile="NA")
        db.session.add(customer)
        db.session.flush()

    total_amount = 0.0
    sale = Sale(
        customer_id=customer.id,
        invoice_date=datetime.utcnow(),
        payment_terms=0,
        total_amount=0,
        balance_due=0,
        user_id=user_id
    )
    db.session.add(sale)
    db.session.flush()

    for item_data in items:
        itemname = item_data.get('itemname')
        quantity = float(item_data.get('quantity') or 0)
        rate = float(item_data.get('rate') or 0)
        tax_percent = float(item_data.get('tax_percent') or 0)

        if not itemname or quantity <= 0 or rate <= 0:
            continue  # skip invalid entries

        # Get or create item
        item = Item.query.filter_by(itemname=itemname, user_id=user_id).first()
        if not item:
            item = Item(itemname=itemname, selling_price=rate, user_id=user_id, stock_quantity=0)
            db.session.add(item)
            db.session.flush()

        subtotal = quantity * rate
        tax_value = subtotal * (tax_percent / 100)
        total = subtotal + tax_value
        total_amount += total

        sale_item = SaleItem(
            sale_id=sale.id,
            item_id=item.id,
            quantity=quantity,
            rate=rate,
            subtotal=subtotal,
            tax_percent=tax_percent,
            tax_value=tax_value,
            total_amount=total,
            user_id=user_id
        )
        db.session.add(sale_item)

        # Reduce stock
        item.stock_quantity -= quantity
        db.session.add(item)

    sale.total_amount = round(total_amount, 2)
    sale.balance_due = round(total_amount, 2)
    db.session.add(sale)
    db.session.commit()

    return jsonify({'message': f"✅ Sale added for {customername} with {len(items)} item(s)."}), 200


@bp.route('/voice_add_purchase_ui')
@login_required
def voice_add_purchase_ui():
    return render_template("voice/voice_add_purchase.html", t=get_translation_dict(session.get('lang', 'en')))


@bp.route('/voice_add_purchase', methods=['POST'])
@login_required
def voice_add_purchase():
    if not check_active_subscription():
        return jsonify({'message': '❌ Subscription required'}), 403

    data = request.get_json()
    if not data or 'vendorname' not in data or 'items' not in data:
        return jsonify({'message': '❌ Invalid input'}), 400

    vendorname = data['vendorname'].strip()
    items = data['items']
    user_id = current_user.id

    if not vendorname or not items:
        return jsonify({'message': '❌ Vendor and at least one item required'}), 400

    # ✅ Helper to parse numeric strings like "$10", "12%", " 15 "
    def parse_float(value):
        try:
            return float(str(value).replace('%', '').replace('$', '').strip())
        except (ValueError, TypeError):
            return 0.0

    # 🔍 Find or create vendor
    vendor = Vendor.query.filter_by(name=vendorname, user_id=user_id).first()
    if not vendor:
        vendor = Vendor(name=vendorname, user_id=user_id, mobile='NA')
        db.session.add(vendor)
        db.session.commit()

    # 🧾 Create Purchase
    total_purchase_amount = 0.0
    purchase = Purchase(
        vendor_id=vendor.id,
        payment_terms='30',
        total_amount=0.0,
        balance_due=0.0,
        invoice_date=datetime.utcnow(),
        user_id=user_id
    )
    db.session.add(purchase)
    db.session.flush()

    purchase_items = []

    for i, item_data in enumerate(items):
        try:
            itemname = item_data.get('itemname', '').strip()
            quantity = parse_float(item_data.get('quantity'))
            rate = parse_float(item_data.get('rate'))
            tax_percent = parse_float(item_data.get('tax_percent'))

            if not itemname or quantity <= 0 or rate <= 0:
                continue  # skip invalid items

            # 🧠 Find or create item
            item = Item.query.filter_by(itemname=itemname, user_id=user_id).first()
            markup = current_user.default_markup_percent or 10.0

            if not item:
                item = Item(
                    itemname=itemname,
                    purchase_price=rate,
                    selling_price=round(rate * (1 + markup / 100), 2),
                    stock_quantity=quantity,
                    user_id=user_id,
                    created_date=datetime.utcnow(),
                    markup_percent=markup,
                    tax_percent=tax_percent
                )
                db.session.add(item)
                db.session.flush()
            else:
                item.purchase_price = rate
                item.selling_price = round(rate * (1 + markup / 100), 2)
                item.markup_percent = markup
                item.tax_percent = tax_percent
                item.stock_quantity += quantity
                db.session.add(item)

            # 📦 Log item movement
            db.session.add(ItemMovement(
                item_id=item.id,
                movement_type="Purchase",
                quantity=quantity,
                movement_date=datetime.utcnow(),
                user_id=user_id
            ))

            # ⚠️ Low stock alert
            if item.stock_quantity < LOW_STOCK_THRESHOLD:
                db.session.add(StockNotification(
                    item_id=item.id,
                    message=f"Only {item.stock_quantity} left.",
                    created_at=datetime.utcnow(),
                    user_id=user_id
                ))

            # ➕ Create PurchaseItem
            subtotal = quantity * rate
            tax_value = subtotal * (tax_percent / 100)
            total = subtotal + tax_value
            total_purchase_amount += total

            purchase_items.append(PurchaseItem(
                purchase_id=purchase.id,
                item_id=item.id,
                quantity=quantity,
                rate=rate,
                subtotal=subtotal,
                tax_percent=tax_percent,
                tax_value=tax_value,
                total_amount=total,
                user_id=user_id
            ))
        except Exception as e:
            print(f"Error processing item {i + 1}: {e}")

    purchase.total_amount = round(total_purchase_amount, 2)
    purchase.balance_due = round(total_purchase_amount, 2)
    db.session.add_all(purchase_items)
    db.session.commit()

    return jsonify({'message': '✅ Purchase added successfully'})


@bp.route('/voice_add_expense_ui')
@login_required
def voice_add_expense_ui():
    return render_template("voice/voice_add_expense.html", t=get_translation_dict(session.get('lang', 'en')))


@bp.route('/voice_add_expense', methods=['POST'])
@login_required
def voice_add_expense():
    if not check_active_subscription():
        return jsonify({'message': '❌ Subscription required'}), 403

    data = request.get_json()
    category = data.get('category', '').strip()
    items = data.get('items', [])
    payment_type = data.get('payment_type', 'Cash').strip().title()

    if not category or not items:
        return jsonify({'message': '❌ Category and items required'}), 400

    def to_float(val):
        try:
            return float(str(val).replace('%', '').replace('₹', '').strip())
        except:
            return 0.0

    user_id = current_user.id

    # ✅ Get or create expense category
    category_obj = ExpenseCategory.query.filter_by(name=category, user_id=user_id).first()
    if not category_obj:
        category_obj = ExpenseCategory(name=category, user_id=user_id)
        db.session.add(category_obj)
        db.session.commit()

    # ✅ Create base Expense record
    expense = Expense(
        user_id=user_id,
        expcat_id=category_obj.id,
        payment_type=payment_type,
        total_amount=0.0
    )
    db.session.add(expense)
    db.session.flush()  # Get expense.id

    total_expense_amount = 0.0

    for item_data in items:
        itemname = item_data.get('itemname', '').strip()
        quantity = to_float(item_data.get('quantity'))
        rate = to_float(item_data.get('rate'))

        if not itemname or quantity <= 0 or rate <= 0:
            continue

        amount = quantity * rate

        expense_item = ExpenseItem(
            expense_id=expense.id,
            user_id=user_id,
            itemname=itemname,
            quantity=quantity,
            rate=rate,
            amount=amount,
            total_amount=amount,
            expense_date=datetime.utcnow()
        )

        total_expense_amount += amount
        db.session.add(expense_item)

    expense.total_amount = total_expense_amount
    db.session.commit()

    return jsonify({'message': '✅ Voice Expense added successfully!'})

@bp.route('/voice_add_estimate_ui')
@login_required
def voice_add_estimate_ui():
    return render_template("voice/voice_add_estimate.html")

@bp.route('/voice_add_estimate', methods=['POST'])
@login_required
def voice_add_estimate():
    if not check_active_subscription():
        return jsonify({'message': '❌ Subscription required'}), 403

    data = request.get_json()
    if not data or 'customername' not in data or 'items' not in data:
        return jsonify({'message': '❌ Invalid input'}), 400

    customername = data['customername'].strip()
    items = data['items']
    user_id = current_user.id

    if not customername or not items:
        return jsonify({'message': '❌ Customer and items required'}), 400

    def parse_float(val):
        try:
            return float(str(val).replace('%', '').replace('$', '').strip())
        except Exception:
            return 0.0

    # ✅ Get or create customer
    customer = Customer.query.filter_by(name=customername, user_id=user_id).first()
    if not customer:
        customer = Customer(name=customername, user_id=user_id, mobile='NA')
        db.session.add(customer)
        db.session.commit()

    # ✅ Auto-generate estimate number like EST-0001
    last_estimate = Estimate.query.filter_by(user_id=user_id).order_by(Estimate.id.desc()).first()
    if last_estimate and last_estimate.estimate_number:
        try:
            last_number = int(str(last_estimate.estimate_number).replace('EST-', ''))
        except:
            last_number = 0
    else:
        last_number = 0
    next_number = last_number + 1
    estimate_number = f"EST-{next_number:04d}"

    # ✅ Create new Estimate
    estimate = Estimate(
        estimate_number=estimate_number,
        customer_id=customer.id,
        date=datetime.utcnow(),
        total_amount=0.0,
        status="Estimate",
        user_id=user_id
    )
    db.session.add(estimate)
    db.session.flush()

    total_amount = 0.0
    estimate_items = []

    for item_data in items:
        itemname = item_data.get('itemname', '').strip()
        quantity = parse_float(item_data.get('quantity'))
        rate = parse_float(item_data.get('rate'))
        tax = parse_float(item_data.get('tax_percent'))

        if not itemname or quantity <= 0 or rate <= 0:
            continue

        # ✅ Get or create Item
        item = Item.query.filter_by(itemname=itemname, user_id=user_id).first()
        if not item:
            item = Item(
                itemname=itemname,
                user_id=user_id,
                purchase_price=rate,
                selling_price=rate,
                stock_quantity=0,
                created_date=datetime.utcnow(),
                markup_percent=0,
                tax_percent=tax
            )
            db.session.add(item)
            db.session.flush()

        subtotal = quantity * rate
        tax_amount = subtotal * (tax / 100)
        total = subtotal + tax_amount
        total_amount += total

        estimate_item = EstimateItem(
            estimate_id=estimate.id,
            item_id=item.id,
            quantity=quantity,
            price=rate,
            subtotal=subtotal,
            tax_percent=tax,
            tax_value=tax_amount
        )
        estimate_items.append(estimate_item)

    estimate.total_amount = round(total_amount, 2)
    db.session.add_all(estimate_items)
    db.session.commit()

    return jsonify({'message': f'✅ Estimate {estimate.estimate_number} created successfully'})


@bp.route('/select_mode')
def select_mode():
    return render_template('select_mode.html')

@bp.route('/set_mode/<mode>')
def set_mode(mode):
    if mode not in ['manual', 'voice']:
        return redirect(url_for('main.select_mode'))
    
    session['mode'] = mode
    
    # Redirect to your main dashboard (change this if needed)
    return redirect(url_for('main.index'))
