"""
AMBU Medical Testing System - Database Setup Script
===================================================

This script creates the complete database structure for the AMBU Medical Testing System
based on the provided table schema. It includes all tables, constraints, and initial
reference data.

"""

import sqlite3
import os
from datetime import datetime


class AMBUDatabaseSetup:
    def __init__(self, db_name="testing_system.db"):
        """Initialize database setup with specified database name"""
        self.db_name = db_name
        self.connection = None
        self.cursor = None

    def connect_database(self):
        """Create connection to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
            # Enable foreign key constraints
            self.cursor.execute("PRAGMA foreign_keys = ON")
            print(f"✅ Connected to database: {self.db_name}")
            return True
        except sqlite3.Error as e:
            print(f"❌ Error connecting to database: {e}")
            return False

    def close_database(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("🔒 Database connection closed")

    def create_tables(self):
        """Create all tables in the correct order to handle foreign key dependencies"""

        # Reference tables first (no foreign keys)
        self.create_roles_table()
        self.create_branches_table()
        self.create_racklocations_table()
        self.create_assignment_status_table()
        self.create_progress_status_table()
        self.create_test_results_table()

        # Main tables with foreign keys
        self.create_users_table()
        self.create_products_table()
        self.create_testing_table()
        self.create_product_tester_assignments_table()
        self.create_product_barcodes_table()
        self.create_message_table()
        self.create_message_notifications_table()
        self.create_private_messages_table()

        # Additional tables
        self.create_notifications_table()
        self.create_batch_sequence_table()
        self.create_activity_log_table()
        self.create_email_config_table()
        self.create_email_templates_table()
        self.create_maturation_notifications_table()
        self.create_sent_emails_table()
        self.create_system_settings_table()
        self.create_user_chat_sessions_table()

    def create_roles_table(self):
        """Create roles table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "roles" (
                    "role_id" INTEGER,
                    "role_name" TEXT,
                    PRIMARY KEY("role_id")
                )
            ''')
            print("✅ Created roles table")
        except sqlite3.Error as e:
            print(f"❌ Error creating roles table: {e}")

    def create_branches_table(self):
        """Create branches table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "branches" (
                    "branch_id" INTEGER,
                    "branch_name" TEXT,
                    PRIMARY KEY("branch_id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created branches table")
        except sqlite3.Error as e:
            print(f"❌ Error creating branches table: {e}")

    def create_racklocations_table(self):
        """Create racklocations table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "racklocations" (
                    "rack_location_id" INTEGER,
                    "rack_location_name" TEXT,
                    PRIMARY KEY("rack_location_id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created racklocations table")
        except sqlite3.Error as e:
            print(f"❌ Error creating racklocations table: {e}")

    def create_assignment_status_table(self):
        """Create assignment_status table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "assignment_status" (
                    "status_id" INTEGER,
                    "status_name" TEXT,
                    PRIMARY KEY("status_id")
                )
            ''')
            print("✅ Created assignment_status table")
        except sqlite3.Error as e:
            print(f"❌ Error creating assignment_status table: {e}")

    def create_progress_status_table(self):
        """Create progress_status table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "progress_status" (
                    "status_id" INTEGER,
                    "status_name" TEXT,
                    PRIMARY KEY("status_id")
                )
            ''')
            print("✅ Created progress_status table")
        except sqlite3.Error as e:
            print(f"❌ Error creating progress_status table: {e}")

    def create_test_results_table(self):
        """Create test_results table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "test_results" (
                    "result_id" INTEGER,
                    "result_name" TEXT,
                    PRIMARY KEY("result_id")
                )
            ''')
            print("✅ Created test_results table")
        except sqlite3.Error as e:
            print(f"❌ Error creating test_results table: {e}")

    def create_users_table(self):
        """Create users table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "users" (
                    "user_id" INTEGER,
                    "username" TEXT,
                    "password" INTEGER CHECK(LENGTH("password") >= 4),
                    "role" INTEGER,
                    "fullname" TEXT,
                    "email" TEXT,
                    "phone_no" TEXT,
                    "branch_id" INTEGER,
                    FOREIGN KEY("branch_id") REFERENCES "branches"("branch_id"),
                    FOREIGN KEY("role") REFERENCES "roles"("role_id"),
                    PRIMARY KEY("user_id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created users table")
        except sqlite3.Error as e:
            print(f"❌ Error creating users table: {e}")

    def create_products_table(self):
        """Create products table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "products" (
                    "product_id" INTEGER,
                    "owner_id" INTEGER,
                    "tester_id" INTEGER,
                    "product_name" TEXT,
                    "product_desc" TEXT,
                    "product_image" TEXT,
                    "arrival_date" DATETIME,
                    "branch_id" INTEGER,
                    "batch" TEXT,
                    "rack_location_id" INTEGER,
                    "sku" INTEGER CHECK("sku" > 0),
                    "manufacture_date" DATETIME,
                    "expired_date" DATETIME,
                    "barcode" TEXT,
                    "barcode_image" TEXT,
                    "excel_name" TEXT,
                    "rejection_comment" TEXT,
                    "location" TEXT,
                    "status" TEXT DEFAULT 'pending',
                    "description" TEXT,
                    "user_id" INTEGER,
                    FOREIGN KEY("owner_id") REFERENCES "users"("user_id"),
                    FOREIGN KEY("tester_id") REFERENCES "users"("user_id"),
                    FOREIGN KEY("rack_location_id") REFERENCES "racklocations"("rack_location_id"),
                    FOREIGN KEY("branch_id") REFERENCES "branches"("branch_id"),
                    PRIMARY KEY("product_id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created products table")
        except sqlite3.Error as e:
            print(f"❌ Error creating products table: {e}")

    def create_testing_table(self):
        """Create testing table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "testing" (
                    "test_id" INTEGER,
                    "user_id" INTEGER,
                    "product_id" INTEGER,
                    "assignment_status_id" INTEGER,
                    "test_start" DATETIME,
                    "test_end" DATETIME,
                    "progress_status_id" INTEGER,
                    "test_result_id" INTEGER,
                    "test_image" TEXT,
                    PRIMARY KEY("test_id" AUTOINCREMENT),
                    FOREIGN KEY("progress_status_id") REFERENCES "progress_status"("status_id"),
                    FOREIGN KEY("user_id") REFERENCES "users"("user_id"),
                    FOREIGN KEY("test_result_id") REFERENCES "test_results"("result_id"),
                    FOREIGN KEY("assignment_status_id") REFERENCES "assignment_status"("status_id"),
                    FOREIGN KEY("product_id") REFERENCES "products"("product_id")
                )
            ''')
            print("✅ Created testing table")
        except sqlite3.Error as e:
            print(f"❌ Error creating testing table: {e}")

    def create_product_tester_assignments_table(self):
        """Create product_tester_assignments table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "product_tester_assignments" (
                    "assignment_id" INTEGER,
                    "product_id" INTEGER,
                    "tester_id" INTEGER,
                    "assigned_by" INTEGER,
                    "assigned_date" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY("tester_id") REFERENCES "users"("user_id"),
                    FOREIGN KEY("product_id") REFERENCES "products"("product_id"),
                    FOREIGN KEY("assigned_by") REFERENCES "users"("user_id"),
                    PRIMARY KEY("assignment_id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created product_tester_assignments table")
        except sqlite3.Error as e:
            print(f"❌ Error creating product_tester_assignments table: {e}")

    def create_product_barcodes_table(self):
        """Create product_barcodes table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "product_barcodes" (
                    "id" INTEGER,
                    "product_id" INTEGER NOT NULL,
                    "seq_no" INTEGER NOT NULL,
                    "barcode" TEXT NOT NULL,
                    "barcode_image" TEXT,
                    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY("product_id") REFERENCES "products"("product_id"),
                    PRIMARY KEY("id" AUTOINCREMENT),
                    UNIQUE("product_id","seq_no")
                )
            ''')
            print("✅ Created product_barcodes table")
        except sqlite3.Error as e:
            print(f"❌ Error creating product_barcodes table: {e}")

    def create_message_table(self):
        """Create message table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "message" (
                    "message_id" INTEGER,
                    "user_id" INTEGER,
                    "role_id" INTEGER,
                    "username" TEXT,
                    "role" TEXT,
                    "message" TEXT,
                    "message_type" TEXT,
                    "read_status" INTEGER DEFAULT 0,
                    "timestamp" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY("user_id") REFERENCES "users"("user_id"),
                    FOREIGN KEY("role_id") REFERENCES "roles"("role_id"),
                    PRIMARY KEY("message_id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created message table")
        except sqlite3.Error as e:
            print(f"❌ Error creating message table: {e}")

    def create_message_notifications_table(self):
        """Create message_notifications table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "message_notifications" (
                    "id" INTEGER,
                    "message_id" INTEGER,
                    "tagged_user_id" INTEGER,
                    "tagged_username" TEXT,
                    "is_read" INTEGER DEFAULT 0,
                    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY("message_id") REFERENCES "message"("message_id"),
                    PRIMARY KEY("id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created message_notifications table")
        except sqlite3.Error as e:
            print(f"❌ Error creating message_notifications table: {e}")

    def create_private_messages_table(self):
        """Create private_messages table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "private_messages" (
                    "id" INTEGER,
                    "sender_user_id" INTEGER,
                    "sender_username" TEXT,
                    "receiver_username" TEXT,
                    "sender_role" TEXT,
                    "message_text" TEXT,
                    "timestamp" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY("id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created private_messages table")
        except sqlite3.Error as e:
            print(f"❌ Error creating private_messages table: {e}")

    def create_notifications_table(self):
        """Create Notifications table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "Notifications" (
                    "id" INTEGER,
                    "user_id" INTEGER,
                    "message" TEXT,
                    "timestamp" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    "read" INTEGER DEFAULT 0,
                    PRIMARY KEY("id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created Notifications table")
        except sqlite3.Error as e:
            print(f"❌ Error creating Notifications table: {e}")

    def create_batch_sequence_table(self):
        """Create BatchSequence table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "BatchSequence" (
                    "date" TEXT,
                    "last_sequence" INTEGER DEFAULT 0,
                    PRIMARY KEY("date")
                )
            ''')
            print("✅ Created BatchSequence table")
        except sqlite3.Error as e:
            print(f"❌ Error creating BatchSequence table: {e}")

    def create_activity_log_table(self):
        """Create activity_log table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "activity_log" (
                    "id" INTEGER,
                    "user" TEXT NOT NULL,
                    "action" TEXT NOT NULL,
                    "timestamp" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    "details" TEXT,
                    PRIMARY KEY("id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created activity_log table")
        except sqlite3.Error as e:
            print(f"❌ Error creating activity_log table: {e}")

    def create_email_config_table(self):
        """Create email_config table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "email_config" (
                    "id" INTEGER,
                    "smtp_server" TEXT,
                    "smtp_port" INTEGER,
                    "sender_email" TEXT,
                    "sender_password" TEXT,
                    "sender_name" TEXT,
                    "use_tls" BOOLEAN DEFAULT 1,
                    PRIMARY KEY("id")
                )
            ''')
            print("✅ Created email_config table")
        except sqlite3.Error as e:
            print(f"❌ Error creating email_config table: {e}")

    def create_email_templates_table(self):
        """Create email_templates table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "email_templates" (
                    "id" INTEGER,
                    "template_type" TEXT UNIQUE,
                    "subject_template" TEXT,
                    "body_template" TEXT,
                    "created_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    "modified_date" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY("id")
                )
            ''')
            print("✅ Created email_templates table")
        except sqlite3.Error as e:
            print(f"❌ Error creating email_templates table: {e}")

    def create_maturation_notifications_table(self):
        """Create maturation_notifications table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "maturation_notifications" (
                    "id" INTEGER,
                    "product_id" INTEGER,
                    "owner_username" TEXT,
                    "notification_date" DATE,
                    "notification_type" TEXT DEFAULT 'daily_alert',
                    "created_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE("product_id","owner_username","notification_date","notification_type"),
                    PRIMARY KEY("id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created maturation_notifications table")
        except sqlite3.Error as e:
            print(f"❌ Error creating maturation_notifications table: {e}")

    def create_sent_emails_table(self):
        """Create sent_emails table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "sent_emails" (
                    "email_id" INTEGER,
                    "sender_email" TEXT NOT NULL,
                    "receiver_email" TEXT NOT NULL,
                    "cc_emails" TEXT,
                    "email_subject" TEXT,
                    "email_message" TEXT,
                    "sent_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY("email_id" AUTOINCREMENT)
                )
            ''')
            print("✅ Created sent_emails table")
        except sqlite3.Error as e:
            print(f"❌ Error creating sent_emails table: {e}")

    def create_system_settings_table(self):
        """Create system_settings table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "system_settings" (
                    "setting_name" TEXT,
                    "setting_value" TEXT,
                    "updated_at" DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY("setting_name")
                )
            ''')
            print("✅ Created system_settings table")
        except sqlite3.Error as e:
            print(f"❌ Error creating system_settings table: {e}")

    def create_user_chat_sessions_table(self):
        """Create user_chat_sessions table"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS "user_chat_sessions" (
                    "user_id" INTEGER,
                    "last_entry_time" DATETIME,
                    "previous_entry_time" DATETIME,
                    "entry_count" INTEGER DEFAULT 0,
                    FOREIGN KEY("user_id") REFERENCES "users"("user_id"),
                    PRIMARY KEY("user_id")
                )
            ''')
            print("✅ Created user_chat_sessions table")
        except sqlite3.Error as e:
            print(f"❌ Error creating user_chat_sessions table: {e}")

    def insert_reference_data(self):
        """Insert initial reference data for lookup tables"""
        try:
            # Insert roles
            roles_data = [
                (1, 'superadmin'),
                (2, 'admin'),
                (3, 'owner'),
                (4, 'tester')
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO roles (role_id, role_name) VALUES (?, ?)", roles_data)

            # Insert assignment statuses
            assignment_statuses = [
                (0, 'Pending'),
                (1, 'Assigned'),
                (2, 'Cancelled')
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO assignment_status (status_id, status_name) VALUES (?, ?)",
                                    assignment_statuses)

            # Insert progress statuses
            progress_statuses = [
                (0, 'On Hold'),
                (1, 'In Progress'),
                (2, 'Testing Complete'),
                (3, 'Sample Expired')
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO progress_status (status_id, status_name) VALUES (?, ?)",
                                    progress_statuses)

            # Insert test results
            test_results = [
                (0, 'Rejected'),
                (1, 'Under Review'),
                (2, 'Approved')
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO test_results (result_id, result_name) VALUES (?, ?)",
                                    test_results)

            # Insert specific branches with IDs
            branches_data = [
                (1, 'George Town'),
                (2, 'Main Branch- Bayan Lepas'),
                (3, 'Bukit Mertajam'),
                (4, 'Butterworth'),
                (5, 'Bukit Bintang'),
                (6, 'Setapak'),
                (7, 'Cheras'),
                (8, 'Mont Kiara')
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO branches (branch_id, branch_name) VALUES (?, ?)",
                                    branches_data)

            # Insert email configuration
            email_config_data = [
                (
                1, 'smtp.gmail.com', 587, 'venniscc04@gmail.com', 'beoj bywk xffl hqoo', 'Laboratory Management System',
                1)
            ]
            self.cursor.executemany("""
                INSERT OR IGNORE INTO email_config 
                (id, smtp_server, smtp_port, sender_email, sender_password, sender_name, use_tls) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, email_config_data)

            # Insert default users
            users_data = [
                ('admin1', '123456', 2, 'Cheong', 'venniscc04@gmail.com', '60123456785')
            ]
            self.cursor.executemany("""
                INSERT OR IGNORE INTO users 
                (username, password, role, fullname, email, phone_no) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, users_data)

            # Insert default rack locations
            rack_locations = [
                ('Rack A1',),
                ('Rack A2',),
                ('Rack B1',),
                ('Rack B2',),
                ('Rack C1',),
                ('Rack C2',),
                ('Refrigeration Unit 1',),
                ('Refrigeration Unit 2',),
                ('Freezer Unit 1',),
                ('Freezer Unit 2',)
            ]
            self.cursor.executemany("INSERT OR IGNORE INTO racklocations (rack_location_name) VALUES (?)",
                                    rack_locations)

            # Insert default email templates
            email_templates = [
                ('assignment_notification', 'Product Assignment Notification',
                 'You have been assigned a new product for testing: {product_name}. Please check your dashboard for details.'),
                ('maturation_alert', 'Product Maturation Alert',
                 'The following products are approaching their expiry date: {product_list}. Please take necessary action.'),
                ('approval_notification', 'Product Approval Notification',
                 'Your product submission "{product_name}" has been approved and is ready for testing.'),
                ('rejection_notification', 'Product Rejection Notification',
                 'Your product submission "{product_name}" has been rejected. Reason: {rejection_reason}')
            ]
            self.cursor.executemany("""
                INSERT OR IGNORE INTO email_templates (template_type, subject_template, body_template) 
                VALUES (?, ?, ?)
            """, email_templates)

            print("✅ Inserted reference data")

        except sqlite3.Error as e:
            print(f"❌ Error inserting reference data: {e}")

    def setup_database(self):
        """Main method to set up the complete database"""
        print("🚀 Starting AMBU Database Setup...")
        print("=" * 60)

        if not self.connect_database():
            return False

        try:
            # Create all tables
            print("\n📋 Creating tables...")
            self.create_tables()

            # Insert reference data
            print("\n📊 Inserting reference data...")
            self.insert_reference_data()

            # Commit changes
            self.connection.commit()
            print("\n✅ Database setup completed successfully!")
            print(f"📁 Database file created: {self.db_name}")
            print(f"📅 Setup completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Display summary
            self.display_database_summary()

            return True

        except sqlite3.Error as e:
            print(f"❌ Error during database setup: {e}")
            if self.connection:
                self.connection.rollback()
            return False

        finally:
            self.close_database()

    def display_database_summary(self):
        """Display a summary of the created database"""
        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = self.cursor.fetchall()

            print("\n" + "=" * 60)
            print("📊 DATABASE SUMMARY")
            print("=" * 60)
            print(f"Database Name: {self.db_name}")
            print(f"Total Tables Created: {len(tables)}")
            print("\nTables:")

            for i, (table_name,) in enumerate(tables, 1):
                if table_name != 'sqlite_sequence':  # Skip system table
                    self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = self.cursor.fetchone()[0]
                    print(f"  {i:2}. {table_name:<25} ({count} records)")

            print("\n🎯 Next Steps:")
            print("  1. Create your first Super Admin user")
            print("  2. Configure email settings")
            print("  3. Add additional users and branches")
            print("  4. Start using the system!")
            print("=" * 60)

        except sqlite3.Error as e:
            print(f"❌ Error displaying summary: {e}")


def main():
    """Main function to run the database setup"""
    print("AMBU Medical Testing System - Database Setup")
    print("=" * 60)

    # Ask user for database name
    db_name = input("Enter database name (default: ambu_testing_system.db): ").strip()
    if not db_name:
        db_name = "ambu_testing_system.db"

    # Check if database already exists
    if os.path.exists(db_name):
        overwrite = input(f"⚠️  Database '{db_name}' already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("❌ Setup cancelled by user")
            return
        else:
            # Backup existing database
            backup_name = f"{db_name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                os.rename(db_name, backup_name)
                print(f"📋 Existing database backed up as: {backup_name}")
            except Exception as e:
                print(f"⚠️  Could not backup existing database: {e}")

    # Create database setup instance
    db_setup = AMBUDatabaseSetup(db_name)

    # Run database setup
    success = db_setup.setup_database()

    if success:
        print("\n🎉 Database setup completed successfully!")
        print("You can now start using the AMBU Medical Testing System.")
    else:
        print("\n❌ Database setup failed!")
        print("Please check the error messages above and try again.")


if __name__ == "__main__":
    main()