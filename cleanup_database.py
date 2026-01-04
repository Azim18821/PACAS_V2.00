"""
Database cleanup utility for PACAS
Removes expired cache entries to prevent database bloat
"""
import sqlite3
from datetime import datetime
from utils.logger import logger

def cleanup_expired_cache(db_path='listings.db'):
    """
    Remove cache entries older than 24 hours
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Delete entries older than 24 hours
        cursor.execute("""
            DELETE FROM listings 
            WHERE created_at <= datetime('now', '-24 hours')
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        # Get database size info
        cursor.execute("SELECT COUNT(*) FROM listings")
        remaining_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info(f"Database cleanup completed: {deleted_count} expired entries removed, {remaining_count} entries remaining")
        return deleted_count, remaining_count
        
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")
        return 0, 0


def get_cache_stats(db_path='listings.db'):
    """
    Get statistics about the cache database
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM listings")
        total = cursor.fetchone()[0]
        
        # Entries less than 1 hour old
        cursor.execute("""
            SELECT COUNT(*) FROM listings 
            WHERE created_at > datetime('now', '-1 hour')
        """)
        fresh = cursor.fetchone()[0]
        
        # Entries between 1-24 hours old
        cursor.execute("""
            SELECT COUNT(*) FROM listings 
            WHERE created_at <= datetime('now', '-1 hour')
            AND created_at > datetime('now', '-24 hours')
        """)
        aging = cursor.fetchone()[0]
        
        # Expired entries (should be cleaned up)
        cursor.execute("""
            SELECT COUNT(*) FROM listings 
            WHERE created_at <= datetime('now', '-24 hours')
        """)
        expired = cursor.fetchone()[0]
        
        # Database file size (in MB)
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        size_bytes = cursor.fetchone()[0]
        size_mb = size_bytes / (1024 * 1024)
        
        conn.close()
        
        stats = {
            'total_entries': total,
            'fresh_entries': fresh,  # < 1 hour
            'aging_entries': aging,   # 1-24 hours
            'expired_entries': expired,  # > 24 hours
            'database_size_mb': round(size_mb, 2)
        }
        
        logger.info(f"Cache stats: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {}


def optimize_database(db_path='listings.db'):
    """
    Optimize database by running VACUUM to reclaim space
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info("Running database optimization (VACUUM)...")
        cursor.execute("VACUUM")
        
        conn.close()
        logger.info("Database optimization completed")
        return True
        
    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        return False


if __name__ == "__main__":
    print("PACAS Database Cleanup Utility")
    print("=" * 50)
    
    # Show current stats
    print("\n📊 Current Cache Statistics:")
    stats = get_cache_stats()
    for key, value in stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Clean up expired entries
    print("\n🧹 Cleaning up expired cache entries...")
    deleted, remaining = cleanup_expired_cache()
    print(f"  ✓ Removed {deleted} expired entries")
    print(f"  ✓ {remaining} entries remaining")
    
    # Optimize database
    print("\n⚡ Optimizing database...")
    if optimize_database():
        print("  ✓ Database optimized")
    else:
        print("  ✗ Optimization failed")
    
    # Show final stats
    print("\n📊 Final Cache Statistics:")
    final_stats = get_cache_stats()
    for key, value in final_stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\n✅ Cleanup complete!")
