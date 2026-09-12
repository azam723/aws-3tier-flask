import os
import psycopg2


connection = psycopg2.connect(
    host=os.environ["DB_HOST"],
    port=os.environ.get("DB_PORT", "5432"),
    database=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
)

cursor = connection.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE
    );
    """
)

cursor.execute(
    """
    INSERT INTO users (name, email)
    VALUES
        ('Alice', 'alice@example.com'),
        ('Bob', 'bob@example.com')
    ON CONFLICT (email) DO NOTHING;
    """
)

connection.commit()

cursor.close()
connection.close()

print("Database initialized successfully.")
