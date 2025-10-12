# Price Optimizer AI - Frontend

A modern, responsive Next.js frontend for the Price Optimizer AI system, designed specifically for eco-conscious brands to monitor competitor pricing and optimize their own pricing strategies.

## 🚀 Features

### Dashboard
- **KPI Overview**: Total products, average margin, potential uplift, and average price change
- **Portfolio Overview**: Complete product catalog with current vs recommended pricing
- **Quick Actions**: Direct access to scraping, analysis, and recommendations
- **Market Insights**: AI-powered competitive intelligence highlights

### Competitor Price Scraping
- **Real-time Progress**: Live monitoring of scraping runs with progress indicators
- **Store Management**: Track scraping status across 15+ eco-conscious competitor stores
- **Product Matching**: Automated matching of scraped products to catalog items
- **Data Export**: CSV export functionality for scraped data

### Competitive Analysis
- **Multi-view Analysis**: Category, store, and price gap analysis with tabbed interface
- **Market Positioning**: Visual indicators for competitive position (above/below/competitive)
- **Price Distribution**: Min/max/median competitor pricing analysis
- **Opportunity Identification**: Highlighted pricing gaps and revenue opportunities

### Pricing Recommendations
- **AI-Powered Optimization**: Advanced recommendations with confidence scoring
- **Scenario Analysis**: Conservative, recommended, and aggressive pricing scenarios
- **Risk Assessment**: Low/medium/high risk categorization with explanations
- **Constraint Management**: Respect for margin requirements and price increase limits
- **Batch Processing**: Optimize entire product catalog at once

## 🛠 Technology Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Icons**: Lucide React
- **State Management**: React hooks with custom API hooks
- **Data Fetching**: Native fetch with error handling

## 📁 Project Structure

```
app/
├── page.tsx                      # Dashboard home page
├── scraping/
│   └── page.tsx                  # Scraping management interface
├── competitive-analysis/
│   └── page.tsx                  # Market analysis dashboard
├── pricing-recommendations/
│   └── page.tsx                  # AI pricing recommendations
├── layout.tsx                    # Root layout with metadata
└── globals.css                   # Global styles

components/
├── navigation.tsx                # Main navigation component
├── app-layout.tsx               # Shared layout wrapper
├── ui/                          # shadcn/ui components
│   ├── card.tsx
│   ├── table.tsx
│   ├── badge.tsx
│   ├── button.tsx
│   ├── tabs.tsx
│   ├── dialog.tsx
│   ├── progress.tsx
│   ├── select.tsx
│   ├── alert.tsx
│   ├── skeleton.tsx
│   └── chart.tsx
└── ui-helpers.tsx               # Custom UI components

lib/
├── api.ts                       # API client and utilities
├── hooks.ts                     # Custom React hooks
└── utils.ts                     # Utility functions
```

## 🎨 Design System

### Color Scheme
- **Primary**: Blue (#3B82F6) - Actions and highlights
- **Success**: Green (#10B981) - Positive metrics and confirmations
- **Warning**: Yellow (#F59E0B) - Alerts and medium risk
- **Danger**: Red (#EF4444) - Errors and high risk
- **Neutral**: Gray (#6B7280) - Text and borders

### Components
- **Cards**: Clean, shadow-based containers for content sections
- **Tables**: Responsive data tables with sorting and filtering
- **Badges**: Status indicators with semantic colors
- **Progress Bars**: Real-time progress indication for long-running operations
- **Dialogs**: Modal interfaces for detailed views and confirmations

### Responsive Design
- **Mobile-first**: Optimized for mobile devices with responsive breakpoints
- **Touch-friendly**: Large click targets and intuitive touch interactions
- **Accessible**: WCAG compliant with proper ARIA labels and keyboard navigation

## 🔗 API Integration

### Endpoints
- `POST /routes/start-scraping` - Initiate scraping run
- `GET /routes/scraping-progress/{runId}` - Monitor scraping progress
- `GET /routes/scraping-results/{runId}` - Retrieve scraped data
- `POST /routes/optimize-price` - Single product optimization
- `POST /routes/optimize-batch` - Batch optimization
- `GET /routes/health` - API health check

### Error Handling
- **Network Errors**: Graceful handling with retry mechanisms
- **API Errors**: User-friendly error messages with suggested actions
- **Loading States**: Skeleton loaders and progress indicators
- **Offline Support**: Cached data and offline indicators

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- pnpm (recommended package manager)

### Installation
```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start
```

### Environment Variables
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000  # Backend API URL
```

## 📊 Key Features Deep Dive

### Real-time Updates
- **Polling**: Automatic progress updates for running scraping operations
- **WebSocket Ready**: Architecture prepared for real-time WebSocket integration
- **State Synchronization**: Consistent state across multiple browser tabs

### Data Visualization
- **Charts**: Integration-ready for competitor price trend visualization
- **Progress Indicators**: Visual progress bars for multi-step operations
- **Status Indicators**: Color-coded status badges throughout the interface

### User Experience
- **Loading States**: Skeleton loading for improved perceived performance
- **Error Recovery**: Clear error messages with recovery suggestions
- **Breadcrumb Navigation**: Clear navigation hierarchy
- **Keyboard Shortcuts**: Power-user keyboard navigation support

### Performance Optimization
- **Code Splitting**: Automatic route-based code splitting via Next.js
- **Image Optimization**: Next.js automatic image optimization
- **Caching**: Intelligent API response caching
- **Bundle Analysis**: Built-in bundle analyzer for optimization

## 🔒 Security Considerations

- **API Authentication**: Ready for JWT token integration
- **CORS Configuration**: Proper cross-origin request handling
- **Input Validation**: Client-side validation with server-side verification
- **XSS Prevention**: Sanitized content rendering

## 🎯 Performance Metrics

- **Core Web Vitals**: Optimized for Google's Core Web Vitals
- **Lighthouse Score**: Target 90+ across all categories
- **Bundle Size**: Optimized bundle splitting and tree shaking
- **Load Time**: Sub-3 second initial page load

## 🧪 Testing Strategy

### Unit Testing
- Component testing with React Testing Library
- Hook testing for custom API hooks
- Utility function testing

### Integration Testing
- API integration testing
- User flow testing
- Cross-browser compatibility testing

### E2E Testing
- Complete user journey testing
- Multi-device testing
- Performance testing under load

## 📈 Analytics & Monitoring

- **User Behavior**: Ready for analytics integration
- **Error Tracking**: Error boundary implementation
- **Performance Monitoring**: Real User Monitoring (RUM) ready
- **API Monitoring**: Request/response time tracking

## 🔄 Deployment

### Vercel (Recommended)
```bash
# Deploy to Vercel
pnpm build
vercel --prod
```

### Docker
```dockerfile
# Dockerfile included for containerized deployment
docker build -t price-optimizer-frontend .
docker run -p 3000:3000 price-optimizer-frontend
```

### Static Export
```bash
# For static hosting
pnpm build
pnpm export
```

## 🤝 Contributing

1. Follow the existing code style and TypeScript patterns
2. Use semantic commit messages
3. Test all new features thoroughly
4. Update documentation for significant changes
5. Ensure accessibility compliance

## 📝 License

Built for eco-conscious brands with competitive pricing intelligence.