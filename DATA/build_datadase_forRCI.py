#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

# --------- CONFIG ----------
DATA_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "TABLE"
DB_PATH = Path("data.db")

# ---------- CLEANING HELPERS ----------
HIDDEN_CHARS = {
    "\u200b",  # zero width space
    "\ufeff",  # BOM
    "\u00a0",  # non-breaking space
}

def clean_text(x):
    """Remove hidden Unicode, normalize internal whitespace, strip."""
    if pd.isna(x):
        return x
    s = str(x)
    for ch in HIDDEN_CHARS:
        s = s.replace(ch, "")
    return " ".join(s.split()).strip()

def clean_df_text_columns(df, cols):
    """Apply clean_text to a list of columns if present."""
    for c in cols:
        if c in df.columns:
            df[c] = df[c].apply(clean_text)
    return df

def standardize_date(date_val):
    """Standardize various date formats to YYYY-MM-DD"""
    if pd.isna(date_val):
        return None
    
    try:
        # If it's already a datetime object
        if isinstance(date_val, (pd.Timestamp, datetime)):
            return date_val.strftime('%Y-%m-%d')
        
        # Convert to string and clean
        date_str = clean_text(str(date_val))
        
        # Try different date formats
        date_formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
            '%Y/%m/%d', '%d-%m-%Y', '%Y%m%d',
            '%d/%m/%y', '%m/%d/%y', '%y/%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try pandas to_datetime as fallback
        return pd.to_datetime(date_val, errors='coerce').strftime('%Y-%m-%d')
    except:
        return None

def to_numeric_safe(val):
    """Convert to numeric, return NaN if conversion fails"""
    try:
        if pd.isna(val):
            return np.nan
        return float(val)
    except:
        return np.nan

# ---------- GENERIC LOAD FUNCTION ----------
def load_excel_file(file_path):
    """Generic function to load any Excel file with consistent cleaning"""
    try:
        print(f"Loading: {file_path.name}")
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Debug: Print initial data info
        print(f"  Initial data shape: {df.shape}")
        print(f"  Columns found: {df.columns.tolist()}")
        
        # Clean column names
        df.columns = [clean_text(str(c)) for c in df.columns]
        
        # Replace empty strings with NaN
        df = df.replace({r'^\s*$': np.nan}, regex=True)
        
        # Clean text columns
        text_cols = df.select_dtypes(include=['object']).columns
        df = clean_df_text_columns(df, text_cols)
        
        print(f"  Successfully loaded {len(df)} records")
        return df
        
    except Exception as e:
        print(f"  Error loading {file_path.name}: {e}")
        return pd.DataFrame()

def load_all_excel_files():
    """Load all Excel files from the TABLE directory"""
    print("Loading all Excel files from TABLE directory...")
    
    # Check if TABLE directory exists
    if not DATA_DIR.exists():
        print(f"ERROR: TABLE directory does not exist: {DATA_DIR.resolve()}")
        return {}
    
    print(f"Looking for Excel files in: {DATA_DIR.resolve()}")
    
    # Find all Excel files
    excel_files = list(DATA_DIR.glob("*.xlsx")) + list(DATA_DIR.glob("*.xls"))
    
    if not excel_files:
        print("No Excel files found in TABLE directory")
        return {}
    
    print(f"Found {len(excel_files)} Excel files:")
    for file in excel_files:
        print(f"  - {file.name}")
    
    # Load all files
    dataframes = {}
    
    for excel_file in excel_files:
        # Use filename without extension as table name
        table_name = excel_file.stem.upper()
        df = load_excel_file(excel_file)
        
        if not df.empty:
            dataframes[table_name] = df
            print(f"  ✅ {table_name}: {len(df)} records loaded")
        else:
            print(f"  ❌ {table_name}: Failed to load or empty")
    
    return dataframes

# ---------- DB CREATION ----------
def create_database(dataframes_dict):
    """Create SQLite database with all tables"""
    print("\nCreating database...")
    
    if not dataframes_dict:
        print("No data to create database with")
        return
    
    # Remove existing database
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Removed existing database")
    
    # Create connection
    conn = sqlite3.connect(DB_PATH)
    
    try:
        tables_created = 0
        
        # Create table for each dataframe
        for table_name, df in dataframes_dict.items():
            if not df.empty:
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                tables_created += 1
                print(f"  ✅ {table_name} table created: {len(df)} records")
        
        print(f"\nTotal tables created: {tables_created}")
        
        # Create some useful indexes (you can customize this based on your data)
        cursor = conn.cursor()
        
        # Example: Create indexes on common columns if they exist
        for table_name in dataframes_dict.keys():
            try:
                # Check if common columns exist and create indexes
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Create indexes on common ID or date columns
                for col in columns:
                    col_lower = col.lower()
                    if any(keyword in col_lower for keyword in ['id', 'date', 'time']):
                        try:
                            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{col} ON {table_name}({col})")
                            print(f"    Index created on {table_name}.{col}")
                        except:
                            pass  # Skip if index creation fails
            except:
                pass  # Skip if table doesn't exist or other error
        
        conn.commit()
        print("Database creation completed successfully")
        
    except Exception as e:
        print(f"Error creating database: {e}")
        
    finally:
        conn.close()

# ---------- MAIN ----------
def main():
    print("=== Generic Excel to SQLite Database Builder ===")
    print(f"Data directory: {DATA_DIR.resolve()}")
    print(f"Output database: {DB_PATH.resolve()}")
    print()
    
    # Load all Excel files from DATA directory
    all_dataframes = load_all_excel_files()
    
    # Summary
    print(f"\nData Summary:")
    total_records = 0
    for table_name, df in all_dataframes.items():
        record_count = len(df)
        total_records += record_count
        print(f"  {table_name}: {record_count} records")
    
    print(f"  Total records across all tables: {total_records}")
    
    if not all_dataframes:
        print("\n❌ No data loaded. Please check your TABLE directory and Excel files.")
        return
    
    # Create database
    create_database(all_dataframes)
    
    print(f"\n✅ Database created successfully: {DB_PATH.resolve()}")
    
    # Quick validation
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Tables in database: {[table[0] for table in tables]}")
        
        # Show record count for each table
        print(f"\nRecord counts in database:")
        for table_name, in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} records")
        
        conn.close()
        
    except Exception as e:
        print(f"Error validating database: {e}")

if __name__ == "__main__":
    main()