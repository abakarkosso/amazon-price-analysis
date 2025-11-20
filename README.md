# Amazon Competitor Analysis

## About

This is a web app I built to analyze Amazon products and their competitors. Give it an ASIN and it'll scrape the product details, find similar competing products, and use GPT-4 to generate insights about pricing and market positioning.

I built this to learn more about web scraping, working with APIs, and integrating LLMs into real applications. It uses Streamlit for the UI, Oxylabs for scraping (Amazon is tough to scrape directly), and OpenAI's API for analysis.

## What it does

### Product Scraping
- Enter any Amazon ASIN and it pulls all the product details (price, rating, images, etc.)
- Works across different Amazon domains (.com, .ca, .co.uk, etc.)
- Handles different locations/zip codes

### Finding Competitors  
- Automatically searches for similar products based on categories
- Grabs the top ~20 competitors
- Uses different sorting strategies (price, rating, featured)

### AI Analysis
- Sends all the competitor data to GPT-4
- Gets back structured insights about market trends, positioning, and pricing
- Includes specific recommendations

### Data & UI
- Saves everything locally in a JSON database (TinyDB)
- Dashboard showing aggregate stats and charts
- Can export data to CSV
- Progress bars for longer operations

## Directory Structure

```
amazon-price-analysis/
├── main.py                    # Streamlit application entry point
├── src/
│   ├── __init__.py           # Package initialization
│   ├── db.py                 # Database operations (TinyDB)
│   ├── llm.py                # LLM analysis and AI integration
│   ├── oxylabs_client.py     # Oxylabs API client and web scraping
│   └── services.py           # Business logic and service layer
├── pyproject.toml            # Project dependencies and metadata
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
└── README.md                 # Project documentation
```

## Setup

### Prerequisites
- Python 3.13 or higher
- Oxylabs account (for web scraping) - [Sign up here](https://oxylabs.io/)
- OpenAI API key (for LLM analysis) - [Get API key here](https://platform.openai.com/api-keys)

### Installation

1. **Clone the Repository:**

```bash
git clone https://github.com/abakarkosso/amazon-price-analysis.git
cd amazon-price-analysis
```

2. **Set Up Virtual Environment:**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. **Install Dependencies:**

```bash
pip install -r requirements.txt
```

Current dependencies:
- `streamlit>=1.49.1` - Web application framework
- `langchain>=0.3.27` - LLM framework and tooling
- `langchain-openai>=0.3.33` - OpenAI integration for LangChain
- `openai>=1.107.2` - OpenAI API client
- `python-dotenv>=1.1.1` - Environment variable management
- `requests>=2.27.0` - HTTP library for API calls
- `tinydb>=4.8.2` - Lightweight JSON database

4. **Configure .env:**

Create `.env` in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API credentials:

```env
# Oxylabs API Credentials
OXYLABS_USERNAME=your_oxylabs_username
OXYLABS_PASSWORD=your_oxylabs_password

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key
```

**Getting API Keys:**
- **Oxylabs**: Sign up at [oxylabs.io](https://oxylabs.io/) and get your credentials from the dashboard
- **OpenAI**: Get your API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

5. **Run the Application:**

```bash
streamlit run main.py
```

The application will open in your browser at `http://localhost:8501`.

### Docker Support

You can also run the application using Docker:

1. **Build the image:**
```bash
docker build -t amazon-analysis .
```

2. **Run the container:**
```bash
docker run -p 8501:8501 --env-file .env amazon-analysis
```

## Usage

### Scraping a Product

1. Enter a product ASIN (e.g., `B0CX23VSAS`)
2. Select the Amazon domain (com, ca, co.uk, de, fr, it, ae)
3. Enter your zip/postal code (e.g., `83980`)
4. Click "Scrape Product"
5. Wait for the product details to be scraped and stored

### Analyzing Competitors

1. Click "Start analyzing competitors" on any product card
2. The system will:
   - Search for competitors based on product categories
   - Scrape detailed information for each competitor
   - Display competitor summary with prices
3. Click "Analyze with LLM" to get AI-powered insights
4. View comprehensive analysis including:
   - Market summary
   - Product positioning
   - Top competitors with key points
   - Actionable recommendations

### Managing Products

- All scraped products are stored in the local database (`data.json`)
- View paginated list of all products
- Each product card shows: image, title, price, brand, domain, and geo location
- Competitors are linked to their parent products

### Refreshing Data

- Click "Refresh Competitors" to re-scrape competitor data
- New products can be scraped at any time
- Database persists between application restarts

## Architecture

The application follows a clean architecture pattern with clear separation of concerns:

- **Presentation Layer** (`main.py`): Streamlit UI components and user interactions
- **Service Layer** (`src/services.py`): Business logic and orchestration
- **Data Layer** (`src/db.py`): Database operations and data persistence
- **API Layer** (`src/oxylabs_client.py`): External API integration and data normalization
- **AI Layer** (`src/llm.py`): LLM integration and analysis generation

## How It Works

### 1. Product Scraping
- Uses Oxylabs API to scrape Amazon product pages
- Extracts detailed information: price, rating, images, categories, brand, etc.
- Normalizes data structure for consistent storage
- Handles multiple Amazon domains and geographic locations

### 2. Competitor Discovery
- Searches Amazon using product title and categories
- Implements multiple search strategies:
  - Featured products
  - Price ascending/descending
  - Average rating
- Deduplicates results and filters invalid products
- Limits results to top 20 competitors for efficiency

### 3. Data Storage
- Stores all scraped data in TinyDB (JSON database)
- Tracks parent-child relationships between products and competitors
- Includes timestamps for data freshness tracking
- Supports efficient querying and searching

### 4. AI Analysis
- Uses OpenAI's GPT-4 model with structured output (Pydantic)
- Generates comprehensive analysis including:
  - Market summary and trends
  - Product positioning analysis
  - Top competitors with key differentiators
  - Actionable pricing and marketing recommendations
- Handles currency conversion and multi-region analysis

## Code Quality

- **Type Hints**: Full type annotation coverage for better code maintainability
- **Docstrings**: Comprehensive documentation for all functions and classes
- **Error Handling**: Robust error handling with user-friendly messages
- **Code Organization**: Clean separation of concerns and modular design
- **Best Practices**: Follows Python PEP 8 style guidelines

## Notes

### API Requirements
- **Oxylabs**: Requires active subscription for web scraping. Rate limits apply based on your plan.
- **OpenAI**: Requires API key with GPT-4 access. Costs are based on API usage.
- Both APIs are necessary for full functionality.

### Data Storage
- All data is stored locally in `data.json` (TinyDB)
- Database file is automatically created on first run
- Data persists between application restarts
- Database file is ignored by git (not committed to repository)

### Rate Limits
- Oxylabs API: Rate limits depend on your subscription plan
- OpenAI API: Rate limits depend on your API tier
- The application includes delays (0.1s) between requests to respect rate limits

### Geographic Support
- Supports multiple Amazon domains: com, ca, co.uk, de, fr, it, ae
- Geographic location affects pricing and availability
- Currency is automatically detected and displayed

### Troubleshooting
- **API Errors**: Check your credentials in `.env` file
- **Scraping Failures**: Verify ASIN is correct and product exists on selected domain
- **LLM Errors**: Ensure OpenAI API key is valid and has GPT-4 access
- **Database Issues**: Delete `data.json` to reset the database

## Limitations

- Requires active Oxylabs and OpenAI API subscriptions
- Rate limits apply based on your API plan
- Data is stored locally (JSON file) - not suitable for production scale
- Scraping may be subject to Amazon's terms of service
- Competitor analysis is limited to top 20 competitors
- Real-time data depends on API availability

## Future Enhancements

- Add support for more Amazon marketplaces
- Implement data export (CSV, JSON, Excel)
- Add price history tracking and alerts
- Implement competitor price monitoring over time
- Add filtering and sorting options for competitors
- Support for batch ASIN processing
- Add visualization charts for price comparisons
- Implement user authentication and multi-user support
- Add database migration to PostgreSQL for production use
- Implement caching to reduce API calls
- Add unit tests and integration tests
- Implement CI/CD pipeline

## License

This project is open source and available under the [MIT License](LICENSE).

## Disclaimer

This tool is for educational and research purposes. Ensure you comply with Amazon's Terms of Service and use web scraping responsibly. Respect rate limits and be mindful of the impact on target servers. The authors are not responsible for any misuse of this tool.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

---

**Built with:** Python, Streamlit, LangChain, OpenAI GPT-4, Oxylabs API, TinyDB

**Author:** Haroun Abakar

**Repository:** [https://github.com/abakarkosso/amazon-price-analysis](https://github.com/abakarkosso/amazon-price-analysis)
