# Restaurant Menu App

[![N|Solid](https://cldup.com/dTxpPi9lDf.thumb.png)](https://nodesource.com/products/nsolid)

Restaurant Menu App is a CRUD catalog app with regard to Restaurant and Menu management powered by Python and HTML, Bootstrap and Javascript.

  - View Restaurant catalog
  - Create, Read, Update, and Delete Restaurants 
  - View Menu Items catalog
  - Create, Read, Update, and Delete Menu Items 
  - View JSON catalog information for Restaurants and Menu Items

### Tech

Restaurant Menu App uses a number of open source projects to work properly:

* [Flask](http://flask.pocoo.org/) - a microframework for Python based on Werkzeug, Jinja 2 and good intentions.
* [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit and Object Relational Mapper that gives application developers the full power and flexibility of SQL.
* [oauth2client](https://oauth2client.readthedocs.io/en/latest/) - Markdown parser done right. Fast and easy to extend.
* [JSON](https://www.json.org/) - (JavaScript Object Notation) is a lightweight data-interchange format. 
* [Bootstrap](https://getbootstrap.com/docs/3.3/) - (v3.3.7) - most popular HTML, CSS, and JS framework for developing responsive, mobile first projects on the web.
* [jQuery](https://jquery.com/) - fast, small, and feature-rich JavaScript library.

### Get Started
First, run the `database_setup.py` file to create the table infrastructure to use for this project.  
```sh
python database_setup.py
```
The restaurant, menu_item and user tables will be created.

Second, run the `lotsofmenus.py` file to load the database with example data if needed.
```sh
python lotsofmenus.py
```

Once done with the above, run the `restaurantmenu.py` file.  This will run the actual project as a debug server.

```sh
python restaurantmenu.py
```

Verify the deployment by navigating to your server address in your preferred browser.

```sh
127.0.0.1:5000
```

[example](example.png)]
