from utils.database import Database
from utils.logger import logger

def main():
    try:
        db = Database()
        logger.info("Starting cache cleanup...")
        db.clear_empty_results()
        logger.info("Cache cleanup completed")
    except Exception as e:
        logger.error(f"Error during cache cleanup: {str(e)}")

if __name__ == "__main__":
    main() 