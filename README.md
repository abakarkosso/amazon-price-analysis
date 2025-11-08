# Amazon Price Competitor Analysis

A full-stack web application for analyzing Amazon product prices and competitors using web scraping and AI-powered insights. This project demonstrates expertise in API integration, data processing, LLM integration, and modern Python development practices.

## 🚀 Key Features

- 🔍 **Product Scraping**: Scrape Amazon product details by ASIN across multiple domains (com, ca, co.uk, de, fr, it, ae)
- 📊 **Competitor Discovery**: Automatically find and analyze competitors based on product categories using multiple search strategies
- 🤖 **AI-Powered Analysis**: Generate intelligent market insights and recommendations using OpenAI GPT-4
- 💾 **Data Storage**: Efficient local data storage using TinyDB with proper data normalization
- 🌍 **Multi-Region Support**: Analyze products from different Amazon domains and geographic locations
- 📈 **Price Comparison**: Compare prices, ratings, and key features across competitors
- 🎨 **Interactive UI**: User-friendly Streamlit interface with real-time progress tracking
- ⚡ **Error Handling**: Comprehensive error handling with user-friendly feedback

## 🛠️ Technologies Used

- **Python 3.13+**: Modern Python with type hints and best practices
- **Streamlit**: Interactive web application framework
- **LangChain**: LLM framework for structured AI interactions
- **OpenAI GPT-4**: Advanced AI analysis and insights
- **Oxylabs API**: Professional web scraping service
- **TinyDB**: Lightweight JSON-based database
- **Pydantic**: Data validation and serialization
- **Requests**: HTTP client for API interactions

## Prerequisites

- Python 3.13 or higher
- Oxylabs account (for web scraping)
- OpenAI API key (for LLM analysis)

## 📦 Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd AmazonPriceCompetitorAnalysisLLM-main
```

2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

Or install as a package:
```bash
pip install -e .
```

4. **Set up environment variables:**
```bash
cp .env.example .env
```

Edit `.env` and add your API credentials:
```env
OXYLABS_USERNAME=your_oxylabs_username
OXYLABS_PASSWORD=your_oxylabs_password
OPENAI_API_KEY=your_openai_api_key
```

## 🚀 Quick Start

1. **Start the application:**
```bash
streamlit run main.py
```

2. **Open your browser:**
Navigate to `http://localhost:8501`

3. **Scrape a product:**
   - Enter a product ASIN (e.g., `B0CX23VSAS`)
   - Select the Amazon domain
   - Enter your zip/postal code
   - Click "Scrape Product"

4. **Analyze competitors:**
   - Click "Start analyzing competitors" on any product card
   - Wait for competitor discovery to complete
   - Click "Analyze with LLM" for AI-powered insights

## 🏗️ Architecture

The application follows a clean architecture pattern with clear separation of concerns:

- **Presentation Layer** (`main.py`): Streamlit UI components and user interactions
- **Service Layer** (`src/services.py`): Business logic and orchestration
- **Data Layer** (`src/db.py`): Database operations and data persistence
- **API Layer** (`src/oxylabs_client.py`): External API integration and data normalization
- **AI Layer** (`src/llm.py`): LLM integration and analysis generation

## 📁 Project Structure

```
.
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

## 🔄 How It Works

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

## Environment Variables

- `OXYLABS_USERNAME`: Your Oxylabs username
- `OXYLABS_PASSWORD`: Your Oxylabs password
- `OPENAI_API_KEY`: Your OpenAI API key

## 💻 Code Quality

- **Type Hints**: Full type annotation coverage for better code maintainability
- **Docstrings**: Comprehensive documentation for all functions and classes
- **Error Handling**: Robust error handling with user-friendly messages
- **Code Organization**: Clean separation of concerns and modular design
- **Best Practices**: Follows Python PEP 8 style guidelines

## 📚 Dependencies

See `requirements.txt` or `pyproject.toml` for complete dependency list:

- `streamlit>=1.49.1`: Web application framework
- `langchain>=0.3.27`: LLM framework and tooling
- `langchain-openai>=0.3.33`: OpenAI integration for LangChain
- `openai>=1.107.2`: OpenAI API client
- `python-dotenv>=1.1.1`: Environment variable management
- `requests>=2.27.0`: HTTP library for API calls
- `tinydb>=4.8.2`: Lightweight JSON database

## Limitations

- Requires active Oxylabs and OpenAI API subscriptions
- Rate limits apply based on your API plan
- Data is stored locally (JSON file)
- Scraping may be subject to Amazon's terms of service

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Disclaimer

This tool is for educational and research purposes. Ensure you comply with Amazon's Terms of Service and use web scraping responsibly. Respect rate limits and be mindful of the impact on target servers.

