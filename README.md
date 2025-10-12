# 🚀 Price Optimizer AI

An intelligent pricing optimization platform for sustainable and eco-conscious businesses. Combines competitive price intelligence with AI-powered market insights to generate data-driven pricing recommendations.

## ✨ Key Features

### 🎯 **Core Pricing Intelligence**
- **Competitor Price Scraping**: Automated monitoring of 15+ eco-conscious stores
- **Smart Price Optimization**: Multi-scenario recommendations with risk assessment
- **Market Analysis**: Category and store-based competitive intelligence
- **Real-time Progress**: Live monitoring of scraping operations

### 🤖 **AI-Enhanced Insights** (NEW!)
- **LLM Integration**: Google Gemini API for advanced market analysis
- **Smart Positioning**: AI-powered brand positioning recommendations
- **Demand Elasticity**: Intelligent price sensitivity assessment
- **Seasonal Factors**: Context-aware seasonal pricing adjustments
- **Enhanced Confidence**: AI-boosted recommendation reliability

### 🎨 **Modern Web Interface**
- **React/Next.js Frontend**: Responsive dashboard with real-time updates
- **Shadcn/UI Components**: Beautiful, accessible component library
- **CSV Export**: Download recommendations for business analysis
- **Progress Monitoring**: Live tracking of long-running operations

## 🛠️ Technology Stack

### Backend (FastAPI + Python)
- **FastAPI**: Modern async web framework
- **SQLAlchemy**: Database ORM with PostgreSQL/SQLite support
- **BeautifulSoup4**: Web scraping engine with rate limiting
- **Gemini API**: LLM integration for market insights
- **AsyncIO**: Full async support for performance

### Frontend (Next.js + TypeScript)
- **Next.js 14**: App Router with server components
- **TypeScript**: Full type safety
- **Tailwind CSS**: Utility-first styling
- **Shadcn/UI**: High-quality component library
- **Real-time Updates**: Live data streaming

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.13+ with uv
- Optional: Gemini API key for AI features

### 1. Clone & Install

```bash
git clone <repository-url>
cd ai-price-optimizer

# Install backend dependencies
cd api && uv sync

# Install frontend dependencies  
cd .. && pnpm install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key (optional)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Start Development Servers

```bash
# Terminal 1: Start backend
uv run fastapi dev api/main.py

# Terminal 2: Start frontend
pnpm dev
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs

## 🤖 LLM Integration Setup

### Get Gemini API Key
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create an API key
3. Add to your `.env` file:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Test LLM Integration
```bash
uv run python test_llm_integration.py
```

**See [LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md) for detailed setup instructions.**

## 📊 Sample Data

The system includes realistic sample data:
- **6 Eco-Products**: Bamboo sunglasses, steel bottles, cork notebooks, etc.
- **12+ Competitor Prices**: Real pricing data from sustainable brands
- **Complete Scraping Run**: Ready-to-analyze competitive intelligence

## 🎯 API Endpoints

### Core Pricing
- `POST /routes/optimize-price` - Single product optimization
- `POST /routes/optimize-batch` - Batch optimization
- `GET /routes/dashboard-stats` - KPI metrics

### Competitive Intelligence  
- `POST /routes/start-scraping` - Start competitor analysis
- `GET /routes/scraping-progress/{run_id}` - Live progress
- `GET /routes/competitive-analysis/categories` - Market analysis

### Data Export
- `GET /routes/runs/{run_id}/export.csv` - CSV download
- `GET /routes/health` - System health check

## 🌱 Supported Eco-Brands

The scraper monitors these sustainable/ethical stores:
- Made Trade, EarthHero, GOODEE
- Package Free Shop, The Citizenry
- Ten Thousand Villages, NOVICA
- DoneGood, Zero Waste Store
- EcoRoots, Wild Minimalist
- And more...

## 🎨 UI Features

### Dashboard
- Portfolio overview with KPIs
- Margin analysis and profit uplift
- Quick action cards

### Scraping Operations
- Real-time progress monitoring
- Store-by-store status tracking
- Error handling and retry logic

### Competitive Analysis
- Category-based market insights
- Store positioning analysis
- Price distribution charts

### Pricing Recommendations
- Multi-scenario analysis (conservative/recommended/aggressive)
- AI-enhanced insights with confidence scoring
- Constraint-based optimization
- CSV export for business analysis

## 🔧 Configuration

### Database Options
- **PostgreSQL**: Production-ready with full features
- **SQLite**: Development/testing with automatic fallback

### LLM Provider
- **Gemini API**: Advanced market insights (optional)
- **Fallback**: Deterministic pricing when LLM unavailable

### Scraping Settings
- Rate limiting and politeness controls
- Robots.txt respect and error handling
- Configurable store selection

## 🚀 Production Deployment

### Backend
```bash
# Set production environment
DATABASE_URL=postgresql+asyncpg://...
GEMINI_API_KEY=prod_api_key

# Deploy with uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
# Build for production
pnpm build

# Deploy to Vercel/Netlify or serve
pnpm start
```

## 📈 Expected Results

### Confidence Improvements
- **Without LLM**: 0.5-0.7 confidence
- **With LLM**: 0.7-0.9 confidence
- **AI Insights**: Smart positioning, elasticity, seasonality

### Business Impact
- **Data-Driven Pricing**: Replace guesswork with intelligence
- **Competitive Advantage**: Real-time market awareness
- **Margin Optimization**: Balance profitability and competitiveness
- **Time Savings**: Automated analysis vs manual research

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

**Built for sustainable businesses who want to optimize pricing while staying competitive in the eco-conscious marketplace.** 🌱
