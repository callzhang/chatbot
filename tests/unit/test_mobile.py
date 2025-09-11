"""
Unit tests for mobile optimization features
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tools.mobile import (
    apply_mobile_optimizations, detect_mobile_device, create_touch_friendly_button,
    create_mobile_chat_input, create_responsive_columns, export_mobile_config,
    import_mobile_config, MOBILE_NAV_ITEMS
)

class TestMobileOptimization:
    """Test mobile optimization functionality"""
    
    def test_apply_mobile_optimizations(self):
        """Test applying mobile CSS optimizations"""
        # This test verifies the function doesn't raise an exception
        try:
            apply_mobile_optimizations()
            assert True
        except Exception as e:
            pytest.fail(f"apply_mobile_optimizations raised an exception: {e}")
    
    def test_detect_mobile_device(self):
        """Test mobile device detection"""
        # This is a simple test since the function currently returns True
        result = detect_mobile_device()
        assert isinstance(result, bool)
    
    def test_mobile_nav_items(self):
        """Test mobile navigation items structure"""
        assert isinstance(MOBILE_NAV_ITEMS, list)
        assert len(MOBILE_NAV_ITEMS) > 0
        
        for item in MOBILE_NAV_ITEMS:
            assert 'icon' in item
            assert 'label' in item
            assert 'page' in item
            assert isinstance(item['icon'], str)
            assert isinstance(item['label'], str)
            assert isinstance(item['page'], str)
    
    def test_export_mobile_config(self, mock_streamlit_session):
        """Test exporting mobile configuration"""
        # Set up mock session state
        mock_streamlit_session.update({
            'haptic_feedback': True,
            'auto_scroll': True,
            'voice_input': False,
            'font_size': 16,
            'mobile_theme': '自动',
            'mobile_power_save': False,
            'mobile_data_save': False,
            'mobile_image_quality': '中'
        })
        
        config = export_mobile_config()
        assert isinstance(config, dict)
        assert 'haptic_feedback' in config
        assert 'auto_scroll' in config
        assert 'voice_input' in config
        assert 'font_size' in config
        assert config['haptic_feedback'] is True
        assert config['font_size'] == 16
    
    def test_import_mobile_config(self, mock_streamlit_session):
        """Test importing mobile configuration"""
        config = {
            'haptic_feedback': True,
            'auto_scroll': False,
            'voice_input': True,
            'font_size': 18,
            'mobile_theme': '深色',
            'mobile_power_save': True,
            'mobile_data_save': True,
            'mobile_image_quality': '高'
        }
        
        import_mobile_config(config)
        
        assert mock_streamlit_session['haptic_feedback'] is True
        assert mock_streamlit_session['auto_scroll'] is False
        assert mock_streamlit_session['voice_input'] is True
        assert mock_streamlit_session['font_size'] == 18
        assert mock_streamlit_session['mobile_theme'] == '深色'
    
    def test_mobile_css_content(self):
        """Test that mobile CSS contains expected elements"""
        from tools.mobile import MOBILE_CSS
        
        assert '@media (max-width: 768px)' in MOBILE_CSS
        assert '.mobile-header' in MOBILE_CSS
        assert '.mobile-nav' in MOBILE_CSS
        assert '.touch-button' in MOBILE_CSS
        assert '.mobile-content' in MOBILE_CSS
        assert 'font-size: 16px' in MOBILE_CSS  # iOS zoom prevention
    
    def test_responsive_breakpoints(self):
        """Test responsive design breakpoints"""
        from tools.mobile import MOBILE_CSS
        
        # Check for mobile breakpoint
        assert '@media (max-width: 768px)' in MOBILE_CSS
        
        # Check for tablet breakpoint
        assert '@media (min-width: 769px) and (max-width: 1024px)' in MOBILE_CSS
        
        # Check for desktop breakpoint
        assert '@media (min-width: 1025px)' in MOBILE_CSS
        
        # Check for PWA support
        assert '@media (display-mode: standalone)' in MOBILE_CSS

