from flask import Flask, request, jsonify, render_template, Response, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from scrapers.zoopla import scrape_zoopla, scrape_zoopla_first_page, scrape_zoopla_page
from scrapers.rightmove_scrape import scrape_rightmove_from_url
from scrapers.rightmove_url import get_final_rightmove_results_url
from scrapers.openrent import scrape_openrent
from utils.validators import validate_search_params, ValidationError, rate_limiter
from utils.logger import logger
from utils.database import Database
from utils.security import scraper_api_monitor, get_client_ip, sanitize_location, validate_price_limits
from utils.lead_capture import (init_leads_table, capture_lead, get_all_leads, get_leads_stats, export_leads_csv,
                                create_user, get_user_by_email, update_last_login,
                                add_favorite, remove_favorite, get_user_favorites, is_favorite)
from scraper_bot import ScraperBot
import os
import hashlib
import time
from datetime import datetime, timedelta
import json
import asyncio
import random
import string
import requests
import bcrypt

load_dotenv(override=True)  # Force override any existing env vars
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Store verification codes temporarily (email -> {code, timestamp})
verification_codes = {}

# Configure CORS with security settings
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, 
     resources={r"/api/*": {"origins": allowed_origins}},
     supports_credentials=True,
     max_age=3600)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Initialize database
db = Database()

# Initialize leads table
init_leads_table()

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

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard to view captured leads"""
    return render_template('admin.html')

@app.route('/api/search', methods=['POST'])
@limiter.limit("10 per minute")
async def search():
    """Handle property search requests"""
    try:
        # Check ScraperAPI limits first
        can_proceed, error_msg = scraper_api_monitor.check_limits()
        if not can_proceed:
            logger.warning(f"API limit reached for {get_client_ip(request)}")
            return jsonify({'error': error_msg}), 429
        
        # Get search parameters from request
        data = request.get_json()
        logger.info(f"Received search request from {get_client_ip(request)}: {data}")
        
        # Sanitize location input
        if 'location' in data and data['location']:
            data['location'] = sanitize_location(data['location'])

        # Validate search parameters
        try:
            validated_data = validate_search_params(data)
            logger.info("Validated search parameters: %s", validated_data)
            
            # Additional price validation for security
            valid_price, price_error = validate_price_limits(
                int(validated_data['min_price']), 
                int(validated_data['max_price'])
            )
            if not valid_price:
                return jsonify({'error': price_error}), 400
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return jsonify({"error": str(e)}), 400

        # If site is combined, use ScraperBot's combined method
        if validated_data['site'] == 'combined':
            logger.info("Processing combined search request")
            
            # Check ScraperAPI limits (combined uses 2x requests)
            can_proceed, error_msg = scraper_api_monitor.check_limits()
            if not can_proceed:
                return jsonify({'error': error_msg}), 429
            
            # Initialize scraper bot
            scraper_bot = ScraperBot()
            
            # Get current page from request or default to 1
            current_page = int(data.get('current_page', 1))
            logger.info(f"Processing combined search for page {current_page}")
            
            # Record API usage (combined = 2 requests)
            scraper_api_monitor.record_request()
            scraper_api_monitor.record_request()
            
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
            
            logger.info(f"Combined search completed. Found {results.get('total_found', 0)} unique listings")
            return jsonify(results)

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
        
        # Record ScraperAPI request (cache miss)
        scraper_api_monitor.record_request()

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

@app.route('/api/zoopla', methods=['POST'])
async def get_zoopla_json():
    """Get Zoopla results in JSON format"""
    try:
        data = request.get_json()
        validated_data = validate_search_params(data)

        results = await scrape_zoopla(
            validated_data['location'],
            validated_data['min_price'],
            validated_data['max_price'],
            validated_data['min_beds'],
            validated_data['max_beds'],
            validated_data['keywords'],
            validated_data['listing_type']
        )

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rightmove', methods=['POST']) 
async def get_rightmove_json():
    """Get Rightmove results in JSON format"""
    try:
        data = request.get_json()
        validated_data = validate_search_params(data)

        url = get_final_rightmove_results_url(
            location=validated_data['location'],
            min_price=validated_data['min_price'],
            max_price=validated_data['max_price'],
            min_beds=validated_data['min_beds'],
            max_beds=validated_data['max_beds'],
            radius="0.0",
            include_sold=True,
            listing_type=validated_data['listing_type']
        )

        results = scrape_rightmove_from_url(url)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/combined', methods=['POST'])
async def get_combined_json():
    """Get combined results in JSON format"""
    try:
        data = request.get_json()
        validated_data = validate_search_params(data)

        scraper_bot = ScraperBot()
        results = await scraper_bot.scrape_combined(
            location=validated_data['location'],
            min_price=validated_data['min_price'],
            max_price=validated_data['max_price'],
            min_beds=validated_data['min_beds'],
            max_beds=validated_data['max_beds'],
            listing_type=validated_data['listing_type'],
            keywords=validated_data['keywords']
        )

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


    #         # Only cache if we have valid results
    #         listings = results.get("listings", []) if isinstance(results, dict) else results
    #         if listings and len(listings) > 0:
    #             db.cache_results(
    #                 validated_data['site'],
    #                 validated_data['location'],
    #                 validated_data['min_price'],
    #                 validated_data['max_price'],
    #                 validated_data['min_beds'],
    #                 validated_data['max_beds'],
    #                 validated_data['keywords'],
    #                 validated_data['listing_type'],
    #                 1,  # First page
    #                 response_data
    #             )
    #             logger.info("Cached valid results with %d listings", len(listings))
    #         else:
    #             logger.info("Skipping cache for empty results")

    #         return jsonify(response_data)

    # except Exception as e:
    #     logger.error("Error processing search request: %s", str(e))
    #     return jsonify({
    #         "error": "Internal server error",
    #         "details": str(e)
    #     }), 500

@app.route('/api/search/next-page', methods=['POST'])
@limiter.limit("20 per minute")
async def next_page():
    """Handle loading the next page of results"""
    try:
        # Check ScraperAPI limits
        can_proceed, error_msg = scraper_api_monitor.check_limits()
        if not can_proceed:
            return jsonify({'error': error_msg}), 429
        
        # Get search parameters and current page from request
        data = request.get_json()
        search_params = data.get('search_params', {})
        current_page = data.get('current_page', 1)

        logger.info(f"Next page request from {get_client_ip(request)}: page {current_page}")
        logger.info("Processing next page request for site: %s, page: %d", search_params['site'], current_page)
        
        # Sanitize location
        if 'location' in search_params and search_params['location']:
            search_params['location'] = sanitize_location(search_params['location'])

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
        
        # Record API usage (cache miss)
        scraper_api_monitor.record_request()

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
@limiter.limit("5 per minute")
async def search_combined():
    """Handle combined property search requests from multiple sites"""
    try:
        # Check ScraperAPI limits (combined uses 2x requests)
        can_proceed, error_msg = scraper_api_monitor.check_limits()
        if not can_proceed:
            return jsonify({'error': error_msg}), 429
        
        # Get search parameters from request
        data = request.get_json()
        logger.info(f"Combined search from {get_client_ip(request)}: {data}")
        
        # Sanitize location
        if 'location' in data and data['location']:
            data['location'] = sanitize_location(data['location'])

        # Validate search parameters
        try:
            validated_data = validate_search_params(data)
            logger.info("Validated search parameters: %s", validated_data)
            
            # Validate price limits for security
            valid_price, price_error = validate_price_limits(
                int(validated_data['min_price']), 
                int(validated_data['max_price'])
            )
            if not valid_price:
                return jsonify({'error': price_error}), 400
        except ValidationError as e:
            logger.error("Validation error: %s", str(e))
            return jsonify({"error": str(e)}), 400

        # Initialize scraper bot
        scraper_bot = ScraperBot()

        # Get current page from request or default to 1
        current_page = int(data.get('current_page', 1))
        logger.info(f"Processing combined search for page {current_page}")
        
        # Record API usage (combined = 2 requests)
        scraper_api_monitor.record_request()
        scraper_api_monitor.record_request()

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

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429

# Health check and stats endpoint
@app.route('/api/health', methods=['GET'])
@limiter.exempt
def health_check():
    """API health check and usage statistics"""
    try:
        usage_stats = scraper_api_monitor.get_usage_stats()
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "api_usage": usage_stats
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

# Email verification functions
def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Send verification code via SMTP"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # SMTP configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL', 'noreply@pacashomes.co.uk')
        sender_password = os.getenv('SENDER_PASSWORD', '')
        sender_name = os.getenv('SENDER_NAME', 'PacasHomes')
        
        if not sender_password:
            logger.warning("SMTP password not configured. Verification code: " + code)
            return False
        
        # Email HTML content
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Email Verification</h1>
                </div>
                <div style="padding: 30px; background: #f9f9f9; border-radius: 10px; margin-top: 20px;">
                    <p style="font-size: 16px; color: #333;">Thank you for creating an account with PacasHomes!</p>
                    <p style="font-size: 16px; color: #333;">Your verification code is:</p>
                    <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <h2 style="color: #667eea; font-size: 32px; letter-spacing: 5px; margin: 0;">{code}</h2>
                    </div>
                    <p style="font-size: 14px; color: #666;">This code will expire in 10 minutes.</p>
                    <p style="font-size: 14px; color: #666;">If you didn't request this code, please ignore this email.</p>
                </div>
                <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
                    <p>© 2026 Aztura LTD trading as PacasHomes. All rights reserved.</p>
                    <p style="margin-top: 5px;">Company No: 16805710</p>
                </div>
            </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Email Verification
        
        Thank you for creating an account with PacasHomes!
        
        Your verification code is: {code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        
        © 2026 Aztura LTD trading as PacasHomes. All rights reserved.
        Company No: 16805710
        """
        
        # Create email message
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart('alternative')
        message['Subject'] = "Verify Your Email - PacasHomes"
        message['From'] = f"{sender_name} <{sender_email}>"
        message['To'] = email
        
        # Attach plain text and HTML versions
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        message.attach(part1)
        message.attach(part2)
        
        # SMTP configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_password = os.getenv('SENDER_PASSWORD', '')
        
        if not sender_password:
            logger.warning(f"SMTP password not configured. Verification code for {email}: {code}")
            return False
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Enable TLS encryption
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        logger.info(f"Verification email sent to {email} via SMTP")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False

# Send verification code endpoint
@app.route('/api/send-verification-code', methods=['POST'])
@limiter.limit("5 per minute")
def send_verification_code():
    """Send verification code to email"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email or '@' not in email:
            return jsonify({"error": "Valid email is required"}), 400
        
        # Generate code
        code = generate_verification_code()
        
        # Store code with timestamp
        verification_codes[email] = {
            'code': code,
            'timestamp': time.time()
        }
        
        # Send email
        email_sent = send_verification_email(email, code)
        
        if not email_sent:
            # For development/testing - return code if email fails
            logger.warning(f"Email not sent. Verification code for {email}: {code}")
        
        return jsonify({
            "success": True,
            "message": "Verification code sent to your email",
            "debug_code": code if not email_sent else None  # Only for testing
        }), 200
        
    except Exception as e:
        logger.error(f"Error sending verification code: {str(e)}")
        return jsonify({"error": "Failed to send verification code"}), 500

# Verify code endpoint
@app.route('/api/verify-code', methods=['POST'])
@limiter.limit("10 per minute")
def verify_code():
    """Verify the code entered by user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return jsonify({"error": "Email and code are required"}), 400
        
        # Check if code exists for this email
        if email not in verification_codes:
            return jsonify({"error": "No verification code found. Please request a new one."}), 400
        
        stored_data = verification_codes[email]
        stored_code = stored_data['code']
        timestamp = stored_data['timestamp']
        
        # Check if code expired (10 minutes)
        if time.time() - timestamp > 600:
            del verification_codes[email]
            return jsonify({"error": "Verification code expired. Please request a new one."}), 400
        
        # Verify code
        if code != stored_code:
            return jsonify({"error": "Invalid verification code"}), 400
        
        # Code is valid - remove it
        del verification_codes[email]
        
        return jsonify({
            "success": True,
            "message": "Email verified successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error verifying code: {str(e)}")
        return jsonify({"error": "Verification failed"}), 500

# User registration endpoint
@app.route('/api/register', methods=['POST'])
@limiter.limit("5 per minute")
def register_user():
    """Register a new user account"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not email or '@' not in email:
            return jsonify({"error": "Valid email is required"}), 400
        
        if not password or len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        if not name:
            return jsonify({"error": "Name is required"}), 400
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({"error": "Email already registered"}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_id = create_user(email, password_hash, name, phone, email_verified=True)
        
        if not user_id:
            return jsonify({"error": "Failed to create account"}), 500
        
        # Set session
        session['user_id'] = user_id
        session['user_email'] = email
        session['user_name'] = name
        
        logger.info(f"User registered: {email}")
        
        return jsonify({
            "success": True,
            "message": "Account created successfully",
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "phone": phone
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

# User login endpoint
@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
def login_user():
    """Login user"""
    try:
        data = request.get_json()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Get user
        user = get_user_by_email(email)
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Update last login
        update_last_login(user['id'])
        
        # Set session
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_name'] = user['name']
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            "success": True,
            "message": "Logged in successfully",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user['name'],
                "phone": user['phone']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

# User logout endpoint
@app.route('/api/logout', methods=['POST'])
def logout_user():
    """Logout user"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

# Get current user endpoint
@app.route('/api/user', methods=['GET'])
def get_current_user():
    """Get current logged in user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    return jsonify({
        "success": True,
        "user": {
            "id": session['user_id'],
            "email": session['user_email'],
            "name": session['user_name']
        }
    }), 200

# Add favorite endpoint
@app.route('/api/favorites/add', methods=['POST'])
@limiter.limit("30 per minute")
def add_favorite_property():
    """Add property to favorites"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        data = request.get_json()
        
        property_url = data.get('property_url', '').strip()
        property_title = data.get('property_title', '').strip()
        property_price = data.get('property_price', '').strip()
        property_image = data.get('property_image', '').strip()
        site = data.get('site', '').strip()
        bedrooms = data.get('bedrooms', '').strip()
        location = data.get('location', '').strip()
        
        if not property_url or not site:
            return jsonify({"error": "Property URL and site are required"}), 400
        
        success = add_favorite(
            session['user_id'],
            property_url,
            property_title,
            property_price,
            property_image,
            site,
            bedrooms,
            location
        )
        
        if success:
            return jsonify({"success": True, "message": "Added to favorites"}), 200
        else:
            return jsonify({"error": "Already in favorites"}), 400
        
    except Exception as e:
        logger.error(f"Error adding favorite: {str(e)}")
        return jsonify({"error": "Failed to add favorite"}), 500

# Remove favorite endpoint
@app.route('/api/favorites/remove', methods=['POST'])
@limiter.limit("30 per minute")
def remove_favorite_property():
    """Remove property from favorites"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        data = request.get_json()
        property_url = data.get('property_url', '').strip()
        
        if not property_url:
            return jsonify({"error": "Property URL is required"}), 400
        
        success = remove_favorite(session['user_id'], property_url)
        
        if success:
            return jsonify({"success": True, "message": "Removed from favorites"}), 200
        else:
            return jsonify({"error": "Failed to remove favorite"}), 500
        
    except Exception as e:
        logger.error(f"Error removing favorite: {str(e)}")
        return jsonify({"error": "Failed to remove favorite"}), 500

# Get favorites endpoint
@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    """Get user's favorite properties"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    try:
        favorites = get_user_favorites(session['user_id'])
        return jsonify({"success": True, "favorites": favorites}), 200
    except Exception as e:
        logger.error(f"Error getting favorites: {str(e)}")
        return jsonify({"error": "Failed to get favorites"}), 500

# Check if property is favorite endpoint
@app.route('/api/favorites/check', methods=['POST'])
def check_favorite():
    """Check if property is in favorites"""
    if 'user_id' not in session:
        return jsonify({"is_favorite": False}), 200
    
    try:
        data = request.get_json()
        property_url = data.get('property_url', '').strip()
        
        if not property_url:
            return jsonify({"is_favorite": False}), 200
        
        is_fav = is_favorite(session['user_id'], property_url)
        return jsonify({"is_favorite": is_fav}), 200
    except Exception as e:
        logger.error(f"Error checking favorite: {str(e)}")
        return jsonify({"is_favorite": False}), 200

# Lead capture endpoint
@app.route('/api/capture-lead', methods=['POST'])
@limiter.limit("20 per minute")
def capture_user_lead():
    """Capture lead when user clicks to view property"""
    try:
        data = request.get_json()
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        property_url = data.get('property_url', '').strip()
        site = data.get('site', '').strip()
        
        if not email or '@' not in email:
            return jsonify({"error": "Valid email is required"}), 400
        
        if not property_url or not site:
            return jsonify({"error": "Property URL and site are required"}), 400
        
        # Optional fields
        property_title = data.get('property_title', '')
        property_price = data.get('property_price', '')
        phone = data.get('phone', '').strip()
        name = data.get('name', '').strip()
        wants_callback = data.get('wants_callback', False)
        lead_type = data.get('lead_type', 'property_view')
        
        # Get user IP
        ip_address = get_client_ip(request)
        
        # Capture the lead
        success = capture_lead(
            email=email,
            property_url=property_url,
            property_title=property_title,
            property_price=property_price,
            site=site,
            ip_address=ip_address,
            phone=phone,
            name=name,
            wants_callback=wants_callback,
            lead_type=lead_type
        )
        
        if success:
            logger.info(f"Lead captured: {email} for {site}")
            return jsonify({"success": True, "message": "Lead captured successfully"})
        else:
            return jsonify({"error": "Failed to capture lead"}), 500
            
    except Exception as e:
        logger.error(f"Error capturing lead: {e}")
        return jsonify({"error": str(e)}), 500

# Admin endpoint to view leads stats
@app.route('/api/admin/leads/stats', methods=['GET'])
@limiter.limit("10 per minute")
def leads_statistics():
    """Get statistics about captured leads"""
    try:
        stats = get_leads_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting leads stats: {e}")
        return jsonify({"error": str(e)}), 500

# Admin endpoint to export leads as CSV
@app.route('/api/admin/leads/export', methods=['GET'])
@limiter.limit("5 per hour")
def export_leads():
    """Export all leads as CSV"""
    try:
        csv_data = export_leads_csv()
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=leads.csv'}
        )
    except Exception as e:
        logger.error(f"Error exporting leads: {e}")
        return jsonify({"error": str(e)}), 500

# Admin endpoint to view recent leads
@app.route('/api/admin/leads', methods=['GET'])
@limiter.limit("10 per minute")
def get_leads():
    """Get all captured leads (recent 100)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        leads = get_all_leads(limit=limit)
        return jsonify({"leads": leads, "count": len(leads)})
    except Exception as e:
        logger.error(f"Error getting leads: {e}")
        return jsonify({"error": str(e)}), 500

# Add a cleanup route to manually trigger database cleanup
@app.route('/api/cleanup', methods=['POST'])
@limiter.limit("1 per hour")
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