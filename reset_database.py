from database.db_manager import DatabaseManager

# Use your PostgreSQL connection string
conn_str = "postgresql://neondb_owner:npg_R81aBEUPvtMC@ep-fragrant-tooth-a1j6h75o-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# 1. Connect to the database
db = DatabaseManager(conn_str)

# 2. Drop and recreate tables (implement drop/create logic in create_tables)
db.create_tables()
print("New PostgreSQL database and tables created successfully.")