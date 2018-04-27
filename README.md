# Item Catalog

# Setup:

* Clone or [download] the repo: `https://github.com/skphi13/catalog.git`
* Install (if necessary): 
  * [Flask](http://flask.pocoo.org/docs/0.11/installation/)
  * [SQLAlchemy](http://docs.sqlalchemy.org/en/latest/intro.html)

# Running:

1. Open terminal to folder location of cloned repo.
2. Run database_setup_catalog.py: `python database_setup_catalog.py`
3. Run database_management.py: `python database_management.py`
4. Run catalog.py to start web app: `python catalog.py`
5. Open browser to [http://localhost:5000/category/](http://localhost:5000/category/)


## Expected functionality:
* Users can login / logout with FB or Google Plus sign in.
* Users cannot Get or Post New, Edit, or Delete pages without being signed in.
* Users cannot Get or Post Edit or Delete game items without being the original creators of the title.
* Logged in users can create new movie title.

