"""
Install Dependencies for Excel Export
Installs openpyxl for Excel file export functionality
"""

import subprocess
import sys

def install_excel_dependencies():
    """Install openpyxl for Excel export"""
    
    print("📦 INSTALLING EXCEL EXPORT DEPENDENCIES")
    print("=" * 50)
    
    try:
        print("Installing openpyxl...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
        print("✅ openpyxl installed successfully!")
        
        # Test import
        import openpyxl
        print("✅ openpyxl is working correctly!")
        
        print("\n🎉 Excel export dependencies installed!")
        print("You can now run export_functions_db.py to export to Excel format")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False
    except ImportError:
        print("❌ Installation completed but import test failed")
        return False

if __name__ == "__main__":
    install_excel_dependencies()