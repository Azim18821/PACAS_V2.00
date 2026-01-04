"""
Lead capture utilities for tracking user interest in properties
"""
import sqlite3
from datetime import datetime

# Import logger setup
import logging
logger = logging.getLogger('PACAS')

def init_leads_table():
    """Initialize the leads table and users/favorites tables in the database"""
    conn = sqlite3.connect('listings.db')
    cursor = conn.cursor()
    
    # Create users table for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            phone TEXT,
            email_verified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    
    # Create favorites table for saved properties
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            property_url TEXT NOT NULL,
            property_title TEXT,
            property_price TEXT,
            property_image TEXT,
            site TEXT,
            bedrooms TEXT,
            location TEXT,
            added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, property_url),
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)
    
    # Create indexes for favorites
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_favorites_added ON favorites(added_at)
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            property_url TEXT NOT NULL,
            property_title TEXT,
            property_price TEXT,
            site TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            phone TEXT,
            name TEXT,
            wants_callback INTEGER DEFAULT 0,
            lead_type TEXT DEFAULT 'property_view'
        )
    """)
    
    # Add new columns if they don't exist (for existing databases)
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN phone TEXT")
        logger.info("Added phone column to leads table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN name TEXT")
        logger.info("Added name column to leads table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN wants_callback INTEGER DEFAULT 0")
        logger.info("Added wants_callback column to leads table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute("ALTER TABLE leads ADD COLUMN lead_type TEXT DEFAULT 'property_view'")
        logger.info("Added lead_type column to leads table")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create indexes for faster queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_timestamp ON leads(timestamp)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_leads_type ON leads(lead_type)
    """)
    
    conn.commit()
    conn.close()
    logger.info("Leads table, users table, and favorites table initialized successfully")

def create_user(email, password_hash, name, phone, email_verified=True):
    """Create a new user account"""
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, phone, email_verified)
            VALUES (?, ?, ?, ?, ?)
        """, (email.lower(), password_hash, name, phone, 1 if email_verified else 0))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"User created: {email}")
        return user_id
    except sqlite3.IntegrityError:
        logger.warning(f"User already exists: {email}")
        return None
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None

def get_user_by_email(email):
    """Get user by email"""
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, name, phone, email_verified, created_at, last_login
            FROM users WHERE email = ?
        """, (email.lower(),))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'password_hash': user[2],
                'name': user[3],
                'phone': user[4],
                'email_verified': user[5],
                'created_at': user[6],
                'last_login': user[7]
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return None

def update_last_login(user_id):
    """Update user's last login time"""
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        """, (user_id,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating last login: {str(e)}")

def add_favorite(user_id, property_url, property_title, property_price, property_image, site, bedrooms='', location=''):
    """Add property to user's favorites"""
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO favorites (user_id, property_url, property_title, property_price, property_image, site, bedrooms, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, property_url, property_title, property_price, property_image, site, bedrooms, location))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Favorite added for user {user_id}")
        return True
    except sqlite3.IntegrityError:
        logger.info(f"Favorite already exists for user {user_id}")
        return False
    except Exception as e:
        logger.error(f"Error adding favorite: {str(e)}")
        return False

def remove_favorite(user_id, property_url):
    """Remove property from user's favorites"""
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM favorites WHERE user_id = ? AND property_url = ?
        """, (user_id, property_url))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Favorite removed for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error removing favorite: {str(e)}")
        return False

def get_user_favorites(user_id):
    """Get all favorites for a user"""
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, property_url, property_title, property_price, property_image, site, bedrooms, location, added_at
            FROM favorites WHERE user_id = ?
            ORDER BY added_at DESC
        """, (user_id,))
        
        favorites = cursor.fetchall()
        conn.close()
        
        return [{
            'id': f[0],
            'property_url': f[1],
            'property_title': f[2],
            'property_price': f[3],
            'property_image': f[4],
            'site': f[5],
            'bedrooms': f[6],
            'location': f[7],
            'added_at': f[8]
        } for f in favorites]
    except Exception as e:
        logger.error(f"Error getting favorites: {str(e)}")
        return []

def is_favorite(user_id, property_url):
    """Check if property is in user's favorites"""
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM favorites WHERE user_id = ? AND property_url = ?
        """, (user_id, property_url))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    except Exception as e:
        logger.error(f"Error checking favorite: {str(e)}")
        return False

def capture_lead(email, property_url, property_title, property_price, site, ip_address=None, phone='', name='', wants_callback=False, lead_type='property_view'):
    """
    Capture a lead when user clicks to view property
    
    Args:
        email: User's email address
        property_url: Full URL to the property listing
        property_title: Property title/address
        property_price: Property price
        site: Source site (Rightmove, Zoopla)
        ip_address: User's IP address (optional)
        phone: User's phone number (optional)
        name: User's full name (optional)
        wants_callback: Whether user wants agent callback
        lead_type: Type of lead (property_view, account_creation)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO leads (email, property_url, property_title, property_price, site, ip_address, phone, name, wants_callback, lead_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (email, property_url, property_title, property_price, site, ip_address, phone, name, 1 if wants_callback else 0, lead_type, datetime.now()))
        
        conn.commit()
        conn.close()
        
        lead_quality = "PREMIUM" if phone else "BASIC"
        logger.info(f"Captured {lead_quality} lead: {email} ({lead_type}) for {site} property")
        return True
    except Exception as e:
        logger.error(f"Error capturing lead: {e}")
        return False

def get_all_leads(limit=None):
    """
    Retrieve all captured leads
    
    Args:
        limit: Maximum number of leads to return (None for all)
    
    Returns:
        list: List of lead dictionaries
    """
    try:
        conn = sqlite3.connect('listings.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT id, email, property_url, property_title, property_price, 
                   site, timestamp, ip_address, phone, name, wants_callback, lead_type
            FROM leads
            ORDER BY timestamp DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        leads = []
        for row in rows:
            leads.append({
                'id': row['id'],
                'email': row['email'],
                'property_url': row['property_url'],
                'property_title': row['property_title'],
                'property_price': row['property_price'],
                'site': row['site'],
                'timestamp': row['timestamp'],
                'ip_address': row['ip_address'],
                'phone': row['phone'] if 'phone' in row.keys() else '',
                'name': row['name'] if 'name' in row.keys() else '',
                'wants_callback': row['wants_callback'] if 'wants_callback' in row.keys() else 0,
                'lead_type': row['lead_type'] if 'lead_type' in row.keys() else 'property_view'
            })
        
        conn.close()
        return leads
    except Exception as e:
        logger.error(f"Error retrieving leads: {e}")
        return []

def get_leads_stats():
    """
    Get statistics about captured leads
    
    Returns:
        dict: Statistics about leads
    """
    try:
        conn = sqlite3.connect('listings.db')
        cursor = conn.cursor()
        
        # Total leads
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]
        
        # Unique emails
        cursor.execute("SELECT COUNT(DISTINCT email) FROM leads")
        unique_emails = cursor.fetchone()[0]
        
        # Leads by site
        cursor.execute("""
            SELECT site, COUNT(*) as count
            FROM leads
            GROUP BY site
        """)
        by_site = dict(cursor.fetchall())
        
        # Leads today
        cursor.execute("""
            SELECT COUNT(*) FROM leads
            WHERE DATE(timestamp) = DATE('now')
        """)
        today = cursor.fetchone()[0]
        
        # Premium leads (with phone)
        cursor.execute("""
            SELECT COUNT(*) FROM leads
            WHERE phone IS NOT NULL AND phone != ''
        """)
        premium_leads = cursor.fetchone()[0]
        
        # Account creation leads
        cursor.execute("""
            SELECT COUNT(*) FROM leads
            WHERE lead_type = 'account_creation'
        """)
        account_leads = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_leads': total_leads,
            'unique_emails': unique_emails,
            'premium_leads': premium_leads,
            'account_leads': account_leads,
            'by_site': by_site,
            'today': today
        }
    except Exception as e:
        logger.error(f"Error getting leads stats: {e}")
        return {}

def export_leads_csv():
    """
    Export leads to CSV format
    
    Returns:
        str: CSV formatted string
    """
    leads = get_all_leads()
    
    if not leads:
        return "email,property_title,property_price,site,property_url,timestamp\n"
    
    csv = "email,property_title,property_price,site,property_url,timestamp,ip_address\n"
    
    for lead in leads:
        # Escape commas and quotes in fields
        email = lead['email'].replace('"', '""')
        title = (lead['property_title'] or '').replace('"', '""')
        price = (lead['property_price'] or '').replace('"', '""')
        site = lead['site']
        url = lead['property_url']
        timestamp = lead['timestamp']
        ip = lead['ip_address'] or ''
        
        csv += f'"{email}","{title}","{price}","{site}","{url}","{timestamp}","{ip}"\n'
    
    return csv
