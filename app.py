from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '7756'
app.config['MYSQL_DB'] = 'user_db'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST' and all(field in request.form for field in ('name', 'email', 'password')):
        username = request.form['name']  # Store form input 'name' as 'username'
        email = request.form['email']
        password = request.form['password']

        # Input validation
        if not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!', 'danger')
        elif not re.match(r'[A-Za-z0-9]+', username):  # Use 'username' in regex validation
            flash('Username must contain only characters and numbers!', 'danger')
        elif not username or not email or not password:
            flash('Please fill out the form!', 'danger')
        else:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cursor.fetchone()

            if account:
                flash('Account already exists!', 'danger')
            else:
                hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
                cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)', (username, email, hashed_password))
                mysql.connection.commit()
                flash('You have successfully registered!', 'success')
                return redirect(url_for('login'))  # Redirect to login page

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and all(field in request.form for field in ('email', 'password')):
        email = request.form['email']
        password = request.form['password']
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()  # Use cursor.fetchone() instead of db.execute

        if account and check_password_hash(account['password'], password):
            session['user_id'] = account['id']
            flash('Login successful!', 'success')
            return redirect(url_for('products'))  # Redirect to products page
        else:
            flash('Invalid credentials!', 'danger')

    return render_template('login.html')


@app.route('/products', methods=['GET'])
def products():
    user_id = session.get('user_id')
    search_query = request.args.get('search', '')
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if search_query:
        cursor.execute('SELECT * FROM products WHERE name LIKE %s', ('%' + search_query + '%',))
        product_list = cursor.fetchall()
    else:
        cursor.execute('SELECT * FROM products')
        product_list = cursor.fetchall()
    
    recommended_products = get_recommendations(user_id) if user_id else []

    return render_template('products.html', products=product_list, recommended=recommended_products)

@app.route('/view_product/<int:product_id>')
def view_product(product_id):
    user_id = session.get('user_id')
    if user_id:
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO user_views (user_id, product_id) VALUES (%s, %s)', (user_id, product_id))
        mysql.connection.commit()
    
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    return render_template('view_product.html', product=product)

def get_recommendations(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute('''
        SELECT p.category FROM user_views uv
        JOIN products p ON uv.product_id = p.id
        WHERE uv.user_id = %s
        ORDER BY uv.timestamp DESC
        LIMIT 1
    ''', (user_id,))
    
    recent_category = cursor.fetchone()
    
    if recent_category:
        cursor.execute('''
            SELECT * FROM products 
            WHERE category = %s AND id NOT IN (
                SELECT product_id FROM user_views WHERE user_id = %s
            )
            LIMIT 4
        ''', (recent_category['category'], user_id))
    else:
        cursor.execute('SELECT * FROM products ORDER BY RAND() LIMIT 4')
    
    return cursor.fetchall()

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    recommended_products = get_recommendations(user_id) if user_id else []

    return render_template('dashboard.html', recommended_products=recommended_products)

@app.route('/search_suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('query', '').lower()
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch products matching the query
    cursor.execute('SELECT * FROM products WHERE LOWER(name) LIKE %s LIMIT 5', ('%' + query + '%',))
    results = cursor.fetchall()

    # Optional: Fetch recommendations based on some criteria (e.g., popular products)
    recommendations = []  # Replace with your logic to get recommendations

    return {
        'results': results,
        'recommendations': recommendations
    }

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
