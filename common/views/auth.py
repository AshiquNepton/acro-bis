# # common/views/auth.py

# from urllib import request
# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.db import connection
# from django.db.utils import OperationalError, DatabaseError
# import logging
# import os
# from dotenv import load_dotenv

# from common.views.company_loader import load_company_to_session


# logger = logging.getLogger(__name__)

# # Business type constants
# BUSINESS_TYPES = {
#     1: 'laundry',
#     2: 'restaurant',
#     3: 'hrms',
# }

# def login_view(request):
#     """
#     Handle user login with business type detection
#     Redirects to appropriate dashboard based on business type
#     """
    
#     # If already logged in, redirect to appropriate dashboard
#     if request.session.get('is_authenticated'):
#         business_type = request.session.get('business_type', 4)
        
#         if business_type == 1:
#             return redirect('laundry:dashboard')
#         elif business_type == 2:
#             return redirect('restaurant:dashboard')
#         elif business_type == 3:
#             return redirect('hrms:dashboard')
#         else:
#             return redirect('common:dashboard')
    
#     if request.method == 'POST':
#         username = request.POST.get('username', '').strip()
#         password = request.POST.get('password', '').strip()
        
#         if not username or not password:
#             messages.error(request, 'Please enter both username and password.')
#             return render(request, 'common/auth/login.html')
        
#         # Try to authenticate
#         try:
#             # Authenticate user
#             success, user_data = authenticate_user(username, password)
            
#             if success:
#                 # Set session variables
#                 request.session['is_authenticated'] = True
#                 request.session['username']         = username
#                 request.session['username'] = user_data.get('username')
#                 request.session['custid'] = user_data.get('custid')
#                 request.session['company_code'] = user_data.get('custid')
#                 request.session['company_name'] = user_data.get('company_name')
#                 request.session['company_expiry'] = user_data.get('company_expiry')
#                 request.session['business_type'] = user_data.get('business_type')  # NEW
#                 request.session['software_id']   = user_data.get('business_type')  # same value, used by sidebar/loader
#                 request.session['module_name']   = BUSINESS_TYPES.get(user_data.get('business_type'), 'ERP').upper()

                
#                 # Customer database credentials (from softwares table)
#                 request.session['db_host'] = user_data.get('customer_db_host')
#                 request.session['db_name'] = user_data.get('customer_db_name')
#                 request.session['db_user'] = user_data.get('customer_db_user')
#                 request.session['db_password'] = user_data.get('customer_db_password')
                
#                 logger.info(f"Login successful for user: {username}")
#                 logger.info(f"Business type: {user_data.get('business_type')} ({BUSINESS_TYPES.get(user_data.get('business_type'), 'Unknown')})")
#                 logger.info(f"Customer DB: {user_data.get('customer_db_host')}/{user_data.get('customer_db_name')}")
                
#                 business_type = user_data.get('business_type')
#                 business_name = BUSINESS_TYPES.get(business_type, 'Unknown')
                
#                 messages.success(request, f'Welcome back, {username}! ({business_name.title()} Business)')
#                 load_company_to_session(request)

#                 # Redirect to next URL if it exists
#                 next_url = request.session.pop('next_url', None)
#                 if next_url:
#                     return redirect(next_url)

#                 # Redirect based on business type
#                 if business_type == 1:
#                     return redirect('laundry:dashboard')
#                 elif business_type == 2:
#                     return redirect('restaurant:dashboard')
#                 elif business_type == 3:
#                     return redirect('hrms:dashboard')
#                 else:
#                     return redirect('common:home')
#             else:
#                 logger.warning(f"Login failed for user: {username}")
#                 messages.error(request, 'Invalid username or password.')
#                 return render(request, 'common/auth/login.html')
                
#         except OperationalError as e:
#             error_msg = str(e).lower()
#             logger.error(f"Database connection error during login: {str(e)}")
            
#             if 'timeout' in error_msg or 'timed out' in error_msg:
#                 messages.error(request, 
#                     'Connection to database server timed out. '
#                     'Please check your network connection or contact administrator.')
#             elif 'could not connect' in error_msg or 'connection refused' in error_msg:
#                 messages.error(request, 
#                     'Cannot reach database server. '
#                     'Please verify server address and firewall settings.')
#             elif 'authentication failed' in error_msg or 'password authentication failed' in error_msg:
#                 messages.error(request, 
#                     'Database authentication failed. '
#                     'Please contact administrator to verify database credentials.')
#             elif 'does not exist' in error_msg or 'no such table' in error_msg:
#                 messages.error(request, 
#                     'Database or table does not exist. '
#                     'Please contact administrator.')
#             else:
#                 messages.error(request, 
#                     'Database connection failed. Please contact administrator.')
            
#             return render(request, 'common/auth/login.html')
            
#         except DatabaseError as e:
#             logger.error(f"Database error during login: {str(e)}")
#             messages.error(request, 
#                 'Database query error. Please contact administrator.')
#             return render(request, 'common/auth/login.html')
            
#         except Exception as e:
#             logger.error(f"Unexpected login error: {str(e)}", exc_info=True)
#             messages.error(request, 
#                 'An unexpected error occurred. Please try again or contact administrator.')
#             return render(request, 'common/auth/login.html')
    
#     # GET request - show login form
#     return render(request, 'common/auth/login.html')


# def get_table_columns(cursor, table_name, query_placeholder):
#     """Get column names for a table"""
#     if query_placeholder == '%s':
#         # PostgreSQL
#         cursor.execute("""
#             SELECT column_name 
#             FROM information_schema.columns 
#             WHERE table_name = %s
#             ORDER BY ordinal_position
#         """, [table_name])
#         columns = [row[0] for row in cursor.fetchall()]
#         return {col.lower(): col for col in columns}
#     else:
#         # SQLite
#         cursor.execute(f"PRAGMA table_info({table_name})")
#         columns = [row[1] for row in cursor.fetchall()]
#         return {col.lower(): col for col in columns}


# def authenticate_user(username, password):
#     """
#     Authenticate user against the 'itemgroups' table in MAIN database
    
#     NEW: Also fetches business type from softwares table
    
#     Returns:
#         tuple: (success: bool, user_data: dict)
#     """
    
#     conn = None
#     cursor = None
    
#     try:
#         # Load environment variables from .env file (MAIN database)
#         env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
#         load_dotenv(env_path)
        
#         # Get MAIN database credentials from .env
#         main_db_host = os.getenv('DB_HOST', '')
#         main_db_port = os.getenv('PORT', '5432')
#         main_db_name = os.getenv('DB_NAME', '')
#         main_db_user = os.getenv('DB_USER', '')
#         main_db_password = os.getenv('DB_PASSWORD', '')
        
#         # Create connection to MAIN database
#         if not main_db_host or main_db_host.strip() == '':
#             # SQLite fallback
#             import sqlite3
#             conn = sqlite3.connect(main_db_name)
#             cursor = conn.cursor()
#             query_placeholder = '?'
#         else:
#             # PostgreSQL
#             import psycopg2
#             conn = psycopg2.connect(
#                 host=main_db_host,
#                 port=main_db_port,
#                 database=main_db_name,
#                 user=main_db_user,
#                 password=main_db_password
#             )
#             conn.autocommit = False
#             cursor = conn.cursor()
#             query_placeholder = '%s'
        
#         # Step 1: Authenticate user from itemgroups table
#         auth_query = f"""
#             SELECT 
#                 description,
#                 narration,
#                 custid
#             FROM itemgroups
#             WHERE description = {query_placeholder}
#             AND narration = {query_placeholder}
#         """
        
#         cursor.execute(auth_query, [username, password])
#         user = cursor.fetchone()
        
#         if not user:
#             logger.warning(f"Authentication failed - invalid credentials for user: {username}")
#             cursor.close()
#             conn.close()
#             return False, {}
        
#         # Extract user data
#         db_username = user[0]
#         db_password = user[1]
#         custid = user[2] if len(user) > 2 else None
        
#         if not custid:
#             logger.error(f"No custid found for user: {username}")
#             cursor.close()
#             conn.close()
#             return False, {}
        
#         # Step 2: Fetch company name from customers table
#         company_name = None
#         company_query = f'SELECT custname FROM customers WHERE custid = {query_placeholder}'
#         cursor.execute(company_query, [custid])
#         company_result = cursor.fetchone()
        
#         if company_result:
#             company_name = company_result[0]
        
#         # Step 3: Get table columns for softwares table
#         column_map = get_table_columns(cursor, 'softwares', query_placeholder)
        
#         # Find column names (handle both capitalize and lowercase)
#         host_col = column_map.get('host', 'host')
#         db_col = column_map.get('db', column_map.get('database', 'DB'))
#         username_col = column_map.get('username', 'username')
#         pwd_col = column_map.get('pwd', 'pwd')
#         dbpass_col = column_map.get('dbpass', pwd_col)
#         expiry_col = column_map.get('expiry', 'expiry')
#         software_col = column_map.get('software', 'software')  # Business type field
        
#         # Step 4: Fetch credentials and business type from softwares table
#         customer_db_query = f"""
#             SELECT 
#                 {host_col},
#                 {db_col},
#                 {username_col},
#                 {pwd_col},
#                 {dbpass_col},
#                 {expiry_col},
#                 {software_col}
#             FROM softwares
#             WHERE custid = {query_placeholder}
#         """
        
#         cursor.execute(customer_db_query, [custid])
#         customer_db_result = cursor.fetchone()
        
#         if not customer_db_result:
#             logger.error(f"No customer database credentials found for custid: {custid}")
#             cursor.close()
#             conn.close()
#             return False, {}
        
#         # Extract data
#         customer_db_host = customer_db_result[0]
#         customer_db_name = customer_db_result[1]
#         customer_db_user = customer_db_result[2]
#         customer_db_password = customer_db_result[4] if customer_db_result[4] else customer_db_result[3]
        
#         # Get company expiry
#         company_expiry = customer_db_result[5] if len(customer_db_result) > 5 else None
#         if company_expiry:
#             try:
#                 company_expiry = company_expiry.strftime('%Y-%m-%d')
#             except:
#                 company_expiry = str(company_expiry)
        
#         # Get business type (software field)
#         business_type = customer_db_result[6] if len(customer_db_result) > 6 else 4  # Default to laundry
        
#         # Convert to integer if needed
#         try:
#             business_type = int(business_type)
#         except (ValueError, TypeError):
#             business_type = 4  # Default to laundry
        
#         print("\n" + "="*80)
#         print("AUTHENTICATION SUCCESS")
#         print("="*80)
#         print(f"User:         {db_username}")
#         print(f"Company:      {company_name}")
#         print(f"Business Type: {business_type} ({BUSINESS_TYPES.get(business_type, 'Unknown')})")
#         print(f"Expiry:       {company_expiry}")
#         print(f"Customer DB:  {customer_db_host}/{customer_db_name}")
#         print("="*80 + "\n")
        
#         # Commit transaction
#         if query_placeholder == '%s':
#             conn.commit()
        
#         # Prepare user data
#         user_data = {
#             'username': db_username,
#             'custid': custid,
#             'company_name': company_name,
#             'company_expiry': company_expiry,
#             'business_type': business_type,  # NEW
            
#             # Customer database credentials
#             'customer_db_host': customer_db_host,
#             'customer_db_name': customer_db_name,
#             'customer_db_user': customer_db_user,
#             'customer_db_password': customer_db_password,
#         }
        
#         # Close connection
#         cursor.close()
#         conn.close()
        
#         return True, user_data
                
#     except Exception as e:
#         logger.error(f"Authentication error: {str(e)}", exc_info=True)
        
#         # Rollback transaction on error
#         try:
#             if conn and query_placeholder == '%s':
#                 conn.rollback()
#         except:
#             pass
        
#         # Close connection on error
#         try:
#             if cursor:
#                 cursor.close()
#             if conn:
#                 conn.close()
#         except:
#             pass
        
#         return False, {}


# def logout_view(request):
#     """Handle user logout"""
    
#     username = request.session.get('username', 'User')
    
#     # Clear session
#     request.session.flush()
    
#     logger.info(f"User logged out: {username}")
#     messages.info(request, 'You have been logged out successfully.')
#     return redirect('common:login')























# common/views/auth.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.utils import OperationalError, DatabaseError
import logging
import os
from dotenv import load_dotenv

from common.views.company_loader import load_company_to_session
from django.contrib.auth.hashers import check_password



logger = logging.getLogger(__name__)

# Business type constants
BUSINESS_TYPES = {
    1: 'laundry',
    2: 'restaurant',
    3: 'hrms',
    4: 'inventory',
    5: 'financial',
    6: 'logistics',
    7: 'gym',
}


def login_view(request):
    """
    Handle user login with company ID validation and business type detection.
    Flow:
      1. Validate company_id against customers.companycode  →  resolve custid
      2. Validate username + password from itemgroups WHERE custid matches
      3. Fetch DB credentials + business type from softwares
    """

    # Already logged in → redirect
    if request.session.get('is_authenticated'):
        business_type = request.session.get('business_type', 4)
        if business_type == 1:
            return redirect('laundry:dashboard')
        elif business_type == 2:
            return redirect('restaurant:dashboard')
        elif business_type == 4:
            return redirect('inventory:dashboard')
        elif business_type == 5:
            return redirect('financial:dashboard')
        else:
            return redirect('common:dashboard')

    if request.method == 'POST':
        company_id = request.POST.get('company_id', '').strip()
        username   = request.POST.get('username',   '').strip()
        password   = request.POST.get('password',   '').strip()

        if not company_id or not username or not password:
            messages.error(request, 'Please enter Company ID, username, and password.')
            return render(request, 'common/auth/login.html')

        try:
            success, user_data = authenticate_user(company_id, username, password)

            if success:
                # ── Populate session ──────────────────────────────────────
                request.session['is_authenticated'] = True
                request.session['username']         = user_data.get('username')
                request.session['custid']           = user_data.get('custid')
                request.session['company_code']     = user_data.get('company_code')   # companycode from customers
                request.session['company_name']     = user_data.get('company_name')
                request.session['company_expiry']   = user_data.get('company_expiry')
                request.session['business_type']    = user_data.get('business_type')
                request.session['software_id']      = user_data.get('business_type')
                request.session['module_name']      = BUSINESS_TYPES.get(
                                                          user_data.get('business_type'), 'ERP'
                                                      ).upper()
                request.session['emp_login_id']     = user_data.get('emp_login_id')   # ← NEW

                # Customer database credentials
                request.session['db_host']     = user_data.get('customer_db_host')
                request.session['db_name']     = user_data.get('customer_db_name')
                request.session['db_user']     = user_data.get('customer_db_user')
                request.session['db_password'] = user_data.get('customer_db_password')

                business_type = user_data.get('business_type')
                business_name = BUSINESS_TYPES.get(business_type, 'Unknown')

                logger.info(f"Login successful  user={username}  company={company_id}  "
                            f"business={business_name}")

                messages.success(
                    request,
                    f'Welcome back, {username}! ({business_name.title()} Business)'
                )
                load_company_to_session(request)

                # Honour ?next= redirect
                next_url = request.session.pop('next_url', None)
                if next_url:
                    return redirect(next_url)

                if business_type == 1:
                    return redirect('laundry:dashboard')
                elif business_type == 2:
                    return redirect('restaurant:dashboard')
                elif business_type == 4:
                    return redirect('inventory:dashboard')
                elif business_type == 5:
                    return redirect('financial:dashboard')
                else:
                    return redirect('common:home')

            else:
                # user_data may contain a hint about which step failed
                reason = user_data.get('reason', 'invalid_credentials')
                logger.warning(f"Login failed  user={username}  company={company_id}  reason={reason}")

                if reason == 'invalid_company':
                    messages.error(request, 'Company ID not found. Please check and try again.')
                else:
                    messages.error(request, 'Invalid username or password.')

                return render(request, 'common/auth/login.html')

        except OperationalError as e:
            error_msg = str(e).lower()
            logger.error(f"DB connection error during login: {e}")

            if 'timeout' in error_msg or 'timed out' in error_msg:
                messages.error(request,
                    'Connection to database server timed out. '
                    'Please check your network connection or contact administrator.')
            elif 'could not connect' in error_msg or 'connection refused' in error_msg:
                messages.error(request,
                    'Cannot reach database server. '
                    'Please verify server address and firewall settings.')
            elif 'authentication failed' in error_msg or 'password authentication failed' in error_msg:
                messages.error(request,
                    'Database authentication failed. '
                    'Please contact administrator to verify database credentials.')
            elif 'does not exist' in error_msg or 'no such table' in error_msg:
                messages.error(request,
                    'Database or table does not exist. '
                    'Please contact administrator.')
            else:
                messages.error(request,
                    'Database connection failed. Please contact administrator.')

            return render(request, 'common/auth/login.html')

        except DatabaseError as e:
            logger.error(f"Database error during login: {e}")
            messages.error(request, 'Database query error. Please contact administrator.')
            return render(request, 'common/auth/login.html')

        except Exception as e:
            logger.error(f"Unexpected login error: {e}", exc_info=True)
            messages.error(request,
                'An unexpected error occurred. Please try again or contact administrator.')
            return render(request, 'common/auth/login.html')

    # GET → show form
    return render(request, 'common/auth/login.html')


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_connection_and_placeholder():
    """
    Build a DB connection to the MAIN database.
    Returns (conn, cursor, query_placeholder)
    """
    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'
    )
    load_dotenv(env_path)

    main_db_host     = os.getenv('DB_HOST', '')
    main_db_port     = os.getenv('PORT', '5432')
    main_db_name     = os.getenv('DB_NAME', '')
    main_db_user     = os.getenv('DB_USER', '')
    main_db_password = os.getenv('DB_PASSWORD', '')

    if not main_db_host or not main_db_host.strip():
        # SQLite fallback
        import sqlite3
        conn   = sqlite3.connect(main_db_name)
        cursor = conn.cursor()
        return conn, cursor, '?'
    else:
        import psycopg2
        conn = psycopg2.connect(
            host=main_db_host,
            port=main_db_port,
            database=main_db_name,
            user=main_db_user,
            password=main_db_password,
        )
        conn.autocommit = False
        cursor = conn.cursor()
        return conn, cursor, '%s'


def get_table_columns(cursor, table_name, query_placeholder):
    """Return {lowercase_col: actual_col} for a given table."""
    if query_placeholder == '%s':
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, [table_name])
    else:
        cursor.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()

    if query_placeholder == '%s':
        columns = [r[0] for r in rows]
    else:
        columns = [r[1] for r in rows]

    return {col.lower(): col for col in columns}


# def authenticate_user(company_id, username, password):
#     """
#     Three-step authentication:

#     Step 1 — Validate company_id against customers.companycode
#              → resolves custid

#     Step 2 — Validate username + password from itemgroups
#              scoped to the resolved custid

#     Step 3 — Fetch DB credentials + business_type from softwares

#     Returns:
#         (True,  user_data_dict)   on success
#         (False, {'reason': ...})  on failure
#     """
#     conn   = None
#     cursor = None

#     try:
#         conn, cursor, ph = _get_connection_and_placeholder()

#         # ── Step 1: Resolve company from customers.companycode ────────────
#         cursor.execute(
#             f"SELECT custid, custname FROM customers WHERE companycode = {ph}",
#             [company_id]
#         )
#         company_row = cursor.fetchone()

#         if not company_row:
#             logger.warning(f"Company ID not found: {company_id}")
#             _close(cursor, conn, ph)
#             return False, {'reason': 'invalid_company'}

#         custid       = company_row[0]
#         company_name = company_row[1]
#         logger.info(f"Company resolved: code={company_id}  custid={custid}  name={company_name}")

#         # ── Step 2: Authenticate credentials in itemgroups for this custid ─
#         #
#         #   Existing schema: description = username, narration = password
#         #   We now also filter by custid so credentials cannot cross companies.
#         #
#         cursor.execute(
#             f"""
#             SELECT description, narration, custid
#             FROM   itemgroups
#             WHERE  description = {ph}
#             AND    narration   = {ph}
#             AND    custid      = {ph}
#             """,
#             [username, password, custid]
#         )
#         user_row = cursor.fetchone()

#         if not user_row:
#             logger.warning(
#                 f"Credentials not matched for user={username}  custid={custid}"
#             )
#             _close(cursor, conn, ph)
#             return False, {'reason': 'invalid_credentials'}

#         db_username = user_row[0]

#         # ── Step 3: Fetch softwares row for DB credentials + business type ─
#         col_map = get_table_columns(cursor, 'softwares', ph)

#         host_col     = col_map.get('host',     'host')
#         db_col       = col_map.get('db',       col_map.get('database', 'DB'))
#         username_col = col_map.get('username', 'username')
#         pwd_col      = col_map.get('pwd',      'pwd')
#         dbpass_col   = col_map.get('dbpass',   pwd_col)
#         expiry_col   = col_map.get('expiry',   'expiry')
#         software_col = col_map.get('software', 'software')

#         cursor.execute(
#             f"""
#             SELECT
#                 {host_col},
#                 {db_col},
#                 {username_col},
#                 {pwd_col},
#                 {dbpass_col},
#                 {expiry_col},
#                 {software_col}
#             FROM softwares
#             WHERE custid = {ph}
#             """,
#             [custid]
#         )
#         sw_row = cursor.fetchone()

#         if not sw_row:
#             logger.error(f"No softwares row found for custid={custid}")
#             _close(cursor, conn, ph)
#             return False, {'reason': 'no_software_record'}

#         customer_db_host     = sw_row[0]
#         customer_db_name     = sw_row[1]
#         customer_db_user     = sw_row[2]
#         customer_db_password = sw_row[4] if sw_row[4] else sw_row[3]

#         company_expiry = sw_row[5] if len(sw_row) > 5 else None
#         if company_expiry:
#             try:
#                 company_expiry = company_expiry.strftime('%Y-%m-%d')
#             except Exception:
#                 company_expiry = str(company_expiry)

#         business_type = sw_row[6] if len(sw_row) > 6 else 4
#         try:
#             business_type = int(business_type)
#         except (ValueError, TypeError):
#             business_type = 4

#         # Commit + close
#         if ph == '%s':
#             conn.commit()
#         _close(cursor, conn, ph)

#         print("\n" + "=" * 80)
#         print("AUTHENTICATION SUCCESS")
#         print("=" * 80)
#         print(f"Company ID:    {company_id}")
#         print(f"User:          {db_username}")
#         print(f"Company:       {company_name}  (custid={custid})")
#         print(f"Business Type: {business_type} ({BUSINESS_TYPES.get(business_type, 'Unknown')})")
#         print(f"Expiry:        {company_expiry}")
#         print(f"Customer DB:   {customer_db_host}/{customer_db_name}")
#         print("=" * 80 + "\n")

#         user_data = {
#             'username':            db_username,
#             'custid':              custid,
#             'company_code':        company_id,        # the code the user typed
#             'company_name':        company_name,
#             'company_expiry':      company_expiry,
#             'business_type':       business_type,
#             'customer_db_host':    customer_db_host,
#             'customer_db_name':    customer_db_name,
#             'customer_db_user':    customer_db_user,
#             'customer_db_password': customer_db_password,
#         }
#         return True, user_data

#     except Exception as e:
#         logger.error(f"Authentication error: {e}", exc_info=True)
#         try:
#             if conn and ph == '%s':
#                 conn.rollback()
#         except Exception:
#             pass
#         _close(cursor, conn, getattr(conn, '_ph', None))
#         return False, {'reason': 'exception'}





def authenticate_user(company_id, username, password):
    """
    Four-step authentication:

    Step 1 — Validate company_id against customers.companycode
             → resolves custid

    Step 2 — Validate username + password from itemgroups
             scoped to the resolved custid

    Step 3 — Fetch DB credentials + business_type from softwares

    Step 4 — Resolve the tenant DB's "ItemGroups"."GroupID" for this user
             (matched by "Description" = username) → emp_login_id

    Returns:
        (True,  user_data_dict)   on success
        (False, {'reason': ...})  on failure
    """
    conn   = None
    cursor = None

    try:
        conn, cursor, ph = _get_connection_and_placeholder()

        # ── Step 1: Resolve company from customers.companycode ────────────
        cursor.execute(
            f"SELECT custid, custname FROM customers WHERE companycode = {ph}",
            [company_id]
        )
        company_row = cursor.fetchone()

        if not company_row:
            logger.warning(f"Company ID not found: {company_id}")
            _close(cursor, conn, ph)
            return False, {'reason': 'invalid_company'}

        custid       = company_row[0]
        company_name = company_row[1]
        logger.info(f"Company resolved: code={company_id}  custid={custid}  name={company_name}")

        # ── Step 2: Authenticate credentials in itemgroups for this custid ─

        cursor.execute(
            f"""
            SELECT description, narration, custid
            FROM   itemgroups
            WHERE  description = {ph}
            AND    custid       = {ph}
            """,
            [username, custid]
        )
        user_row = cursor.fetchone()

        if not user_row or not check_password(password, user_row[1]):
            logger.warning(f"Credentials not matched for user={username}  custid={custid}")
            _close(cursor, conn, ph)
            return False, {'reason': 'invalid_credentials'}

        db_username = user_row[0]

        # ── Step 3: Fetch softwares row for DB credentials + business type ─
        col_map = get_table_columns(cursor, 'softwares', ph)

        host_col     = col_map.get('host',     'host')
        db_col       = col_map.get('db',       col_map.get('database', 'DB'))
        username_col = col_map.get('username', 'username')
        pwd_col      = col_map.get('pwd',      'pwd')
        dbpass_col   = col_map.get('dbpass',   pwd_col)
        expiry_col   = col_map.get('expiry',   'expiry')
        software_col = col_map.get('software', 'software')

        cursor.execute(
            f"""
            SELECT
                {host_col},
                {db_col},
                {username_col},
                {pwd_col},
                {dbpass_col},
                {expiry_col},
                {software_col}
            FROM softwares
            WHERE custid = {ph}
            """,
            [custid]
        )
        sw_row = cursor.fetchone()

        if not sw_row:
            logger.error(f"No softwares row found for custid={custid}")
            _close(cursor, conn, ph)
            return False, {'reason': 'no_software_record'}

        customer_db_host     = sw_row[0]
        customer_db_name     = sw_row[1]
        customer_db_user     = sw_row[2]
        customer_db_password = sw_row[4] if sw_row[4] else sw_row[3]

        company_expiry = sw_row[5] if len(sw_row) > 5 else None
        if company_expiry:
            try:
                company_expiry = company_expiry.strftime('%Y-%m-%d')
            except Exception:
                company_expiry = str(company_expiry)

        business_type = sw_row[6] if len(sw_row) > 6 else 4
        try:
            business_type = int(business_type)
        except (ValueError, TypeError):
            business_type = 4

        # Commit + close MAIN db connection — done with it
        if ph == '%s':
            conn.commit()
        _close(cursor, conn, ph)

        # ── Step 4: Resolve emp_login_id from the TENANT DB's "ItemGroups" ──
        emp_login_id = _resolve_tenant_group_id(
            customer_db_host, customer_db_name,
            customer_db_user, customer_db_password,
            username
        )
        if emp_login_id is None:
            logger.warning(
                f"No matching ItemGroups row in tenant DB '{customer_db_name}' "
                f"for username={username}"
            )
            # Non-fatal: login still proceeds, but EnteredBy-style fields
            # won't have a valid GroupID until this is fixed on the tenant side.

        print("\n" + "=" * 80)
        print("AUTHENTICATION SUCCESS")
        print("=" * 80)
        print(f"Company ID:    {company_id}")
        print(f"User:          {db_username}")
        print(f"Company:       {company_name}  (custid={custid})")
        print(f"Business Type: {business_type} ({BUSINESS_TYPES.get(business_type, 'Unknown')})")
        print(f"Expiry:        {company_expiry}")
        print(f"Customer DB:   {customer_db_host}/{customer_db_name}")
        print(f"emp_login_id:  {emp_login_id}")
        print("=" * 80 + "\n")

        user_data = {
            'username':            db_username,
            'custid':              custid,
            'company_code':        company_id,        # the code the user typed
            'company_name':        company_name,
            'company_expiry':      company_expiry,
            'business_type':       business_type,
            'customer_db_host':    customer_db_host,
            'customer_db_name':    customer_db_name,
            'customer_db_user':    customer_db_user,
            'customer_db_password': customer_db_password,
            'emp_login_id':        emp_login_id,        # tenant ItemGroups.GroupID
        }
        return True, user_data

    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        try:
            if conn and ph == '%s':
                conn.rollback()
        except Exception:
            pass
        _close(cursor, conn, getattr(conn, '_ph', None))
        return False, {'reason': 'exception'}


def _resolve_tenant_group_id(db_host, db_name, db_user, db_password, username):
    """
    Connect to the tenant DB and look up "ItemGroups"."GroupID" for the row
    where "Description" = username (exact match). Returns None on any
    failure (missing row, connection error) so login can still proceed.
    """
    tconn = None
    try:
        import psycopg2
        tconn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        tcursor = tconn.cursor()
        tcursor.execute(
            'SELECT "GroupID" FROM "ItemGroups" WHERE "Description" = %s LIMIT 1',
            [username]
        )
        row = tcursor.fetchone()
        tcursor.close()
        return row[0] if row else None
    except Exception as e:
        logger.error(f"Could not resolve tenant GroupID for user={username}: {e}")
        return None
    finally:
        try:
            if tconn:
                tconn.close()
        except Exception:
            pass




def _close(cursor, conn, ph=None):
    """Safely close cursor and connection."""
    try:
        if cursor:
            cursor.close()
    except Exception:
        pass
    try:
        if conn:
            conn.close()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
#  Logout
# ─────────────────────────────────────────────────────────────────────────────

def logout_view(request):
    """Handle user logout."""
    username = request.session.get('username', 'User')
    request.session.flush()
    logger.info(f"User logged out: {username}")
    messages.info(request, 'You have been logged out successfully.')
    return redirect('common:login')