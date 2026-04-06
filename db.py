from mysql.connector import Error, pooling

from config import Config


connection_pool = None


def get_pool():
    global connection_pool

    if connection_pool is None:
        # A small connection pool is enough for this mini project.
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="municipal_tax_pool",
            pool_size=5,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
        )

    return connection_pool


def get_connection():
    # Every database helper asks the pool for a fresh connection.
    return get_pool().get_connection()


def fetch_all(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def fetch_one(query, params=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def execute_query(query, params=None, many=False):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        if many:
            cursor.executemany(query, params or [])
        else:
            cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid
    except Error:
        # Rollback keeps the database safe if an insert or update fails.
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def call_procedure(name, args):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Stored procedures are used for tax generation logic.
        cursor.callproc(name, args)
        connection.commit()
        results = []
        for stored_result in cursor.stored_results():
            results.extend(stored_result.fetchall())
        return results
    finally:
        cursor.close()
        connection.close()
