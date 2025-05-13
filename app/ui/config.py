"""
Configuration for the BlueAbel AIOS UI.

This module contains centralized configuration settings for the UI,
including theme colors, icons, API endpoints, and other settings.
"""

import os
from typing import Dict, Any

# API configuration
API_ENDPOINT = os.environ.get("BLUEABEL_API_ENDPOINT", "http://localhost:8081")

# Content type configuration
CONTENT_TYPE_ICONS = {
    "url": "🔗",
    "pdf": "📄",
    "text": "📝",
    "audio": "🔊",
    "social": "📱",
    "image": "🖼️",
    "video": "🎬",
    "unknown": "❓"
}

CONTENT_TYPE_COLORS = {
    "url": "#c2e0f4",     # Light blue
    "pdf": "#f5d5cb",     # Light coral
    "text": "#d5f5d5",    # Light green
    "audio": "#e6d9f2",   # Light purple
    "social": "#fce8c5",  # Light orange
    "image": "#d4f5f2",   # Light teal
    "video": "#f2e2ff",   # Light lavender
    "unknown": "#f0f0f0"  # Light gray
}

# UI theme configuration
THEME = {
    "primary_color": "#4a6bf2",  # Blue
    "secondary_color": "#50c878", # Green
    "background_color": "#ffffff",
    "text_color": "#333333",
    "accent_color": "#5e66ff",
    "error_color": "#e74c3c",
    "warning_color": "#f39c12",
    "info_color": "#3498db",
    "success_color": "#2ecc71",
    "font_family": "sans-serif",
    "border_radius": "5px",
    "spacing_unit": "8px",
}

# Dark mode theme
DARK_THEME = {
    "primary_color": "#6c8fff",
    "secondary_color": "#72e59a",
    "background_color": "#1e1e1e",
    "text_color": "#f0f0f0",
    "accent_color": "#5dade2",
    "error_color": "#ff6b6b",
    "warning_color": "#ffb84d",
    "info_color": "#5dade2",
    "success_color": "#5ecc8f",
    "font_family": "sans-serif",
    "border_radius": "5px",
    "spacing_unit": "8px",
}

# LLM Provider configuration
LLM_PROVIDERS = [
    {"name": "Auto", "value": None, "description": "Automatically select based on content"},
    {"name": "OpenAI", "value": "openai", "description": "Use OpenAI models (GPT-3.5, GPT-4)"},
    {"name": "Anthropic", "value": "anthropic", "description": "Use Anthropic models (Claude)"},
    {"name": "Local", "value": "local", "description": "Use local LLM models (Ollama)"}
]

# Model configuration
MODELS = {
    "openai": [
        {"name": "GPT-4 Turbo", "value": "gpt-4-turbo"},
        {"name": "GPT-4", "value": "gpt-4"},
        {"name": "GPT-3.5 Turbo", "value": "gpt-3.5-turbo"}
    ],
    "anthropic": [
        {"name": "Claude 3 Opus", "value": "claude-3-opus-20240229"},
        {"name": "Claude 3 Sonnet", "value": "claude-3-sonnet-20240229"},
        {"name": "Claude 3 Haiku", "value": "claude-3-haiku-20240307"}
    ],
    "local": [
        {"name": "Llama 3", "value": "llama3"},
        {"name": "Mistral", "value": "mistral"},
        {"name": "Llama 3 (8B)", "value": "llama3:8b"},
        {"name": "Mistral (7B)", "value": "mistral:7b"},
        {"name": "Orca Mini", "value": "orca-mini"}
    ]
}

# Page configuration
PAGES = {
    "Content Management": [
        {"name": "Process Content", "icon": "🆕", "description": "Process and analyze new content"},
        {"name": "View Knowledge", "icon": "📚", "description": "Browse and search knowledge repository"},
        {"name": "Search", "icon": "🔍", "description": "Advanced search capabilities"}
    ],
    "Prompt Management": [
        {"name": "Component Editor", "icon": "✏️", "description": "Create and edit prompt components"},
        {"name": "Component Library", "icon": "📋", "description": "Browse and manage prompt components"}
    ],
    "System": [
        {"name": "Dashboard", "icon": "📊", "description": "System status and analytics"},
        {"name": "Settings", "icon": "⚙️", "description": "Configure system settings"},
        {"name": "Google OAuth Setup", "icon": "🔐", "description": "Configure Google OAuth for email access"}
    ]
}

# Default settings
DEFAULT_SETTINGS = {
    "appearance": {
        "theme": "light",
        "date_format": "%Y-%m-%d",
        "time_format": "%H:%M:%S",
        "timezone": "UTC",
    },
    "content": {
        "max_content_length": 100000,
        "auto_tag": True,
        "auto_entities": True,
        "default_content_type": "url",
    },
    "llm": {
        "use_local_llm": False,
        "local_model": "llama3",
        "cloud_provider": "openai",
        "cloud_model": "gpt-3.5-turbo",
        "temperature": 0.0,
    },
    "display": {
        "items_per_page": 10,
        "show_summaries": True,
        "max_summary_length": 200,
    },
}

def get_page_config() -> Dict[str, Any]:
    """
    Get the page configuration for Streamlit.
    """
    return {
        "page_title": "Bluelabel AIOS - ContentMind",
        "page_icon": "🧠",
        "layout": "wide",
        "initial_sidebar_state": "expanded",
        "menu_items": {
            "About": "# Bluelabel AIOS\nAn intelligent content processing system.",
            "Get Help": "https://github.com/yourusername/blueabel_AIOS/issues",
            "Report a Bug": "https://github.com/yourusername/blueabel_AIOS/issues/new"
        }
    }

def get_theme(is_dark_mode: bool = False) -> Dict[str, Any]:
    """
    Get the theme configuration based on current mode.
    
    Args:
        is_dark_mode: Whether to use dark mode theme
        
    Returns:
        Dictionary with theme settings
    """
    return DARK_THEME if is_dark_mode else THEME

def get_custom_css() -> str:
    """
    Get custom CSS for application styling.
    
    Returns:
        CSS string to inject into the application
    """
    return """
    /* Main styles */
    .main {
        background-color: #fcfcfc;
    }
    
    /* Dark mode styles */
    .dark-mode .main {
        background-color: #1e1e1e;
        color: #f0f0f0;
    }
    
    /* Primary button styling - blue instead of red */
    .stButton button,
    button[kind=primary], 
    button[data-baseweb=button][kind=primary] {
        background-color: #4a6bf2 !important;
        border-color: #4a6bf2 !important;
        color: white !important;
        border-radius: 6px;
        font-weight: 500;
    }
    
    /* Button hover state */
    .stButton button:hover,
    button[kind=primary]:hover, 
    button[data-baseweb=button][kind=primary]:hover {
        background-color: #3a5be2 !important;
        border-color: #3a5be2 !important;
    }
    
    /* Form inputs styling */
    .stTextInput input, .stSelectbox, .stTextArea textarea {
        border-radius: 6px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #4a6bf2 !important;
    }
    
    /* Make Streamlit tabs use blue */
    .st-emotion-cache-6qob1r.eczjsme3, 
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #4a6bf2 !important;
        color: white !important;
    }
    
    /* Make the tab indicator blue */
    .st-emotion-cache-1n76uvr.eczjsme4,
    div[role="tablist"] [data-testid="stVerticalBlock"] > div:last-child {
        background-color: #4a6bf2 !important;
    }
    
    /* Card styles */
    .stCard {
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    
    /* Tag styles */
    .tag {
        display: inline-block;
        padding: 4px 10px;
        margin-right: 8px;
        margin-bottom: 8px;
        border-radius: 12px;
        font-size: 0.9em;
    }
    
    /* Dashboard widget styles */
    .widget {
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    
    /* Sidebar improvements */
    .css-1v3fvcr {
        border-right: 1px solid rgba(0, 0, 0, 0.1);
    }
    
    /* Active page highlight */
    .active-page {
        font-weight: bold;
        color: #4a6bf2;
    }
    
    /* IMPORTANT: Fix for duplicate sidebar issue */
    /* This ensures only the first instance of each sidebar element is shown */
    /* Hide duplicate sidebar headers */
    [data-testid="stSidebar"] .sidebar-content:not(:first-of-type) {
        display: none !important;
    }
    
    /* Hide duplicate sidebar elements */
    [data-testid="stSidebar"] > div:not(:first-child) h1,
    [data-testid="stSidebar"] > div:not(:first-child) h2,
    [data-testid="stSidebar"] > div:not(:first-child) h3 {
        display: none !important;
    }
    
    /* Ensure we only show one set of sidebar navigation */
    [data-testid="stSidebar"] {
        overflow-y: auto !important;
    }
    
    /* Control sidebar element duplication */
    [data-testid="stSidebar"] > div > div:nth-child(n+2) .sidebar-navigation {
        display: none !important;
    }
    """