# PixelLens

🔍 **Developer-focused tracking pixel validation tool using step-by-step test cases**

PixelLens is a developer-focused tracking pixel validation tool that provides:
- **Step-by-step test cases** with per-step pixel validation
- **AI-driven user interactions** via browser-use for complex actions
- **Network-layer monitoring** for accurate pixel detection
- **Developer-friendly CLI** for CI/CD integration

## 🎯 Key Features

### 📋 Step-by-Step Test Cases
- Define test cases as a series of validation steps
- Validate expected pixels at each step of user journey
- Clear success/failure feedback per step
- Perfect for debugging conversion funnels

### ✨ AI-Powered Interactions
- Natural language action descriptions for complex interactions
- Basic page load validation without AI overhead
- Handles dynamic content and layout changes
- Real user behavior simulation

### 🔍 Network-First Detection
- Monitors HTTP requests, not DOM elements
- Resilient to website redesigns
- Comprehensive pixel classification
- Per-step pixel detection

### 🛠️ Developer Experience
- Simple CLI interface
- YAML configuration files as test suites
- CI/CD ready
- JSON output format

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd pixellens

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package (makes 'plens' command available)
pip install -e .

# Install Playwright browsers
python -m playwright install
```

### Basic Usage

```bash
# Run all test cases in config file
plens --config sample-config.yml

# Run a specific test case
plens --config sample-config.yml --test-case ecommerce_complete_flow

# Run all test cases and save results
plens --config sample-config.yml --save all-results.json

# Run specific test case and save results
plens --config sample-config.yml --test-case basic_pageload --save results.json
```

**Alternative**: If you don't want to install the package, you can run it directly:

```bash
# Run all test cases without installing
python -m cli.main --config sample-config.yml

# Run specific test case without installing
python -m cli.main --config sample-config.yml --test-case basic_pageload
```

## 📖 Configuration

### Test Case Structure

Create `config.yml` with step-by-step test cases:

```yaml
test_cases:
  # E-commerce funnel validation
  ecommerce_complete_flow:
    description: "Full e-commerce purchase funnel validation"
    start_url: "https://demo.evershop.io"
    steps:
      - name: "Page Load"
        action: "load_page"
        expect_pixels: ["GA4 page_view", "Facebook PageView"]
        
      - name: "View Product"  
        action: "Click on any product link"
        expect_pixels: ["GA4 view_item", "Facebook ViewContent"]
        
      - name: "Add to Cart"
        action: "Click add to cart button"  
        expect_pixels: ["GA4 add_to_cart", "Facebook AddToCart"]
        
      - name: "Start Checkout"
        action: "Navigate to checkout page"
        expect_pixels: ["GA4 begin_checkout", "Facebook InitiateCheckout"]

  # Simple page load test
  basic_pageload:
    description: "Simple page load pixel validation"
    start_url: "https://example.com"
    steps:
      - name: "Page Load"
        action: "load_page"
        expect_pixels: ["GA4 page_view", "Hotjar"]

# Global settings
default_config:
  timeout: 30 # Timeout in seconds per step
  headless: true # Run browser in headless mode
  wait_for_network_idle: true # Wait for network to be idle between steps
  step_delay: 2 # Seconds to wait between steps for pixels to fire
```

### Action Types

- **`load_page`**: Basic page load validation (no AI, fast execution)
- **Any other description**: Uses AI agent to execute the action (e.g., "Click add to cart button", "Fill out email form")

## 🔬 Example Output

### Step-by-Step Results
```json
{
  "test_case": "ecommerce_complete_flow",
  "url": "https://demo.evershop.io",
  "success": true,
  "execution_time": 45.67,
  "steps": [
    {
      "step_name": "Page Load",
      "action": "load_page",
      "success": true,
      "execution_time": 3.21,
      "expected_pixels": ["GA4 page_view", "Facebook PageView"],
      "detected_pixels": ["Google Analytics 4", "Facebook Pixel"],
      "passed_pixels": ["GA4 page_view", "Facebook PageView"],
      "failed_pixels": []
    },
    {
      "step_name": "View Product",
      "action": "Click on any product link",
      "success": true,
      "execution_time": 8.45,
      "expected_pixels": ["GA4 view_item", "Facebook ViewContent"],
      "detected_pixels": ["Google Analytics 4", "Facebook Pixel"],
      "passed_pixels": ["GA4 view_item", "Facebook ViewContent"],
      "failed_pixels": []
    }
  ]
}
```

## 🏗️ Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Interface │───▶│  Test Executor   │───▶│ Network Monitor │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   browser-use    │
                       │   AI Agent       │
                       └──────────────────┘
```

**Test Executor**: Orchestrates step-by-step test case execution

**Network Monitor**: Captures and classifies HTTP requests per step

**browser-use AI Agent**: Executes complex actions using natural language

**CLI Interface**: Developer-friendly command line tool with JSON output

### Supported Tracking Platforms

- **Google Analytics** (GA4, Universal)
- **Google Tag Manager**
- **Facebook Pixel**
- **Hotjar**
- **Segment**
- **Mixpanel**
- **Amplitude** 
- **Klaviyo**
- **Snowplow**
- **Pinterest**
- **TikTok**
- **LinkedIn**
- **Twitter**
- **Snapchat**
- And more...

## 🎯 Use Cases

### E-commerce Conversion Tracking
Validate that each step of your purchase funnel fires the correct tracking pixels:
- Product page views → `view_item` events
- Add to cart → `add_to_cart` events  
- Checkout initiation → `begin_checkout` events

### Lead Generation Validation
Ensure form submissions and signups trigger lead tracking:
- Newsletter signups → Lead generation pixels
- Contact form submissions → Conversion tracking
- Account creation → Registration events

### Content Engagement Testing
Verify engagement tracking on content sites:
- Page views → Analytics page tracking
- Scroll events → Engagement pixels
- Social sharing → Social media pixels

### CI/CD Integration
Run pixel validation as part of your deployment pipeline:
- Automated testing on staging environments
- Regression testing for tracking implementations
- Pre-production validation

## 🚧 Current Status

**Production Ready Features:**
- Step-by-step test case execution
- Basic page load validation
- AI-powered complex interactions
- Network-layer pixel detection
- JSON output format

**Known Limitations:**
1. **AI Action Reliability**: Complex actions may occasionally fail
2. **Pixel Pattern Coverage**: Some niche tracking platforms may not be detected
3. **Performance**: Not optimized for large-scale batch processing
4. **Browser Dependencies**: Requires Playwright browser installation

## 🎯 Advantages Over Existing Tools

### vs ObservePoint/DataTrue
- **10x cheaper**: No $25k+ annual licensing fees
- **Developer-native**: CLI, Git integration, CI/CD ready
- **Step-by-step validation**: Precise failure identification
- **Layout-independent**: Network monitoring vs DOM inspection

### vs Traditional Testing Tools
- **Zero maintenance**: No CSS selector updates needed
- **Real behavior**: AI agent simulates actual user interactions
- **Comprehensive**: Validates pixels at each step of user journey
- **Debugging-friendly**: Clear step-by-step failure reporting

## 🔮 Future Roadmap

- **Enhanced AI Actions**: More reliable complex interaction execution
- **Visual Test Builder**: GUI for creating test cases
- **Cloud Service**: Hosted validation with API access
- **CI/CD Plugins**: GitHub Actions, Jenkins, CircleCI integrations
- **Enterprise Features**: Team management, advanced analytics
- **Browser Extensions**: Real-time pixel debugging for developers

## 📄 License

AGPL-3.0 License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions and feedback welcome!

---

**Built with**: Python, Playwright, browser-use, Click, Rich