# PACAS (Property Analysis and Comparison System)

A web application for analyzing and comparing property listings from multiple sources including Rightmove and Zoopla.

## Features

- Multi-source property search (Rightmove, Zoopla)
- Advanced filtering and sorting options
- Responsive design for all devices
- Caching system for improved performance
- Location validation and error handling
- Dark mode support

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pacas.git
cd pacas
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
cp .env.example .env
```
Edit the `.env` file with your configuration settings.

5. Run the application:
```bash
python main.py
```

## Project Structure

- `main.py` - Main application entry point
- `rightmove_bot.py` - Rightmove scraper implementation
- `zoopla_bot.py` - Zoopla scraper implementation
- `scraper_bot.py` - Base scraper functionality
- `static/` - CSS, JavaScript, and other static assets
- `templates/` - HTML templates
- `utils/` - Utility functions
- `scrapers/` - Scraper-specific code

## Development

- Python 3.8+
- Flask web framework
- SQLite database
- Modern CSS with CSS variables
- Responsive design principles

## License

Private - All rights reserved 