import os
import json
import re
import sqlite3
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

# =========================
# Env & Model Initialization
# =========================
load_dotenv()

WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
if not WATSONX_PROJECT_ID or not WATSONX_API_KEY:
    raise RuntimeError("Missing WATSONX_PROJECT_ID or WATSONX_API_KEY in environment.")

credentials = Credentials(url="https://us-south.ml.cloud.ibm.com", api_key=WATSONX_API_KEY)

model = ModelInference(
    model_id="openai/gpt-oss-120b",
    params={
        "frequency_penalty": 0,
        "max_tokens": 2000,
        "presence_penalty": 0,
        "temperature": 0,
        "top_p": 1,
    },
    credentials=credentials,
    project_id=WATSONX_PROJECT_ID,
)

# =========================
# SQLite (school.db)
# =========================
DB_PATH = os.getenv("DB_PATH", "../DATA/data.db")

def _connect_db() -> sqlite3.Connection:
    # Thread-safe for FastAPI dev; set row_factory for dict-like rows
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

db_conn = _connect_db()

def run_select(sql: str) -> Dict[str, Any]:
    """
    Execute a SELECT-only SQL statement and return rows + columns.
    """
    # Basic safety: only allow SELECT; no multiple statements
    stripped = sql.strip().rstrip(";").lstrip("(").strip()  # tolerate surrounding parens
    if not stripped.lower().startswith("select"):
        raise HTTPException(status_code=400, detail=f"Only SELECT queries are allowed. SQL: {sql}")
    if ";" in sql.strip().rstrip(";"):
        raise HTTPException(status_code=400, detail="Multiple statements are not allowed.")

    try:
        cur = db_conn.execute(sql)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = [dict(row) for row in cur.fetchall()]
        return {"columns": cols, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL execution error: {e}")

# =========================
# Prompt Templates
# =========================
SQL_GENERATION_PROMPT = """
You are a senior SQL expert. Convert the user's natural language question into a SQL query for a SQLite database with this schema:

TABLE SALES_LOGISTICS (
    SalesOrder,               -- Sales Order Number
    SalesType,               -- Refers to the abbreviation for type of Sales Order (e.g., 'ZODM': domestic, 'ZOEX': international)
    OverallStatus,         -- Overall Status of the Sales Order (e.g., 'A': Completed and 'B': Incomplete)
    SalesDate2,            -- Sales Order Date as a format: YYYY-MM-DD (e.g, 2023-12-31)
    Plant,                 -- Plant code (e.g., ''1000': RC and '1100': Food, '2000': RMP)	
    PuchaseOrder,           -- Puchase Order Number, PO Number. 
    LineItemNo,             -- consists of sequence item in Sales Order. 	
    OrderQty,              -- Order Quantity
    DeliveryQty,           -- Delivery Quantity
    OpenQty,               -- consists of outstanding balance
    SalesUnit,            -- Sales Unit of Measure (e.g., 'PCS': pieces, 'SET': set, 'SH': sheet)
    RequestedDlDate2,          -- Date the customer wants to receive the item as a format: YYYY-MM-DD (e.g, 2023-12-31)
    NameSoldtoParty,         -- Name of the Sold-to Party (Customer name)	
    NameEmployee,          -- Name of the Employee who created the Sales Order
    PurchaseOrderDate2,       -- Date of the Purchase Order as a format: YYYY-MM-DD (e.g, 2023-12-31)
    Currency,             -- Currency (e.g., 'THB': Thai Baht, 'USD': US Dollar)
    DeliveryStatus,       -- Delivery or Shipping status (e.g., 'A': Completed and 'B': not yet sent)
    ShiptoParty,            -- Shipping Location (Customer code)	
    uploaded           -- Date the record was uploaded to the database as a format: YYYY-MM-DD (e.g, 2023-12-31)
);


TABLE MATERIAL_MANUFACTURING (
SalesOrder,             -- Sales Order Number
MG2,                  -- '3PC': 3 piece can, 'END': normal cap or shell cap, 'EOE': easy to open cap, 'POE': quick peel cap, 'EOS': Spoon cap, '2PC': 2 piece can, 'SOT': Stay On Tab
Material1,          -- Material Number code,
MaterialDes,       -- Material Description or name of material
Uom,              -- Unit of Measure code (e.g., 'PCS': Piece, 'BLK': Blank, 'SET': Set, 'ST': Strip, 'SH': Shearline Sheet, 'SHT': Sheet of Color printing coating
MatGroup1,         -- Material Group, Types of Steel (Note: 'A': Aluminum and 'L': Laminate and 'S': Steel)
MatGroup3,      -- Material Group 3, Types of Can Size, Lid Size
MatGroup4,    -- Material Group 4, '1': Color Printing, '2': No Color Printing, '999': Other Jobs, 'OEM': Contract Jobs, 'Z01': Claim Jobs
PricingUnit,       -- Price per unit. 
NetPrice        -- Net Price
);

TABLE WAREHOUSE_STOCK (
SalesOrder,        -- Sales Order Number
Sloc,          -- Storage Location
GoodRecipient,         -- Good Recipient Number
Batch,        -- Batch Number
UnrestrictQty,         -- Unrestricted Quantity
InspQty,         -- Balance waiting for QC Inspection
BlockQty,         -- Balance stuck in Block
UnrestrictValue,    -- Balance value in Unrestricted, UR balance value, available balance value
InspValue,     -- QC inspection balance value, QC check balance value
BlockValue,   -- Block balance value, unsold balance value
StockWH,    -- Stock Warehouse
StockWIP,   -- Stock Work In Progress
StockHold,      -- Stock on Hold
StockQI,        -- Stock Quality Inspection
StockBlock    -- Stock Block
);


Guidelines:
- SQLite-compatible SQL only.
- When using aggregate functions like GROUP_CONCAT(DISTINCT ...), ensure that only one argument (one column or one expression) is provided inside the DISTINCT. If you need to combine multiple columns, concatenate them into a single string first (e.g., (col1 || ' ' || col2)), then use DISTINCT on the result. SQLite does not allow DISTINCT with multiple arguments in aggregate functions.
- Your query must start with SELECT and does not contain any other SQL commands. (e.g., no INSERT, UPDATE, DELETE, CREATE, DROP, etc.)
- Do not use WITH (Common Table Expressions/CTEs). Write all queries using only SELECT, subqueries, and derived tables. Avoid starting queries with WITH.
- If your query uses UNION or UNION ALL, you must not put ORDER BY before or between any UNION/UNION ALL statements. The ORDER BY clause must come only once, after all UNION/UNION ALL statements, at the very end of the query. Do not generate ORDER BY in any subquery or before a UNION/UNION ALL.
- Use JOINs when connecting tables: 
  * SALES_LOGISTICS.SalesOrder = WAREHOUSE_STOCK.SalesOrder
  * SALES_LOGISTICS.SalesOrder = MATERIAL_MANUFACTURING.SalesOrder
- Date columns should use SQLite date functions when needed (DATE(), DATETIME(), etc.)
- If ambiguous, choose the most reasonable interpretation.
- Some fields may have fixed set of possible values use them if known.
- This helps prevent missing results due to calendar system or formatting inconsistencies.

Common query patterns:
- Order quantity: SELECT from SALES_LOGISTICS table

Respond ONLY with a valid SQL query. No explanation, no markdown, no extra text - just the SQL query.
""".strip()

EXPLANATION_PROMPT = """
You are a data analyst explaining query results to users. Given:
1. Original question: {question}
2. SQL query executed: {sql_query}
3. Query results: {results_summary}

Provide a clear, concise, and direct answer to the user's question.
Keep the explanation conversational and accessible to non-technical users.
You may provide a brief, friendly introduction (e.g., "From the database, we found that ...") but always include the full list.
Do not lie or give false information
Only give the direct answer in the same language as the question.
""".strip()

# =========================
# Pydantic Schemas
# =========================
class Text2SQLRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    assumptions: Optional[str] = Field(None, description="Optional clarifications/assumptions")
    # Optional: cap result size
    limit: Optional[int] = Field(500, ge=1, le=10000, description="Max rows to return")

class Text2SQLResponse(BaseModel):
    sql_query: str
    explanation: str
    results: Dict[str, Any]      # {columns: [...], rows: [...], row_count: n}

# =========================
# Utilities
# =========================
def extract_sql_query(model_output: str) -> str:
    """
    Clean extraction of SQL query from model output.
    Handles various response formats and cleans the SQL.
    """
    content = model_output.strip()
    
    # Remove markdown code blocks if present
    if content.startswith("```"):
        lines = content.split('\n')
        # Find first line after opening ```
        start_idx = 1
        if len(lines) > 1 and lines[1].strip().lower() in ['sql', 'sqlite']:
            start_idx = 2
        
        # Find closing ```
        end_idx = len(lines)
        for i in range(start_idx, len(lines)):
            if lines[i].strip() == "```":
                end_idx = i
                break
        
        content = '\n'.join(lines[start_idx:end_idx]).strip()
    
    # Try to parse as JSON (legacy support)
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "sql_query" in parsed:
            return str(parsed["sql_query"]).strip()
    except (json.JSONDecodeError, KeyError):
        pass
    
    # Clean up common prefixes/suffixes
    prefixes_to_remove = [
        "sql query:", "query:", "sql:", "answer:", "result:",
        "here's the sql:", "here is the sql:", "the sql query is:"
    ]
    
    content_lower = content.lower()
    for prefix in prefixes_to_remove:
        if content_lower.startswith(prefix):
            content = content[len(prefix):].strip()
            break
    
    # Remove trailing explanations (look for common patterns)
    lines = content.split('\n')
    sql_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Stop at explanation-like content
        if any(line.lower().startswith(phrase) for phrase in [
            "this query", "explanation:", "this will", "note:", 
            "the above", "this sql", "//", "--", "#"
        ]):
            break
            
        sql_lines.append(line)
    
    result = ' '.join(sql_lines).strip()
    
    # Final cleanup
    result = result.rstrip(';').strip() + ';'
    
    if not result or result == ';':
        raise ValueError("No valid SQL query found in model output")
    
    return result

def format_results_summary(results: Dict[str, Any]) -> str:
    """
    Create a concise summary of query results for explanation generation.
    """
    row_count = results.get("row_count", 0)
    columns = results.get("columns", [])
    rows = results.get("rows", [])
    
    if row_count == 0:
        return "No results found."
    
    summary = f"Found {row_count} result{'s' if row_count != 1 else ''}.\n"
    summary += f"Columns: {', '.join(columns)}\n"
    
    # Include sample data (first few rows)
    if rows:
        sample_size = min(50, len(rows))
        summary += f"Sample data (first {sample_size} row{'s' if sample_size != 1 else ''}):\n"
        for i, row in enumerate(rows[:sample_size]):
            summary += f"Row {i+1}: {dict(row)}\n"
    
    return summary

def maybe_wrap_with_limit(sql: str, limit: Optional[int]) -> str:
    """
    Add LIMIT clause if not already present and limit is specified.
    """
    if not limit:
        return sql
    # Simple LIMIT appender if none present
    low = sql.lower()
    if " limit " in low:
        return sql
    return sql.rstrip().rstrip(";") + f" LIMIT {limit};"

def generate_explanation(question: str, sql_query: str, results: Dict[str, Any]) -> str:
    """
    Generate explanation using the AI model after query execution.
    """
    try:
        results_summary = format_results_summary(results)
        
        prompt = EXPLANATION_PROMPT.format(
            question=question,
            sql_query=sql_query,
            results_summary=results_summary
        )
        
        messages = [
            {"role": "system", "content": "You are a helpful data analyst."},
            {"role": "user", "content": prompt}
        ]
        
        out = model.chat(messages=messages)
        explanation = out["choices"][0]["message"]["content"].strip()
        
        return explanation
        
    except Exception as e:
        # Fallback explanation if AI generation fails
        row_count = results.get("row_count", 0)
        return f"Query executed successfully. Found {row_count} result{'s' if row_count != 1 else ''}."

# =========================
# FastAPI App
# =========================
app = FastAPI(
    title="Text2SQL + Execute (School DB)",
    version="1.0.0",
    description="Turns NL questions into SQL with watsonx.ai gpt-oss-120b and executes on SQLite school.db."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    # Basic DB check
    try:
        db_conn.execute("SELECT 1;").fetchone()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "db_connected": db_ok, "db_path": os.path.abspath(DB_PATH)}

@app.post("/text2sql", response_model=Text2SQLResponse)
def text2sql(req: Text2SQLRequest):
    """
    Generate SQL from NL question, execute it on school.db, and return results with AI-generated explanation.
    """
    try:
        # Step 1: Generate SQL query
        user_content = req.question
        if req.assumptions:
            user_content += f"\n\nAdditional assumptions/notes: {req.assumptions}"
            
        messages = [
            {"role": "system", "content": SQL_GENERATION_PROMPT},
            {"role": "user", "content": user_content}
        ]
        
        sql_out = model.chat(messages=messages)
        sql_content = sql_out["choices"][0]["message"]["content"]
        
        # Step 2: Extract and clean SQL query
        sql_query = extract_sql_query(sql_content)
        
        # Step 3: Execute query
        sql_to_run = maybe_wrap_with_limit(sql_query, req.limit)
        results = run_select(sql_to_run)
        
        # Step 4: Generate explanation based on results
        explanation = generate_explanation(req.question, sql_query, results)

        return Text2SQLResponse(
            sql_query=sql_query,
            explanation=explanation,
            results=results
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"SQL parsing error: {ve}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model/DB error: {e}")

# Local dev
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, timeout_keep_alive=60)
