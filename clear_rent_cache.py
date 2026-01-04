"""
Clear specific cache entry for combined rent search
"""
import sqlite3

def clear_combined_rent_cache():
    conn = sqlite3.connect('listings.db')
    cursor = conn.cursor()
    
    # Delete combined rent searches
    cursor.execute("""
        DELETE FROM listings 
        WHERE site = 'Combined' 
        AND listing_type = 'rent'
    """)
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"Cleared {deleted} combined rent cache entries")

if __name__ == "__main__":
    clear_combined_rent_cache()
