#!/bin/bash

# Stardust.ai Chatbot Setup Script
# This script helps you set up the Stardust.ai chatbot quickly

set -e

echo "🌟 Welcome to Stardust.ai Chatbot Setup! 🌟"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[SETUP]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_header "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_header "Checking pip installation..."
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
    else
        print_error "pip3 is not installed. Please install pip first."
        exit 1
    fi
}

# Create virtual environment
create_venv() {
    print_header "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
}

# Activate virtual environment
activate_venv() {
    print_header "Activating virtual environment..."
    source venv/bin/activate
    print_status "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_header "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Dependencies installed successfully"
}

# Create .env file
create_env_file() {
    print_header "Setting up environment configuration..."
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Stardust.ai Chatbot Configuration
OPENAI_API_KEY=your_openai_api_key_here
BING_COOKIE=your_bing_cookie_here
GOOGLE_API_KEY=your_google_api_key_here
DEBUG=false
STREAMING=true
EOF
        print_status ".env file created"
        print_warning "Please edit .env file and add your API keys"
    else
        print_warning ".env file already exists"
    fi
}

# Create Streamlit secrets
create_streamlit_secrets() {
    print_header "Setting up Streamlit configuration..."
    mkdir -p .streamlit
    
    if [ ! -f ".streamlit/secrets.toml" ]; then
        cat > .streamlit/secrets.toml << EOF
# Stardust.ai Chatbot Secrets
openai-key = "your_openai_api_key_here"
debug = false
streaming = true
EOF
        print_status "Streamlit secrets.toml created"
        print_warning "Please edit .streamlit/secrets.toml and add your API keys"
    else
        print_warning "Streamlit secrets.toml already exists"
    fi

    # Create config.toml
    cat > .streamlit/config.toml << EOF
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
EOF
    print_status "Streamlit config.toml created"
}

# Check Docker installation
check_docker() {
    print_header "Checking Docker installation..."
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version 2>&1 | cut -d' ' -f3 | cut -d',' -f1)
        print_status "Docker $DOCKER_VERSION found"
        return 0
    else
        print_warning "Docker not found. You can still run the app with Python."
        return 1
    fi
}

# Main setup function
main() {
    echo "Starting setup process..."
    echo ""
    
    check_python
    check_pip
    create_venv
    activate_venv
    install_dependencies
    create_env_file
    create_streamlit_secrets
    
    echo ""
    echo "🎉 Setup completed successfully! 🎉"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env and .streamlit/secrets.toml with your API keys"
    echo "2. Run the application:"
    echo "   source venv/bin/activate"
    echo "   streamlit run home.py"
    echo ""
    
    if check_docker; then
        echo "🐳 Docker setup available:"
        echo "   docker-compose up -d"
        echo ""
    fi
    
    echo "📚 For more information, check the README.md file"
    echo "🌟 Welcome to Stardust.ai! 🌟"
}

# Run main function
main "$@"
