import sqlalchemy as sa
import sqlalchemy.orm as so
from app import create_app, db
from app.models import Customer, Item, Category, User

app=create_app()

@app.shell_context_processor
def make_shell_contect():
	return {'sa':sa, 'so':so, 'db':db, 'User':User, 'Customer':Customer, 'Items': Item, 'Category': Category}
