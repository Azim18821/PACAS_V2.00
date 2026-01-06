import sqlite3
import json
from datetime import datetime, timedelta
from utils.logger import logger

class Database:
    def __init__(self):
        """Initialize database connection"""
        self.db_path = 'listings.db'  # Changed from 'utils/listings.db'
        self.init_db()

    def init_db(self):
        """Initialize the database and create tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create listings table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS listings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        site TEXT,
                        location TEXT,
                        min_price TEXT,
                        max_price TEXT,
                        min_beds TEXT,
                        max_beds TEXT,
                        keywords TEXT,
                        listing_type TEXT,
                        sort_by TEXT,
                        page_number INTEGER,
                        results TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type, sort_by, page_number)
                    )
                ''')
                
                # Check if page_number column exists
                cursor.execute("PRAGMA table_info(listings)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'page_number' not in columns:
                    # Add page_number column if it doesn't exist
                    cursor.execute('ALTER TABLE listings ADD COLUMN page_number INTEGER')
                    # Update existing rows to have page_number = 1
                    cursor.execute('UPDATE listings SET page_number = 1 WHERE page_number IS NULL')
                
                if 'sort_by' not in columns:
                    # Add sort_by column if it doesn't exist
                    cursor.execute('ALTER TABLE listings ADD COLUMN sort_by TEXT')
                    # Update existing rows to have sort_by = 'newest'
                    cursor.execute("UPDATE listings SET sort_by = 'newest' WHERE sort_by IS NULL")
                
                # Create index for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_listings_search 
                    ON listings(site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type, sort_by, page_number)
                ''')
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error("Error initializing database: %s", str(e))
            raise

    def get_cached_results(self, site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type, page_number, sort_by='newest'):
        """Get cached results if they exist and are not too old"""
        try:
            # Convert empty strings to NULL for SQL
            def clean_param(param):
                if param == "" or param == "0" or param is None:
                    return None
                return param

            params = [
                clean_param(site),
                clean_param(location),
                clean_param(min_price),
                clean_param(max_price),
                clean_param(min_beds),
                clean_param(max_beds),
                clean_param(keywords),
                clean_param(listing_type),
                clean_param(sort_by) or 'newest',
                page_number
            ]
            
            # Log the parameters being used
            logger.info("Checking cache with parameters: %s", params)
            
            # Use parameterized query with proper NULL handling
            query = """
                SELECT results, created_at
                FROM listings
                WHERE site = ?
                AND (location = ? OR (location IS NULL AND ? IS NULL))
                AND (min_price = ? OR (min_price IS NULL AND ? IS NULL))
                AND (max_price = ? OR (max_price IS NULL AND ? IS NULL))
                AND min_beds = ?
                AND max_beds = ?
                AND (keywords = ? OR (keywords IS NULL AND ? IS NULL))
                AND (listing_type = ? OR (listing_type IS NULL AND ? IS NULL))
                AND (sort_by = ? OR (sort_by IS NULL AND ? IS NULL))
                AND page_number = ?
                AND created_at > datetime('now', '-24 hours')
            """
            
            # Double the parameters for NULL comparison (except site, min_beds, max_beds, and page_number)
            query_params = [params[0]]  # Add site parameter first
            for i, param in enumerate(params[1:-1]):  # Exclude site and page_number
                if i in [3, 4]:  # min_beds and max_beds
                    query_params.append(param)  # Add once
                else:
                    query_params.extend([param, param])  # Add twice for NULL comparison
            query_params.append(params[-1])  # Add page_number last
            
            # Log the query and parameters
            logger.info("Executing query: %s", query)
            logger.info("With parameters: %s", query_params)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, query_params)
                result = cursor.fetchone()
                
                if result:
                    results, created_at = result
                    logger.info("Found cached results from %s", created_at)
                    return json.loads(results)
                else:
                    logger.info("No valid cached results found")
                    return None
                
        except Exception as e:
            logger.error("Error getting cached results: %s", str(e))
            return None

    def cache_results(self, site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type, page_number, results, sort_by='newest'):
        """Cache search results"""
        try:
            # Convert empty strings to NULL for SQL
            def clean_param(param):
                if param == "" or param == "0" or param is None:
                    return None
                return param

            params = [
                clean_param(site),
                clean_param(location),
                clean_param(min_price),
                clean_param(max_price),
                clean_param(min_beds),
                clean_param(max_beds),
                clean_param(keywords),
                clean_param(listing_type),
                clean_param(sort_by) or 'newest',
                page_number,
                json.dumps(results)
            ]
            
            # Log the parameters being cached
            logger.info("Attempting to cache results with parameters: %s", params[:-1])  # Exclude results from log
            
            # Use INSERT OR REPLACE to handle duplicates
            query = """
                INSERT OR REPLACE INTO listings 
                (site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type, sort_by, page_number, results, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                logger.info("Successfully cached results for site: %s, location: %s, sort_by: %s, page: %d", site, location, sort_by, page_number)
                
        except Exception as e:
            logger.error("Error caching results: %s", str(e))
            logger.error("Parameters that caused error: site=%s, location=%s, min_price=%s, max_price=%s, min_beds=%s, max_beds=%s, keywords=%s, listing_type=%s, page=%d",
                        site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type, page_number)

    def cleanup_old_results(self, max_age_hours=24):
        """Remove results older than max_age_hours"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
                cursor.execute('''
                    DELETE FROM listings 
                    WHERE created_at < ?
                ''', (cutoff_time.isoformat(),))
                
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old results")
                
        except Exception as e:
            logger.error(f"Error cleaning up old results: {str(e)}")
            # Don't raise the exception, just log it
            pass 