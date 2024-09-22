from faker import Faker
import MySQLdb

# Initialize Faker object
fake = Faker()

# Connect to MySQL database
db = MySQLdb.connect(
    host="localhost",
    user="root",
    passwd="7756",
    db="user_db"
)
cursor = db.cursor()

# Function to create dummy products
def create_dummy_products(n):
    for _ in range(n):
        product_name = fake.word().capitalize() + ' ' + fake.word().capitalize()  # Random product name
        description = fake.sentence(nb_words=10)  # Random product description
        price = round(fake.random_number(digits=5), 2)  # Random price
        category = fake.word().capitalize()  # Random category (could be Guitar, Amp, etc.)
        
        # SQL insert query
        query = '''
        INSERT INTO products (name, description, price, category)
        VALUES (%s, %s, %s, %s)
        '''
        
        # Execute query
        cursor.execute(query, (product_name, description, price, category))

    db.commit()

# Generate and insert 100 dummy products
create_dummy_products(100)

# Close the connection
cursor.close()
db.close()
