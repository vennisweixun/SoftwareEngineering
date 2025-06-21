import sys
import sqlite3
import time
import random
import string
import importlib
import subprocess
import datetime
from datetime import timezone, timedelta
from flask import Flask, render_template
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QDateEdit,
    QGridLayout, QVBoxLayout, QHBoxLayout, QFileDialog, QFrame, QCalendarWidget,
    QFormLayout, QMessageBox, QStackedLayout, QSizePolicy, QButtonGroup, QDialog,
    QComboBox, QScrollArea, QStyledItemDelegate, QListWidget, QListWidgetItem,
    QGroupBox, QSplitter
)
from PyQt5.QtGui import QIcon, QPixmap, QFont, QPainter, QPainterPath, QColor, QImage, QTextCursor
from PyQt5.QtCore import QDate, Qt, QSize, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer, pyqtSignal
import os
import hashlib  # Import hashlib
import ctypes
from ctypes import wintypes
import shutil  # For file operations

# Import barcode libraries
import barcode
from barcode.writer import ImageWriter

# Malaysia timezone (UTC+8)
MALAYSIA_TZ = timezone(timedelta(hours=8))


# === Chat Database Functions ===
def create_chat_tables():
    """Create necessary chat tables in medical_system.db"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()

        # Create roles table if it doesn't exist (compatible with existing structure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY,
                role_name TEXT UNIQUE NOT NULL
            )
        """)

        # Insert default roles if they don't exist
        roles = [
            (1, 'superadmin'),
            (2, 'admin'),
            (3, 'owner'),
            (4, 'tester')
        ]

        for role_id, role_name in roles:
            cursor.execute("INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (?, ?)",
                           (role_id, role_name))

        # Create message table for chat
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role_id INTEGER,
                username TEXT,
                role TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        """)

        # Create private messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS private_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_user_id INTEGER,
                sender_username TEXT,
                receiver_username TEXT,
                sender_role TEXT,
                message_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create activity log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                role_id INTEGER,
                role TEXT,
                activity TEXT,
                description TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        """)

        # Create notification table for tagged messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                tagged_user_id INTEGER,
                tagged_username TEXT,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES message (message_id)
            )
        """)

        conn.commit()
        conn.close()
        print("✓ Chat tables created successfully in medical_system.db")
        return True

    except Exception as e:
        print(f"Error creating chat tables: {e}")
        return False


def get_all_messages():
    """Get all messages from the message table"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, role, message, timestamp, message_id
            FROM message
            WHERE role IN ('admin', 'superadmin') 
            AND message NOT LIKE '[ACTIVITY]%'
            ORDER BY timestamp ASC
        """)
        messages = cursor.fetchall()
        conn.close()
        return messages
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []


def insert_message(user_id, username, role, role_id, message_text):
    """Insert a new message into the message table"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO message (user_id, role_id, username, role, message, timestamp)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, role_id, username, role, message_text))
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id
    except Exception as e:
        print(f"Error inserting message: {e}")
        return None


def get_all_chat_users(current_username):
    """Get all users for private messaging - owners can only chat with superadmin, admin, and tester"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()

        # First, check if the testing_system.db exists (from Chat.py) to get proper roles
        try:
            chat_conn = sqlite3.connect("testing_system.db")
            chat_cursor = chat_conn.cursor()
            chat_cursor.execute("""
                SELECT u.username, r.role_name, u.username as fullname 
                FROM users u 
                LEFT JOIN roles r ON u.role = r.role_id 
                WHERE u.username != ? AND r.role_name IN ('superadmin', 'admin', 'tester')
                ORDER BY r.role_name, u.username
            """, (current_username,))
            users = chat_cursor.fetchall()
            chat_conn.close()

            if users:  # If we found users from Chat.py database
                return users
        except:
            pass  # Chat.py database not available, continue with medical_system.db

        # Fallback: Get users from medical_system.db (but filter to only non-owners)
        # Since medical_system.db doesn't have role info, we'll create mock admin/tester roles
        cursor.execute("""
            SELECT username, 'admin' as role_name, username as fullname 
            FROM Users 
            WHERE username != ? AND username != 'owner'
            ORDER BY username
        """, (current_username,))
        users = cursor.fetchall()
        conn.close()
        return users
    except Exception as e:
        print(f"Error getting chat users: {e}")
        return []


def insert_private_message(sender_user_id, sender_username, receiver_username, sender_role, message_text):
    """Insert a private message"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO private_messages 
            (sender_user_id, sender_username, receiver_username, sender_role, message_text)
            VALUES (?, ?, ?, ?, ?)
        """, (sender_user_id, sender_username, receiver_username, sender_role, message_text))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error inserting private message: {e}")
        return False


def get_private_messages(username1, username2):
    """Get private messages between two users"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sender_username, receiver_username, message_text, timestamp, sender_role
            FROM private_messages 
            WHERE (sender_username = ? AND receiver_username = ?) 
               OR (sender_username = ? AND receiver_username = ?)
            ORDER BY timestamp ASC
            LIMIT 50
        """, (username1, username2, username2, username1))
        messages = cursor.fetchall()
        conn.close()
        return messages
    except Exception as e:
        print(f"Error getting private messages: {e}")
        return []


def format_malaysia_time(timestamp_str=None):
    """Format timestamp to Malaysia time"""
    try:
        if timestamp_str:
            if 'T' in timestamp_str or '-' in timestamp_str:
                dt = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                try:
                    dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    dt = dt.replace(tzinfo=MALAYSIA_TZ)
                except:
                    dt = datetime.datetime.now(MALAYSIA_TZ)
        else:
            dt = datetime.datetime.now(MALAYSIA_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime.datetime.now(MALAYSIA_TZ).strftime("%Y-%m-%d %H:%M:%S")


# Function to change title bar color on Windows
def set_window_title_bar_color(hwnd, color_rgb):
    """
    Set the title bar color on Windows 10/11
    hwnd: Window handle
    color_rgb: RGB color as integer (e.g., 0x1e1e1e for dark gray)
    """
    try:
        # Windows API constants
        DWMWA_CAPTION_COLOR = 35
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20

        # Get DWM functions
        dwmapi = ctypes.windll.dwmapi

        # Set caption color
        caption_color = wintypes.DWORD(color_rgb)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_CAPTION_COLOR,
            ctypes.byref(caption_color),
            ctypes.sizeof(caption_color)
        )

        # Optionally set dark mode (for better contrast)
        dark_mode = wintypes.BOOL(True)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(dark_mode),
            ctypes.sizeof(dark_mode)
        )

        return True
    except Exception as e:
        print(f"Failed to set title bar color: {e}")
        return False


# --- Profile Widget (from Owner Profile.py, refactored) ---
class ProfileWidget(QWidget):
    def __init__(self, username, user_id, branch):
        super().__init__()
        self.username = username
        self.user_id = user_id
        self.branch_val = branch
        self.is_editable = False  # Keep track of edit state
        self.initUI()  # Initialize UI elements
        user_data = self.load_user_data()  # Load user data and get the result

        # Determine if the user is new based on loaded data
        is_new_user = not (user_data and user_data[1] and user_data[2])  # Check if email or phone is empty

        if is_new_user:
            self.set_new_user_edit_mode()  # Start in new user edit mode for new users
        else:
            self.set_view_mode()  # Start in view mode for existing users

    def load_user_data(self):
        conn = sqlite3.connect("medical_system.db")
        c = conn.cursor()
        c.execute("SELECT username, email, phone_no, branch FROM Users WHERE user_id=?", (self.user_id,))
        result = c.fetchone()
        conn.close()

        if result:
            username, email, phone, branch = result
            self.name.setText(username)
            self.owner_id.setText(str(self.user_id))
            self.branch.setText(branch)
            self.email.setText(email if email else "")
            self.phone_number.setText(phone if phone else "")

            self.name.setReadOnly(True)
            self.owner_id.setReadOnly(True)
            self.branch.setReadOnly(True)

            # Only load profile picture if it exists and user has data
            if email and phone:  # Only load profile pic if user has completed their profile
                profile_pic_path = f"profile_pics/{self.user_id}.png"
                if os.path.exists(profile_pic_path):
                    pixmap = QPixmap(profile_pic_path)
                    if not pixmap.isNull():
                        self.profile_pic.setPixmap(self.crop_to_circle(pixmap, 180))
                        self.profile_pic.setText("")  # Clear any text
            else:
                # For new users, show blank profile
                self.set_default_avatar()
            return result  # Return result
        return None  # Return None if no result

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)

        self.title = QLabel("Profile")
        self.title.setFont(QFont("Arial", 28, QFont.Bold))
        self.title.setStyleSheet("color: #5D3A00;")
        self.title.setAlignment(Qt.AlignCenter)
        main_layout.addSpacing(50)  # Increased from 20 to 30 to move profile down 10pt
        main_layout.addWidget(self.title)
        main_layout.addSpacing(10)

        white_frame = QFrame()
        white_frame.setFixedSize(1100, 550)
        white_frame.setStyleSheet("background-color: #eeeded; border-radius: 20px;")
        frame_layout = QVBoxLayout(white_frame)

        edit_layout = QHBoxLayout()
        edit_layout.addStretch()
        self.edit_btn = QPushButton()  # Store as instance variable
        self.edit_btn.setIcon(QIcon("C:\\Kai Shuang\\3.png"))
        self.edit_btn.setIconSize(QSize(40, 40))
        self.edit_btn.setFixedSize(60, 60)
        self.edit_btn.setStyleSheet("border: none;")
        self.edit_btn.clicked.connect(self.toggle_full_edit_mode)  # Connect to toggle_full_edit_mode
        edit_layout.addWidget(self.edit_btn)
        frame_layout.addLayout(edit_layout)

        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignTop)

        self.profile_pic = QLabel()
        self.profile_pic.setFixedSize(180, 180)
        self.profile_pic.setStyleSheet("border: 1px solid gray; background-color: #fff; border-radius: 90px;")
        self.profile_pic.setAlignment(Qt.AlignCenter)
        self.set_default_avatar()

        upload_btn = QPushButton("Upload Photo")
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #538cc6;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 10px;
            }
        """)
        self.upload_btn = upload_btn  # Store as instance variable
        self.upload_btn.clicked.connect(self.upload_photo)  # Connect upload button
        avatar_layout.addWidget(self.profile_pic)
        avatar_layout.addSpacing(10)
        avatar_layout.addWidget(self.upload_btn, alignment=Qt.AlignHCenter)

        self.form_layout = QFormLayout()  # Store form_layout as instance variable
        self.form_layout.setVerticalSpacing(25)

        self.name_label = QLabel("Name:")
        self.name = QLineEdit()
        self.owner_id_label = QLabel("Owner ID:")
        self.owner_id = QLineEdit()
        self.phone_number_label = QLabel("Phone Number:")
        self.phone_number = QLineEdit()
        self.email_label = QLabel("Email:")
        self.email = QLineEdit()
        self.branch_label = QLabel("Branch:")
        self.branch = QLineEdit()

        # New password fields
        self.password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.confirm_password_label = QLabel("Confirm Password:")
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)

        for field in [self.name, self.owner_id, self.phone_number, self.email, self.branch, self.password_input,
                      self.confirm_password_input]:
            field.setFixedWidth(500)
            field.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #773a1f;
                    border-radius: 15px;
                    padding: 10px;
                    font-size: 15px;
                }
            """)

        # Add all rows to the form layout initially
        self.form_layout.addRow(self.name_label, self.name)
        self.form_layout.addRow(self.owner_id_label, self.owner_id)
        self.form_layout.addRow(self.phone_number_label, self.phone_number)
        self.form_layout.addRow(self.email_label, self.email)
        self.form_layout.addRow(self.branch_label, self.branch)

        self.form_layout.addRow(self.password_label, self.password_input)
        self.form_layout.addRow(self.confirm_password_label, self.confirm_password_input)

        save_btn = QPushButton("Save Changes")
        self.save_btn = save_btn  # Store as instance variable
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #538cc6;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 10px;
            }
        """)
        self.save_btn.clicked.connect(self.save_changes)
        self.form_layout.addRow("", self.save_btn)

        content_layout = QHBoxLayout()
        content_layout.addStretch()
        content_layout.addLayout(avatar_layout)
        content_layout.addSpacing(50)
        content_layout.addLayout(self.form_layout)  # Use instance variable
        content_layout.addStretch()

        frame_layout.addStretch()
        frame_layout.addLayout(content_layout)
        frame_layout.addStretch()

        center_frame_layout = QHBoxLayout()
        center_frame_layout.addStretch()
        center_frame_layout.addWidget(white_frame)
        center_frame_layout.addStretch()

        main_layout.addLayout(center_frame_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def set_default_avatar(self):
        # Create a blank white pixmap
        blank_pixmap = QPixmap(180, 180)
        blank_pixmap.fill(Qt.white)
        self.profile_pic.setPixmap(blank_pixmap)
        self.profile_pic.setStyleSheet("""
            QLabel {
                border: 1px solid gray;
                background-color: #fff;
                border-radius: 90px;
                color: #666666;
                font-size: 18px;
            }
        """)
        self.profile_pic.setText("Upload\nPhoto")

    def upload_photo(self):
        if not self.is_editable:
            return  # Only allow upload in edit mode
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Profile Photo", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            original_pixmap = QPixmap(file_path)
            if original_pixmap.isNull():
                return
            os.makedirs("profile_pics", exist_ok=True)
            cropped_pixmap = self.crop_to_circle(original_pixmap, 180)
            save_path = f"profile_pics/{self.user_id}.png"
            cropped_pixmap.save(save_path)
            self.profile_pic.setPixmap(cropped_pixmap)

    def crop_to_circle(self, pixmap, size):
        w = pixmap.width()
        h = pixmap.height()
        side = min(w, h)
        x = (w - side) // 2
        y = (h - side) // 2
        square_pixmap = pixmap.copy(x, y, side, side).scaled(size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        masked_pixmap = QPixmap(size, size)
        masked_pixmap.fill(Qt.transparent)
        painter = QPainter(masked_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, square_pixmap)
        painter.end()
        return masked_pixmap

    def set_view_mode(self):
        self.is_editable = False
        self.edit_btn.show()  # Show edit button in view mode

        # Set fields editability
        self.name.setReadOnly(True)
        self.owner_id.setReadOnly(True)
        self.branch.setReadOnly(True)
        self.email.setReadOnly(True)
        self.phone_number.setReadOnly(True)
        self.password_input.setReadOnly(True)
        self.confirm_password_input.setReadOnly(True)

        # Control visibility for view mode
        self.name_label.setVisible(True)
        self.name.setVisible(True)
        self.owner_id_label.setVisible(True)
        self.owner_id.setVisible(True)
        self.branch_label.setVisible(True)
        self.branch.setVisible(True)
        self.phone_number_label.setVisible(True)
        self.phone_number.setVisible(True)
        self.email_label.setVisible(True)
        self.email.setVisible(True)

        # Hide edit-specific fields and buttons
        self.password_label.setVisible(False)
        self.password_input.setVisible(False)
        self.confirm_password_label.setVisible(False)
        self.confirm_password_input.setVisible(False)
        self.save_btn.setVisible(False)
        self.upload_btn.setVisible(False)

        # Clear password fields when switching out of edit mode
        self.password_input.clear()
        self.confirm_password_input.clear()

        # Re-add rows in view mode order
        self.rearrange_form_layout(mode="view")

    def set_new_user_edit_mode(self):
        self.is_editable = True
        self.edit_btn.hide()  # Hide edit button for initial new user setup

        # Set fields editability
        self.name.setReadOnly(True)
        self.owner_id.setReadOnly(True)
        self.branch.setReadOnly(True)
        self.email.setReadOnly(False)  # Email is editable for new users
        self.phone_number.setReadOnly(False)  # Phone number is editable for new users
        self.password_input.setReadOnly(True)  # Password fields are not editable initially
        self.confirm_password_input.setReadOnly(True)

        # Control visibility for new user edit mode
        self.name_label.setVisible(True)
        self.name.setVisible(True)
        self.owner_id_label.setVisible(True)
        self.owner_id.setVisible(True)
        self.branch_label.setVisible(True)
        self.branch.setVisible(True)
        self.phone_number_label.setVisible(True)
        self.phone_number.setVisible(True)
        self.email_label.setVisible(True)
        self.email.setVisible(True)

        # Hide password fields initially for new users
        self.password_label.setVisible(False)
        self.password_input.setVisible(False)
        self.confirm_password_label.setVisible(False)
        self.confirm_password_input.setVisible(False)

        # Show save and upload buttons
        self.save_btn.setVisible(True)
        self.upload_btn.setVisible(True)

        # Clear password fields just in case
        self.password_input.clear()
        self.confirm_password_input.clear()

        # Re-add rows in new user edit mode order
        self.rearrange_form_layout(mode="new_user_edit")

    def set_full_edit_mode(self):
        self.is_editable = True
        self.edit_btn.hide()  # Hide edit button in full edit mode

        # Set fields editability
        self.name.setReadOnly(True)
        self.owner_id.setReadOnly(True)
        self.branch.setReadOnly(True)
        self.email.setReadOnly(False)
        self.phone_number.setReadOnly(False)
        self.password_input.setReadOnly(False)
        self.confirm_password_input.setReadOnly(False)

        # Apply stylesheet to editable fields to remove focus outline
        editable_style = """
            QLineEdit {
                border: 2px solid #773a1f;
                border-radius: 15px;
                padding: 10px;
                font-size: 15px;
            }
            QLineEdit:focus {
                outline: none; /* Remove default focus outline */
                border: 2px solid #773a1f; /* Keep the border */
            }
        """
        self.email.setStyleSheet(editable_style)
        self.phone_number.setStyleSheet(editable_style)
        self.password_input.setStyleSheet(editable_style)
        self.confirm_password_input.setStyleSheet(editable_style)

        # Set read-only fields style back to default or view style if needed
        view_style = """
            QLineEdit {
                border: 2px solid #773a1f;
                border-radius: 15px;
                padding: 10px;
                font-size: 15px;
                background-color: #eeeded; /* Indicate read-only */
            }
        """
        self.name.setStyleSheet(view_style)
        self.owner_id.setStyleSheet(view_style)
        self.branch.setStyleSheet(view_style)

        # Control visibility for full edit mode
        self.email_label.setVisible(True)
        self.email.setVisible(True)
        self.phone_number_label.setVisible(True)
        self.phone_number.setVisible(True)
        self.password_label.setVisible(True)
        self.password_input.setVisible(True)
        self.confirm_password_label.setVisible(True)
        self.confirm_password_input.setVisible(True)

        # Hide view-specific fields
        self.name_label.setVisible(False)
        self.name.setVisible(False)
        self.owner_id_label.setVisible(False)
        self.owner_id.setVisible(False)
        self.branch_label.setVisible(False)
        self.branch.setVisible(False)

        # Show save and upload buttons
        self.save_btn.setVisible(True)
        self.upload_btn.setVisible(True)

        # Re-add rows in full edit mode order
        self.rearrange_form_layout(mode="full_edit")

    def toggle_full_edit_mode(self):
        # This is called by the edit_btn. It should only switch to full edit mode.
        self.set_full_edit_mode()

    def rearrange_form_layout(self, mode):
        # Remove all current items from the layout first
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            # We don't delete widgets as they are reused, just take them out of the layout
            # No need to set visibility to False here as it's done in the mode setting functions

        # Add items back based on the mode
        if mode == "view":
            self.form_layout.addRow(self.name_label, self.name)
            self.form_layout.addRow(self.owner_id_label, self.owner_id)
            self.form_layout.addRow(self.phone_number_label, self.phone_number)
            self.form_layout.addRow(self.email_label, self.email)
            self.form_layout.addRow(self.branch_label, self.branch)
            # Save button is hidden in view mode, but we add its row structure to keep layout consistent
            self.form_layout.addRow("", self.save_btn)
        elif mode == "new_user_edit":
            # Order for new user edit mode: Name, Owner ID, Phone, Email, Branch, Save
            self.form_layout.addRow(self.name_label, self.name)
            self.form_layout.addRow(self.owner_id_label, self.owner_id)
            self.form_layout.addRow(self.phone_number_label, self.phone_number)
            self.form_layout.addRow(self.email_label, self.email)
            self.form_layout.addRow(self.branch_label, self.branch)
            self.form_layout.addRow("", self.save_btn)  # Save button row
        elif mode == "full_edit":
            # Order for full edit mode: Phone, Email, Password, Confirm Password, Save
            self.form_layout.addRow(self.phone_number_label, self.phone_number)
            self.form_layout.addRow(self.email_label, self.email)
            self.form_layout.addRow(self.password_label, self.password_input)
            self.form_layout.addRow(self.confirm_password_label, self.confirm_password_input)
            self.form_layout.addRow("", self.save_btn)  # Save button row

    def save_changes(self):
        if not self.is_editable:
            return  # Ensure we are in edit mode to save

        email = self.email.text().strip()
        phone = self.phone_number.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validation for email and phone number (always required when saving)
        if not email or not phone:
            QMessageBox.warning(self, "Missing Information", "Please fill in both email and phone number.")
            return  # Stop saving if fields are empty

        # Validation for password fields if they are visible (meaning we are in edit mode)
        if self.password_label.isVisible():
            if password or confirm_password:
                if password != confirm_password:
                    QMessageBox.warning(self, "Password Mismatch", "Password and Confirm Password do not match.")
                    return
                if len(password) < 6:
                    QMessageBox.warning(self, "Password Too Short", "Password must be at least 6 characters long.")
                    return

        conn = sqlite3.connect("medical_system.db")
        c = conn.cursor()

        # Update email and phone number
        c.execute("UPDATE Users SET email=?, phone_no=? WHERE user_id=?", (email, phone, self.user_id))

        # Update password if provided and passwords match and are long enough
        if self.password_label.isVisible() and password and (password == confirm_password) and (len(password) >= 6):
            # Hash the password before saving
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            c.execute("UPDATE Users SET password=? WHERE user_id=?", (hashed_password, self.user_id))

        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Profile updated successfully!")
        self.set_view_mode()  # Exit edit mode and go to view mode after saving

    def close_app(self):
        QApplication.quit()


class PopupWindow(QWidget):
    def __init__(self, title):
        super().__init__()
        self.setWindowTitle(title)
        self.setFixedSize(300, 150)
        self.setStyleSheet("background-color: #fff0e6;")
        layout = QVBoxLayout()
        label = QLabel(f"This is the {title} window")
        label.setFont(QFont("Arial", 14))
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)


# --- Custom Delegate for Filter Dropdown ---
class FilterItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = {
            "All": {"bg": "#d6e0f5", "text": "#222", "border": "#5c85d6"},  # Blue border for All
            "Pending": {"bg": "#666666", "text": "white", "border": "#444444"},  # Grey
            "Approved": {"bg": "#219150", "text": "white", "border": "#1a7340"},  # Green
            "Rejected": {"bg": "#e74c3c", "text": "white", "border": "#c0392b"}  # Red
        }

    def paint(self, painter, option, index):
        item_text = index.data(Qt.DisplayRole)
        color_scheme = self.colors.get(item_text, self.colors["All"])

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Create smaller item rectangle with more margin
        rect = option.rect.adjusted(8, 3, -8, -3)

        # Draw background with border
        painter.setPen(QColor(color_scheme["border"]))
        painter.setBrush(QColor(color_scheme["bg"]))
        painter.drawRoundedRect(rect, 10, 10)  # Smaller border radius

        # Draw text centered
        painter.setPen(QColor(color_scheme["text"]))
        painter.setFont(QFont("Arial", 14, QFont.Bold))  # Smaller font size
        painter.drawText(rect, Qt.AlignCenter | Qt.AlignVCenter,
                         item_text)  # Ensure both horizontal and vertical centering

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(140, 40)  # Smaller overall size


# --- Product Submissions Widget ---
class ProductSubmissionsWidget(QWidget):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Ensure this widget expands vertically
        self.setStyleSheet("background-color: #d6e0f5;")  # Set consistent background

        title = QLabel("Product Submissions")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #5D3A00; background-color: transparent;")
        title.setAlignment(Qt.AlignCenter)
        self.main_layout.addSpacing(10)  # Added 10pt spacing to move title and all content down
        self.main_layout.addWidget(title)
        self.main_layout.addSpacing(0)  # Keep minimal spacing

        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.addStretch()
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["All", "Pending", "Approved", "Rejected"])  # Removed 'Under Review'

        # Set custom delegate for colored dropdown items
        self.filter_delegate = FilterItemDelegate()
        self.status_filter_combo.setItemDelegate(self.filter_delegate)

        # Set initial styling and connect change event
        self.update_filter_styling()
        self.status_filter_combo.currentIndexChanged.connect(self.on_filter_changed)

        filter_layout.addWidget(self.status_filter_combo)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)
        self.main_layout.addSpacing(0)  # Keep minimal spacing

        # Scroll Area for Product Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none; 
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.products_container = QWidget()  # Widget to hold all product cards
        self.products_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # Allow container to expand
        self.products_container.setStyleSheet("background-color: transparent;")  # Ensure transparent background
        self.products_layout = QVBoxLayout(self.products_container)
        self.products_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.products_layout.setSpacing(5)  # Reduced spacing between cards

        self.scroll_area.setWidget(self.products_container)
        self.scroll_area.setFixedHeight(980)  # Calculated for 3 cards (3*320 + 2*10 = 980)
        self.main_layout.addWidget(self.scroll_area, 1)  # Added stretch factor
        self.main_layout.addStretch()  # Added to push content to the top

        # Initial load of products
        self.load_products()

    def update_filter_styling(self):
        """Update the filter dropdown styling with consistent orange color and colored item frames"""
        # Use the same orange color scheme for all filter options
        selected_color = {"bg": "#d6e0f5", "text": "#222", "border": "#5c85d6"}  # Blue border for All

        style = f"""
            QComboBox {{
                padding: 12px 35px 12px 25px;
                border: 2px solid {selected_color['border']};
                border-radius: 25px;  /* More oval shape */
                font-family: "Times New Roman";
                font-size: 20px;
                font-weight: bold;
                background-color: {selected_color['bg']};
                color: {selected_color['text']};
                min-width: 160px;
                min-height: 50px;
                text-align: center;  /* Center the text */
            }}
            QComboBox::drop-down {{
                border: none;
                background: transparent;
                width: 25px;
                margin-right: 10px;
            }}
            QComboBox::down-arrow {{
                image: url("C:/Kai Shuang/9.png");
                border: none;
                background: transparent;
                width: 16px;
                height: 16px;
                margin-right: 8px;
                margin-top: 2px;
            }}
            QComboBox:hover {{
                border: 2px solid {selected_color['border']};
                background-color: {selected_color['bg']};
                opacity: 0.8;
            }}
            QComboBox:pressed {{
                background-color: #d6e0f5;
            }}
            QComboBox QAbstractItemView {{
                background-color: white;
                border: 2px solid #ddd;
                border-radius: 15px;
                padding: 8px;
                selection-background-color: transparent;
                selection-color: transparent;
                outline: none;
                show-decoration-selected: 0;
            }}
            QComboBox::item {{
                min-height: 40px;
                border: none;
                background: transparent;
                margin: 1px;
                padding: 0px;
            }}
            QComboBox::item:selected {{
                background: transparent;
                border: none;
            }}
            QComboBox::item:hover {{
                background: transparent;
                border: none;
            }}
        """

        self.status_filter_combo.setStyleSheet(style)

    def on_filter_changed(self):
        """Handle filter change event"""
        self.update_filter_styling()  # Update styling based on new selection
        self.load_products()  # Reload products with new filter

    def showEvent(self, event):
        super().showEvent(event)
        self.load_products()

    def load_products(self):
        # Clear existing cards
        while self.products_layout.count():
            item = self.products_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        selected_status = self.status_filter_combo.currentText()

        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()

        query = """
            SELECT product_id, product_name, manufacture_date, expired_date, arrival_date, 
                   location, batch, barcode, barcode_image, sku, product_image, status, description
            FROM Products
            WHERE user_id = ?
        """
        params = [self.user_id]

        if selected_status != "All":
            query += " AND status = ?"
            params.append(selected_status.lower())

        query += " ORDER BY product_id DESC"

        cursor.execute(query, params)
        products = cursor.fetchall()
        conn.close()

        if not products:
            no_products_label = QLabel("No product submissions found for this filter.")
            no_products_label.setFont(QFont("Arial", 16))
            no_products_label.setAlignment(Qt.AlignCenter)
            self.products_layout.addWidget(no_products_label)
        else:
            for product in products:
                product_data = {
                    "product_id": product[0],
                    "product_name": product[1],
                    "manufacture_date": product[2],
                    "expired_date": product[3],
                    "arrival_date": product[4],
                    "location": product[5],
                    "batch": product[6],
                    "barcode": product[7],
                    "barcode_image": product[8],
                    "sku": product[9],
                    "product_image": product[10],
                    "status": product[11],
                    "description": product[12],
                    # Assuming branch is not directly in Products table, if needed, join with Users table.
                    # For now, let's pass a placeholder or retrieve it from OwnerMainWindow if consistent
                    "branch": ""  # Placeholder for branch - will need to fetch if truly dynamic
                }
                # Fetch branch from Users table for the product's owner
                conn_branch = sqlite3.connect("medical_system.db")
                cursor_branch = conn_branch.cursor()
                cursor_branch.execute(
                    "SELECT branch FROM Users WHERE user_id = (SELECT user_id FROM Products WHERE product_id = ?)",
                    (product[0],))
                branch_result = cursor_branch.fetchone()
                conn_branch.close()
                if branch_result:
                    product_data["branch"] = branch_result[0]

                card = ProductCardWidget(product_data)
                self.products_layout.addWidget(card)


# --- Product Card Widget ---
class ProductCardWidget(QFrame):
    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setFixedSize(1200, 320)  # Increased width from 1050 to 1200 and height from 280 to 320

        # Check if product is approved or rejected to make it clickable
        self.is_approved = self.product_data.get('status', '').lower() == 'approved'
        self.is_rejected = self.product_data.get('status', '').lower() == 'rejected'
        self.is_clickable = self.is_approved or self.is_rejected

        if self.is_clickable:
            self.setStyleSheet("""
                ProductCardWidget {
                    background-color: white;
                    border: none;
                    border-radius: 15px;
                    margin: 5px;
                }
                ProductCardWidget:hover {
                    background-color: #f8f9fa;
                    border: none;
                }
            """)
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setStyleSheet("""
                ProductCardWidget {
                    background-color: white;
                    border: none;
                    border-radius: 15px;
                    margin: 5px;
                }
            """)

        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(35, 15, 15, 15)  # Increased left margin to move content right
        main_layout.setSpacing(25)  # Increased spacing between sections

        # Product Image
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setStyleSheet("background-color: #cccccc; border-radius: 10px; border: 1px solid #d08b5b;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("No Image")
        if self.product_data['product_image'] and os.path.exists(self.product_data['product_image']):
            pixmap = QPixmap(self.product_data['product_image'])
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.image_label.setText("")
        # Add small spacing to move photo to the right
        main_layout.addSpacing(10)  # Move photo to the right
        main_layout.addWidget(self.image_label)

        # Add spacing between photo and information sections
        main_layout.addSpacing(40)  # Reduced spacing to move information to the left

        # Create a main content layout that will contain both left and right sections
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)  # Reduced spacing to allow room for right shift
        content_layout.setContentsMargins(0, 40, 0, 0)  # Add top margin to move content down

        # Product Info Layout (Left Side) - Basic Information with Description
        info_layout_left = QVBoxLayout()
        info_layout_left.setSpacing(6)  # Reduced spacing to prevent overlap
        info_layout_left.setContentsMargins(0, 0, 0, 0)  # Remove margins to save space

        # Fix description display - handle None/empty values
        description_text = self.product_data.get('description', '') or ''
        if not description_text or description_text.lower() == 'none':
            description_text = "No description available"

        self.product_name_label = QLabel(
            f"<b style='color: #5D3A00;'>Product Name:</b> <span style='color: #555;'>{self.product_data['product_name']}</span>")

        # Description section right after Product Name
        description_title = QLabel("<b style='color: #5D3A00;'>Description:</b>")
        description_title.setFont(QFont("Times New Roman", 12))  # Decreased font size by 0.5pt
        description_title.setStyleSheet("""
            QLabel {
                color: #222;
                padding: 1px 0px;
                background-color: transparent;
                margin: 0px;
            }
        """)

        # Scrollable description text - controlled size to prevent overlap
        self.description_text = QTextEdit()
        self.description_text.setPlainText(description_text)
        self.description_text.setReadOnly(True)
        self.description_text.setFont(QFont("Times New Roman", 12))  # Decreased font size by 0.5pt
        self.description_text.setFixedHeight(80)  # Reduced height to prevent overlap
        self.description_text.setFixedWidth(400)  # Keep wide width for readability
        self.description_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d08b5b;
                border-radius: 6px;
                padding: 4px;
                background-color: #f9f9f9;
                color: #555;
                margin: 0px;
            }
            QTextEdit:focus {
                border: 2px solid #d08b5b;
                background-color: #fff;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        self.arrival_date_label = QLabel(
            f"<b style='color: #5D3A00;'>Arrival Date:</b> <span style='color: #555;'>{self.product_data['arrival_date']}</span>")
        self.manufacture_date_label = QLabel(
            f"<b style='color: #5D3A00;'>Manufacture Date:</b> <span style='color: #555;'>{self.product_data['manufacture_date']}</span>")

        # Set font and styling for left side labels with reduced padding
        for label in [self.product_name_label, self.arrival_date_label, self.manufacture_date_label]:
            label.setFont(QFont("Times New Roman", 12))  # Decreased font size by 0.5pt
            label.setStyleSheet("""
                QLabel {
                    color: #222;
                    padding: 1px 0px;
                    background-color: transparent;
                    margin: 0px;
                }
            """)
            label.setWordWrap(True)

        # Add all elements to left layout with careful spacing
        info_layout_left.addWidget(self.product_name_label)
        info_layout_left.addSpacing(2)  # Small spacing
        info_layout_left.addWidget(description_title)
        info_layout_left.addWidget(self.description_text)
        info_layout_left.addSpacing(4)  # Small spacing before dates
        info_layout_left.addWidget(self.arrival_date_label)
        info_layout_left.addWidget(self.manufacture_date_label)
        info_layout_left.addStretch()

        # Set fixed width for left section with description
        left_widget = QWidget()
        left_widget.setLayout(info_layout_left)
        left_widget.setFixedWidth(420)  # Slightly reduced width
        content_layout.addWidget(left_widget)

        # Add some spacing to push right section to the right
        content_layout.addSpacing(20)  # Reduced spacing to move sections closer to left

        # Product Info Layout (Right Side) - Expiry Date first to align with Product Name
        info_layout_right = QVBoxLayout()
        info_layout_right.setSpacing(6)  # Reduced spacing to match left side
        info_layout_right.setContentsMargins(0, 0, 0, 0)  # Reset margins for precise alignment
        self.expiry_date_label = QLabel(
            f"<b style='color: #5D3A00;'>Expiry Date:</b> <span style='color: #555;'>{self.product_data['expired_date']}</span>")
        self.branch_label = QLabel(
            f"<b style='color: #5D3A00;'>Branch:</b> <span style='color: #555;'>{self.product_data['branch']}</span>")
        self.sku_label = QLabel(
            f"<b style='color: #5D3A00;'>SKU:</b> <span style='color: #555;'>{self.product_data['sku']}</span>")
        self.rack_location_label = QLabel(
            f"<b style='color: #5D3A00;'>Rack Location:</b> <span style='color: #555;'>{self.product_data['location']}</span>")
        self.batch_label = QLabel(
            f"<b style='color: #5D3A00;'>Batch:</b> <span style='color: #555;'>{self.product_data['batch']}</span>")

        for label in [self.branch_label, self.sku_label, self.rack_location_label, self.batch_label,
                      self.expiry_date_label]:
            label.setFont(QFont("Times New Roman", 12))  # Decreased font size by 0.5pt
            label.setStyleSheet("""
                QLabel {
                    color: #222;
                    padding: 1px 0px;
                    background-color: transparent;
                    margin: 0px;
                }
            """)
            label.setWordWrap(True)

        info_layout_right.addWidget(self.expiry_date_label)
        info_layout_right.addWidget(self.branch_label)
        info_layout_right.addWidget(self.sku_label)
        info_layout_right.addWidget(self.rack_location_label)
        info_layout_right.addWidget(self.batch_label)
        info_layout_right.addStretch()

        # Right side widget with controlled width
        right_widget = QWidget()
        right_widget.setLayout(info_layout_right)
        right_widget.setFixedWidth(280)  # Fixed width to match left side
        content_layout.addWidget(right_widget)

        main_layout.addLayout(content_layout)

        # Add stretch to push status to far right
        main_layout.addStretch()

        # Status Label (Bottom Right)
        status_container = QWidget()
        status_container.setFixedSize(180, 320)  # Match card height
        status_layout = QVBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.addStretch()  # Push status to bottom

        self.status_label = QLabel(self.product_data['status'].capitalize())
        self.status_label.setFont(QFont("Times New Roman", 14, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedSize(160, 56)
        status_text = self.product_data['status'].lower()
        if status_text == "approved":
            self.status_label.setStyleSheet(
                "background-color: #219150; border-radius: 18px; color: white; font-weight: bold;")
        elif status_text == "rejected":
            self.status_label.setStyleSheet(
                "background-color: #e74c3c; border-radius: 18px; color: white; font-weight: bold;")
        elif status_text == "pending":
            self.status_label.setStyleSheet(
                "background-color: #666666; border-radius: 18px; color: white; font-weight: bold;")
        else:
            self.status_label.setStyleSheet(
                "background-color: #f5cba7; border-radius: 18px; color: #222; font-weight: bold;")

        status_layout.addWidget(self.status_label, alignment=Qt.AlignRight)
        status_layout.addSpacing(40)  # Reduced from 25 to 20 to move status up by 5pt

        main_layout.addWidget(status_container)
        self.setLayout(main_layout)

    def mousePressEvent(self, event):
        """Handle mouse click events - open detail window for approved/rejected products"""
        if event.button() == Qt.LeftButton and self.is_clickable:
            self.open_detail_window()
        super().mousePressEvent(event)

    def open_detail_window(self):
        """Open the appropriate detail window based on product status"""
        try:
            if self.is_approved:
                detail_window = ProductDetailWindow(self.product_data, self)
                detail_window.exec_()
            elif self.is_rejected:
                rejected_window = RejectedProductDetailWindow(self.product_data, self)
                # Connect the resubmitted signal to refresh the parent widget
                rejected_window.product_resubmitted.connect(self.refresh_parent_submissions)
                rejected_window.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open product details: {str(e)}")

    def refresh_parent_submissions(self):
        """Find and refresh the ProductSubmissionsWidget from this card's perspective"""
        try:
            # Start from this card widget and go up the hierarchy
            current_widget = self.parent()

            # Traverse up the widget hierarchy to find ProductSubmissionsWidget
            while current_widget:
                if isinstance(current_widget, ProductSubmissionsWidget):
                    current_widget.load_products()
                    return

                # Check if current widget has a load_products method
                if hasattr(current_widget, 'load_products') and hasattr(current_widget, 'user_id'):
                    current_widget.load_products()
                    return

                # Move up one level in the hierarchy
                current_widget = current_widget.parent()

            # If we couldn't find it through parent hierarchy, try to find it from the main window
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if isinstance(widget, OwnerMainWindow):
                        if hasattr(widget, 'product_submissions_widget'):
                            widget.product_submissions_widget.load_products()
                            return

        except Exception as e:
            print(f"Error refreshing from card widget: {e}")
            # Fallback: try to find any ProductSubmissionsWidget in the application
            try:
                app = QApplication.instance()
                if app:
                    for widget in app.allWidgets():
                        if isinstance(widget, ProductSubmissionsWidget):
                            widget.load_products()
                            break
            except Exception as e2:
                print(f"Card widget fallback refresh also failed: {e2}")


# --- Chat Widget (Integrated from Chat.py) ---
class NotificationWidget(QWidget):
    def __init__(self, user_info=None, parent=None):
        super().__init__(parent)
        self.user_info = user_info or {}
        self.active_pm_user = None
        self.active_pm_role = None
        self.selected_user_item = None  # Track currently selected user item for visual feedback

        # Define role colors
        self.role_colors = {
            'superadmin': '#FF9800',  # Orange
            'admin': '#4CAF50',  # Green
            'owner': '#2196F3',  # Blue
            'tester': '#E91E63'  # Pink
        }

        # Initialize chat database tables
        create_chat_tables()

        self.setupUI()
        self.load_messages()
        self.load_available_users()

        # Auto-refresh every 3 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(3000)

    def setupUI(self):
        # Main layout with owner blue theme
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Chat / Announcement")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setStyleSheet("color: #5D3A00; background-color: transparent;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)
        main_layout.addLayout(header_layout)

        # Content layout - horizontal split
        content_layout = QHBoxLayout()
        content_layout.setSpacing(15)

        # Left side - Chat area (70% width)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Global chat display
        chat_group = QGroupBox("Global Chat Room")
        chat_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 12px;
                margin: 8px 0px;
                padding-top: 20px;
                background: rgba(255, 255, 255, 0.9);
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 8px 16px;
                color: white;
                background: #2196F3;
                border-radius: 6px;
            }
        """)

        chat_layout = QVBoxLayout()
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.95);
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                padding: 12px;
            }
        """)
        chat_layout.addWidget(self.chat_display)
        chat_group.setLayout(chat_layout)
        left_layout.addWidget(chat_group)

        # Read-only message for owners
        readonly_label = QLabel("📢 You can view messages from admins but cannot send messages in the public chat room.")
        readonly_label.setStyleSheet("""
            QLabel {
                color: #666; 
                font-style: italic; 
                padding: 10px; 
                background-color: #f0f8ff;
                border: 1px solid #2196F3;
                border-radius: 8px;
                font-size: 13px;
            }
        """)
        readonly_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(readonly_label)

        content_layout.addWidget(left_widget, 7)  # 70% width

        # Right side - Users and Private Chat (30% width)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Users list
        users_group = QGroupBox("All Users")
        users_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 12px;
                margin: 8px 0px;
                padding-top: 20px;
                background: rgba(255, 255, 255, 0.9);
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 8px 16px;
                color: white;
                background: #2196F3;
                border-radius: 6px;
            }
        """)

        users_layout = QVBoxLayout()

        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍")
        self.user_search = QLineEdit()
        self.user_search.setPlaceholderText("Search users...")
        self.user_search.textChanged.connect(self.search_users)
        self.user_search.setStyleSheet("""
            QLineEdit {
                font-size: 12px;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 15px;
                background-color: white;
            }
        """)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.user_search)
        users_layout.addLayout(search_layout)

        # Users list
        self.users_list = QListWidget()
        self.users_list.itemClicked.connect(self.start_private_chat)
        self.users_list.setMaximumHeight(200)
        self.users_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
                selection-background-color: #2196F3;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 4px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                border: 2px solid #0D47A1;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background: #e3f2fd;
                border: 1px solid #90CAF9;
                border-radius: 4px;
            }
            QListWidget::item:selected:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                           stop:0 #1976D2, stop:1 #1565C0);
                color: white;
                border: 2px solid #0D47A1;
            }
        """)
        users_layout.addWidget(self.users_list)

        pm_info = QLabel("💬 Chat with Admins & Staff")
        pm_info.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        users_layout.addWidget(pm_info)

        users_group.setLayout(users_layout)
        right_layout.addWidget(users_group)

        # Private message area
        pm_group = QGroupBox("Private Messages")
        pm_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 12px;
                margin: 8px 0px;
                padding-top: 20px;
                background: rgba(255, 255, 255, 0.9);
                font-size: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 8px 16px;
                color: white;
                background: #2196F3;
                border-radius: 6px;
            }
        """)

        pm_layout = QVBoxLayout()

        # Active conversation indicator
        self.active_pm_label = QLabel("Select admin/staff to start messaging")
        self.active_pm_label.setStyleSheet("""
            QLabel {
                color: #888; 
                font-size: 10px; 
                padding: 4px; 
                border-bottom: 1px solid #eee;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        pm_layout.addWidget(self.active_pm_label)

        # Private message display
        self.pm_display = QTextEdit()
        self.pm_display.setReadOnly(True)
        self.pm_display.setMinimumHeight(180)
        self.pm_display.setMaximumHeight(220)
        self.pm_display.setPlaceholderText("Private messages will appear here...")
        self.pm_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
                padding: 8px;
            }
        """)
        pm_layout.addWidget(self.pm_display)

        # Private message input
        self.pm_input = QTextEdit()
        self.pm_input.setPlaceholderText("Type private message...")
        self.pm_input.setEnabled(False)
        self.pm_input.setMinimumHeight(50)
        self.pm_input.setMaximumHeight(70)
        self.pm_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
                background-color: #f8f9fa;
            }
            QTextEdit:focus {
                border-color: #2196F3;
                background-color: white;
            }
        """)
        pm_layout.addWidget(self.pm_input)

        # Send button
        self.pm_send_btn = QPushButton("Send Private Message")
        self.pm_send_btn.clicked.connect(self.send_private_message)
        self.pm_send_btn.setEnabled(False)
        self.pm_send_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QPushButton:disabled {
                background: #ccc;
                color: #666;
            }
        """)
        pm_layout.addWidget(self.pm_send_btn)

        pm_group.setLayout(pm_layout)
        right_layout.addWidget(pm_group)

        content_layout.addWidget(right_widget, 3)  # 30% width
        main_layout.addLayout(content_layout)

    def refresh_all(self):
        """Refresh messages and users"""
        self.load_messages()
        self.load_available_users()

        # Refresh private messages if active
        if self.active_pm_user:
            self.load_private_messages_inline()

    def load_messages(self):
        """Load and display global chat messages"""
        messages = get_all_messages()

        # Save scroll position
        scrollbar = self.chat_display.verticalScrollBar()
        was_at_bottom = scrollbar.value() == scrollbar.maximum()

        self.chat_display.clear()

        for message in messages:
            username, role, text, timestamp, message_id = message

            # Format timestamp
            time_str = format_malaysia_time(timestamp)

            # Get role color and icon
            role_color = self.role_colors.get(role.lower(), '#666666')
            role_icons = {
                'superadmin': '👑',
                'admin': '📢',
                'owner': '🏢',
                'tester': '🧪'
            }
            role_icon = role_icons.get(role.lower(), '👤')

            # Format message bubble
            bubble_style = (
                f"background: linear-gradient(135deg, {role_color}15 0%, {role_color}08 100%); "
                f"border: 2px solid {role_color}30; border-radius: 12px; "
                f"margin: 8px 0; padding: 12px;"
            )

            formatted_message = (
                f"<div style='{bubble_style}'>"
                f"<div style='color: {role_color}; font-weight: bold; font-size: 13px; margin-bottom: 4px;'>"
                f"{role_icon} {username} ({role.title()})"
                f"</div>"
                f"<div style='color: #666; font-size: 11px; margin-bottom: 8px;'>{time_str}</div>"
                f"<div style='font-size: 14px; color: #333;'>{text}</div>"
                f"</div>"
            )

            self.chat_display.append(formatted_message)

        # Restore scroll position
        if was_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def load_available_users(self):
        """Load users for private messaging"""
        current_username = self.user_info.get('username', '')
        users = get_all_chat_users(current_username)

        self.all_users = users
        self.populate_users_list(users)

    def populate_users_list(self, users):
        """Populate the users list"""
        self.users_list.clear()
        selected_username = None

        # Remember the currently selected user
        if self.selected_user_item and self.active_pm_user:
            selected_username = self.active_pm_user

        for username, role_name, fullname in users:
            display_name = fullname if fullname else username

            # Use role-specific icons
            role_icons = {
                'superadmin': '👑',
                'admin': '📢',
                'tester': '🧪',
                'owner': '🏢'
            }
            role_icon = role_icons.get(role_name.lower(), '👤')

            item_text = f"{role_icon} {username} ({role_name.title()})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, {'username': username, 'role_name': role_name, 'fullname': fullname})
            self.users_list.addItem(item)

            # Restore selection if this was the previously selected user
            if selected_username and username == selected_username:
                item.setSelected(True)
                self.selected_user_item = item
                self.users_list.setCurrentItem(item)

    def search_users(self):
        """Filter users based on search text"""
        search_text = self.user_search.text().strip().lower()

        if not search_text:
            if hasattr(self, 'all_users'):
                self.populate_users_list(self.all_users)
        else:
            if hasattr(self, 'all_users'):
                filtered_users = []
                for username, role_name, fullname in self.all_users:
                    if (search_text in username.lower() or
                            (fullname and search_text in fullname.lower())):
                        filtered_users.append((username, role_name, fullname))
                self.populate_users_list(filtered_users)

    def start_private_chat(self, item):
        """Start private chat with selected user"""
        # Track the selected item for visual feedback
        self.selected_user_item = item

        user_data = item.data(Qt.UserRole)
        target_username = user_data['username']
        target_role = user_data.get('role_name', 'user')

        self.activate_private_chat(target_username, target_role)

    def activate_private_chat(self, target_username, target_role):
        """Activate private messaging"""
        self.active_pm_user = target_username
        self.active_pm_role = target_role

        # Update UI
        self.active_pm_label.setText(f"Chat with {target_username}")
        self.pm_input.setEnabled(True)
        self.pm_input.setPlaceholderText(f"Type message to {target_username}...")
        self.pm_send_btn.setEnabled(True)

        # Load messages
        self.load_private_messages_inline()

    def load_private_messages_inline(self):
        """Load private messages for active conversation"""
        if not self.active_pm_user:
            return

        current_username = self.user_info.get('username', '')
        messages = get_private_messages(current_username, self.active_pm_user)

        self.pm_display.clear()

        if not messages:
            self.pm_display.setPlaceholderText(f"No messages with {self.active_pm_user} yet. Start the conversation!")
            return

        for message in messages:
            sender, receiver, text, timestamp, sender_role = message

            time_str = format_malaysia_time(timestamp)
            role_color = self.role_colors.get(sender_role.lower(), '#2196F3')

            # Role icons
            role_icons = {
                'superadmin': '👑',
                'admin': '📢',
                'owner': '🏢',
                'tester': '🧪'
            }
            role_icon = role_icons.get(sender_role.lower(), '👤')

            bubble_style = (
                f"background: linear-gradient(135deg, {role_color}15 0%, {role_color}08 100%); "
                f"border: 2px solid {role_color}30; border-radius: 12px; "
                f"margin: 6px 0; padding: 10px;"
            )

            formatted_message = (
                f"<div style='{bubble_style}'>"
                f"<div style='color: {role_color}; font-weight: bold; font-size: 12px; margin-bottom: 2px;'>"
                f"{role_icon} {sender}"
                f"</div>"
                f"<div style='color: #666; font-size: 10px; margin-bottom: 6px;'>{time_str}</div>"
                f"<div style='font-size: 13px; color: #333;'>{text}</div>"
                f"</div>"
            )

            self.pm_display.append(formatted_message)

        # Scroll to bottom
        scrollbar = self.pm_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def send_private_message(self):
        """Send a private message"""
        if not self.active_pm_user:
            return

        message_text = self.pm_input.toPlainText().strip()
        if not message_text:
            return

        user_id = self.user_info.get('user_id', 0)
        username = self.user_info.get('username', '')
        role = 'owner'  # Owner role for this application

        success = insert_private_message(user_id, username, self.active_pm_user, role, message_text)

        if success:
            self.pm_input.clear()
            self.load_private_messages_inline()
        else:
            QMessageBox.warning(self, "Error", "Failed to send private message")

    def closeEvent(self, event):
        """Stop timer when widget is closed"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        event.accept()


# --- Product Form Widget (from add product.py, refactored) ---
class ProductFormWidget(QWidget):
    def __init__(self, user_id=None, branch=None):
        super().__init__()
        self.user_id_val = user_id  # Store user_id
        self.branch_val = branch  # Store branch
        self.photo_uploaded = False  # Flag to track if a photo has been uploaded

        # Initialize batch sequence for current day - load from database
        self._last_batch_date = QDate.currentDate()
        self._batch_sequence = self.load_batch_sequence()

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.title_label = QLabel("Add Product Information")
        self.title_label.setFont(QFont("Arial", 24, QFont.Bold))  # Reduced from 28 to 24
        self.title_label.setStyleSheet("color: #5D3A00;")
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)
        self.white_frame = QFrame()
        self.white_frame.setStyleSheet(
            "background-color: white; border-radius: 15px; box-shadow: 0px 0px 10px rgba(0,0,0,0.1);")
        self.white_frame.setFixedWidth(1400)  # Increased from 1200 to 1400
        white_layout = QGridLayout(self.white_frame)
        white_layout.setContentsMargins(50, 50, 50, 50)  # Increased margins from 40 to 50
        white_layout.setSpacing(25)  # Increased spacing from 20 to 25

        # --- Photo Upload Area with Edit Button (edit button outside, square) ---
        photo_edit_row = QHBoxLayout()
        photo_edit_row.setContentsMargins(0, 0, 0, 0)
        photo_edit_row.setSpacing(15)  # Added spacing between photo and edit button

        # Photo area
        photo_widget = QWidget()
        photo_widget.setFixedSize(280, 280)  # Slightly reduced from 300x300
        photo_widget.setStyleSheet("background: transparent;")
        photo_vlayout = QVBoxLayout(photo_widget)
        photo_vlayout.setContentsMargins(0, 0, 0, 0)
        photo_vlayout.setSpacing(0)
        self.photo_label = QLabel("Upload\nPhoto")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setFixedSize(280, 280)  # Slightly reduced from 300x300
        self.photo_label.setStyleSheet(
            "background-color: #666; color: white; font-size: 20px; border-radius: 10px;"  # Reduced font from 24 to 20
        )
        self.photo_label.mousePressEvent = self.upload_photo
        photo_vlayout.addWidget(self.photo_label)
        photo_edit_row.addWidget(photo_widget)

        # Edit button outside, bottom right (square, no outline, aligned with photo bottom)
        edit_button_col = QVBoxLayout()
        edit_button_col.addStretch()
        edit_button = QPushButton()
        edit_button.setIcon(QIcon(r"C:\Kai Shuang\6.png"))
        edit_button.setIconSize(QSize(24, 24))
        edit_button.setFixedSize(36, 36)
        edit_button.setStyleSheet(
            """
            QPushButton {
                background-color: #fff;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #d6e0f5;
            }
            """
        )
        edit_button.setToolTip("Upload Photo")
        edit_button.clicked.connect(self.upload_photo)
        edit_button_col.addWidget(edit_button, alignment=Qt.AlignRight | Qt.AlignBottom)
        edit_button_col.setContentsMargins(0, 0, 0, 0)  # No extra margin, aligns with photo bottom
        photo_edit_row.addLayout(edit_button_col)

        font_label = QFont("Arial", 10, QFont.Bold)  # Reduced from 12 to 10

        def create_label(text):
            label = QLabel(text)
            label.setFont(font_label)
            label.setStyleSheet("color: #5D3A00; margin-bottom: 5px;")  # Added margin for better spacing
            return label

        input_style = "padding: 10px; border: 1px solid #8B5A2B; border-radius: 5px; background-color: #eeeded; font-size: 11px;"  # Added font-size
        read_only_style = """
            QLineEdit {
                padding: 10px;
                border: 1px solid #8B5A2B;
                border-radius: 5px;
                background-color: #d3d3d3; /* Grayed out background */
                color: #555555; /* Darker text color */
                font-size: 11px;
            }
        """
        self.owner_id = QLineEdit()
        self.owner_id.setStyleSheet(read_only_style)  # Apply read-only style
        self.owner_id.setReadOnly(True)  # Make read only
        if self.user_id_val is not None:
            self.owner_id.setText(str(self.user_id_val))

        self.update_date = self.create_custom_dateedit()
        self.update_date.setStyleSheet(input_style)
        self.update_date.setDate(QDate.currentDate())  # Set to current date
        self.branch = QLineEdit()
        self.branch.setStyleSheet(read_only_style)  # Apply read-only style
        self.branch.setReadOnly(True)  # Make read only
        if self.branch_val is not None:
            self.branch.setText(self.branch_val)

        self.product_name = QLineEdit()
        self.product_name.setStyleSheet(input_style)
        self.arrival_date = self.create_custom_dateedit()
        self.arrival_date.setStyleSheet(input_style)
        self.arrival_date.setDate(QDate.currentDate())  # Set to current date
        self.description = QTextEdit()
        self.description.setFixedHeight(100)  # Increased from 120 to provide more space
        self.description.setStyleSheet(input_style + " font-family: Arial; line-height: 1.4;")  # Better text styling
        self.manufacture_date = self.create_custom_dateedit()
        self.manufacture_date.setStyleSheet(input_style)
        self.manufacture_date.setDate(QDate.currentDate())  # Set to current date
        self.expiry_date = self.create_custom_dateedit()
        self.expiry_date.setStyleSheet(input_style)
        self.expiry_date.setDate(QDate.currentDate())  # Set to current date
        self.rack_location = QLineEdit()
        self.rack_location.setStyleSheet(input_style)
        self.batch = QLineEdit()
        self.batch.setStyleSheet(input_style)
        self.batch.setReadOnly(True)  # Make batch read-only
        self.update_batch_code()  # Generate initial batch code

        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(30)  # Increased spacing
        top_section_layout.addLayout(photo_edit_row)
        right_fields_layout = QVBoxLayout()
        right_fields_layout.setSpacing(20)  # Increased spacing from 15 to 20
        owner_id_layout = QVBoxLayout()
        owner_id_layout.setSpacing(5)  # Added spacing between label and field
        owner_id_layout.addWidget(create_label("Owner ID:"))
        owner_id_layout.addWidget(self.owner_id)
        right_fields_layout.addLayout(owner_id_layout)
        update_date_layout = QVBoxLayout()
        update_date_layout.setSpacing(5)
        update_date_layout.addWidget(create_label("Update Date:"))
        update_date_layout.addWidget(self.update_date)
        right_fields_layout.addLayout(update_date_layout)
        branch_layout = QVBoxLayout()
        branch_layout.setSpacing(5)
        branch_layout.addWidget(create_label("Branch:"))
        branch_layout.addWidget(self.branch)
        right_fields_layout.addLayout(branch_layout)
        right_fields_layout.addStretch()
        top_section_layout.addLayout(right_fields_layout)
        white_layout.addLayout(top_section_layout, 0, 0, 1, 5)

        # Product name and SKU row with better spacing
        product_sku_layout = QHBoxLayout()
        product_sku_layout.setSpacing(20)  # Added spacing between elements
        product_name_layout = QVBoxLayout()
        product_name_layout.setSpacing(5)
        product_name_layout.addWidget(create_label("Product Name:"))
        product_name_layout.addWidget(self.product_name)
        product_sku_layout.addLayout(product_name_layout, 3)  # Increased stretch factor

        sku_layout = QVBoxLayout()
        sku_layout.setSpacing(5)
        sku_label = create_label("SKU:")
        self.sku = QLineEdit()
        self.sku.setFixedWidth(150)  # Increased from 120 to 150
        self.sku.setStyleSheet(input_style)
        sku_layout.addWidget(sku_label)
        sku_layout.addWidget(self.sku)
        product_sku_layout.addLayout(sku_layout, 1)

        arrival_date_layout = QVBoxLayout()
        arrival_date_layout.setSpacing(5)
        arrival_date_layout.addWidget(create_label("Arrival Date:"))
        arrival_date_layout.addWidget(self.arrival_date)
        product_sku_layout.addLayout(arrival_date_layout, 1)
        white_layout.addLayout(product_sku_layout, 1, 0, 1, 5)

        # Description with better spacing and visibility
        description_layout = QVBoxLayout()
        description_layout.setSpacing(8)  # Increased spacing
        description_layout.addWidget(create_label("Description:"))
        description_layout.addWidget(self.description)
        white_layout.addLayout(description_layout, 2, 0, 1, 5)

        # Dates row with better spacing
        dates_layout = QHBoxLayout()
        dates_layout.setSpacing(20)  # Added spacing
        manufacture_date_layout = QVBoxLayout()
        manufacture_date_layout.setSpacing(5)
        manufacture_date_layout.addWidget(create_label("Manufacture Date:"))
        manufacture_date_layout.addWidget(self.manufacture_date)
        dates_layout.addLayout(manufacture_date_layout)
        expiry_date_layout = QVBoxLayout()
        expiry_date_layout.setSpacing(5)
        expiry_date_layout.addWidget(create_label("Expiry Date:"))
        expiry_date_layout.addWidget(self.expiry_date)
        dates_layout.addLayout(expiry_date_layout)
        white_layout.addLayout(dates_layout, 3, 0, 1, 5)

        # Rack and batch row with better spacing
        rack_batch_layout = QHBoxLayout()
        rack_batch_layout.setSpacing(20)  # Added spacing
        rack_location_layout = QVBoxLayout()
        rack_location_layout.setSpacing(5)
        rack_location_layout.addWidget(create_label("Rack Location:"))
        rack_location_layout.addWidget(self.rack_location)
        rack_batch_layout.addLayout(rack_location_layout)
        batch_layout = QVBoxLayout()
        batch_layout.setSpacing(5)
        batch_layout.addWidget(create_label("Batch:"))
        batch_layout.addWidget(self.batch)
        rack_batch_layout.addLayout(batch_layout)
        white_layout.addLayout(rack_batch_layout, 4, 0, 1, 5)

        # Submit button with better styling
        submit_btn = QPushButton("Submit")
        submit_btn.setStyleSheet(
            "background-color: #7094db; color: white; font-weight: bold; padding: 12px 24px; border-radius: 20px; font-size: 12px;")  # Reduced font size and increased padding
        submit_btn.setCursor(Qt.PointingHandCursor)
        submit_btn.setFixedWidth(140)  # Increased from 120
        submit_layout = QHBoxLayout()
        submit_layout.addStretch()
        submit_layout.addWidget(submit_btn)
        white_layout.addLayout(submit_layout, 5, 0, 1, 5)
        frame_container = QHBoxLayout()
        frame_container.addWidget(self.white_frame, alignment=Qt.AlignCenter)
        main_layout.addLayout(frame_container)
        self.setLayout(main_layout)

        # Connect the submit button
        submit_btn.clicked.connect(self.submit_product)

    def upload_photo(self, event=None):
        print("DEBUG: upload_photo method called.")  # Added for debugging
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            pixmap = QPixmap(file_name).scaled(280, 280, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.photo_label.setPixmap(pixmap)
            self.photo_label.setText("")  # Clear the "Upload Photo" text when image is uploaded
            self.photo_uploaded = True  # Set flag to True after successful upload
            self.uploaded_image_path = file_name  # Store the file path

    def create_custom_dateedit(self):
        dateedit = QDateEdit()
        dateedit.setCalendarPopup(True)
        calendar = QCalendarWidget()
        calendar.setNavigationBarVisible(True)
        calendar.setFirstDayOfWeek(Qt.Monday)
        calendar.setFixedSize(410, 220)
        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: #d6e0f5;
                border: 1px solid #8B5A2B;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton {
                background-color: #7094db;
                color: white;
                font-size: 15px;
                height: 32px;
                width: 80px;
                border-radius: 6px;
                margin: 2px;
            }
            QCalendarWidget QToolButton#qt_calendar_prevmonth,
            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                background-color: #d6e0f5;
                color: #5D3A00;
                border-radius: 14px;
                min-width: 28px;
                min-height: 28px;
            }
            QCalendarWidget QMenu {
                background-color: #d6e0f5;
                color: #5D3A00;
                font-size: 13px;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #d6e0f5;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 13px;
                color: #5D3A00;
                background-color: #FFFFFF;
                selection-background-color: #7094db;
                selection-color: white;
                border-radius: 4px;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #B0B0B0;
            }
            QCalendarWidget QSpinBox {
                width: 54px;
                font-size: 13px;
                background: #d6e0f5;
                border: 1px solid #8B5A2B;
                border-radius: 4px;
            }
        """)
        dateedit.setCalendarWidget(calendar)
        dateedit.setDisplayFormat("dd MMMM yyyy")
        return dateedit

    def validate_inputs(self):
        # Check if all required fields are filled
        if not self.product_name.text().strip():
            QMessageBox.warning(self, "Missing Information", "Product Name is required.")
            return False
        if not self.description.toPlainText().strip():
            QMessageBox.warning(self, "Missing Information", "Description is required.")
            return False
        if not self.sku.text().strip():
            QMessageBox.warning(self, "Missing Information", "SKU is required.")
            return False
        if not self.rack_location.text().strip():
            QMessageBox.warning(self, "Missing Information", "Rack Location is required.")
            return False
        if not self.batch.text().strip():
            QMessageBox.warning(self, "Missing Information", "Batch is required.")
            return False

        # Check if photo is uploaded
        if not self.photo_uploaded:
            QMessageBox.warning(self, "Missing Photo", "Please upload a product photo.")
            return False

        # All validations passed
        return True

    def submit_product(self):
        if self.validate_inputs():
            # Collect data
            product_data = {
                "product_image": self.uploaded_image_path if hasattr(self, 'uploaded_image_path') else None,
                "product_name": self.product_name.text().strip(),
                "description": self.description.toPlainText().strip(),
                "branch": self.branch.text().strip(),
                "arrival_date": self.arrival_date.date().toString("dd/MM/yyyy"),
                "manufacture_date": self.manufacture_date.date().toString("dd/MM/yyyy"),
                "expiry_date": self.expiry_date.date().toString("dd/MM/yyyy"),
                "sku": self.sku.text().strip(),
                "rack_location": self.rack_location.text().strip(),
                "batch": self.batch.text().strip(),  # Use the generated batch code
                "owner_id": self.owner_id.text().strip()
            }

            # Increment batch sequence for the next submission
            self._batch_sequence += 1

            # Save the updated batch sequence to database
            self.save_batch_sequence()

            # Process and save to DB immediately (no longer showing review window or processing dialog)
            self._process_and_show_review(product_data)

        else:
            QMessageBox.warning(self, "Missing Information", "Please fill up all the information")

    def update_batch_code(self):
        current_date = QDate.currentDate()

        # Reset sequence if date changes (new day)
        if current_date != self._last_batch_date:
            self._batch_sequence = 0
            self._last_batch_date = current_date

        date_str = current_date.toString("yyyyMMdd")
        # Convert sequence to letter (A, B, C...)
        batch_letter = chr(ord('A') + self._batch_sequence)

        self.batch.setText(f"B{date_str}{batch_letter}")

    def clear_all_fields(self):
        """Clear all form fields and reset to initial state for new product entry"""
        # Clear text fields
        self.product_name.clear()
        self.description.clear()
        self.sku.clear()
        self.rack_location.clear()

        # Reset dates to current date
        current_date = QDate.currentDate()
        self.update_date.setDate(current_date)
        self.arrival_date.setDate(current_date)
        self.manufacture_date.setDate(current_date)
        self.expiry_date.setDate(current_date)

        # Update batch code for next product
        self.update_batch_code()

        # Clear photo and reset photo flag
        self.photo_uploaded = False
        if hasattr(self, 'uploaded_image_path'):
            delattr(self, 'uploaded_image_path')

        # Reset photo label to default state
        self.set_default_photo()

    def set_default_photo(self):
        """Reset photo label to default upload state"""
        self.photo_label.clear()
        self.photo_label.setPixmap(QPixmap())  # Clear any existing pixmap
        self.photo_label.setText("Upload\nPhoto")
        self.photo_label.setStyleSheet(
            "background-color: #666; color: white; font-size: 20px; border-radius: 10px;"
        )

    def load_batch_sequence(self):
        """Load the last batch sequence for today from database"""
        try:
            conn = sqlite3.connect("medical_system.db")
            cursor = conn.cursor()

            # Create table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS BatchSequence (
                    date TEXT PRIMARY KEY,
                    last_sequence INTEGER DEFAULT 0
                )
            """)

            today = QDate.currentDate().toString("yyyy-MM-dd")
            cursor.execute("SELECT last_sequence FROM BatchSequence WHERE date = ?", (today,))
            result = cursor.fetchone()

            conn.close()

            if result:
                return result[0]
            else:
                return 0

        except Exception as e:
            print(f"Error loading batch sequence: {e}")
            return 0

    def save_batch_sequence(self):
        """Save the current batch sequence to database"""
        try:
            conn = sqlite3.connect("medical_system.db")
            cursor = conn.cursor()

            today = QDate.currentDate().toString("yyyy-MM-dd")
            cursor.execute("""
                INSERT OR REPLACE INTO BatchSequence (date, last_sequence) 
                VALUES (?, ?)
            """, (today, self._batch_sequence))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"Error saving batch sequence: {e}")

    def _process_and_show_review(self, product_data):
        """Process product data, save to DB, and show review window."""
        absolute_barcode_path = None  # Initialize to None

        try:
            # Generate barcode and image (barcode image data no longer needed for review, but path for DB is)
            barcode_value = ''.join(random.choices(string.digits, k=12))
            product_data["barcode"] = barcode_value
            barcode_class = barcode.get_barcode_class('code128')
            code128 = barcode_class(barcode_value, writer=ImageWriter())
            os.makedirs("barcodes", exist_ok=True)
            barcode_path = f"barcodes/{product_data['sku']}_{barcode_value}.png"

            # Save the barcode image file (needed for database, even if not displayed)
            code128.save(barcode_path)
            absolute_barcode_path = os.path.abspath(barcode_path)
            product_data["barcode_image"] = absolute_barcode_path  # Store path for database

            # Save product data to the database HERE
            conn = sqlite3.connect("medical_system.db")
            cursor = conn.cursor()

            cursor.execute("""
                           INSERT INTO Products (user_id, product_name, description, manufacture_date, expired_date, arrival_date,
                                                 location, batch, barcode, barcode_image, sku, product_image)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                           """, (
                int(product_data["owner_id"]),
                product_data["product_name"],
                product_data["description"],
                product_data["manufacture_date"],
                product_data["expiry_date"],
                product_data["arrival_date"],
                product_data["rack_location"],
                product_data["batch"],
                product_data["barcode"],
                product_data["barcode_image"],  # Still save the path to DB
                product_data["sku"],
                product_data["product_image"]
            ))

            # Get the product_id of the newly inserted product
            product_id = cursor.lastrowid
            product_data["product_id"] = product_id  # Add product_id to data

            conn.commit()
            conn.close()

            # Show success message directly
            QMessageBox.information(self, "Success",
                                    "Your submission has been received and is pending admin approval. Please check on the Product Submissions.")

            # Clear all fields for new product entry
            self.clear_all_fields()

            # Refresh Product Submissions if available
            if hasattr(self.parent(), 'product_submissions_widget'):
                self.parent().product_submissions_widget.load_products()

        except Exception as e:
            # Show error message if database operation fails
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to process product information: {str(e)}"
            )
            # If saving fails, perhaps clean up the generated barcode file?
            if absolute_barcode_path and os.path.exists(absolute_barcode_path):
                try:
                    os.remove(absolute_barcode_path)
                except Exception as cleanup_e:
                    print(f"Failed to clean up barcode file: {cleanup_e}")


# === Notification System ===
class NotificationSystem:
    @staticmethod
    def check_notifications(user_id, role):
        """Check for notifications for the given user"""
        try:
            conn = sqlite3.connect("medical_system.db")
            cursor = conn.cursor()

            if role == 'admin':
                # For admin users, check for product approval notifications
                cursor.execute("""
                               SELECT notification_id, message, timestamp, is_read, product_id
                               FROM Notifications
                               WHERE user_id = ? AND is_read = 0
                               ORDER BY timestamp DESC
                               """, (user_id,))

                notifications = cursor.fetchall()
                conn.close()
                return notifications
            else:
                # For regular users, check for product status notifications
                cursor.execute("""
                               SELECT notification_id, message, timestamp, is_read, product_id
                               FROM Notifications
                               WHERE user_id = ? AND is_read = 0
                               ORDER BY timestamp DESC
                               """, (user_id,))

                notifications = cursor.fetchall()
                conn.close()
                return notifications
        except Exception as e:
            print(f"Error checking notifications: {e}")
            return []

    @staticmethod
    def mark_as_read(notification_id):
        """Mark a notification as read"""
        try:
            conn = sqlite3.connect("medical_system.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE Notifications SET is_read = 1 WHERE notification_id = ?", (notification_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False


# === Toggle Switch ===
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
            self.animate_switch()

    def animate_switch(self):
        start_position = self._circle_position
        end_position = self.width() - 27 if self._checked else 3
        self.animation.setStartValue(start_position)
        self.animation.setEndValue(end_position)
        self.animation.start()

    @pyqtProperty(int)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, value):
        self._circle_position = value
        self.update()


# --- Sidebar Button ---
class SidebarButton(QPushButton):
    def __init__(self, icon_path, tooltip_text, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)  # Increased size
        icon = QIcon(icon_path)
        if icon.isNull():
            print(f"DEBUG: Failed to load icon from path: {icon_path}")
        else:
            print(f"DEBUG: Successfully loaded icon from path: {icon_path}")
        self.setIcon(icon)
        self.setIconSize(QSize(48, 48))  # Increased icon size
        self.setToolTip(tooltip_text)
        self.setCheckable(True)  # Make buttons checkable for selection state
        self.default_style()

    def default_style(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 8px; /* Make default slightly rounded */
            }
            QPushButton:hover {
                background-color: #d6e0f5; /* Lighter shade on hover */
                border-radius: 8px;
            }
            QPushButton:checked {
                background-color: #d6e0f5; /* Match sidebar background when selected */
                border: none; /* Remove border on checked state */
                border-left: 4px solid #7a4a1c; /* Left outline when selected */
                border-right: 4px solid #7a4a1c; /* Right outline when selected */
                border-radius: 0; /* Remove rounded corners when selected */
            }
            QPushButton:focus {
                outline: none; /* Remove default focus outline */
                /* border-left and border-right are now in :checked state */
            }
        """)


# --- Main Window ---
class OwnerMainWindow(QWidget):
    def __init__(self, username, user_id, branch):
        super().__init__()
        self.setWindowTitle("Owner Dashboard")

        # Set window flags and palette for title bar color
        from PyQt5.QtGui import QPalette
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#d6e0f5"))
        self.setPalette(palette)

        self.setStyleSheet("""
            OwnerMainWindow {
                background-color: #d6e0f5;
                color: #000000;
            }
            QWidget {
                background-color: #d6e0f5;
            }
        """)
        self.username = username
        self.user_id = user_id
        self.branch = branch
        self.initUI()

        # Connect the window's destroyed signal to quit the application
        self.destroyed.connect(QApplication.quit)

        # Show window maximized by default
        self.showMaximized()

    def initUI(self):
        # Main layout: horizontal, sidebar (buttons) + central content
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar for navigation buttons
        sidebar = QFrame()
        sidebar.setFixedWidth(120)
        sidebar.setStyleSheet("background-color: #d6e0f5;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 40, 0, 40)  # Added bottom margin for logout button
        sidebar_layout.setSpacing(30)

        # Navigation buttons (always visible)
        btn_size = QSize(100, 100)  # Use size from SidebarButton class
        icon_size = QSize(48, 48)  # Use icon size from SidebarButton class

        # Use QButtonGroup to manage checkable state for navigation buttons
        self.nav_button_group = QButtonGroup(self)
        self.nav_button_group.setExclusive(True)  # Only one button can be checked at a time

        # Main navigation buttons (top)
        nav_buttons_data = [
            ("C:\\Kai Shuang\\1.png", "Profile", self.show_profile, True),
            ("C:\\Kai Shuang\\7.png", "Add Product", self.show_add_product, True),
            ("C:\\Kai Shuang\\4.png", "Product Submissions", self.show_product_submissions, True),
            ("C:\\Kai Shuang\\8.png", "Notification", self.show_notification, True)
        ]

        self.sidebar_buttons = {}
        for path, tooltip, slot, is_checkable in nav_buttons_data:
            btn = SidebarButton(path, tooltip)  # Use SidebarButton class
            btn.setCheckable(is_checkable)
            btn.clicked.connect(slot)

            if is_checkable:
                self.nav_button_group.addButton(btn)  # Add checkable buttons to group

            sidebar_layout.addWidget(btn, alignment=Qt.AlignHCenter)
            self.sidebar_buttons[tooltip] = btn

        # Add stretch to push logout button to bottom
        sidebar_layout.addStretch()

        # Logout button (bottom)
        logout_btn = SidebarButton("C:\\Kai Shuang\\2.png", "Logout", parent=self)
        logout_btn.setCheckable(False)  # Logout is not checkable
        logout_btn.clicked.connect(self.logout)  # Connect the logout function
        sidebar_layout.addWidget(logout_btn, alignment=Qt.AlignHCenter)
        self.sidebar_buttons["Logout"] = logout_btn

        # Set the Profile button as initially checked
        if "Profile" in self.sidebar_buttons:
            self.sidebar_buttons["Profile"].setChecked(True)

        # Central content area (profile/add product)
        content_frame = QFrame()
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        self.stacked_layout = QStackedLayout()
        self.profile_widget = ProfileWidget(self.username, self.user_id, self.branch)
        self.product_form_widget = ProductFormWidget(self.user_id, self.branch)
        # New: Instances for Product Submissions and Notification pages
        self.product_submissions_widget = ProductSubmissionsWidget(self.user_id)
        self.product_submissions_widget.setSizePolicy(QSizePolicy.Expanding,
                                                      QSizePolicy.MinimumExpanding)  # Ensure this is set

        # Pass user info to notification widget for chat functionality
        user_info = {
            'username': self.username,
            'user_id': self.user_id,
            'role_name': 'owner',
            'branch': self.branch
        }
        self.notification_widget = NotificationWidget(user_info)

        self.stacked_layout.addWidget(self.profile_widget)
        self.stacked_layout.addWidget(self.product_form_widget)
        # New: Add new widgets to stacked layout
        self.stacked_layout.addWidget(self.product_submissions_widget)
        self.stacked_layout.addWidget(self.notification_widget)

        content_layout.addLayout(self.stacked_layout)
        content_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_frame)
        self.setLayout(main_layout)
        self.show_profile()

    def showEvent(self, event):
        """Called when the window is shown - set title bar color here"""
        super().showEvent(event)
        # Convert #d6e0f5 to RGB integer: RGB(235, 240, 250) = 0xebf0fa
        color_rgb = 0xebf0fa
        hwnd = int(self.winId())
        set_window_title_bar_color(hwnd, color_rgb)

    def show_profile(self):
        self.stacked_layout.setCurrentWidget(self.profile_widget)

    def show_add_product(self):
        self.stacked_layout.setCurrentWidget(self.product_form_widget)

    # New: Methods to show the new pages
    def show_product_submissions(self):
        self.stacked_layout.setCurrentWidget(self.product_submissions_widget)

    def show_notification(self):
        self.stacked_layout.setCurrentWidget(self.notification_widget)

    def logout(self):
        """Handle logout and return to login page"""
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Import and show login window first, then close current window
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("login_module", "Login.py")
                login_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(login_module)
                self.login_window = login_module.LoginWindow()
                self.login_window.show()
                # Close current window after login window is shown
                self.close()
            except Exception as e:
                print(f"Error opening login window: {e}")
                # If login window fails to open, try alternative approach
                try:
                    import subprocess
                    subprocess.Popen([sys.executable, "Login.py"])
                    self.close()
                except Exception as e2:
                    print(f"Failed to start login process: {e2}")
                    QApplication.quit()

    def closeEvent(self, event):
        # This method is called when the window is closed
        # Only quit if we're not returning to login
        if not hasattr(self, 'login_window'):
            QApplication.quit()
        event.accept()  # Accept the close event

    def default_style(self):
        return """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffe5d0, stop:1 #f8cfa9);
                border: none;
                border-radius: 22px;
                margin: 0;
                box-shadow: 0 2px 12px rgba(160, 120, 80, 0.10);
                transition: background 0.2s, transform 0.2s;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #ffd7b0, stop:1 #f7b97a);
                box-shadow: 0 6px 24px rgba(160, 120, 80, 0.18);
                transform: scale(1.06);
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d08b5b, stop:1 #b86a2a);
                color: white;
                box-shadow: 0 8px 32px rgba(208, 139, 91, 0.25);
                transform: scale(1.10);
            }
             QPushButton:focus {
                outline: 2px solid #7a4a1c; /* Rectangular outline */
                border-radius: 0; /* Remove rounded corners for outline */
            }
        """


# --- Product Detail Window ---
class ProductDetailWindow(QDialog):
    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setWindowTitle("Review Product Information")
        self.setFixedSize(650, 750)  # Same size as rejected window
        self.setStyleSheet("background-color: #eeeded;")
        self.setModal(True)

        # Generate barcode when window opens
        self.barcode_image_path = None
        self.generate_barcode()

        self.initUI()

    def generate_barcode(self):
        """Generate barcode image for the product"""
        try:
            if self.product_data.get('barcode'):
                barcode_value = self.product_data['barcode']
                barcode_class = barcode.get_barcode_class('code128')
                code128 = barcode_class(barcode_value, writer=ImageWriter())

                # Create temp directory if it doesn't exist
                os.makedirs("temp_barcodes", exist_ok=True)

                # Generate barcode image
                temp_path = f"temp_barcodes/temp_{barcode_value}"
                code128.save(temp_path)
                self.barcode_image_path = f"{temp_path}.png"

        except Exception as e:
            print(f"Error generating barcode: {e}")
            self.barcode_image_path = None

    def initUI(self):
        # Create scroll area for the entire content
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #eeeded;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Create main content widget
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #eeeded;")

        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # Header with centered title and decorative lines
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Left line
        left_line = QFrame()
        left_line.setFrameShape(QFrame.HLine)
        left_line.setFrameShadow(QFrame.Sunken)
        left_line.setStyleSheet("color: #8B5A2B; background-color: #8B5A2B; height: 2px;")
        header_layout.addWidget(left_line)

        # Title
        title = QLabel("Review Product Information")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #5D3A00; background-color: transparent; padding: 0px 10px;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        # Right line
        right_line = QFrame()
        right_line.setFrameShape(QFrame.HLine)
        right_line.setFrameShadow(QFrame.Sunken)
        right_line.setStyleSheet("color: #8B5A2B; background-color: #8B5A2B; height: 2px;")
        header_layout.addWidget(right_line)

        main_layout.addLayout(header_layout)

        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)

        # Left side - Product image and barcode
        left_layout = QVBoxLayout()
        left_layout.setSpacing(25)

        # Product Image
        product_image_label = QLabel("Product Image:")
        product_image_label.setFont(QFont("Arial", 14, QFont.Bold))  # Increased by 2pt
        product_image_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        left_layout.addWidget(product_image_label)

        self.product_image = QLabel()
        self.product_image.setFixedSize(220, 220)  # Slightly larger
        self.product_image.setStyleSheet("background-color: #cccccc; border-radius: 10px; border: 1px solid #d08b5b;")
        self.product_image.setAlignment(Qt.AlignCenter)
        self.product_image.setText("No Image")

        if self.product_data.get('product_image') and os.path.exists(self.product_data['product_image']):
            pixmap = QPixmap(self.product_data['product_image'])
            if not pixmap.isNull():
                self.product_image.setPixmap(pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.product_image.setText("")

        left_layout.addWidget(self.product_image)

        # Barcode section
        barcode_label = QLabel("Barcode:")
        barcode_label.setFont(QFont("Arial", 14, QFont.Bold))  # Increased by 2pt
        barcode_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        left_layout.addWidget(barcode_label)

        self.barcode_display = QLabel()
        self.barcode_display.setFixedSize(220, 110)  # Adjusted to match image width
        self.barcode_display.setStyleSheet("background-color: white; border: 1px solid #d08b5b; border-radius: 5px;")
        self.barcode_display.setAlignment(Qt.AlignCenter)

        if self.barcode_image_path and os.path.exists(self.barcode_image_path):
            barcode_pixmap = QPixmap(self.barcode_image_path)
            if not barcode_pixmap.isNull():
                self.barcode_display.setPixmap(
                    barcode_pixmap.scaled(210, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                self.barcode_display.setText("Barcode Error")
        else:
            self.barcode_display.setText("No Barcode")

        left_layout.addWidget(self.barcode_display)

        # Download button
        download_btn = QPushButton("📥 Download Barcode")
        download_btn.setFixedSize(180, 45)  # Slightly larger
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #7094db;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a7bc4;
            }
        """)
        download_btn.clicked.connect(self.download_barcode)
        left_layout.addWidget(download_btn, alignment=Qt.AlignCenter)

        left_layout.addStretch()
        content_layout.addLayout(left_layout)

        # Right side - Product information (read-only form layout)
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        # Read-only style for approved products
        readonly_style = """
            QLineEdit, QTextEdit {
                background-color: #f9f9f9;
                border: 2px solid #d08b5b;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                color: #333;
            }
        """

        # Product Name (read-only)
        product_name_label = QLabel("Product Name:")
        product_name_label.setFont(QFont("Arial", 13, QFont.Bold))
        product_name_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        right_layout.addWidget(product_name_label)

        product_name_edit = QLineEdit(self.product_data.get('product_name', ''))
        product_name_edit.setReadOnly(True)
        product_name_edit.setStyleSheet(readonly_style)
        right_layout.addWidget(product_name_edit)

        # Description (read-only)
        description_label = QLabel("Description:")
        description_label.setFont(QFont("Arial", 13, QFont.Bold))
        description_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        right_layout.addWidget(description_label)

        description_edit = QTextEdit()
        description_edit.setPlainText(self.product_data.get('description', ''))
        description_edit.setReadOnly(True)
        description_edit.setFixedHeight(80)
        description_edit.setStyleSheet(readonly_style)
        right_layout.addWidget(description_edit)

        # Other fields (all read-only)
        fields_data = [
            ("Branch:", 'branch'),
            ("Arrival Date:", 'arrival_date'),
            ("Manufacture Date:", 'manufacture_date'),
            ("Expiry Date:", 'expired_date'),
            ("SKU:", 'sku'),
            ("Rack Location:", 'location'),
            ("Batch:", 'batch')
        ]

        for label_text, field_key in fields_data:
            field_label = QLabel(label_text)
            field_label.setFont(QFont("Arial", 13, QFont.Bold))
            field_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
            right_layout.addWidget(field_label)

            field_edit = QLineEdit(str(self.product_data.get(field_key, '')))
            field_edit.setReadOnly(True)
            field_edit.setStyleSheet(readonly_style)
            right_layout.addWidget(field_edit)

        right_layout.addStretch()
        content_layout.addLayout(right_layout)
        main_layout.addLayout(content_layout)

        # Bottom decorative line
        bottom_line = QFrame()
        bottom_line.setFrameShape(QFrame.HLine)
        bottom_line.setFrameShadow(QFrame.Sunken)
        bottom_line.setStyleSheet("color: #8B5A2B; background-color: #8B5A2B; height: 2px;")
        main_layout.addWidget(bottom_line)

        # Set up scroll area
        scroll_area.setWidget(content_widget)

        # Main layout for the dialog
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(scroll_area)

    def download_barcode(self):
        """Download the barcode image"""
        if not self.barcode_image_path or not os.path.exists(self.barcode_image_path):
            QMessageBox.warning(self, "Download Error", "Barcode image not available for download.")
            return

        # Open file dialog to save barcode
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Barcode",
            f"barcode_{self.product_data.get('sku', 'product')}.png",
            "PNG Files (*.png)"
        )

        if file_path:
            try:
                # Copy the barcode file to the selected location
                import shutil
                shutil.copy2(self.barcode_image_path, file_path)
                QMessageBox.information(self, "Download Success", f"Barcode saved to: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Download Error", f"Failed to save barcode: {str(e)}")

    def closeEvent(self, event):
        """Clean up temporary barcode file when window closes"""
        if self.barcode_image_path and os.path.exists(self.barcode_image_path):
            try:
                os.remove(self.barcode_image_path)
            except Exception as e:
                print(f"Failed to clean up temporary barcode: {e}")

        # Clean up temp directory if empty
        try:
            if os.path.exists("temp_barcodes") and not os.listdir("temp_barcodes"):
                os.rmdir("temp_barcodes")
        except Exception as e:
            print(f"Failed to clean up temp directory: {e}")

        event.accept()


# --- Rejected Product Detail Window ---
class RejectedProductDetailWindow(QDialog):
    # Signal emitted when product is successfully resubmitted
    product_resubmitted = pyqtSignal()

    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setWindowTitle("Review Product Information")
        self.setFixedSize(650, 750)  # Slightly taller for edit functionality
        self.setStyleSheet("background-color: #eeeded;")
        self.setModal(True)

        # Get rejection comment from database
        self.rejection_comment = self.get_rejection_comment()

        self.initUI()

    def get_rejection_comment(self):
        """Get rejection comment from database"""
        try:
            conn = sqlite3.connect("medical_system.db")
            cursor = conn.cursor()
            # Assuming there's a rejection_comment field in Products table or separate table
            cursor.execute("SELECT rejection_comment FROM Products WHERE product_id = ?",
                           (self.product_data['product_id'],))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else "No comment provided by admin."
        except Exception as e:
            print(f"Error getting rejection comment: {e}")
            return "No comment available."

    def initUI(self):
        # Create scroll area for the entire content
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #eeeded;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 20px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::handle:vertical:pressed {
                background: #808080;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Create main content widget
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #eeeded;")

        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # Header with centered title and decorative lines
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        # Left line
        left_line = QFrame()
        left_line.setFrameShape(QFrame.HLine)
        left_line.setFrameShadow(QFrame.Sunken)
        left_line.setStyleSheet("color: #8B5A2B; background-color: #8B5A2B; height: 2px;")
        header_layout.addWidget(left_line)

        # Title
        title = QLabel("Review Product Information")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setStyleSheet("color: #5D3A00; background-color: transparent; padding: 0px 10px;")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        # Right line
        right_line = QFrame()
        right_line.setFrameShape(QFrame.HLine)
        right_line.setFrameShadow(QFrame.Sunken)
        right_line.setStyleSheet("color: #8B5A2B; background-color: #8B5A2B; height: 2px;")
        header_layout.addWidget(right_line)

        main_layout.addLayout(header_layout)

        # Content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)

        # Left side - Product image and admin comment
        left_layout = QVBoxLayout()
        left_layout.setSpacing(25)

        # Product Image (non-editable)
        product_image_label = QLabel("Product Image:")
        product_image_label.setFont(QFont("Arial", 14, QFont.Bold))
        product_image_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        left_layout.addWidget(product_image_label)

        self.product_image = QLabel()
        self.product_image.setFixedSize(220, 220)
        self.product_image.setStyleSheet("background-color: #cccccc; border-radius: 10px; border: 1px solid #d08b5b;")
        self.product_image.setAlignment(Qt.AlignCenter)
        self.product_image.setText("No Image")

        if self.product_data.get('product_image') and os.path.exists(self.product_data['product_image']):
            pixmap = QPixmap(self.product_data['product_image'])
            if not pixmap.isNull():
                self.product_image.setPixmap(pixmap.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self.product_image.setText("")

        left_layout.addWidget(self.product_image)

        # Admin Comment section (replaces barcode)
        comment_label = QLabel("Admin Comment:")
        comment_label.setFont(QFont("Arial", 14, QFont.Bold))
        comment_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        left_layout.addWidget(comment_label)

        self.comment_display = QTextEdit()
        self.comment_display.setPlainText(self.rejection_comment)
        self.comment_display.setReadOnly(True)
        self.comment_display.setFixedSize(220, 110)
        self.comment_display.setStyleSheet("""
            QTextEdit {
                background-color: #fff5f5;
                border: 2px solid #e74c3c;
                border-radius: 5px;
                padding: 8px;
                font-size: 11px;
                color: #c0392b;
                font-weight: bold;
            }
        """)
        left_layout.addWidget(self.comment_display)

        left_layout.addStretch()
        content_layout.addLayout(left_layout)

        # Right side - Editable product information
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        # Create editable fields
        input_style = """
            QLineEdit, QTextEdit {
                background-color: white;
                border: 2px solid #d08b5b;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                color: #333;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #7094db;
            }
        """

        readonly_style = """
            QLineEdit {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 8px;
                font-size: 12px;
                color: #666;
            }
        """

        # Product Name (editable)
        product_name_label = QLabel("Product Name:")
        product_name_label.setFont(QFont("Arial", 13, QFont.Bold))
        product_name_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        right_layout.addWidget(product_name_label)

        self.product_name_edit = QLineEdit(self.product_data.get('product_name', ''))
        self.product_name_edit.setStyleSheet(input_style)
        right_layout.addWidget(self.product_name_edit)

        # Description (editable)
        description_label = QLabel("Description:")
        description_label.setFont(QFont("Arial", 13, QFont.Bold))
        description_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        right_layout.addWidget(description_label)

        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(self.product_data.get('description', ''))
        self.description_edit.setFixedHeight(80)
        self.description_edit.setStyleSheet(input_style)
        right_layout.addWidget(self.description_edit)

        # Branch (read-only)
        branch_label = QLabel("Branch:")
        branch_label.setFont(QFont("Arial", 13, QFont.Bold))
        branch_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
        right_layout.addWidget(branch_label)

        self.branch_edit = QLineEdit(self.product_data.get('branch', ''))
        self.branch_edit.setReadOnly(True)
        self.branch_edit.setStyleSheet(readonly_style)
        right_layout.addWidget(self.branch_edit)

        # Editable dates and other fields
        fields_data = [
            ("Arrival Date:", 'arrival_date', True),
            ("Manufacture Date:", 'manufacture_date', True),
            ("Expiry Date:", 'expired_date', True),
            ("SKU:", 'sku', True),
            ("Rack Location:", 'location', True),
            ("Batch:", 'batch', False)  # Read-only
        ]

        self.editable_fields = {}
        for label_text, field_key, is_editable in fields_data:
            field_label = QLabel(label_text)
            field_label.setFont(QFont("Arial", 13, QFont.Bold))
            field_label.setStyleSheet("color: #5D3A00; background-color: transparent;")
            right_layout.addWidget(field_label)

            field_edit = QLineEdit(str(self.product_data.get(field_key, '')))
            if is_editable:
                field_edit.setStyleSheet(input_style)
                self.editable_fields[field_key] = field_edit
            else:
                field_edit.setReadOnly(True)
                field_edit.setStyleSheet(readonly_style)

            right_layout.addWidget(field_edit)

        # Store editable widgets for easy access
        self.editable_fields['product_name'] = self.product_name_edit
        self.editable_fields['description'] = self.description_edit

        right_layout.addStretch()
        content_layout.addLayout(right_layout)
        main_layout.addLayout(content_layout)

        # Edit and Submit buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.edit_btn = QPushButton("📝 Edit Product")
        self.edit_btn.setFixedSize(150, 45)
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.edit_btn.clicked.connect(self.enable_editing)
        button_layout.addWidget(self.edit_btn)

        self.submit_btn = QPushButton("🔄 Resubmit to Admin")
        self.submit_btn.setFixedSize(180, 45)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #7094db;
                color: white;
                font-weight: bold;
                border-radius: 12px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a7bc4;
            }
        """)
        self.submit_btn.setVisible(False)  # Initially hidden
        self.submit_btn.clicked.connect(self.resubmit_product)
        button_layout.addWidget(self.submit_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # Bottom decorative line
        bottom_line = QFrame()
        bottom_line.setFrameShape(QFrame.HLine)
        bottom_line.setFrameShadow(QFrame.Sunken)
        bottom_line.setStyleSheet("color: #8B5A2B; background-color: #8B5A2B; height: 2px;")
        main_layout.addWidget(bottom_line)

        # Set up scroll area
        scroll_area.setWidget(content_widget)

        # Main layout for the dialog
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(scroll_area)

    def enable_editing(self):
        """Enable editing mode and activate submit button"""
        self.edit_btn.setVisible(False)  # Hide edit button
        self.submit_btn.setVisible(True)  # Show resubmit button
        QMessageBox.information(self, "Edit Mode",
                                "You can now edit the product information. Click 'Resubmit to Admin' when done.")

    def resubmit_product(self):
        """Resubmit the edited product to admin"""
        reply = QMessageBox.question(self, 'Resubmit Product',
                                     'Are you sure you want to resubmit this product to admin for review?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Get edited values
                updated_data = {
                    'product_name': self.product_name_edit.text().strip(),
                    'description': self.description_edit.toPlainText().strip(),
                    'arrival_date': self.editable_fields['arrival_date'].text().strip(),
                    'manufacture_date': self.editable_fields['manufacture_date'].text().strip(),
                    'expired_date': self.editable_fields['expired_date'].text().strip(),
                    'sku': self.editable_fields['sku'].text().strip(),
                    'location': self.editable_fields['location'].text().strip()
                }

                # Validate required fields
                if not all([updated_data['product_name'], updated_data['description'],
                            updated_data['sku'], updated_data['location']]):
                    QMessageBox.warning(self, "Missing Information",
                                        "Please fill in all required fields (Product Name, Description, SKU, Rack Location).")
                    return

                # Update database
                conn = sqlite3.connect("medical_system.db")
                cursor = conn.cursor()

                cursor.execute("""
                    UPDATE Products 
                    SET product_name=?, description=?, arrival_date=?, manufacture_date=?, 
                        expired_date=?, sku=?, location=?, status='pending', rejection_comment=NULL
                    WHERE product_id=?
                """, (
                    updated_data['product_name'],
                    updated_data['description'],
                    updated_data['arrival_date'],
                    updated_data['manufacture_date'],
                    updated_data['expired_date'],
                    updated_data['sku'],
                    updated_data['location'],
                    self.product_data['product_id']
                ))

                conn.commit()
                conn.close()

                QMessageBox.information(self, "Success",
                                        "Product has been resubmitted successfully! Status changed to Pending.")

                # Find the ProductSubmissionsWidget and refresh it
                self.refresh_product_submissions()

                # Emit signal to notify that product was resubmitted
                self.product_resubmitted.emit()

                self.accept()  # Close dialog

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to resubmit product: {str(e)}")

    def refresh_product_submissions(self):
        """Find and refresh the ProductSubmissionsWidget"""
        try:
            # Start from the dialog's parent (ProductCardWidget)
            current_widget = self.parent()

            # Traverse up the widget hierarchy to find ProductSubmissionsWidget
            while current_widget:
                if isinstance(current_widget, ProductSubmissionsWidget):
                    current_widget.load_products()
                    return

                # Check if current widget has a load_products method (might be ProductSubmissionsWidget)
                if hasattr(current_widget, 'load_products') and hasattr(current_widget, 'user_id'):
                    current_widget.load_products()
                    return

                # Move up one level in the hierarchy
                current_widget = current_widget.parent()

            # If we couldn't find it through parent hierarchy, try to find it from the main window
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if isinstance(widget, OwnerMainWindow):
                        if hasattr(widget, 'product_submissions_widget'):
                            widget.product_submissions_widget.load_products()
                            return

        except Exception as e:
            print(f"Error refreshing product submissions: {e}")
            # Fallback: try to find any ProductSubmissionsWidget in the application
            try:
                app = QApplication.instance()
                if app:
                    for widget in app.allWidgets():
                        if isinstance(widget, ProductSubmissionsWidget):
                            widget.load_products()
                            break
            except Exception as e2:
                print(f"Fallback refresh also failed: {e2}")


# Function to add rejection_comment column if it doesn't exist
def ensure_rejection_comment_column():
    """Add rejection_comment column to Products table if it doesn't exist"""
    try:
        conn = sqlite3.connect("medical_system.db")
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute("PRAGMA table_info(Products)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'rejection_comment' not in columns:
            cursor.execute("ALTER TABLE Products ADD COLUMN rejection_comment TEXT")
            print("Added rejection_comment column to Products table")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error ensuring rejection_comment column: {e}")


if __name__ == "__main__":
    # Ensure database has the required columns and tables
    ensure_rejection_comment_column()

    # Initialize chat tables in medical_system.db
    create_chat_tables()

    app = QApplication(sys.argv)
    # For testing, use dummy user info
    username = "Kai Shuang"
    user_id = 4
    branch = "Raja Uda"
    window = OwnerMainWindow(username, user_id, branch)
    window.show()
    sys.exit(app.exec_())
