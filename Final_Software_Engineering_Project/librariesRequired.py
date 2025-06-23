"""
Medical Testing System - Required Libraries
==========================================

This file contains all the required libraries and dependencies for the Medical Testing System.
Run this file to check which libraries are installed and get installation commands.

Usage:
    python libraries_required.py

Author: Medical Testing System Team
Date: 2024
"""

import sys
import subprocess
import importlib
from typing import List, Tuple, Dict

# =============================================================================
# REQUIRED LIBRARIES CONFIGURATION
# =============================================================================

# Core dependencies (absolutely required)
CORE_DEPENDENCIES = {
    'PyQt5': {
        'install_cmd': 'pip install PyQt5',
        'description': 'GUI framework for the desktop application interface',
        'modules_to_check': ['PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui'],
        'critical': True
    },
    'pandas': {
        'install_cmd': 'pip install pandas',
        'description': 'Data manipulation and Excel export functionality',
        'modules_to_check': ['pandas'],
        'critical': True
    },
    'matplotlib': {
        'install_cmd': 'pip install matplotlib',
        'description': 'Chart generation and data visualization',
        'modules_to_check': ['matplotlib.pyplot', 'matplotlib.backends.backend_qt5agg'],
        'critical': True
    },
    'reportlab': {
        'install_cmd': 'pip install reportlab',
        'description': 'PDF report generation and document creation',
        'modules_to_check': ['reportlab.lib.pagesizes', 'reportlab.platypus', 'reportlab.lib.styles'],
        'critical': True
    },
    'python-barcode': {
        'install_cmd': 'pip install python-barcode[images]',
        'description': 'Barcode generation for product identification',
        'modules_to_check': ['barcode', 'barcode.writer'],
        'critical': True
    },
    'fpdf2': {
        'install_cmd': 'pip install fpdf2',
        'description': 'Alternative PDF generation for reports',
        'modules_to_check': ['fpdf'],
        'critical': True
    },
    'openpyxl': {
        'install_cmd': 'pip install openpyxl',
        'description': 'Excel file creation and manipulation',
        'modules_to_check': ['openpyxl', 'openpyxl.utils'],
        'critical': True
    },
    'Pillow': {
        'install_cmd': 'pip install Pillow',
        'description': 'Image processing and manipulation',
        'modules_to_check': ['PIL', 'PIL.Image'],
        'critical': True
    },
    'yagmail': {
        'install_cmd': 'pip install yagmail',
        'description': 'Email sending functionality',
        'modules_to_check': ['yagmail'],
        'critical': True
    },
    'flask': {
        'install_cmd': 'pip install flask',
        'description': 'Web framework for API and web interface',
        'modules_to_check': ['flask'],
        'critical': True
    },
    'cryptography': {
        'install_cmd': 'pip install cryptography',
        'description': 'Cryptographic functions and security',
        'modules_to_check': ['cryptography'],
        'critical': True
    },
    'httpx': {
        'install_cmd': 'pip install httpx',
        'description': 'Modern HTTP client for API requests',
        'modules_to_check': ['httpx'],
        'critical': True
    },
    'qrcode': {
        'install_cmd': 'pip install qrcode',
        'description': 'QR code generation functionality',
        'modules_to_check': ['qrcode'],
        'critical': True
    },
    'requests': {
        'install_cmd': 'pip install requests',
        'description': 'HTTP library for API requests',
        'modules_to_check': ['requests'],
        'critical': True
    }
}

# Built-in Python modules (should be available by default)
BUILTIN_MODULES = {
    'sqlite3': 'Database connectivity',
    'datetime': 'Date and time handling',
    'os': 'Operating system interface',
    'sys': 'System-specific parameters',
    'random': 'Random number generation',
    'time': 'Time-related functions',
    'string': 'String operations',
    'hashlib': 'Secure hashing algorithms',
    'smtplib': 'SMTP email client',
    'email': 'Email message handling',
    'ctypes': 'Foreign function library',
    'shutil': 'High-level file operations',
    'subprocess': 'Subprocess management',
    'importlib': 'Import utilities',
    're': 'Regular expressions',
    'gc': 'Garbage collection'
}

# Optional dependencies (enhance functionality but not critical)
OPTIONAL_DEPENDENCIES = {
    'writer': {
        'install_cmd': 'pip install writer',
        'description': 'Additional barcode writing functionality',
        'modules_to_check': ['writer'],
        'critical': False
    }
}


# =============================================================================
# INSTALLATION COMMANDS
# =============================================================================

def get_install_all_command() -> str:
    """Get the complete pip install command for all dependencies."""
    core_packages = []
    for pkg_name, pkg_info in CORE_DEPENDENCIES.items():
        if pkg_name == 'python-barcode':
            core_packages.append('python-barcode[images]')
        else:
            core_packages.append(pkg_name)

    return f"pip install {' '.join(core_packages)}"


def get_install_optional_command() -> str:
    """Get the pip install command for optional dependencies."""
    optional_packages = [pkg_name for pkg_name in OPTIONAL_DEPENDENCIES.keys()]
    return f"pip install {' '.join(optional_packages)}"


# =============================================================================
# DEPENDENCY CHECKING FUNCTIONS
# =============================================================================

def check_module_availability(module_name: str) -> bool:
    """Check if a specific module can be imported."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def check_dependencies() -> Dict[str, Dict]:
    """Check the availability of all dependencies."""
    results = {
        'core': {},
        'builtin': {},
        'optional': {},
        'summary': {
            'core_missing': 0,
            'core_total': len(CORE_DEPENDENCIES),
            'builtin_missing': 0,
            'builtin_total': len(BUILTIN_MODULES),
            'optional_missing': 0,
            'optional_total': len(OPTIONAL_DEPENDENCIES)
        }
    }

    # Check core dependencies
    print("=" * 60)
    print("CHECKING CORE DEPENDENCIES")
    print("=" * 60)

    for pkg_name, pkg_info in CORE_DEPENDENCIES.items():
        pkg_available = True
        missing_modules = []

        for module in pkg_info['modules_to_check']:
            if not check_module_availability(module):
                pkg_available = False
                missing_modules.append(module)

        results['core'][pkg_name] = {
            'available': pkg_available,
            'missing_modules': missing_modules,
            'install_cmd': pkg_info['install_cmd'],
            'description': pkg_info['description']
        }

        status = "✅ INSTALLED" if pkg_available else "❌ MISSING"
        print(f"{pkg_name:<20} {status}")
        if not pkg_available:
            results['summary']['core_missing'] += 1
            print(f"  └─ Missing modules: {', '.join(missing_modules)}")
            print(f"  └─ Install: {pkg_info['install_cmd']}")

    # Check built-in modules
    print("\n" + "=" * 60)
    print("CHECKING BUILT-IN PYTHON MODULES")
    print("=" * 60)

    for module_name, description in BUILTIN_MODULES.items():
        available = check_module_availability(module_name)
        results['builtin'][module_name] = {
            'available': available,
            'description': description
        }

        status = "✅ AVAILABLE" if available else "❌ MISSING"
        print(f"{module_name:<20} {status}")
        if not available:
            results['summary']['builtin_missing'] += 1

    # Check optional dependencies
    print("\n" + "=" * 60)
    print("CHECKING OPTIONAL DEPENDENCIES")
    print("=" * 60)

    for pkg_name, pkg_info in OPTIONAL_DEPENDENCIES.items():
        pkg_available = True
        missing_modules = []

        for module in pkg_info['modules_to_check']:
            if not check_module_availability(module):
                pkg_available = False
                missing_modules.append(module)

        results['optional'][pkg_name] = {
            'available': pkg_available,
            'missing_modules': missing_modules,
            'install_cmd': pkg_info['install_cmd'],
            'description': pkg_info['description']
        }

        status = "✅ INSTALLED" if pkg_available else "⚠️ OPTIONAL"
        print(f"{pkg_name:<20} {status}")
        if not pkg_available:
            results['summary']['optional_missing'] += 1

    return results


def print_installation_summary(results: Dict[str, Dict]):
    """Print a summary of what needs to be installed."""
    print("\n" + "=" * 60)
    print("INSTALLATION SUMMARY")
    print("=" * 60)

    summary = results['summary']

    print(f"Core Dependencies: {summary['core_total'] - summary['core_missing']}/{summary['core_total']} installed")
    print(
        f"Built-in Modules:  {summary['builtin_total'] - summary['builtin_missing']}/{summary['builtin_total']} available")
    print(
        f"Optional Packages: {summary['optional_total'] - summary['optional_missing']}/{summary['optional_total']} installed")

    if summary['core_missing'] > 0:
        print(f"\n❌ {summary['core_missing']} CRITICAL dependencies are missing!")
        print("   The system WILL NOT work without these packages.")
        print("\n🔧 QUICK INSTALL ALL CORE DEPENDENCIES:")
        print(f"   {get_install_all_command()}")

        print("\n📦 INDIVIDUAL INSTALL COMMANDS:")
        for pkg_name, pkg_info in results['core'].items():
            if not pkg_info['available']:
                print(f"   {pkg_info['install_cmd']}")

    if summary['optional_missing'] > 0:
        print(f"\n⚠️ {summary['optional_missing']} optional dependencies are missing.")
        print("   The system will work but some features may be limited.")
        print(f"\n🔧 INSTALL OPTIONAL DEPENDENCIES:")
        print(f"   {get_install_optional_command()}")

    if summary['builtin_missing'] > 0:
        print(f"\n⚠️ {summary['builtin_missing']} built-in modules are missing.")
        print("   This may indicate a Python installation issue.")

    if summary['core_missing'] == 0 and summary['builtin_missing'] == 0:
        print("\n🎉 ALL REQUIRED DEPENDENCIES ARE INSTALLED!")
        print("   The Medical Testing System should work properly.")


def install_missing_dependencies(results: Dict[str, Dict], install_optional: bool = False):
    """Automatically install missing dependencies."""
    print("\n" + "=" * 60)
    print("INSTALLING MISSING DEPENDENCIES")
    print("=" * 60)

    missing_core = []
    for pkg_name, pkg_info in results['core'].items():
        if not pkg_info['available']:
            missing_core.append(pkg_info['install_cmd'])

    if missing_core:
        print("Installing core dependencies...")
        for cmd in missing_core:
            print(f"Running: {cmd}")
            try:
                subprocess.check_call(cmd.split())
                print("✅ Success!")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed: {e}")

    if install_optional:
        missing_optional = []
        for pkg_name, pkg_info in results['optional'].items():
            if not pkg_info['available']:
                missing_optional.append(pkg_info['install_cmd'])

        if missing_optional:
            print("\nInstalling optional dependencies...")
            for cmd in missing_optional:
                print(f"Running: {cmd}")
                try:
                    subprocess.check_call(cmd.split())
                    print("✅ Success!")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed: {e}")


# =============================================================================
# SYSTEM REQUIREMENTS CHECK
# =============================================================================

def check_system_requirements():
    """Check if the system meets the minimum requirements."""
    print("=" * 60)
    print("SYSTEM REQUIREMENTS CHECK")
    print("=" * 60)

    # Check Python version
    python_version = sys.version_info
    min_python = (3, 7)

    if python_version >= min_python:
        print(
            f"Python Version: ✅ {python_version.major}.{python_version.minor}.{python_version.micro} (minimum: {min_python[0]}.{min_python[1]})")
    else:
        print(
            f"Python Version: ❌ {python_version.major}.{python_version.minor}.{python_version.micro} (minimum: {min_python[0]}.{min_python[1]})")
        print("   Please upgrade Python to version 3.7 or higher")

    # Check platform
    import platform
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")

    if platform.system() == "Windows":
        print("Platform: ✅ Windows (Optimized)")
    else:
        print("Platform: ⚠️ Non-Windows (May require additional setup)")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main function to run dependency checking."""
    print("Medical Testing System - Library Dependencies Checker")
    print("=" * 60)

    # Check system requirements
    check_system_requirements()

    # Check dependencies
    results = check_dependencies()

    # Print summary
    print_installation_summary(results)

    # Ask if user wants to auto-install
    if results['summary']['core_missing'] > 0:
        print("\n" + "=" * 60)
        response = input("Would you like to automatically install missing core dependencies? (y/n): ")
        if response.lower() in ['y', 'yes']:
            install_optional = input("Also install optional dependencies? (y/n): ").lower() in ['y', 'yes']
            install_missing_dependencies(results, install_optional)

            print("\nRe-checking dependencies after installation...")
            results = check_dependencies()
            print_installation_summary(results)


if __name__ == "__main__":
    main() 