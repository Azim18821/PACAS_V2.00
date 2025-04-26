from flask import Flask, request, jsonify, render_template, Response, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import sqlite3
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from dotenv import load_dotenv
from scrapers.zoopla import scrape_zoopla, scrape_zoopla_first_page, scrape_zoopla_page
from scrapers.rightmove_scrape import scrape_rightmove_from_url
from scrapers.rightmove_url import get_final_rightmove_results_url
from scrapers.openrent import scrape_openrent
from utils.validators import validate_search_params, ValidationError, rate_limiter
from utils.logger import logger
from utils.database import Database
from scraper_bot import ScraperBot
import os
import hashlib
import time
from datetime import datetime, timedelta
import json
import asyncio
import secrets
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


load_dotenv()
app = Flask('app')
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['WTF_CSRF_SECRET_KEY'] = secrets.token_hex(32)

CORS(app)
csrf = CSRFProtect(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

# Exempt search endpoints from login requirement 
app.config['LOGIN_DISABLED'] = True

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Import User model
from models.user import User

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# Initialize database
db = Database()

# Cache storage with timestamps (for backward compatibility)
cache = {}
CACHE_DURATION = timedelta(minutes=5)

def generate_listing_id(listing):
    base = f"{listing.get('title', '')}_{listing.get('price', '')}_{listing.get('address', '')}"
    return hashlib.md5(base.encode()).hexdigest()

def deduplicate_listings(listings):
    seen_ids = set()
    deduped = []
    for listing in listings:
        listing['id'] = generate_listing_id(listing)
        if listing['id'] not in seen_ids:
            seen_ids.add(listing['id'])
            deduped.append(listing)
    return deduped

def get_cache_key(site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type):
    """Generate a unique cache key for the search parameters"""
    params = f"{site}:{location}:{min_price}:{max_price}:{min_beds}:{max_beds}:{keywords}:{listing_type}"
    return hashlib.md5(params.encode()).hexdigest()

def get_cached_results(cache_key):
    """Get results from cache if they exist and are not expired"""
    if cache_key in cache:
        timestamp, results = cache[cache_key]
        if datetime.now() - timestamp < CACHE_DURATION:
            logger.info("Cache hit!")
            return results
        else:
            del cache[cache_key]
    return None

def cache_results(cache_key, results):
    """Store results in cache with current timestamp"""
    cache[cache_key] = (datetime.now(), results)
    # Clean up old cache entries
    for key in list(cache.keys()):
        timestamp, _ = cache[key]
        if datetime.now() - timestamp > CACHE_DURATION:
            del cache[key]

async def scrape_site(site, location, min_price, max_price, min_beds, max_beds, keywords, listing_type, page=1):
    """Scrape a specific site with the given parameters"""
    try:
        if site == "zoopla":
            logger.info("[Zoopla] Starting scrape...")
            results = await scrape_zoopla(location, min_price, max_price, min_beds, max_beds, keywords, listing_type)
            logger.info("[Zoopla] Scrape completed. Found %d results", len(results))
            return results
        elif site == "rightmove":
            logger.info("[Rightmove] Starting scrape with listing type: %s, page: %d", listing_type, page)
            url = get_final_rightmove_results_url(
                location=location,
                min_price=min_price,
                max_price=max_price,
                min_beds=min_beds,
                max_beds=max_beds,
                radius="0.0",
                include_sold=True,
                listing_type=listing_type,
                page=page  # Pass the page parameter
            )
            if not url:
                logger.error("[Rightmove] Failed to generate URL")
                return []
            results = scrape_rightmove_from_url(url, page=page)
            logger.info("[Rightmove] Scrape completed. Found %d results", len(results["listings"]))
            return results
        elif site == "openrent":
            logger.info("[OpenRent] Starting scrape...")
            results = scrape_openrent(location, min_price, max_price, min_beds, keywords)
            logger.info("[OpenRent] Scrape completed. Found %d results", len(results))
            return results
        else:
            logger.error("Unknown site: %s", site)
            return {"listings": [], "total_found": 0, "total_pages": 0}
    except Exception as e:
        logger.error("Error scraping %s: %s", site, str(e))
        return {"listings": [], "total_found": 0, "total_pages": 0}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.get_by_email(email)
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.get_by_email(email):
            flash('Email already registered.')
            return redirect(url_for('register'))

        if User.create_user(username, email, password):
            flash('Registration successful. Please login.')
            return redirect(url_for('login'))
        else:
            flash('Registration failed.')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/api/search', methods=['POST'])
@limiter.limit("50/hour") #Example rate limit
async def search():
    """Handle property search requests"""
    try:
        # Get search parameters from request
        data = request.get_json()
        logger.info("Received search request: %s", data)

        # Validate search parameters
        try:
            validated_data = validate_search_params(data)
            logger.info("Validated search parameters: %s", validated_data)
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return jsonify({"error": str(e)}), 400

        # If site is combined, redirect to combined endpoint
        if validated_data['site'] == 'combined':
            logger.info("Redirecting combined search to combined endpoint")
            return await search_combined()

        # Check database cache first
        cached_results = db.get_cached_results(
            validated_data['site'],
            validated_data['location'],
            validated_data['min_price'],
            validated_data['max_price'],
            validated_data['min_beds'],
            validated_data['max_beds'],
            validated_data['keywords'],
            validated_data['listing_type'],
            1  # First page
        )

        if cached_results:
            logger.info("Found valid cached results in database")
            return jsonify(cached_results)

        # If not in cache, scrape the site
        if validated_data['site'] == 'zoopla':
            logger.info("Scraping Zoopla...")
            try:
                # Get first page and total pages
                first_page_results, total_pages = await scrape_zoopla_first_page(
                    validated_data['location'],
                    validated_data['min_price'],
                    validated_data['max_price'],
                    validated_data['min_beds'],
                    validated_data['max_beds'],
                    validated_data['keywords'],
                    validated_data['listing_type'],
                    1  # First page
                )

                # Prepare response
                response_data = {
                    "listings": first_page_results,
                    "total_found": len(first_page_results),
                    "total_pages": total_pages,
                    "current_page": 1,
                    "is_complete": False,
                    "search_params": validated_data
                }

                # Only cache if we have valid results
                if first_page_results and len(first_page_results) > 0:
                    db.cache_results(
                        validated_data['site'],
                        validated_data['location'],
                        validated_data['min_price'],
                        validated_data['max_price'],
                        validated_data['min_beds'],
                        validated_data['max_beds'],
                        validated_data['keywords'],
                        validated_data['listing_type'],
                        1,  # First page
                        response_data
                    )
                    logger.info("Cached valid results with %d listings", len(first_page_results))
                else:
                    logger.info("Skipping cache for empty results")

                return jsonify(response_data)
            except Exception as e:
                logger.error("Error scraping Zoopla first page: %s", str(e))
                return jsonify({
                    "error": f"Error scraping Zoopla: {str(e)}",
                    "details": "Failed to fetch first page of results"
                }), 500
        else:
            # For other sites, use regular scraping
            results = await scrape_site(
                validated_data['site'],
                validated_data['location'],
                validated_data['min_price'],
                validated_data['max_price'],
                validated_data['min_beds'],
                validated_data['max_beds'],
                validated_data['keywords'],
                validated_data['listing_type'],
                1  # First page
            )

            # Prepare response
            response_data = {
                "listings": results.get("listings", []) if isinstance(results, dict) else results,
                "total_found": len(results.get("listings", [])) if isinstance(results, dict) else len(results),
                "total_pages": results.get("total_pages", 1) if isinstance(results, dict) else 1,
                "current_page": 1,
                "is_complete": True,
                "search_params": validated_data
            }

            # Only cache if we have valid results
            listings = results.get("listings", []) if isinstance(results, dict) else results
            if listings and len(listings) > 0:
                db.cache_results(
                    validated_data['site'],
                    validated_data['location'],
                    validated_data['min_price'],
                    validated_data['max_price'],
                    validated_data['min_beds'],
                    validated_data['max_beds'],
                    validated_data['keywords'],
                    validated_data['listing_type'],
                    1,  # First page
                    response_data
                )
                logger.info("Cached valid results with %d listings", len(listings))
            else:
                logger.info("Skipping cache for empty results")

            return jsonify(response_data)

    except Exception as e:
        logger.error("Error processing search request: %s", str(e))
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/api/search/next-page', methods=['POST'])
@limiter.limit("50/hour") #Example rate limit
async def next_page():
    """Handle loading the next page of results"""
    try:
        # Get search parameters and current page from request
        data = request.get_json()
        search_params = data.get('search_params', {})
        current_page = data.get('current_page', 1)

        logger.info("Received next page request: %s", data)
        logger.info("Processing next page request for site: %s, page: %d", search_params['site'], current_page)

        # Validate and clean parameters using validate_search_params
        try:
            validated_params = validate_search_params(search_params)
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return jsonify({
                "error": "Invalid parameters",
                "details": str(e)
            }), 400

        # If site is combined, use the scraper bot's scrape_combined method
        if validated_params['site'] == 'combined':
            logger.info("Processing combined search for page %d", current_page)
            scraper_bot = ScraperBot()
            results = await scraper_bot.scrape_combined(
                location=validated_params['location'],
                min_price=validated_params['min_price'],
                max_price=validated_params['max_price'],
                min_beds=validated_params['min_beds'],
                max_beds=validated_params['max_beds'],
                listing_type=validated_params['listing_type'],
                page=current_page,
                keywords=validated_params['keywords']
            )
            return jsonify(results)

        # Check cache for current page
        cached_results = db.get_cached_results(
            validated_params['site'],
            validated_params['location'],
            validated_params['min_price'],
            validated_params['max_price'],
            validated_params['min_beds'],
            validated_params['max_beds'],
            validated_params['keywords'],
            validated_params['listing_type'],
            current_page
        )

        if cached_results:
            logger.info("Found valid cached results for page %d", current_page)
            logger.info("Rightmove cached page %d: has_next_page=%s, total_pages=%d", 
                       current_page, cached_results.get('has_next_page', True),
                       cached_results.get('total_pages', 1))
            return jsonify(cached_results)

        # If not in cache, scrape the requested page
        if validated_params['site'] == 'rightmove':
            url = get_final_rightmove_results_url(
                location=validated_params['location'],
                min_price=validated_params['min_price'],
                max_price=validated_params['max_price'],
                min_beds=validated_params['min_beds'],
                max_beds=validated_params.get('max_beds', ''),
                radius="0.0",
                include_sold=True,
                listing_type=validated_params['listing_type'],
                page=current_page  # Pass the current page number
            )
            if not url:
                logger.error("Failed to generate Rightmove URL for params: %s", validated_params)
                return jsonify({
                    "error": "Failed to generate Rightmove URL",
                    "details": "Could not construct valid URL with the provided parameters"
                }), 400

            logger.info("Scraping Rightmove URL: %s", url)
            page_results = scrape_rightmove_from_url(url, page=current_page)

            if not page_results or 'listings' not in page_results:
                logger.error("Invalid response from Rightmove scraper")
                return jsonify({
                    "error": "Invalid response from Rightmove",
                    "details": "Failed to fetch page of results"
                }), 500

            # Ensure we have the has_next_page flag
            if 'has_next_page' not in page_results:
                page_results['has_next_page'] = current_page < page_results.get('total_pages', 1)

            logger.info("Rightmove page %d: has_next_page=%s, total_pages=%d", 
                       current_page, page_results['has_next_page'], 
                       page_results.get('total_pages', 1))

            # Cache the results
            db.cache_results(
                validated_params['site'],
                validated_params['location'],
                validated_params['min_price'],
                validated_params['max_price'],
                validated_params['min_beds'],
                validated_params['max_beds'],
                validated_params['keywords'],
                validated_params['listing_type'],
                current_page,
                page_results
            )

            return jsonify(page_results)
        elif validated_params['site'] == 'zoopla':
            # Scrape the current page and get total pages
            page_results, total_pages = await scrape_zoopla_first_page(
                validated_params['location'],
                validated_params['min_price'],
                validated_params['max_price'],
                validated_params['min_beds'],
                validated_params['max_beds'],
                validated_params['keywords'],
                validated_params['listing_type'],
                current_page
            )

            # Format Zoopla results to match the expected structure
            response_data = {
                "listings": page_results,
                "total_found": len(page_results),
                "total_pages": total_pages,
                "current_page": current_page,
                "has_next_page": current_page < total_pages,
                "search_params": validated_params
            }

            # Only cache if we have valid results
            if page_results and len(page_results) > 0:
                db.cache_results(
                    validated_params['site'],
                    validated_params['location'],
                    validated_params['min_price'],
                    validated_params['max_price'],
                    validated_params['min_beds'],
                    validated_params['max_beds'],
                    validated_params['keywords'],
                    validated_params['listing_type'],
                    current_page,
                    response_data
                )
                logger.info("Cached results for page %d", current_page)
            else:
                logger.info("Skipping cache for page %d - no valid results", current_page)

            return jsonify(response_data)
        else:
            return jsonify({
                "error": "Unsupported site",
                "details": f"Site {validated_params['site']} is not supported for pagination"
            }), 400

    except Exception as e:
        logger.error("Error in next_page: %s", str(e))
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.route('/api/search/combined', methods=['POST'])
@limiter.limit("50/hour") #Example rate limit
async def search_combined():
    """Handle combined property search requests from multiple sites"""
    try:
        # Get search parameters from request
        data = request.get_json()
        logger.info("Received combined search request: %s", data)

        # Validate search parameters
        try:
            validated_data = validate_search_params(data)
            logger.info("Validated search parameters: %s", validated_data)
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return jsonify({"error": str(e)}), 400

        # Initialize scraper bot
        scraper_bot = ScraperBot()

        # Get current page from request or default to 1
        current_page = int(data.get('current_page', 1))
        logger.info(f"Processing combined search for page {current_page}")

        # Use the scrape_combined method directly
        results = await scraper_bot.scrape_combined(
            location=validated_data['location'],
            min_price=validated_data['min_price'],
            max_price=validated_data['max_price'],
            min_beds=validated_data['min_beds'],
            max_beds=validated_data['max_beds'],
            listing_type=validated_data['listing_type'],
            page=current_page,
            keywords=validated_data['keywords']
        )

        # Add search parameters to response
        results['search_params'] = validated_data

        logger.info(f"Combined search completed. Found {results['total_found']} unique listings across {results['total_pages']} pages")
        return jsonify(results)

    except Exception as e:
        logger.error("Error processing combined search request: %s", str(e))
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Add a cleanup route to manually trigger database cleanup
@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Clean up old results from the database"""
    try:
        db.cleanup_old_results()
        return jsonify({"message": "Cleanup completed successfully"})
    except Exception as e:
        logger.error("Error during cleanup: %s", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)