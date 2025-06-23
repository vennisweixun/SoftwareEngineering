import sys
import sqlite3
import time
import random
import string
import importlib
import subprocess
import datetime
from datetime import timezone, timedelta
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QDateEdit,
    QGridLayout, QVBoxLayout, QHBoxLayout, QFileDialog, QFrame, QCalendarWidget,
    QFormLayout, QMessageBox, QStackedLayout, QSizePolicy, QButtonGroup, QDialog,
    QComboBox, QScrollArea, QStyledItemDelegate, QListWidget, QListWidgetItem,
    QGroupBox, QSplitter, QMainWindow, QSpacerItem
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPainter, QPainterPath, QColor, QImage, QTextCursor, QPalette
from PyQt5.QtCore import QDate, Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer, pyqtSignal
import os
import hashlib  # Import hashlib
import ctypes
from ctypes import wintypes
import shutil  # For file operations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import the owner dashboard module
try:
    from ksOwner0613 import OwnerMainWindow as OwnerDashboard

    OWNER_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ksOwner0613 module: {e}")
    OWNER_MODULE_AVAILABLE = False

# Import the Dashboard from newdashboard.py
try:
    from newdashboard import Dashboard
except ImportError:
    print("⚠️  Warning: newdashboard.py not found. Dashboard functionality will be limited.")
    Dashboard = None

# Import the TesterHomePage from testerDashboard.py
try:
    from testerDashboard import TesterHomePage as TesterDashboard
except ImportError:
    print("⚠️  Warning: testerDashboard.py not found. Tester functionality will be limited.")
    TesterDashboard = None


class ToggleSwitch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 30)
        self._checked = False

        self._circle_position = 3
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        if self._checked:
            painter.setBrush(QColor("#00c853"))  # Green
        else:
            painter.setBrush(QColor("#cfd8dc"))  # Grey

        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15, 15)

        # Circle
        painter.setBrush(Qt.white)
        painter.drawEllipse(int(self._circle_position), 3, 24, 24)

    def mousePressEvent(self, event):
        self.toggle()
        super().mousePressEvent(event)

    def toggle(self):
        self.setChecked(not self._checked)

    def isChecked(self):
        return self._checked

    def setChecked(self, state):
        if self._checked != state:
            self._checked = state
            self.animate()

    def animate(self):
        start = self._circle_position
        end = 33 if self._checked else 3
        self.animation.stop()
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.start()
        self.update()

    def get_circle_position(self):
        return self._circle_position

    def set_circle_position(self, pos):
        self._circle_position = pos
        self.update()

    circle_position = pyqtProperty(int, fget=get_circle_position, fset=set_circle_position)


class OwnerWindow(QMainWindow):
    """Simple Owner Window for users with 'owner' role"""

    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        # Use the full owner dashboard if available, otherwise fallback to basic UI
        if OWNER_MODULE_AVAILABLE:
            self.setup_full_dashboard()
        else:
            self.setupUI()

    def setup_full_dashboard(self):
        """Setup the full owner dashboard from ksOwner0613.py"""
        try:
            # Don't show this window at all, just create the full dashboard
            self.setWindowFlags(Qt.Tool)  # Make this window invisible
            self.hide()

            # Extract user information
            username = self.user_info.get('username', '')
            user_id = self.user_info.get('user_id', 0)
            branch_id = self.user_info.get('branch_id', 1)

            # Create and show the full owner dashboard
            self.owner_dashboard = OwnerDashboard(username, user_id, branch_id)
            self.owner_dashboard.show()

            # Connect the dashboard's destroyed signal to quit the application
            self.owner_dashboard.destroyed.connect(self.close_completely)

        except Exception as e:
            print(f"Error setting up full dashboard: {e}")
            # Fallback to basic UI if there's an error
            self.setWindowFlags(Qt.Window)  # Reset window flags
            self.show()
            self.setupUI()

    def close_completely(self):
        """Close this window completely when the dashboard is closed"""
        self.close()
        self.deleteLater()

    def setupUI(self):
        """Fallback basic UI if full dashboard is not available"""
        self.setWindowTitle("Owner Dashboard")
        self.setGeometry(100, 100, 1200, 800)

        # Set window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f8ff;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        # Welcome message
        welcome_label = QLabel(f"Welcome, {self.user_info.get('fullname', 'Owner')}!")
        welcome_label.setFont(QFont("Arial", 24, QFont.Bold))
        welcome_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        header_layout.addWidget(welcome_label)

        header_layout.addStretch()

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setFont(QFont("Arial", 12))
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)

        layout.addLayout(header_layout)

        # Content area
        content_label = QLabel("Owner Dashboard - Basic View")
        content_label.setFont(QFont("Arial", 18))
        content_label.setStyleSheet("color: #34495e; margin: 20px 0;")
        content_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(content_label)

        # Info message
        info_label = QLabel(
            "The full owner dashboard module (ksOwner0613.py) is not available.\nThis is a basic fallback interface.")
        info_label.setFont(QFont("Arial", 14))
        info_label.setStyleSheet("color: #7f8c8d; margin: 20px 0;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)

        layout.addStretch()

        print(f"✓ Owner Window opened for user: {self.user_info.get('username')}")

    def logout(self):
        """Handle logout"""
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            print(f"✓ User '{self.user_info.get('username')}' logged out from Owner Window")
            self.close()

            # Show the login window again
            self.show_login_window()

    def show_login_window(self):
        """Show the login window again"""
        self.login_window = SignInSignUpWindow()
        self.login_window.show()


class TesterWindow(QMainWindow):
    """Tester Window for users with 'tester' role"""

    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.setupUI()

    def setupUI(self):
        self.setWindowTitle(f"Tester Portal - {self.user_info.get('fullname', self.user_info.get('username', 'User'))}")
        self.setGeometry(150, 150, 900, 700)

        # Set styling with a blue theme for testers
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F8FF;
            }
            QLabel {
                color: #333333;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Welcome message
        welcome_label = QLabel("🧪 Tester Portal")
        welcome_label.setFont(QFont("Arial", 32, QFont.Bold))
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setStyleSheet("color: #2E86C1; margin: 20px;")
        layout.addWidget(welcome_label)

        # User info
        user_info_label = QLabel(f"Welcome, {self.user_info.get('fullname', self.user_info.get('username', 'User'))}!")
        user_info_label.setFont(QFont("Arial", 18))
        user_info_label.setAlignment(Qt.AlignCenter)
        user_info_label.setStyleSheet("color: #566573; margin: 10px;")
        layout.addWidget(user_info_label)

        # Role info
        role_label = QLabel(f"Role: {self.user_info.get('role_name', 'Tester')}")
        role_label.setFont(QFont("Arial", 14))
        role_label.setAlignment(Qt.AlignCenter)
        role_label.setStyleSheet("color: #85929E; margin: 10px;")
        layout.addWidget(role_label)

        # Tester-specific features section
        features_frame = QFrame()
        features_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #AED6F1;
                border-radius: 10px;
                padding: 20px;
                margin: 20px;
            }
        """)
        features_layout = QVBoxLayout()

        features_title = QLabel("🔬 Tester Dashboard")
        features_title.setFont(QFont("Arial", 20, QFont.Bold))
        features_title.setAlignment(Qt.AlignCenter)
        features_title.setStyleSheet("color: #2E86C1; margin-bottom: 15px;")
        features_layout.addWidget(features_title)

        # Quick action buttons for testers
        buttons_layout = QVBoxLayout()

        pending_tests_btn = QPushButton("📋 View Pending Tests")
        pending_tests_btn.setFixedSize(250, 45)
        pending_tests_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2E86C1;
            }
        """)
        buttons_layout.addWidget(pending_tests_btn, alignment=Qt.AlignCenter)

        my_assignments_btn = QPushButton("📝 My Test Assignments")
        my_assignments_btn.setFixedSize(250, 45)
        my_assignments_btn.setStyleSheet("""
            QPushButton {
                background-color: #5DADE2;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #3498DB;
            }
        """)
        buttons_layout.addWidget(my_assignments_btn, alignment=Qt.AlignCenter)

        submit_results_btn = QPushButton("✅ Submit Test Results")
        submit_results_btn.setFixedSize(250, 45)
        submit_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        buttons_layout.addWidget(submit_results_btn, alignment=Qt.AlignCenter)

        features_layout.addLayout(buttons_layout)

        # Info text
        info_label = QLabel("Tester-specific features and test management tools will be implemented here.")
        info_label.setFont(QFont("Arial", 12))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #7B7D7D; margin: 15px;")
        features_layout.addWidget(info_label)

        features_frame.setLayout(features_layout)
        layout.addWidget(features_frame)

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedSize(120, 40)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        logout_btn.clicked.connect(self.logout)

        # Center the logout button
        logout_layout = QHBoxLayout()
        logout_layout.addStretch()
        logout_layout.addWidget(logout_btn)
        logout_layout.addStretch()
        layout.addLayout(logout_layout)

        central_widget.setLayout(layout)

        print(f"✓ Tester Window opened for user: {self.user_info.get('username')}")

    def logout(self):
        """Handle logout"""
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            print(f"✓ User '{self.user_info.get('username')}' logged out from Tester Portal")
            self.close()

            # Show the login window again
            self.show_login_window()

    def show_login_window(self):
        """Show the login window again"""
        self.login_window = SignInSignUpWindow()
        self.login_window.show()


class BlurOverlay(QWidget):
    """Semi-transparent overlay widget to create blur effect"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 0px;
        """)
        self.hide()


class SignInSignUpWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shelf Life Management - User Authentication")
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(800, 500)

        # Store reference to opened windows
        self.dashboard_window = None
        self.owner_window = None
        self.tester_window = None

        # Green theme colors for login side
        self.green_colors = {
            'primary': '#A8E6A3',  # Light green
            'secondary': '#C8F7C5',  # Lighter green
            'accent': '#81C784',  # Medium green
            'dark': '#4CAF50',  # Dark green
            'text': '#333333',  # Dark gray
            'background': '#F1F8E9',  # Very light green
            'white': '#FFFFFF',  # White
            'error': '#FF4444'  # Error red
        }

        # Orange theme colors for signup side
        self.orange_colors = {
            'primary': '#FFCC80',  # Light orange
            'secondary': '#FFE0B2',  # Lighter orange
            'accent': '#FFB74D',  # Medium orange
            'dark': '#FF9800',  # Dark orange
            'text': '#333333',  # Dark gray
            'background': '#FFF8E1',  # Very light orange
            'white': '#FFFFFF',  # White
            'error': '#FF4444'  # Error red
        }

        self.setupUI()
        self.applyStyles()

        # Make the window full screen
        self.showMaximized()

    def setupUI(self):
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main horizontal layout - now only for sign in
        self.main_layout = QHBoxLayout()
        central_widget.setLayout(self.main_layout)

        # Sign In Section (full width now)
        self.signin_widget = self.createSignInWidget()
        self.main_layout.addWidget(self.signin_widget, 100)

        # Remove all signup-related widgets and methods

    def createSignInWidget(self):
        widget = QFrame()
        widget.setObjectName("signinFrame")
        layout = QVBoxLayout()

        # Title
        title = QLabel("Sign In")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Welcome back to Shelf Life Management")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(subtitle)

        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Form container
        form_container = QWidget()
        form_container.setMaximumWidth(400)
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout()

        # Username field
        self.signin_username = QLineEdit()
        self.signin_username.setObjectName("inputField")
        self.signin_username.setPlaceholderText("Enter your username")
        form_layout.addRow("Username *", self.signin_username)

        # Password field
        self.signin_password = QLineEdit()
        self.signin_password.setObjectName("inputField")
        self.signin_password.setEchoMode(QLineEdit.Password)
        self.signin_password.setPlaceholderText("Enter your password (numbers only)")
        self.signin_password.returnPressed.connect(self.signIn)
        form_layout.addRow("Password *", self.signin_password)

        form_container.setLayout(form_layout)

        # Center the form
        form_wrapper = QHBoxLayout()
        form_wrapper.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        form_wrapper.addWidget(form_container)
        form_wrapper.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(form_wrapper)
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Sign In button
        signin_btn = QPushButton("Sign In")
        signin_btn.setObjectName("primaryButton")
        signin_btn.setMaximumWidth(200)
        signin_btn.clicked.connect(self.signIn)

        btn_wrapper = QHBoxLayout()
        btn_wrapper.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        btn_wrapper.addWidget(signin_btn)
        btn_wrapper.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(btn_wrapper)

        # Reset Password link
        reset_password_btn = QPushButton("Forgot Password?")
        reset_password_btn.setObjectName("resetPasswordLink")
        reset_password_btn.setMaximumWidth(150)
        reset_password_btn.clicked.connect(self.show_reset_password_dialog)
        reset_password_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #4CAF50;
                border: none;
                font-size: 12px;
                text-decoration: underline;
                padding: 5px;
            }
            QPushButton:hover {
                color: #2E7D32;
                font-weight: bold;
            }
        """)

        reset_btn_wrapper = QHBoxLayout()
        reset_btn_wrapper.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        reset_btn_wrapper.addWidget(reset_password_btn)
        reset_btn_wrapper.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(reset_btn_wrapper)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        widget.setLayout(layout)
        return widget

    def handle_database_lock(self):
        """Handle database lock by clearing connections and removing lock files"""
        try:
            # Force garbage collection to close any lingering connections
            import gc
            gc.collect()

            # Small delay to allow cleanup
            time.sleep(0.1)

            # Remove any SQLite lock files if they exist
            lock_files = ["testing_system.db-wal", "testing_system.db-shm"]
            for lock_file in lock_files:
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                        print(f"   Removed lock file: {lock_file}")
                    except OSError as e:
                        print(f"   Could not remove {lock_file}: {e}")

            print("   Database lock handling completed")
        except Exception as e:
            print(f"   Error handling database lock: {e}")

    def open_admin_dashboard(self, user_info):
        """Open the admin dashboard in fullscreen"""
        try:
            if Dashboard is None:
                QMessageBox.critical(self, "Error",
                                     "Dashboard module not found!\nPlease ensure 'newdashboard.py' is in the same directory.")
                return

            role_name = user_info['role_name']
            print(f"   Opening Dashboard for {role_name.lower()} user...")

            # Add extensive error handling
            print("   Step 1: Creating Dashboard object...")
            self.dashboard_window = Dashboard(user_role=role_name, user_info=user_info)
            print("   Step 2: Dashboard object created successfully")

            # Show the dashboard window in fullscreen
            print("   Step 3: Showing Dashboard window in fullscreen...")

            # Multiple fullscreen methods for maximum compatibility
            self.dashboard_window.showMaximized()  # Maximized mode
            self.dashboard_window.showFullScreen()  # True fullscreen mode

            print("   Step 4: Dashboard window shown in fullscreen successfully")

            # Ensure the window is brought to front and has focus
            self.dashboard_window.raise_()
            self.dashboard_window.activateWindow()

            # Additional focus and fullscreen enforcement
            self.dashboard_window.setWindowState(self.dashboard_window.windowState() | Qt.WindowMaximized)
            print("   Step 5: Fullscreen mode enforced")

            print(f"✓ Dashboard opened successfully")
            print(f"   User: {user_info['fullname'] or user_info['username']}")
            print(f"   Role: {user_info['role_name']}")

            # Close the login window
            self.close()

        except Exception as e:
            print(f"✗ Error opening dashboard: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Dashboard Error",
                                 f"Error opening dashboard: {str(e)}")

    def open_owner_window(self, user_info):
        """Open the owner-specific dashboard"""
        try:
            print(f"   Opening Owner Dashboard...")

            # Get branch_id from database if not in user_info
            if 'branch_id' not in user_info:
                try:
                    conn = sqlite3.connect("testing_system.db", timeout=30.0)
                    cursor = conn.cursor()
                    cursor.execute("SELECT branch_id FROM users WHERE user_id = ?", (user_info['user_id'],))
                    result = cursor.fetchone()
                    user_info['branch_id'] = result[0] if result else 1
                    conn.close()
                except Exception as e:
                    print(f"Warning: Could not get branch_id: {e}")
                    user_info['branch_id'] = 1  # Default branch_id

            # Create and show owner window (which will handle the full dashboard)
            self.owner_window = OwnerWindow(user_info)
            self.owner_window.show()

            print(f"✓ Owner Dashboard opened")
            print(f"   User: {user_info['fullname'] or user_info['username']}")
            print(f"   Role: {user_info['role_name']}")
            print(f"   Branch ID: {user_info.get('branch_id', 'Unknown')}")

            # Close the login window
            self.close()

        except Exception as e:
            print(f"✗ Error opening owner dashboard: {str(e)}")
            QMessageBox.critical(self, "Owner Dashboard Error",
                                 f"Error opening owner dashboard: {str(e)}")

    def open_tester_window(self, user_info):
        """Open the tester-specific dashboard"""
        try:
            if TesterDashboard is None:
                QMessageBox.critical(self, "Error",
                                     "TesterDashboard module not found!\nPlease ensure 'testerDashboard.py' is in the same directory.")
                return

            print(f"   Opening Tester Dashboard...")

            # Create and show tester dashboard in fullscreen
            self.tester_window = TesterDashboard(user_info)
            self.tester_window.showMaximized()  # Open in fullscreen like admin dashboard

            print(f"✓ Tester Dashboard opened in fullscreen mode")
            print(f"   User: {user_info['fullname'] or user_info['username']}")
            print(f"   Role: {user_info['role_name']}")

            # Close the login window
            self.close()

        except Exception as e:
            print(f"✗ Error opening tester dashboard: {str(e)}")
            QMessageBox.critical(self, "Tester Dashboard Error",
                                 f"Error opening tester dashboard: {str(e)}")

    def validateSignIn(self):
        username = self.signin_username.text().strip()
        password = self.signin_password.text().strip()

        if not username:
            QMessageBox.warning(self, "Error", "Username is required")
            return False

        if not password:
            QMessageBox.warning(self, "Error", "Password is required")
            return False

        # Validate password is numeric
        try:
            int(password)
        except ValueError:
            QMessageBox.warning(self, "Error", "Password must be numeric")
            return False

        return True

    def signIn(self):
        if not self.validateSignIn():
            return

        username = self.signin_username.text().strip()
        password = int(self.signin_password.text().strip())

        conn = None
        try:
            # Connect with timeout and enable WAL mode for better concurrency
            conn = sqlite3.connect("testing_system.db", timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            cursor = conn.cursor()

            # Check user credentials
            cursor.execute("""
                SELECT u.user_id, u.username, r.role_name, u.fullname, u.email
                FROM users u
                LEFT JOIN roles r ON u.role = r.role_id
                WHERE u.username = ? AND u.password = ?
            """, (username, password))

            user = cursor.fetchone()

            if user:
                user_info = {
                    'user_id': user[0],
                    'username': user[1],
                    'role_name': user[2],
                    'fullname': user[3],
                    'email': user[4]
                }

                print(f"✓ User '{username}' successfully signed in from database")
                print(f"  - User ID: {user_info['user_id']}")
                print(f"  - Full Name: {user_info['fullname'] or user_info['username']}")
                print(f"  - Role: {user_info['role_name']}")
                print(f"  - Email: {user_info['email']}")

                # Check if password is an 8-digit reset code
                if len(str(password)) == 8 and 10000000 <= password <= 99999999:
                    print(f"🔐 Reset code detected - redirecting to password reset page")
                    self.open_password_reset_page(user_info)
                    return

                # Role-based redirection for normal passwords
                role = user_info['role_name'].lower()

                if role == 'admin' or role == 'superadmin':
                    if role == 'admin':
                        print(f"🚀 Redirecting admin user to Dashboard...")
                    else:
                        print(f"👑 Redirecting super admin to Dashboard...")
                    self.open_admin_dashboard(user_info)
                elif role == 'owner':
                    print(f"🏢 Redirecting owner user to Owner Dashboard...")
                    self.open_owner_window(user_info)
                elif role == 'tester':
                    print(f"🧪 Redirecting tester user to Tester Dashboard...")
                    self.open_tester_window(user_info)
                else:
                    # For any other unknown roles
                    print(f"🔧 Unknown role '{role}' - showing general success message")
                    QMessageBox.information(self, "Success",
                                            f"Welcome back, {user_info['fullname'] or user_info['username']}!\nRole: {user_info['role_name']}\n\nSpecific interface for your role will be implemented soon.")
                    self.close()

            else:
                print(f"✗ Sign in failed for username '{username}' - Invalid credentials")
                QMessageBox.warning(self, "Error", "Invalid username or password")

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"✗ Database is locked, attempting to resolve...")
                self.handle_database_lock()
                QMessageBox.warning(self, "Database Busy",
                                    "Database is temporarily busy. Please try again in a moment.")
            else:
                print(f"✗ Database operational error during sign in: {str(e)}")
                QMessageBox.critical(self, "Database Error", f"Database error: {str(e)}")
        except sqlite3.Error as e:
            print(f"✗ Database error during sign in: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"An error occurred: {str(e)}")
        except Exception as e:
            print(f"✗ Unexpected error during sign in: {str(e)}")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
        finally:
            if conn:
                conn.close()

    def show_reset_password_dialog(self):
        """Show reset password dialog"""
        try:
            self.reset_dialog = ResetPasswordDialog(self)
            self.reset_dialog.show()
        except Exception as e:
            print(f"✗ Error opening reset password dialog: {e}")
            QMessageBox.critical(self, "Error", f"Error opening reset password dialog: {str(e)}")

    def open_password_reset_page(self, user_info):
        """Open password reset page after login with reset code"""
        try:
            print(f"   Opening Password Reset Page for user: {user_info['username']}")

            # Create and show password reset page
            self.password_reset_page = PasswordResetPage(user_info)
            self.password_reset_page.show()

            # Ensure the window is brought to front and has focus
            self.password_reset_page.raise_()
            self.password_reset_page.activateWindow()

            print(f"✓ Password Reset Page opened successfully")

            # Close the login window
            self.close()

        except Exception as e:
            print(f"✗ Error opening password reset page: {str(e)}")
            QMessageBox.critical(self, "Password Reset Error",
                                 f"Error opening password reset page: {str(e)}")

    def applyStyles(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.green_colors['background']};
            }}

            QFrame#signinFrame {{
                background-color: {self.green_colors['white']};
            }}

            QLabel#title {{
                font-size: 32px;
                font-weight: bold;
                color: {self.green_colors['dark']};
                margin: 20px;
            }}

            QLabel#subtitle {{
                font-size: 16px;
                color: {self.green_colors['text']};
                margin-bottom: 10px;
            }}



            QWidget#formContainer {{
                background-color: transparent;
            }}

            QLineEdit#inputField {{
                padding: 12px 15px;
                border: 2px solid {self.green_colors['secondary']};
                border-radius: 8px;
                font-size: 14px;
                background-color: {self.green_colors['white']};
                color: {self.green_colors['text']};
                min-height: 20px;
            }}

            QLineEdit#inputField:focus {{
                border-color: {self.green_colors['accent']};
                outline: none;
            }}

            QComboBox#comboBox {{
                padding: 12px 15px;
                border: 2px solid {self.green_colors['secondary']};
                border-radius: 8px;
                font-size: 14px;
                background-color: {self.green_colors['white']};
                color: {self.green_colors['text']};
                min-height: 20px;
            }}

            QComboBox#comboBox:focus {{
                border-color: {self.green_colors['accent']};
            }}

            QComboBox#comboBox::drop-down {{
                border: none;
                width: 20px;
            }}

            QPushButton#primaryButton {{
                background-color: {self.green_colors['dark']};
                color: {self.green_colors['white']};
                border: none;
                border-radius: 8px;
                padding: 15px 30px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }}

            QPushButton#primaryButton:hover {{
                background-color: {self.green_colors['accent']};
            }}

            QPushButton#primaryButton:pressed {{
                background-color: {self.green_colors['dark']};
            }}



            QFormLayout QLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {self.green_colors['text']};
                margin-bottom: 5px;
            }}
        """)


class CreateAccountDialog(QMainWindow):
    user_created = pyqtSignal()  # Signal to notify when user is created

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Create New Account - Shelf Life Management")
        self.setFixedSize(550, 750)
        self.setWindowModality(Qt.ApplicationModal)

        # Set modern theme for create account dialog
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFF8E1;
            }
        """)

        self.setupUI()
        self.load_branches()

    def generate_temporary_password(self):
        """Generate a random 4-digit temporary password"""
        import random
        self.temp_password = str(random.randint(1000, 9999))
        self.password_input.setText(self.temp_password)
        print(f"🔐 Generated temporary password: {self.temp_password}")

    def setupUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main scroll area for better UX on smaller screens
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #FFF8E1; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(30, 20, 30, 30)
        scroll_layout.setSpacing(0)

        # Header section with gradient background
        header_widget = QWidget()
        header_widget.setFixedHeight(100)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #FF6F00, stop:0.5 #FF8F00, stop:1 #FFA000);
                border-radius: 15px;
                margin-bottom: 25px;
            }
        """)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(25, 15, 25, 15)

        title = QLabel("🎯 Create New Account")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; margin: 0px;")

        subtitle = QLabel("Add a new user to the Shelf Life Management")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin: 5px 0px 0px 0px;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_widget.setLayout(header_layout)
        scroll_layout.addWidget(header_widget)

        # Form container with white background and shadow effect
        form_container = QWidget()
        form_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #E0E0E0;
            }
        """)

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(35, 25, 35, 25)
        form_layout.setSpacing(20)

        # Full Name Field
        fullname_container = self.create_field_container("👤 Full Name", "Enter the user's full name", True)
        self.fullname_input = fullname_container.findChild(QLineEdit)
        form_layout.addWidget(fullname_container)

        # Role Field
        role_container = self.create_field_container("💼 Role", "Select user role", True, field_type="combo")
        self.role_combo = role_container.findChild(QComboBox)
        self.role_combo.addItems(["Select Role", "Super Admin", "Admin", "Owner", "Tester"])
        self.role_combo.currentTextChanged.connect(self.on_role_changed)
        form_layout.addWidget(role_container)

        # Branch Field (conditional)
        self.branch_container = self.create_field_container("🏢 Branch", "Select branch location", True,
                                                            field_type="combo")
        self.branch_combo = self.branch_container.findChild(QComboBox)
        self.branch_container.setVisible(False)  # Initially hidden
        form_layout.addWidget(self.branch_container)

        # Temporary Password Field (Auto-generated)
        password_container = self.create_field_container("🔒 Temporary Password", "Auto-generated 4-digit password",
                                                         True)
        self.password_input = password_container.findChild(QLineEdit)
        self.password_input.setReadOnly(True)
        self.password_input.setMaxLength(4)
        self.password_input.setEchoMode(QLineEdit.Password)  # Mask password with asterisks
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #FFE0B2;
                border-radius: 10px;
                font-size: 13px;
                background-color: #F5F5F5;
                color: #666666;
                min-height: 20px;
                font-weight: bold;
                text-align: center;
                letter-spacing: 2px;
            }
        """)
        # Generate and display temporary password
        self.generate_temporary_password()
        form_layout.addWidget(password_container)

        # Email Field
        email_container = self.create_field_container("📧 Email Address", "Enter email address for notifications", True)
        self.email_input = email_container.findChild(QLineEdit)
        form_layout.addWidget(email_container)

        form_container.setLayout(form_layout)
        scroll_layout.addWidget(form_container)

        # Email notification section (Mandatory for temporary password)
        notification_widget = QWidget()
        notification_widget.setStyleSheet("""
            QWidget {
                background-color: #E8F5E9;
                border-radius: 12px;
                border: 1px solid #A5D6A7;
                margin: 15px 0px;
            }
        """)

        notification_layout = QHBoxLayout()
        notification_layout.setContentsMargins(20, 15, 20, 15)

        # Info icon
        info_label = QLabel("ℹ️")
        info_label.setFont(QFont("Segoe UI", 14))

        # Notification text
        notification_text = QLabel("Temporary password will be sent via email notification")
        notification_text.setFont(QFont("Segoe UI", 11, QFont.Medium))
        notification_text.setStyleSheet("color: #2E7D32; background: transparent; border: none;")

        notification_layout.addWidget(info_label)
        notification_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        notification_layout.addWidget(notification_text)
        notification_layout.addStretch()

        notification_widget.setLayout(notification_layout)
        scroll_layout.addWidget(notification_widget)

        # Buttons section
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 10)

        cancel_btn = QPushButton("✖ Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 11, QFont.Medium))
        cancel_btn.setFixedSize(120, 42)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 21px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        cancel_btn.clicked.connect(self.close)

        create_btn = QPushButton("✓ Create Account")
        create_btn.setFont(QFont("Segoe UI", 11, QFont.Medium))
        create_btn.setFixedSize(150, 42)
        create_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #FF8F00, stop:1 #FF6F00);
                color: white;
                border: none;
                border-radius: 21px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #FFA000, stop:1 #FF8F00);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #FF6F00, stop:1 #E65100);
            }
        """)
        create_btn.clicked.connect(self.create_account)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addItem(QSpacerItem(15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(create_btn)
        button_layout.addStretch()

        button_container.setLayout(button_layout)
        scroll_layout.addWidget(button_container)

        scroll_widget.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        central_widget.setLayout(main_layout)

    def create_field_container(self, label_text, placeholder, required=False, field_type="input", items=None):
        """Create a modern field container with label above input"""
        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label with icon and required indicator
        label = QLabel(label_text + (" *" if required else ""))
        label.setFont(QFont("Segoe UI", 11, QFont.Medium))
        label.setStyleSheet("""
            QLabel {
                color: #FF6F00;
                font-weight: 600;
                margin: 0px;
                padding: 0px;
                background: transparent;
            }
        """)
        layout.addWidget(label)

        # Input field
        if field_type == "combo":
            field = QComboBox()
            if items:
                field.addItems(items)
            field.setStyleSheet("""
                QComboBox {
                    padding: 12px 15px;
                    border: 2px solid #FFE0B2;
                    border-radius: 10px;
                    font-size: 13px;
                    background-color: #FAFAFA;
                    color: #333333;
                    min-height: 20px;
                    selection-background-color: #FF8F00;
                }
                QComboBox:focus {
                    border-color: #FF8F00;
                    background-color: white;
                }
                QComboBox:hover {
                    border-color: #FFCC80;
                    background-color: white;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 30px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid #FF8F00;
                    margin-right: 10px;
                }
                QComboBox QAbstractItemView {
                    border: 2px solid #FFE0B2;
                    border-radius: 8px;
                    background-color: white;
                    selection-background-color: #FFF3E0;
                    selection-color: #FF6F00;
                    padding: 5px;
                }
            """)
        else:
            field = QLineEdit()
            field.setPlaceholderText(placeholder)
            field.setStyleSheet("""
                QLineEdit {
                    padding: 12px 15px;
                    border: 2px solid #FFE0B2;
                    border-radius: 10px;
                    font-size: 13px;
                    background-color: #FAFAFA;
                    color: #333333;
                    min-height: 20px;
                }
                QLineEdit:focus {
                    border-color: #FF8F00;
                    background-color: white;
                }
                QLineEdit:hover {
                    border-color: #FFCC80;
                    background-color: white;
                }
            """)

        layout.addWidget(field)
        container.setLayout(layout)
        return container

    def get_input_style(self):
        """Legacy input style - kept for compatibility"""
        return """
            QLineEdit, QComboBox {
                padding: 12px 15px;
                border: 2px solid #FFE0B2;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
                color: #333333;
                min-height: 20px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #FFB74D;
            }
        """

    def load_branches(self):
        """Load branches from database"""
        try:
            conn = sqlite3.connect("testing_system.db", timeout=10.0)
            cursor = conn.cursor()

            # Check if branches table has data, if not, insert sample branches
            cursor.execute("SELECT COUNT(*) FROM branches")
            branch_count = cursor.fetchone()[0]

            if branch_count == 0:
                print("No branches found, inserting sample branches...")
                sample_branches = [
                    ("Main Branch - Kuala Lumpur",),
                    ("Branch 2 - Penang",),
                    ("Branch 3 - Johor Bahru",),
                    ("Branch 4 - Kuching",),
                    ("Branch 5 - Kota Kinabalu",)
                ]
                cursor.executemany("INSERT INTO branches (branch_name) VALUES (?)", sample_branches)
                conn.commit()
                print(f"✓ Inserted {len(sample_branches)} sample branches")

            cursor.execute("SELECT branch_id, branch_name FROM branches ORDER BY branch_name")
            branches = cursor.fetchall()

            self.branch_combo.clear()
            self.branch_combo.addItem("Select Branch", None)

            for branch_id, branch_name in branches:
                self.branch_combo.addItem(branch_name, branch_id)

            conn.close()
            print(f"✓ Loaded {len(branches)} branches for selection")

        except Exception as e:
            print(f"✗ Error loading branches: {e}")
            QMessageBox.warning(self, "Database Error", f"Could not load branches: {e}")

    def on_role_changed(self, role_text):
        """Show/hide branch selection based on role"""
        # Show branch selection only for Owner (role_id = 3)
        is_owner = role_text.lower() == "owner"
        self.branch_container.setVisible(is_owner)

    def validate_form(self):
        """Validate form inputs"""
        fullname = self.fullname_input.text().strip()
        role = self.role_combo.currentText()
        email = self.email_input.text().strip()

        # Validate full name
        if not fullname:
            QMessageBox.warning(self, "Validation Error", "Full name is required.")
            self.fullname_input.setFocus()
            return False

        if len(fullname) < 2:
            QMessageBox.warning(self, "Validation Error", "Full name must be at least 2 characters long.")
            self.fullname_input.setFocus()
            return False

        # Validate role selection
        if role in ["Select Role", ""]:
            QMessageBox.warning(self, "Validation Error", "Please select a role.")
            self.role_combo.setFocus()
            return False

        # Validate branch selection for Owner role
        if role.lower() == "owner":
            if not self.branch_combo.currentData():
                QMessageBox.warning(self, "Validation Error", "Please select a branch for Owner role.")
                self.branch_combo.setFocus()
                return False

        # Validate email
        if not email:
            QMessageBox.warning(self, "Validation Error", "Email address is required.")
            self.email_input.setFocus()
            return False

        # Basic email format validation
        if "@" not in email or "." not in email.split("@")[-1]:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid email address.")
            self.email_input.setFocus()
            return False

        return True

    def create_account(self):
        """Create new user account"""
        if not self.validate_form():
            return

        fullname = self.fullname_input.text().strip()
        role = self.role_combo.currentText()
        password = int(self.temp_password)  # Use the generated temporary password
        email = self.email_input.text().strip()
        branch_id = self.branch_combo.currentData() if role.lower() == "owner" else None

        # Map role to role_id
        role_mapping = {
            "super admin": 1,
            "admin": 2,
            "owner": 3,
            "tester": 4
        }
        role_id = role_mapping.get(role.lower(), 3)

        conn = None
        try:
            print(f"⚡ Creating account for '{fullname}' with role '{role}'...")

            conn = sqlite3.connect("testing_system.db", timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # Generate username from fullname (remove spaces, lowercase)
            username = fullname.replace(" ", "").lower()

            # Check if username already exists, add number if needed
            original_username = username
            counter = 1
            while True:
                cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                username = f"{original_username}{counter}"
                counter += 1

            # Insert new user with temporary password
            cursor.execute("""
                INSERT INTO users (username, password, role, fullname, email, branch_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (username, password, role_id, fullname, email, branch_id))

            new_user_id = cursor.lastrowid
            conn.commit()

            print(f"✓ USER ACCOUNT CREATED SUCCESSFULLY!")
            print(f"  - User ID: {new_user_id}")
            print(f"  - Username: {username}")
            print(f"  - Full Name: {fullname}")
            print(f"  - Role: {role} (role_id: {role_id})")
            print(f"  - Email: {email}")
            print(f"  - Temporary Password: {self.temp_password}")
            print(f"  - Branch ID: {branch_id}")

            # Send email notification with temporary password (mandatory)
            email_sent = False
            print(f"📧 Sending temporary password notification to {email}...")
            email_sent = self.send_email_notification(email, username, self.temp_password, fullname)

            # Show success message
            success_msg = f"Account created successfully!\n\nUser: {fullname}\nUsername: {username}\nRole: {role}"
            if branch_id:
                branch_name = self.branch_combo.currentText()
                success_msg += f"\nBranch: {branch_name}"

            success_msg += f"\n\nTemporary Password: {self.temp_password}"

            if email_sent:
                success_msg += f"\n\n✓ Email with temporary password sent to: {email}"
            else:
                success_msg += f"\n\n⚠️ Could not send email notification"

            success_msg += "\n\nThe user must use this temporary password for first login."

            QMessageBox.information(self, "Success", success_msg)

            # Emit signal to notify parent dashboard
            self.user_created.emit()

            # Refresh parent dashboard user table if available
            if self.parent_window and hasattr(self.parent_window, 'load_user_data'):
                self.parent_window.load_user_data()

            # Clear form and close
            self.clear_form()
            self.close()

        except sqlite3.Error as e:
            print(f"✗ Database error during account creation: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"Error creating account: {str(e)}")
        except Exception as e:
            print(f"✗ Unexpected error during account creation: {str(e)}")
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def send_email_notification(self, to_email, username, password, fullname):
        """Send email notification with account credentials"""
        from_email = "venniscc04@gmail.com"
        email_password = "beoj bywk xffl hqoo"
        subject = "🔐 Your Temporary Login Credentials - Shelf Life Management System"
        body = f"""Dear {fullname},

Welcome to the Shelf Life Management System!

Your account has been successfully created. Please find your temporary login credentials below:

Account Details:
- Username: {username}
- Temporary Password: {password}

🚨 IMPORTANT NOTICE:
This is a TEMPORARY PASSWORD for your first login only. For security reasons, you will be required to change this password upon your first successful login.

Next Steps:
1. Log in to the Shelf Life Management using the credentials above
2. You will be prompted to create a new permanent password
3. Complete your profile setup if required

If you have any questions or need assistance, please contact your system administrator.

Thank you for joining our platform!

Best regards,
Shelf Life Management Team

---
This is an automated message. Please do not reply to this email."""

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(from_email, email_password)
                server.send_message(msg)
            print(f"✓ Temporary password email sent to {to_email}")
            return True
        except Exception as e:
            print(f"✗ Failed to send temporary password email: {e}")
            return False

    def clear_form(self):
        """Clear all form fields and generate new temporary password"""
        self.fullname_input.clear()
        self.role_combo.setCurrentIndex(0)
        self.email_input.clear()
        self.branch_combo.setCurrentIndex(0)
        self.branch_container.setVisible(False)
        # Generate new temporary password
        self.generate_temporary_password()


class ResetPasswordDialog(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle("Reset Password - Shelf Life Management")
        self.setFixedSize(500, 600)
        self.setWindowModality(Qt.ApplicationModal)

        # Set theme for reset password dialog
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E8F5E9;
            }
        """)

        self.setupUI()

    def setupUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(25)

        # Header section
        header_widget = QWidget()
        header_widget.setFixedHeight(100)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4CAF50, stop:0.5 #66BB6A, stop:1 #81C784);
                border-radius: 15px;
                margin-bottom: 20px;
            }
        """)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(25, 15, 25, 15)

        title = QLabel("🔐 Reset Password")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; margin: 0px;")

        subtitle = QLabel("Enter your username to receive a reset code")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin: 5px 0px 0px 0px;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)

        # Form container
        form_container = QWidget()
        form_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #E0E0E0;
            }
        """)

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(30, 25, 30, 25)
        form_layout.setSpacing(20)

        # Username field
        username_container = self.create_field_container("👤 Username", "Enter your username", True)
        self.username_input = username_container.findChild(QLineEdit)
        form_layout.addWidget(username_container)

        # Info message
        info_label = QLabel("ℹ️ An 8-digit reset code will be sent to your registered email address")
        info_label.setFont(QFont("Segoe UI", 10))
        info_label.setStyleSheet("""
            QLabel {
                color: #2E7D32;
                background-color: #F1F8E9;
                border: 1px solid #C8E6C9;
                border-radius: 8px;
                padding: 10px;
                margin: 10px 0px;
            }
        """)
        info_label.setWordWrap(True)
        form_layout.addWidget(info_label)

        form_container.setLayout(form_layout)
        main_layout.addWidget(form_container)

        # Buttons
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)

        cancel_btn = QPushButton("✖ Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 11, QFont.Medium))
        cancel_btn.setFixedSize(120, 40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.close)

        send_code_btn = QPushButton("📧 Send Reset Code")
        send_code_btn.setFont(QFont("Segoe UI", 11, QFont.Medium))
        send_code_btn.setFixedSize(160, 40)
        send_code_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #66BB6A, stop:1 #4CAF50);
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #81C784, stop:1 #66BB6A);
            }
        """)
        send_code_btn.clicked.connect(self.send_reset_code)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addItem(QSpacerItem(15, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(send_code_btn)
        button_layout.addStretch()

        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        central_widget.setLayout(main_layout)

    def create_field_container(self, label_text, placeholder, required=False):
        """Create a field container with label above input"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label
        label = QLabel(label_text + (" *" if required else ""))
        label.setFont(QFont("Segoe UI", 11, QFont.Medium))
        label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: 600;
                margin: 0px;
                padding: 0px;
                background: transparent;
            }
        """)
        layout.addWidget(label)

        # Input field
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #C8E6C9;
                border-radius: 10px;
                font-size: 13px;
                background-color: #FAFAFA;
                color: #333333;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #81C784;
                background-color: white;
            }
        """)

        layout.addWidget(field)
        container.setLayout(layout)
        return container

    def send_reset_code(self):
        """Send reset code to user's email"""
        username = self.username_input.text().strip()

        if not username:
            QMessageBox.warning(self, "Validation Error", "Please enter your username.")
            self.username_input.setFocus()
            return

        # Check if user exists and get email
        try:
            conn = sqlite3.connect("testing_system.db", timeout=30.0)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT user_id, username, fullname, email 
                FROM users 
                WHERE username = ?
            """, (username,))

            user = cursor.fetchone()

            if not user:
                QMessageBox.warning(self, "User Not Found",
                                    f"No account found with username '{username}'.\nPlease check your username and try again.")
                self.username_input.setFocus()
                conn.close()
                return

            user_id, username, fullname, email = user

            if not email:
                QMessageBox.warning(self, "No Email",
                                    "No email address found for this account.\nPlease contact your administrator.")
                conn.close()
                return

            # Generate 8-digit reset code
            import random
            reset_code = str(random.randint(10000000, 99999999))

            # Store reset code in database (you might want to create a password_resets table)
            # For now, we'll temporarily update the user's password with the reset code
            cursor.execute("UPDATE users SET password = ? WHERE user_id = ?", (int(reset_code), user_id))
            conn.commit()
            conn.close()

            # Send email with reset code
            if self.send_reset_email(email, username, fullname, reset_code):
                QMessageBox.information(self, "Reset Code Sent",
                                        f"An 8-digit reset code has been sent to:\n{email}\n\n"
                                        f"Please check your email and use the code to log in, then change your password.")
                self.close()
            else:
                QMessageBox.warning(self, "Email Error",
                                    "Failed to send reset code email.\nPlease try again or contact support.")

            print(f"✓ Reset code {reset_code} generated and sent for user: {username}")

        except Exception as e:
            print(f"✗ Error during password reset: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            if 'conn' in locals():
                conn.close()

    def send_reset_email(self, to_email, username, fullname, reset_code):
        """Send reset code email"""
        from_email = "venniscc04@gmail.com"
        email_password = "beoj bywk xffl hqoo"
        subject = "🔐 Password Reset Code - Shelf Life Management"
        body = f"""Dear {fullname or username},

You have requested to reset your password for the Shelf Life Management System.

Your 8-digit reset code is: {reset_code}

🚨 IMPORTANT INSTRUCTIONS:
1. Use this code as your temporary password to log in
2. After logging in with this code, you will be prompted to set a new password
3. This code is valid for one-time use only
4. If you did not request this reset, please contact your administrator immediately

For security reasons, please do not share this code with anyone.

Best regards,
Shelf Life Management Team

---
This is an automated message. Please do not reply to this email."""

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(from_email, email_password)
                server.send_message(msg)
            print(f"✓ Reset code email sent to {to_email}")
            return True
        except Exception as e:
            print(f"✗ Failed to send reset code email: {e}")
            return False


class PasswordResetPage(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.setWindowTitle("Set New Password - Shelf Life Management")
        self.setFixedSize(450, 800)

        # Ensure window appears on top and stays visible
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)

        # Set theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E8F5E9;
            }
        """)

        self.setupUI()

    def setupUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout - optimized for 450x800 dimensions
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        # Header section - reduced height for better space usage
        header_widget = QWidget()
        header_widget.setFixedHeight(100)
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #4CAF50, stop:0.5 #66BB6A, stop:1 #81C784);
                border-radius: 15px;
                margin-bottom: 20px;
            }
        """)

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(5)

        title = QLabel("🔒 Set New Password")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; margin: 0px;")

        welcome_msg = QLabel(f"Welcome, {self.user_info['fullname'] or self.user_info['username']}!")
        welcome_msg.setFont(QFont("Segoe UI", 11))
        welcome_msg.setAlignment(Qt.AlignCenter)
        welcome_msg.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin: 3px 0px;")

        subtitle = QLabel("Please create a new secure password")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.8); margin: 0px;")

        header_layout.addWidget(title)
        header_layout.addWidget(welcome_msg)
        header_layout.addWidget(subtitle)
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)

        # Form container
        form_container = QWidget()
        form_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #E0E0E0;
            }
        """)

        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(15)

        # Current user info
        user_info_widget = QWidget()
        user_info_widget.setStyleSheet("""
            QWidget {
                background-color: #F1F8E9;
                border: 1px solid #C8E6C9;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        user_info_layout = QVBoxLayout()
        user_info_layout.setContentsMargins(12, 8, 12, 8)
        user_info_layout.setSpacing(3)

        info_title = QLabel("📋 Account Information")
        info_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        info_title.setStyleSheet("color: #2E7D32; margin-bottom: 3px;")

        username_label = QLabel(f"Username: {self.user_info['username']}")
        username_label.setFont(QFont("Segoe UI", 9))
        username_label.setStyleSheet("color: #388E3C;")

        role_label = QLabel(f"Role: {self.user_info['role_name']}")
        role_label.setFont(QFont("Segoe UI", 9))
        role_label.setStyleSheet("color: #388E3C;")

        user_info_layout.addWidget(info_title)
        user_info_layout.addWidget(username_label)
        user_info_layout.addWidget(role_label)
        user_info_widget.setLayout(user_info_layout)
        form_layout.addWidget(user_info_widget)

        # New password field
        new_password_container = self.create_field_container("🔐 New Password", "Enter your new password (4+ digits)",
                                                             True)
        self.new_password_input = new_password_container.findChild(QLineEdit)
        self.new_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(new_password_container)

        # Confirm password field
        confirm_password_container = self.create_field_container("🔒 Confirm Password", "Re-enter your new password",
                                                                 True)
        self.confirm_password_input = confirm_password_container.findChild(QLineEdit)
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(confirm_password_container)

        # Password requirements
        requirements_widget = QWidget()
        requirements_widget.setStyleSheet("""
            QWidget {
                background-color: #FFF3E0;
                border: 1px solid #FFCC80;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        requirements_layout = QVBoxLayout()
        requirements_layout.setContentsMargins(8, 8, 8, 8)
        requirements_layout.setSpacing(5)

        req_title = QLabel("📝 Password Requirements:")
        req_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        req_title.setStyleSheet("color: #F57C00; margin-bottom: 5px;")

        req_text = QLabel("• Minimum 4 digits\n• Numbers only\n• No spaces or special characters")
        req_text.setFont(QFont("Segoe UI", 9))
        req_text.setStyleSheet("color: #E65100; line-height: 1.3;")

        requirements_layout.addWidget(req_title)
        requirements_layout.addWidget(req_text)
        requirements_widget.setLayout(requirements_layout)
        form_layout.addWidget(requirements_widget)

        form_container.setLayout(form_layout)
        main_layout.addWidget(form_container)

        # Buttons - adjusted for narrower width
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)
        button_layout.setSpacing(10)

        cancel_btn = QPushButton("✖ Cancel")
        cancel_btn.setFont(QFont("Segoe UI", 10, QFont.Medium))
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        cancel_btn.clicked.connect(self.cancel_reset)

        update_btn = QPushButton("✓ Update Password")
        update_btn.setFont(QFont("Segoe UI", 10, QFont.Medium))
        update_btn.setFixedSize(140, 40)
        update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #66BB6A, stop:1 #4CAF50);
                color: white;
                border: none;
                border-radius: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #81C784, stop:1 #66BB6A);
            }
        """)
        update_btn.clicked.connect(self.update_password)

        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addItem(QSpacerItem(15, 15, QSizePolicy.Fixed, QSizePolicy.Minimum))
        button_layout.addWidget(update_btn)
        button_layout.addStretch()

        button_container.setLayout(button_layout)
        main_layout.addWidget(button_container)

        central_widget.setLayout(main_layout)

    def create_field_container(self, label_text, placeholder, required=False):
        """Create a field container with label above input"""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Label
        label = QLabel(label_text + (" *" if required else ""))
        label.setFont(QFont("Segoe UI", 10, QFont.Medium))
        label.setStyleSheet("""
            QLabel {
                color: #4CAF50;
                font-weight: 600;
                margin: 0px;
                padding: 0px;
                background: transparent;
            }
        """)
        layout.addWidget(label)

        # Input field - adjusted for narrower width
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 2px solid #C8E6C9;
                border-radius: 8px;
                font-size: 12px;
                background-color: #FAFAFA;
                color: #333333;
                min-height: 18px;
                max-width: 380px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
                background-color: white;
            }
            QLineEdit:hover {
                border-color: #81C784;
                background-color: white;
            }
        """)

        layout.addWidget(field)
        container.setLayout(layout)
        return container

    def update_password(self):
        """Update user's password"""
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        # Validate inputs
        if not new_password:
            QMessageBox.warning(self, "Validation Error", "Please enter a new password.")
            self.new_password_input.setFocus()
            return

        if not confirm_password:
            QMessageBox.warning(self, "Validation Error", "Please confirm your new password.")
            self.confirm_password_input.setFocus()
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Validation Error", "Passwords do not match. Please try again.")
            self.confirm_password_input.clear()
            self.confirm_password_input.setFocus()
            return

        # Validate password format (numeric, minimum 4 digits)
        try:
            password_int = int(new_password)
            if len(new_password) < 4:
                QMessageBox.warning(self, "Validation Error", "Password must be at least 4 digits long.")
                self.new_password_input.setFocus()
                return
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Password must contain only numbers.")
            self.new_password_input.setFocus()
            return

        # Update password in database
        try:
            conn = sqlite3.connect("testing_system.db", timeout=30.0)
            cursor = conn.cursor()

            cursor.execute("UPDATE users SET password = ? WHERE user_id = ?",
                           (password_int, self.user_info['user_id']))

            if cursor.rowcount > 0:
                conn.commit()
                print(f"✓ Password updated successfully for user: {self.user_info['username']}")

                QMessageBox.information(self, "Success",
                                        f"Password updated successfully!\n\nYou can now log in with your new password.")

                # Close this window and show login window
                self.close()
                self.show_login_window()
            else:
                QMessageBox.warning(self, "Update Failed", "Failed to update password. Please try again.")

            conn.close()

        except Exception as e:
            print(f"✗ Error updating password: {e}")
            QMessageBox.critical(self, "Database Error", f"Error updating password: {str(e)}")
            if 'conn' in locals():
                conn.close()

    def cancel_reset(self):
        """Cancel password reset and return to login"""
        reply = QMessageBox.question(self, "Cancel Password Reset",
                                     "Are you sure you want to cancel?\n\nYou will need to use the reset code again to log in.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.close()
            self.show_login_window()

    def show_login_window(self):
        """Show the login window again"""
        try:
            self.login_window = SignInSignUpWindow()
            self.login_window.show()

            # Ensure the login window is brought to front and has focus
            self.login_window.raise_()
            self.login_window.activateWindow()

            print(f"✓ Login window opened successfully")
        except Exception as e:
            print(f"✗ Error opening login window: {e}")
            # If we can't open login window, just exit the application
            QApplication.quit()


def main():
    app = QApplication(sys.argv)

    print("=" * 60)
    print("🏥 Shelf Life Management - USER AUTHENTICATION")
    print("=" * 60)

    # Check if database exists and is accessible
    try:
        print("🔍 Checking database connection...")
        conn = sqlite3.connect("testing_system.db", timeout=10.0)
        cursor = conn.cursor()

        # Test basic connectivity
        cursor.execute("SELECT COUNT(*) FROM users LIMIT 1")
        user_count = cursor.fetchone()[0]

        # Test if roles table exists and has data
        cursor.execute("SELECT COUNT(*) FROM roles")
        role_count = cursor.fetchone()[0]

        conn.close()

        print(f"✓ Database connection successful")
        print(f"✓ Found {user_count} users in database")
        print(f"✓ Found {role_count} roles configured")
        print("✓ Application ready to start")
        print("-" * 60)

    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("✗ Database tables not found")
            QMessageBox.critical(None, "Database Error",
                                 "Database tables not found.\nPlease run 'python databaseSetup1.py' first to create the database structure.")
        else:
            print(f"✗ Database error: {str(e)}")
            QMessageBox.critical(None, "Database Error",
                                 f"Database error: {str(e)}\nPlease check if 'python databaseSetup1.py' was run successfully.")
        sys.exit()
    except sqlite3.Error as e:
        print(f"✗ Database connection failed: {str(e)}")
        QMessageBox.critical(None, "Database Error",
                             f"Database error: {str(e)}\nPlease run 'python databaseSetup1.py' first.")
        sys.exit()
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        QMessageBox.critical(None, "Error", f"Unexpected error: {str(e)}")
        sys.exit()

    window = SignInSignUpWindow()
    window.show()

    print("🚀 Application window displayed")
    print("📋 Ready for user authentication")
    print("=" * 60)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()