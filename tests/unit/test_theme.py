"""
Unit tests for theme management system
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.theme import (
    initialize_theme, get_current_theme, set_theme, get_theme_config,
    apply_theme_css, create_theme_selector, get_theme_icon,
    export_theme_config, import_theme_config, THEMES
)

class TestThemeManagement:
    """Test theme management functionality"""
    
    def test_initialize_theme(self, mock_streamlit_session):
        """Test theme initialization"""
        initialize_theme()
        assert 'theme' in mock_streamlit_session
        assert 'theme_config' in mock_streamlit_session
        assert mock_streamlit_session['theme'] == 'light'
    
    def test_get_current_theme(self, mock_streamlit_session):
        """Test getting current theme"""
        mock_streamlit_session['theme'] = 'dark'
        theme = get_current_theme()
        assert theme == 'dark'
    
    def test_set_theme(self, mock_streamlit_session):
        """Test setting theme"""
        result = set_theme('dark')
        assert result is True
        assert mock_streamlit_session['theme'] == 'dark'
        assert mock_streamlit_session['theme_config'] == THEMES['dark']
    
    def test_set_invalid_theme(self, mock_streamlit_session):
        """Test setting invalid theme"""
        result = set_theme('invalid_theme')
        assert result is False
    
    def test_get_theme_config(self, mock_streamlit_session):
        """Test getting theme configuration"""
        config = get_theme_config('light')
        assert config == THEMES['light']
        assert 'primaryColor' in config
        assert 'backgroundColor' in config
        assert 'textColor' in config
    
    def test_get_theme_config_default(self, mock_streamlit_session):
        """Test getting default theme configuration"""
        mock_streamlit_session['theme'] = 'nonexistent'
        config = get_theme_config()
        assert config == THEMES['light']  # Should fallback to light theme
    
    def test_apply_theme_css(self):
        """Test applying theme CSS"""
        # This test verifies the function doesn't raise an exception
        try:
            apply_theme_css('light')
            assert True
        except Exception as e:
            pytest.fail(f"apply_theme_css raised an exception: {e}")
    
    def test_get_theme_icon(self):
        """Test getting theme icons"""
        assert get_theme_icon('light') == '☀️'
        assert get_theme_icon('dark') == '🌙'
        assert get_theme_icon('stardust') == '✨'
        assert get_theme_icon('ocean') == '🌊'
        assert get_theme_icon('nonexistent') == '🎨'
    
    def test_export_theme_config(self):
        """Test exporting theme configuration"""
        config_json = export_theme_config('light')
        assert isinstance(config_json, str)
        assert 'primaryColor' in config_json
        assert 'backgroundColor' in config_json
    
    def test_import_theme_config(self):
        """Test importing theme configuration"""
        valid_config = '{"primaryColor": "#FF0000", "backgroundColor": "#FFFFFF", "secondaryBackgroundColor": "#F0F0F0", "textColor": "#000000"}'
        result = import_theme_config(valid_config)
        assert result is True
        
        # Test invalid JSON
        invalid_config = 'invalid json'
        result = import_theme_config(invalid_config)
        assert result is False
    
    def test_theme_css_content(self):
        """Test that theme CSS contains expected elements"""
        from tools.theme import THEME_CSS
        
        for theme_name, css in THEME_CSS.items():
            assert '.stApp' in css
            assert '.main .block-container' in css
            assert '.stChatMessage' in css
    
    def test_theme_colors(self):
        """Test theme color configurations"""
        for theme_name, config in THEMES.items():
            assert 'primaryColor' in config
            assert 'backgroundColor' in config
            assert 'secondaryBackgroundColor' in config
            assert 'textColor' in config
            assert 'font' in config
            
            # Validate color format (hex colors)
            assert config['primaryColor'].startswith('#')
            assert config['backgroundColor'].startswith('#')
            assert config['secondaryBackgroundColor'].startswith('#')
            assert config['textColor'].startswith('#')

