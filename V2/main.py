# Importing the required libraries
import tkinter
from tkinter import ttk, Label, simpledialog
from CTkMessagebox import CTkMessagebox
from CTkScrollableDropdown import *
import customtkinter
from customtkinter import *
from CTkXYFrame import *
from PIL import Image, ImageTk
import webbrowser
import sqlite3
import pywinstyles
import random
import datetime
import pygame
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fitplus.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants for better maintainability
COLORS = {
    'primary_bg': '#242424',
    'secondary_bg': '#313131',
    'frame_bg': '#3c3c3c',
    'button_bg': '#000000',
    'button_hover': '#1a1a1a',
    'border': '#ffffff',
    'text': '#ffffff'
}

FONTS = {
    'title': ("Impact", 36),
    'subtitle': ("Impact", 16),
    'input': ("Calibri", 16),
    'dropdown': ("Impact", 12),
    'button': ("Impact", 14),
    'output': ("Calibri", 18),
    'large_button': ("Roboto Medium", -40),
    'section_title': ("Impact", 35)
}

# Performance constants
PARTICLE_COUNT = 50  # Reduced from 100
PARTICLE_UPDATE_INTERVAL = 16  # ~60 FPS
PARTICLE_RESPAWN_TIME = 15

# Validation constants
MIN_PASSWORD_LENGTH = 6
MIN_USERNAME_LENGTH = 3
MAX_WEIGHT = 500  # kg
MAX_PR = 1000  # kg

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# Enhanced Particle System with memory leak fixes

class Particle:
    def __init__(self, canvas):
        try:
            self.canvas = canvas
            self.radius = min(self.canvas.size, 5)  # Limit particle size
            canvas_width = max(self.canvas.winfo_width(), 800)
            canvas_height = max(self.canvas.winfo_height(), 600)
            
            self.x = random.randint(self.radius, canvas_width - self.radius)
            self.y = random.randint(self.radius, canvas_height - self.radius)
            self.dx = random.uniform(-0.5, 0.5)  # Slower movement for better performance
            self.dy = random.uniform(-0.5, 0.5)
            self.lifetime = random.randint(100, 300)  # Particle lifetime
            self.age = 0
        except Exception as e:
            logger.error(f"Error creating particle: {e}")
            self.x = self.y = 50
            self.dx = self.dy = 0.1

    def move(self):
        try:
            self.x += self.dx
            self.y += self.dy
            self.age += 1
            if hasattr(self, 'id'):
                self.canvas.move(self.id, self.dx, self.dy)
        except Exception as e:
            logger.error(f"Error moving particle: {e}")

    def is_expired(self):
        return self.age > self.lifetime

class ParticleFrame(tkinter.Canvas):
    def __init__(self,
                 master,
                 fg_color="black",
                 particle_color="white",
                 particle_size=3,
                 particle_count=PARTICLE_COUNT,
                 respawn=PARTICLE_RESPAWN_TIME,
                 **kwargs):

        super().__init__(master, bg=fg_color,
                         highlightthickness=0,
                         borderwidth=0, **kwargs)
        
        self.color = particle_color
        self.size = particle_size
        self.particles = []
        self.num_particles = particle_count
        self.respawn = respawn
        self._stop = False
        self.max_particles = particle_count * 2  # Limit total particles
        
        self.after(200, self.start)
        self.bind("<Destroy>", lambda e: self.stop())
        
    def stop(self):
        self._stop = True
        self.cleanup_particles()
        
    def cleanup_particles(self):
        """Clean up particle objects to prevent memory leaks"""
        try:
            for particle in self.particles[:]:
                if hasattr(particle, 'id'):
                    self.delete(particle.id)
            self.particles.clear()
        except Exception as e:
            logger.error(f"Error cleaning up particles: {e}")
        
    def create_particles(self):
        if self._stop:
            return
            
        try:
            # Remove expired particles first
            self.particles = [p for p in self.particles if not p.is_expired()]
            
            # Limit total particles
            particles_to_create = min(
                self.num_particles - len(self.particles),
                self.max_particles - len(self.particles)
            )
            
            for _ in range(max(0, particles_to_create)):
                particle = Particle(self)
                try:
                    particle.id = self.create_oval(
                        particle.x - self.size,
                        particle.y - self.size,
                        particle.x + self.size,
                        particle.y + self.size,
                        fill=self.color, outline=self.color
                    )
                    self.particles.append(particle)
                except Exception as e:
                    logger.error(f"Error creating particle oval: {e}")
                    
            self.after(self.respawn * 1000, self.create_particles)
        except Exception as e:
            logger.error(f"Error in create_particles: {e}")
        
    def move_particles(self):
        try:
            expired_particles = []
            for particle in self.particles:
                particle.move()
                if particle.is_expired():
                    expired_particles.append(particle)
            
            # Remove expired particles
            for particle in expired_particles:
                try:
                    if hasattr(particle, 'id'):
                        self.delete(particle.id)
                    self.particles.remove(particle)
                except Exception as e:
                    logger.error(f"Error removing expired particle: {e}")
                    
        except Exception as e:
            logger.error(f"Error moving particles: {e}")

    def start(self):
        self.create_particles()
        self.after(PARTICLE_UPDATE_INTERVAL, self.update_simulation)
        self._stop = False
        
    def update_simulation(self):
        if self._stop:
            return
        try:
            self.move_particles()
            self.after(PARTICLE_UPDATE_INTERVAL, self.update_simulation)
        except Exception as e:
            logger.error(f"Error in update_simulation: {e}")

dropdown_theme_created = False

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# Enhanced Database Operations with proper error handling

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = sqlite3.connect('fitplus.db', timeout=10.0)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def setup_database():
    """Setup database with enhanced error handling and better field types"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                security_question TEXT NOT NULL,
                security_answer TEXT NOT NULL,
                daily_calorie_limit INTEGER DEFAULT 2000,
                daily_calorie_intake INTEGER DEFAULT 0,
                daily_fat REAL DEFAULT 0,
                daily_carbs REAL DEFAULT 0,
                daily_protein REAL DEFAULT 0,
                daily_sugars REAL DEFAULT 0,
                current_weight REAL DEFAULT 0,
                ideal_weight REAL DEFAULT 0,
                bench_press_pr REAL DEFAULT 0,
                squat_pr REAL DEFAULT 0,
                deadlift_pr REAL DEFAULT 0,
                last_update DATE DEFAULT (DATE('now')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database setup completed successfully")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database setup error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def validate_input(value, input_type, min_val=None, max_val=None):
    """Generic input validation function"""
    try:
        if input_type == 'string':
            if not isinstance(value, str) or not value.strip():
                return False, "Input cannot be empty"
            return True, value.strip()
        
        elif input_type == 'username':
            value = value.strip()
            if len(value) < MIN_USERNAME_LENGTH:
                return False, f"Username must be at least {MIN_USERNAME_LENGTH} characters"
            if not value.replace('_', '').replace('-', '').isalnum():
                return False, "Username can only contain letters, numbers, hyphens, and underscores"
            return True, value
        
        elif input_type == 'password':
            if len(value) < MIN_PASSWORD_LENGTH:
                return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
            return True, value
        
        elif input_type == 'numeric':
            try:
                num_val = float(value)
                if min_val is not None and num_val < min_val:
                    return False, f"Value must be at least {min_val}"
                if max_val is not None and num_val > max_val:
                    return False, f"Value must be at most {max_val}"
                return True, num_val
            except ValueError:
                return False, "Please enter a valid number"
                
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, "Validation error occurred"

def update_user_data(username, **kwargs):
    """Generic function to update user data"""
    if not kwargs:
        return False, "No data to update"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic query
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [username]
        
        query = f"UPDATE users SET {set_clause} WHERE username = ?"
        cursor.execute(query, values)
        
        if cursor.rowcount == 0:
            return False, "User not found"
        
        conn.commit()
        logger.info(f"Updated user data for {username}: {kwargs}")
        return True, "Update successful"
        
    except sqlite3.Error as e:
        logger.error(f"Error updating user data: {e}")
        if conn:
            conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        if conn:
            conn.close()

def get_user_data(username, fields=None):
    """Generic function to get user data"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if fields:
            field_list = ", ".join(fields)
            query = f"SELECT {field_list} FROM users WHERE username = ?"
        else:
            query = "SELECT * FROM users WHERE username = ?"
        
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        
        if result:
            if fields:
                return dict(zip(fields, result))
            else:
                # Return all fields as dict
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
        return None
        
    except sqlite3.Error as e:
        logger.error(f"Error getting user data: {e}")
        return None
    finally:
        if conn:
            conn.close()

def register_user(username, password, security_question, security_answer):
    """Enhanced user registration with validation"""
    # Validate inputs
    valid, username = validate_input(username, 'username')
    if not valid:
        return False, username
    
    valid, password = validate_input(password, 'password')
    if not valid:
        return False, password
    
    valid, security_question = validate_input(security_question, 'string')
    if not valid:
        return False, "Security question is required"
    
    valid, security_answer = validate_input(security_answer, 'string')
    if not valid:
        return False, "Security answer is required"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, security_question, security_answer)
            VALUES (?, ?, ?, ?)
        ''', (username, password, security_question, security_answer))
        conn.commit()
        logger.info(f"User {username} registered successfully")
        return True, "Registration successful"
    except sqlite3.IntegrityError:
        logger.warning(f"Registration failed - username {username} already exists")
        return False, "Username already exists"
    except sqlite3.Error as e:
        logger.error(f"Registration error: {e}")
        if conn:
            conn.rollback()
        return False, "Registration failed - database error"
    finally:
        if conn:
            conn.close()

def login_user(username, password):
    """Enhanced login with validation"""
    valid, username = validate_input(username, 'string')
    if not valid:
        return False, username
    
    valid, password = validate_input(password, 'string')
    if not valid:
        return False, password
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        if result and result[0] == password:
            logger.info(f"User {username} logged in successfully")
            return True, "Login successful"
        else:
            logger.warning(f"Login failed for user {username}")
            return False, "Invalid username or password"
            
    except sqlite3.Error as e:
        logger.error(f"Login error: {e}")
        return False, "Login failed - database error"
    finally:
        if conn:
            conn.close()

def forgot_password(username, security_answer):
    """Enhanced forgot password with validation"""
    valid, username = validate_input(username, 'string')
    if not valid:
        return None, username
    
    valid, security_answer = validate_input(security_answer, 'string')
    if not valid:
        return None, "Security answer is required"
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT password FROM users WHERE username = ? AND security_answer = ?
        ''', (username, security_answer))
        result = cursor.fetchone()
        
        if result:
            logger.info(f"Password retrieved for user {username}")
            return result[0], "Password retrieved successfully"
        else:
            logger.warning(f"Password retrieval failed for user {username}")
            return None, "Incorrect username or security answer"
            
    except sqlite3.Error as e:
        logger.error(f"Password retrieval error: {e}")
        return None, "Database error occurred"
    finally:
        if conn:
            conn.close()

def delete_account():
    """Enhanced account deletion with validation"""
    try:
        username = user_var.get().strip()
        if not username:
            logger.warning("Delete account attempted with empty username")
            return False, "Username is required"
        
        success, message = update_user_data(username, deleted_at=datetime.datetime.now())
        if success:
            # Instead of actually deleting, we could mark as deleted
            # For now, we'll still delete as per original functionality
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
            conn.close()
            
            # Hide the main app frame and show the login screen
            mainapp.pack_forget()
            frame.pack(expand=True)
            particle_frame.pack(expand=True, fill="both")
            
            # Clear the username and password fields
            user_var.set("")
            pass_var.set("")
            
            logger.info(f"Account deleted for user {username}")
            return True, "Account deleted successfully"
        else:
            return False, message
            
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        return False, "Error deleting account"
    
def open_youtube_video(url):
    """Safely open YouTube videos - Global function"""
    try:
        webbrowser.open(url)
        logger.info(f"Opened YouTube video: {url}")
    except Exception as e:
        logger.error(f"Error opening YouTube video {url}: {e}")
        CTkMessagebox(title="Error", message="Could not open video", 
                    icon="warning", justify=CENTER, button_color="black")

def open_recipe_link(url):
    """Safely open recipe links - Global function"""
    try:
        webbrowser.open(url)
        logger.info(f"Opened recipe: {url}")
    except Exception as e:
        logger.error(f"Error opening recipe {url}: {e}")
        CTkMessagebox(title="Error", message="Could not open recipe", 
                    icon="warning", justify=CENTER, button_color="black")

def check_and_reset_calorie_data(username):
    """Enhanced daily reset with better error handling"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT last_update FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if not result:
            logger.warning(f"User {username} not found for calorie reset")
            return False
        
        last_update = result[0] if result[0] else "1970-01-01"
        today = datetime.date.today().isoformat()
        
        if last_update < today:
            cursor.execute('''
                UPDATE users SET 
                daily_calorie_intake = 0,
                daily_fat = 0,
                daily_carbs = 0,
                daily_protein = 0,
                daily_sugars = 0,
                last_update = ?
                WHERE username = ?
            ''', (today, username))
            conn.commit()
            logger.info(f"Daily nutrition data reset for user {username}")
            return True
        return False
        
    except sqlite3.Error as e:
        logger.error(f"Error resetting calorie data: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

# Enhanced wrapper functions for backward compatibility
def update_current_weight(username, new_weight):
    valid, weight = validate_input(str(new_weight), 'numeric', 0, MAX_WEIGHT)
    if not valid:
        logger.error(f"Invalid weight value: {weight}")
        return False, weight
    
    success, message = update_user_data(username, current_weight=weight)
    if success:
        logger.info(f"Current weight updated for {username}: {weight}")
    return success, message

def update_ideal_weight(username, new_weight):
    valid, weight = validate_input(str(new_weight), 'numeric', 0, MAX_WEIGHT)
    if not valid:
        logger.error(f"Invalid ideal weight value: {weight}")
        return False, weight
    
    success, message = update_user_data(username, ideal_weight=weight)
    if success:
        logger.info(f"Ideal weight updated for {username}: {weight}")
    return success, message

def update_bench_press_pr(username, new_pr):
    valid, pr = validate_input(str(new_pr), 'numeric', 0, MAX_PR)
    if not valid:
        logger.error(f"Invalid bench press PR: {pr}")
        return False, pr
    
    success, message = update_user_data(username, bench_press_pr=pr)
    if success:
        logger.info(f"Bench press PR updated for {username}: {pr}")
    return success, message

def update_squat_pr(username, new_pr):
    valid, pr = validate_input(str(new_pr), 'numeric', 0, MAX_PR)
    if not valid:
        logger.error(f"Invalid squat PR: {pr}")
        return False, pr
    
    success, message = update_user_data(username, squat_pr=pr)
    if success:
        logger.info(f"Squat PR updated for {username}: {pr}")
    return success, message

def update_deadlift_pr(username, new_pr):
    valid, pr = validate_input(str(new_pr), 'numeric', 0, MAX_PR)
    if not valid:
        logger.error(f"Invalid deadlift PR: {pr}")
        return False, pr
    
    success, message = update_user_data(username, deadlift_pr=pr)
    if success:
        logger.info(f"Deadlift PR updated for {username}: {pr}")
    return success, message

def get_user_calorie_limit(username):
    try:
        data = get_user_data(username, ['daily_calorie_limit'])
        return data['daily_calorie_limit'] if data else 2000
    except Exception as e:
        logger.error(f"Error getting calorie limit: {e}")
        return 2000

def get_user_calorie_intake(username):
    try:
        check_and_reset_calorie_data(username)
        data = get_user_data(username, ['daily_calorie_intake'])
        return data['daily_calorie_intake'] if data else 0
    except Exception as e:
        logger.error(f"Error getting calorie intake: {e}")
        return 0

def reset_daily_calorie_intake(username):
    success, message = update_user_data(username, daily_calorie_intake=0)
    if success:
        logger.info(f"Daily calorie intake reset for {username}")
    return success, message

def reset_nutrition(username):
    success, message = update_user_data(username, 
                                       daily_fat=0,
                                       daily_carbs=0,
                                       daily_protein=0,
                                       daily_sugars=0)
    if success:
        logger.info(f"Nutrition data reset for {username}")
    return success, message

def save_new_calorie_limit(username, new_limit):
    valid, limit = validate_input(str(new_limit), 'numeric', 500, 5000)
    if not valid:
        return False, limit
    
    success, message = update_user_data(username, daily_calorie_limit=int(limit))
    if success:
        logger.info(f"Calorie limit updated for {username}: {limit}")
    return success, message

def add_food_to_intake(selected_item_name):
    """Enhanced food addition with better error handling"""
    global items, current_username
    
    try:
        if not selected_item_name or not current_username:
            logger.warning("Missing item name or username for food addition")
            return False, "Invalid selection"
        
        selected_item = next((item for item in items if item["name"] == selected_item_name), None)
        if not selected_item:
            logger.warning(f"Food item not found: {selected_item_name}")
            return False, "Food item not found"

        # Get current intake from database
        current_data = get_user_data(current_username, [
            'daily_calorie_intake', 'daily_fat', 'daily_carbs', 
            'daily_protein', 'daily_sugars'
        ])
        
        if not current_data:
            logger.error(f"User data not found: {current_username}")
            return False, "User data not found"

        # Calculate new values
        new_intake = current_data['daily_calorie_intake'] + selected_item["calories"]
        new_fats = current_data['daily_fat'] + selected_item["fat"]
        new_carbs = current_data['daily_carbs'] + selected_item["carbs"]
        new_protein = current_data['daily_protein'] + selected_item["protein"]
        new_sugars = current_data['daily_sugars'] + selected_item["sugars"]

        # Update database
        success, message = update_user_data(current_username,
                                           daily_calorie_intake=new_intake,
                                           daily_fat=new_fats,
                                           daily_carbs=new_carbs,
                                           daily_protein=new_protein,
                                           daily_sugars=new_sugars)
        
        if success:
            # Refresh the UI
            update_calorie_counter_section()
            logger.info(f"Added {selected_item_name} to {current_username}'s intake")
            return True, "Food added successfully"
        else:
            return False, message
            
    except Exception as e:
        logger.error(f"Error adding food to intake: {e}")
        return False, "Error adding food item"

# Safe file operations
def safe_load_image(path, size=None, default_size=(100, 100)):
    """Safely load images with fallback"""
    try:
        if not os.path.exists(path):
            logger.warning(f"Image file not found: {path}")
            # Create a simple placeholder image
            img = Image.new('RGB', size or default_size, color='gray')
        else:
            img = Image.open(path)
            if size:
                img = img.resize(size)
        return img
    except Exception as e:
        logger.error(f"Error loading image {path}: {e}")
        # Return placeholder
        return Image.new('RGB', size or default_size, color='gray')

def safe_load_ctk_image(path, size=None):
    """Safely load CTkImage with fallback"""
    try:
        img = safe_load_image(path, size)
        return CTkImage(dark_image=img, light_image=img, size=size or (100, 100))
    except Exception as e:
        logger.error(f"Error creating CTkImage: {e}")
        # Create simple placeholder
        placeholder = Image.new('RGB', size or (100, 100), color='gray')
        return CTkImage(dark_image=placeholder, light_image=placeholder, size=size or (100, 100))

# Initialize database
try:
    if not setup_database():
        logger.error("Failed to setup database")
        sys.exit(1)
except Exception as e:
    logger.error(f"Critical database error: {e}")
    sys.exit(1)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

# Global variables with proper initialization
current_theme = {"theme": "dark"}
current_username = ""
selected_food = ""

# Initialize the main application
try:
    app = customtkinter.CTk()
    app.configure(bg=COLORS['primary_bg'])
    app.title("FitPlus")
    app.resizable(False, False)
    
    # Safe icon loading
    if os.path.exists("fitplus_smallicon.ico"):
        app.iconbitmap("fitplus_smallicon.ico")
    else:
        logger.warning("Icon file not found: fitplus_smallicon.ico")
    
    window_height = 800
    window_width = 1400

    # Calculate screen dimensions
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))
    app.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

    # Initialize particle system
    particle_frame = ParticleFrame(app)
    particle_frame.pack(expand=True, fill="both")

    frame = customtkinter.CTkFrame(particle_frame, corner_radius=10)
    frame.pack(expand=True)
    pywinstyles.set_opacity(frame, 0.9)

    # Safe image loading
    fitplus_img = safe_load_ctk_image("fitplus.png", (213, 164))
    fitplus_smallicon = safe_load_ctk_image("fitplus_smallicon.ico", (96, 96))

except Exception as e:
    logger.error(f"Error initializing application: {e}")
    sys.exit(1)

# Security questions
security_questions = [
    "Where were you born?", 
    "What is your pet's name?", 
    "What is your mother's name?", 
    "Your favourite colour?"
]

# UI Setup
title = customtkinter.CTkLabel(frame, text="FitPlus Authentication", font=FONTS['title'])
title.pack(padx=20, pady=10)

userTitle = customtkinter.CTkLabel(frame, text="Username", font=FONTS['subtitle'])
userTitle.pack(padx=18, pady=12)

user_var = tkinter.StringVar()
username = customtkinter.CTkEntry(frame, width=350, height=40, textvariable=user_var, 
                                border_color="white", font=FONTS['input'])
username.pack(padx=18, pady=0)

passTitle = customtkinter.CTkLabel(frame, text="Password", font=FONTS['subtitle'])
passTitle.pack(padx=18, pady=12)

pass_var = tkinter.StringVar()
password = customtkinter.CTkEntry(frame, width=350, height=40, textvariable=pass_var, 
                                border_color="white", font=FONTS['input'], show="*")  # Password masking
password.pack(padx=18, pady=0)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def loginClick():
    """Enhanced login function with better error handling"""
    try:
        username_input = user_var.get().strip()
        password_input = pass_var.get().strip()
        
        if not username_input or not password_input:
            CTkMessagebox(title="Login Error", 
                         message="Please enter both username and password", 
                         icon="warning", justify=CENTER, button_color="black")
            return
        
        success, message = login_user(username_input, password_input)
        if success:
            global current_username
            current_username = username_input
            CTkMessagebox(title="Login Successful", 
                         message="You have been logged in successfully", 
                         icon="check", justify=CENTER, button_color="black")
            frame.pack_forget()
            particle_frame.pack_forget()
            FitPlusApp()
        else:
            CTkMessagebox(title="Login Failed", 
                         message=message, 
                         icon="cancel", justify=CENTER, button_color="black")
    except Exception as e:
        logger.error(f"Login error: {e}")
        CTkMessagebox(title="Error", 
                     message="An error occurred during login", 
                     icon="cancel", justify=CENTER, button_color="black")

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

# Registration Frame Setup with enhanced error handling
def hide_registration_show_login():
    registration_frame.lower()

registration_frame = customtkinter.CTkFrame(app, width=800, height=475)
registration_frame.place(x=0, y=0, relwidth=1, relheight=1)
registration_particle_frame = ParticleFrame(registration_frame)
registration_particle_frame.pack(expand=True, fill="both")
registration_inner_frame = customtkinter.CTkFrame(registration_particle_frame, corner_radius=10)
registration_inner_frame.pack(expand=True)
pywinstyles.set_opacity(registration_inner_frame, 0.9)
registration_frame.lower()

def show_registration():
    registration_frame.lift()
    for widget in registration_inner_frame.winfo_children():
        widget.destroy()

    title = customtkinter.CTkLabel(registration_inner_frame, text="Registration", 
                                 font=FONTS['title'], text_color='white')
    title.pack(padx=20, pady=3)

    back_button = customtkinter.CTkButton(registration_inner_frame, text="Back", 
                                        command=hide_registration_show_login, 
                                        fg_color="black", hover_color="grey", 
                                        font=FONTS['button'], width=30)
    back_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

    userTitle = customtkinter.CTkLabel(registration_inner_frame, text="Username", 
                                     font=FONTS['subtitle']).pack(pady=3)
    userReg_var = tkinter.StringVar()
    userInp = customtkinter.CTkEntry(registration_inner_frame, width=350, height=40, 
                                   textvariable=userReg_var, border_color="white", 
                                   font=FONTS['input']).pack(padx=40)

    passTitle = customtkinter.CTkLabel(registration_inner_frame, text="Password", 
                                     font=FONTS['subtitle']).pack(pady=6)
    passReg_var = tkinter.StringVar()
    passInp = customtkinter.CTkEntry(registration_inner_frame, width=350, height=40, 
                                   textvariable=passReg_var, border_color="white", 
                                   font=FONTS['input'], show="*").pack()  # Password masking

    securityTitle = customtkinter.CTkLabel(registration_inner_frame, text="Security Question", 
                                         font=FONTS['subtitle']).pack(pady=6)
    securityQ_var = tkinter.StringVar()

    # Enhanced dropdown with better styling
    security_dropdown = ttk.Combobox(registration_inner_frame, textvariable=securityQ_var, 
                                   values=security_questions, state="readonly", 
                                   font=FONTS['dropdown'], width=25)
    security_dropdown.pack()

    # Enhanced dropdown styling
    global dropdown_theme_created
    combostyle = ttk.Style()

    if not dropdown_theme_created:
        combostyle.theme_create('combostyle', parent='alt',
            settings={
                'TCombobox': {
                    'configure': {
                        'fieldbackground': registration_inner_frame.cget("fg_color")[1],
                        'selectbackground':'',
                        'selectforeground': "white",
                        'bordercolor':'grey',
                        'background': ''}},
                'TScrollbar':{
                        'configure': {
                        'background': ''}
                    }})
        dropdown_theme_created = True
    combostyle.theme_use('combostyle')
    security_dropdown.option_add("*TCombobox*Listbox*Foreground", "white")
    security_dropdown.option_add("*TCombobox*Listbox*Background", 
                                registration_inner_frame.cget("fg_color")[1])
    security_dropdown.option_add("*TCombobox*Listbox*selectBackground", "white")
    security_dropdown.option_add("*TCombobox*Listbox*selectForeground", "black")

    securityAnsTitle = customtkinter.CTkLabel(registration_inner_frame, text="Security Answer", 
                                            font=FONTS['subtitle']).pack(pady=6)
    securityAns_var = tkinter.StringVar()
    securityAnsInp = customtkinter.CTkEntry(registration_inner_frame, width=350, height=40, 
                                          textvariable=securityAns_var, border_color="white", 
                                          font=FONTS['input']).pack()

    def regValidation():
        """Enhanced registration validation"""
        try:
            username = userReg_var.get().strip()
            password = passReg_var.get().strip()
            security_question = securityQ_var.get().strip()
            security_answer = securityAns_var.get().strip()

            # Enhanced validation
            if not all([username, password, security_question, security_answer]):
                CTkMessagebox(title="Registration Error", 
                            message="All fields are required", 
                            icon="warning", justify=CENTER, button_color="black")
                return

            success, message = register_user(username, password, security_question, security_answer)
            if success:
                CTkMessagebox(title="Registration Successful", 
                            message="You have been registered successfully", 
                            icon="check", justify=CENTER, button_color="black")
                hide_registration_show_login()
            else:
                CTkMessagebox(title="Registration Failed", 
                            message=message, 
                            icon="warning", justify=CENTER, button_color="black")
                
        except Exception as e:
            logger.error(f"Registration validation error: {e}")
            CTkMessagebox(title="Error", 
                        message="An error occurred during registration", 
                        icon="cancel", justify=CENTER, button_color="black")
    
    regConfirm = customtkinter.CTkButton(registration_inner_frame, command=regValidation, 
                                       text="Confirm", fg_color="black", hover_color="grey", 
                                       font=FONTS['button'])
    regConfirm.pack(padx=18, pady=18)

# Enhanced forgot password functionality
def hide_forgot_password_show_login():
    forgot_password_frame.lower()

forgot_password_frame = customtkinter.CTkFrame(app, width=800, height=475)
forgot_password_frame.place(x=0, y=0, relwidth=1, relheight=1)
forgot_password_particle_frame = ParticleFrame(forgot_password_frame)
forgot_password_particle_frame.pack(expand=True, fill="both")
forgot_password_inner_frame = customtkinter.CTkFrame(forgot_password_particle_frame, corner_radius=10)
forgot_password_inner_frame.pack(expand=True)
pywinstyles.set_opacity(forgot_password_inner_frame, 0.9)
forgot_password_frame.lower()

def show_forgot_password():
    forgot_password_frame.lift()
    for widget in forgot_password_inner_frame.winfo_children():
        widget.destroy()

    title = customtkinter.CTkLabel(forgot_password_inner_frame, text="Forgot Password", 
                                 font=FONTS['title'], text_color='white')
    title.pack(padx=20, pady=10)

    back_button = customtkinter.CTkButton(forgot_password_inner_frame, text="Back", 
                                        command=hide_forgot_password_show_login, 
                                        fg_color="black", hover_color="grey", 
                                        font=FONTS['button'], width=30)
    back_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

    userTitle = customtkinter.CTkLabel(forgot_password_inner_frame, text="Username", 
                                     font=FONTS['subtitle'])
    userTitle.pack(pady=6)
    user_var_forgot = tkinter.StringVar()
    username_entry = customtkinter.CTkEntry(forgot_password_inner_frame, width=350, height=40, 
                                           textvariable=user_var_forgot, border_color="white", 
                                           font=FONTS['input'])
    username_entry.pack(padx=40)

    securityQTitle = customtkinter.CTkLabel(forgot_password_inner_frame, text="Security Question", 
                                          font=FONTS['subtitle'])
    securityQTitle.pack(pady=6)
    securityQ_var_forgot = tkinter.StringVar()
    security_dropdown = ttk.Combobox(forgot_password_inner_frame, textvariable=securityQ_var_forgot, 
                                   values=security_questions, state="readonly", 
                                   width=25, font=FONTS['dropdown'])
    security_dropdown.pack()

    # Apply dropdown styling
    global dropdown_theme_created
    combostyle = ttk.Style()
    if not dropdown_theme_created:
        combostyle.theme_create('combostyle', parent='alt',
            settings={
                'TCombobox': {
                    'configure': {
                        'fieldbackground': forgot_password_inner_frame.cget("fg_color")[1],
                        'selectbackground':'',
                        'selectforeground': "white",
                        'bordercolor':'grey',
                        'background': ''}},
                'TScrollbar':{
                        'configure': {
                        'background': ''}
                    }})
        dropdown_theme_created = True
    combostyle.theme_use('combostyle')
    security_dropdown.option_add("*TCombobox*Listbox*Foreground", "white")
    security_dropdown.option_add("*TCombobox*Listbox*Background", 
                                forgot_password_inner_frame.cget("fg_color")[1])
    security_dropdown.option_add("*TCombobox*Listbox*selectBackground", "white")
    security_dropdown.option_add("*TCombobox*Listbox*selectForeground", "black")

    securityAnsTitle = customtkinter.CTkLabel(forgot_password_inner_frame, text="Security Answer", 
                                            font=FONTS['subtitle'])
    securityAnsTitle.pack(pady=6)
    securityAns_var_forgot = tkinter.StringVar()
    securityAnsInp = customtkinter.CTkEntry(forgot_password_inner_frame, width=350, height=40, 
                                          textvariable=securityAns_var_forgot, border_color="white", 
                                          font=FONTS['input'])
    securityAnsInp.pack()

    def validate_answer():
        """Enhanced password retrieval validation"""
        try:
            username = user_var_forgot.get().strip()
            security_answer = securityAns_var_forgot.get().strip()
            
            if not username or not security_answer:
                CTkMessagebox(title="Validation Error", 
                            message="Please enter both username and security answer", 
                            icon="warning", justify=CENTER, button_color="black")
                return
            
            password, message = forgot_password(username, security_answer)
            if password:
                CTkMessagebox(title="Password Retrieved", 
                            message=f"Your password is: {password}", 
                            icon="check", justify=CENTER, button_color="black")
            else:
                CTkMessagebox(title="Validation Failed", 
                            message=message, 
                            icon="cancel", justify=CENTER, button_color="black")
                
        except Exception as e:
            logger.error(f"Password retrieval error: {e}")
            CTkMessagebox(title="Error", 
                        message="An error occurred while retrieving password", 
                        icon="cancel", justify=CENTER, button_color="black")
    
    validate_button = customtkinter.CTkButton(forgot_password_inner_frame, command=validate_answer, 
                                            text="Retrieve Password", fg_color="black", 
                                            hover_color="grey", font=FONTS['button'])
    validate_button.pack(padx=18, pady=18)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

# Main application buttons
loginButton = customtkinter.CTkButton(frame, text="Login", command=loginClick, 
                                    fg_color="black", hover_color="grey", font=FONTS['button'])
loginButton.pack(padx=18, pady=16)

RegisterButton = customtkinter.CTkButton(frame, text="Register", command=show_registration, 
                                       fg_color="black", hover_color="grey", font=FONTS['button'])
RegisterButton.pack(padx=18, pady=0)

forgot_password_button = customtkinter.CTkButton(frame, text="Forgot Password", 
                                               command=show_forgot_password, 
                                               fg_color="black", hover_color="grey", 
                                               font=FONTS['button'])
forgot_password_button.pack(padx=18, pady=16)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def FitPlusApp():
    """Enhanced main application with better error handling and performance"""
    
    def switch_page(page):
        """Enhanced page switching with error handling"""
        try:
            pages = [workoutPage, nutritionPage, progressPage, settingsPage, dashboardPage]
            for p in pages:
                p.pack_forget()
            page.pack(expand=True, fill='both')

            # Ensure fixed widgets stay on top
            fixed_widgets = [workoutButton, progressButton, nutritionButton, settingsButton, dashboardButton]
            for widget in fixed_widgets:
                widget.lift()
        except Exception as e:
            logger.error(f"Error switching pages: {e}")
    
    def MealToNutrition():
        try:
            MealsFrame.lower()
            Frame6.lift()
            nutritionTitle.lift()
        except Exception as e:
            logger.error(f"Error in MealToNutrition: {e}")

    def CalorieToNutrition():
        try:
            CalorieCounter_Frame.lower()
            Frame6.lift()
            nutritionTitle.lift()
        except Exception as e:
            logger.error(f"Error in CalorieToNutrition: {e}")

    def open_calorie_settings():
        """Enhanced calorie settings with better validation"""
        try:
            current_username = user_var.get().strip()
            if not current_username:
                CTkMessagebox(title="Error", message="No user logged in", 
                            icon="warning", justify=CENTER, button_color="black")
                return

            # Create settings frame
            calorie_settings_frame = customtkinter.CTkFrame(CalorieCounter_Frame, width=400, height=200, 
                                                          fg_color="#3c3c3c", border_color="white", 
                                                          border_width=2)
            calorie_settings_frame.place(relx=0.5, rely=0.8, anchor='center')

            calorie_limit_label = customtkinter.CTkLabel(calorie_settings_frame, 
                                                       text="Set your daily calorie limit:", 
                                                       font=("Calibri", 15))
            calorie_limit_label.place(relx=0.5, rely=0.2, anchor='center')

            daily_calorie_limit = get_user_calorie_limit(current_username)
            current_limit = customtkinter.CTkLabel(calorie_settings_frame, 
                                                  text=f"Current limit: {daily_calorie_limit} kcal", 
                                                  font=("Calibri", 15))
            current_limit.place(relx=0.5, rely=0.8, anchor='center')

            new_calorie_limit_var = tkinter.StringVar()
            new_calorie_limit_entry = customtkinter.CTkEntry(calorie_settings_frame, 
                                                            textvariable=new_calorie_limit_var, 
                                                            width=100)
            new_calorie_limit_entry.place(relx=0.5, rely=0.4, anchor='center')

            def close_calorie_settings():
                calorie_settings_frame.destroy()

            close_button = customtkinter.CTkButton(calorie_settings_frame, text="Close", 
                                                 command=close_calorie_settings, 
                                                 fg_color="black", hover_color="grey", 
                                                 font=FONTS['button'], width=30)
            close_button.place(relx=0.9, rely=0.15, anchor='center')
           
            def save_and_close():
                try:
                    new_limit = new_calorie_limit_var.get().strip()
                    if not new_limit:
                        CTkMessagebox(title="Error", message="Please enter a calorie limit", 
                                    icon="warning", justify=CENTER, button_color="black")
                        return
                    
                    success, message = save_new_calorie_limit(current_username, new_limit)
                    if success:
                        reset_daily_calorie_intake(current_username)
                        reset_nutrition(current_username)
                        calorie_settings_frame.destroy()
                        update_calorie_counter_section()
                        CTkMessagebox(title="Success", message="Calorie limit updated successfully", 
                                    icon="check", justify=CENTER, button_color="black")
                    else:
                        CTkMessagebox(title="Error", message=message, 
                                    icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error saving calorie limit: {e}")
                    CTkMessagebox(title="Error", message="Error updating calorie limit", 
                                icon="cancel", justify=CENTER, button_color="black")

            save_button = customtkinter.CTkButton(calorie_settings_frame, text="Save", 
                                                command=save_and_close, fg_color="black", 
                                                hover_color="grey", font=FONTS['button'])
            save_button.place(relx=0.5, rely=0.6, anchor='center')
            
        except Exception as e:
            logger.error(f"Error opening calorie settings: {e}")
            CTkMessagebox(title="Error", message="Error opening settings", 
                        icon="cancel", justify=CENTER, button_color="black")

    # Main application frame
    global mainapp
    mainapp = customtkinter.CTkFrame(app, width=1400, height=800)
    mainapp.pack(expand=True, fill='both')

    # Create all page frames
    workoutPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    nutritionPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    progressPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    settingsPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    dashboardPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    
    # Show dashboard by default
    dashboardPage.pack(expand=True, fill='both')

    # Create workout frames
    Frame1 = customtkinter.CTkFrame(master=workoutPage, width=280, height=800, 
                                  border_width=0, corner_radius=0, fg_color=COLORS['secondary_bg'])
    Frame1.place(x=0, y=0)

    Frame2 = customtkinter.CTkFrame(master=workoutPage, width=1120, height=800, corner_radius=0)
    Frame2.place(x=280, y=0)

    workoutsframe = customtkinter.CTkFrame(master=workoutPage, width=1123, height=800, 
                                         border_width=0, fg_color=COLORS['frame_bg'], 
                                         corner_radius=0)
    workoutsframe.place(x=280, y=0)

    # Navigation buttons with enhanced error handling
    workoutButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont('Impact', size=23),
        width=238, height=46, corner_radius=23, border_width=1,
        text='Workouts',
        fg_color=COLORS['button_bg'], bg_color=COLORS['secondary_bg'],
        hover_color=COLORS['secondary_bg'], border_color=COLORS['border'],
        command=lambda: switch_page(workoutPage))
    workoutButton.place(x=22, y=153)

    def progressSwitch():
        try:
            switch_page(progressPage)
            update_progress_section()
        except Exception as e:
            logger.error(f"Error switching to progress: {e}")
    
    progressButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont('Impact', size=23),
        width=238, height=46, corner_radius=23, border_width=1,
        text='Progress',
        fg_color=COLORS['button_bg'], bg_color=COLORS['secondary_bg'],
        hover_color=COLORS['secondary_bg'], border_color=COLORS['border'],
        command=progressSwitch)
    progressButton.place(x=22, y=299)

    def nutrition_switchpage():
        try:
            switch_page(nutritionPage)
            Frame6.lift()
            nutritionTitle.lift()
        except Exception as e:
            logger.error(f"Error switching to nutrition: {e}")

    nutritionButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont('Impact', size=23),
        width=238, height=46, corner_radius=23, border_width=1,
        text='Nutrition',
        fg_color=COLORS['button_bg'], bg_color=COLORS['secondary_bg'],
        hover_color=COLORS['secondary_bg'], border_color=COLORS['border'],
        command=nutrition_switchpage)
    nutritionButton.place(x=22, y=226)

    # Create nutrition frames
    Frame4 = customtkinter.CTkFrame(master=nutritionPage, width=280, height=800, 
                                  border_width=0, corner_radius=0, fg_color=COLORS['secondary_bg'])
    Frame4.place(x=0, y=0)

    Frame5 = customtkinter.CTkFrame(master=nutritionPage, width=1123, height=800, corner_radius=0)
    Frame5.place(x=280, y=0)

    Frame6 = customtkinter.CTkFrame(master=nutritionPage, width=1123, height=800, 
                                  border_width=0, fg_color=COLORS['frame_bg'], corner_radius=0)
    Frame6.place(x=280, y=0)

    # Nutrition buttons with enhanced error handling
    def safe_update_meals():
        try:
            update_meals_section()
        except Exception as e:
            logger.error(f"Error updating meals section: {e}")
            CTkMessagebox(title="Error", message="Error loading meals section", 
                        icon="warning", justify=CENTER, button_color="black")

    def safe_update_calorie_counter():
        try:
            update_calorie_counter_section()
        except Exception as e:
            logger.error(f"Error updating calorie counter: {e}")
            CTkMessagebox(title="Error", message="Error loading calorie counter", 
                        icon="warning", justify=CENTER, button_color="black")

    ButtonMeals = customtkinter.CTkButton(
        master=Frame6, text="Meals", command=safe_update_meals,
        font=FONTS['large_button'], fg_color="black", hover_color="grey",
        width=400, height=400, corner_radius=20)
    ButtonMeals.place(x=110, y=180)

    ButtonCalorieCounter = customtkinter.CTkButton(
        master=Frame6, text="Calorie Counter", command=safe_update_calorie_counter,
        font=FONTS['large_button'], fg_color="black", hover_color="grey",
        width=400, height=400, corner_radius=20)
    ButtonCalorieCounter.place(x=610, y=180)

    # Create progress frames
    Frame7 = customtkinter.CTkFrame(master=progressPage, width=280, height=800, 
                                  border_width=0, corner_radius=0, fg_color=COLORS['secondary_bg'])
    Frame7.place(x=0, y=0)

    Frame8 = customtkinter.CTkFrame(master=progressPage, width=1120, height=800, corner_radius=0)
    Frame8.place(x=280, y=0)

    Frame9 = customtkinter.CTkFrame(master=progressPage, width=1123, height=800, 
                                  border_width=0, fg_color=COLORS['frame_bg'], corner_radius=0)
    Frame9.place(x=280, y=0)

    # Create settings frames
    Frame10 = customtkinter.CTkFrame(master=settingsPage, width=280, height=800, 
                                   border_width=0, fg_color=COLORS['secondary_bg'], corner_radius=0)
    Frame10.place(x=0, y=0)

    Frame11 = customtkinter.CTkFrame(master=settingsPage, width=1120, height=800, 
                                   corner_radius=0, fg_color='#2b2b2b')
    Frame11.place(x=280, y=0)

    Frame12 = customtkinter.CTkFrame(master=settingsPage, width=1123, height=800, 
                                   border_width=0, fg_color=COLORS['frame_bg'], corner_radius=0)
    Frame12.place(x=280, y=0)

    def clicksettings():
        try:
            switch_page(settingsPage)
            update_settings_section()
        except Exception as e:
            logger.error(f"Error switching to settings: {e}")

    settingsButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont('Impact', size=23),
        width=147, height=46, corner_radius=23, border_width=1,
        text='Settings',
        fg_color=COLORS['button_bg'], bg_color=COLORS['secondary_bg'],
        hover_color=COLORS['secondary_bg'], border_color=COLORS['border'],
        command=clicksettings)
    settingsButton.place(x=66, y=732)

    dashboardButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont('Impact', size=23),
        width=126, height=46, corner_radius=23, border_width=1,
        text='Dashboard',
        fg_color=COLORS['button_bg'], bg_color=COLORS['secondary_bg'],
        hover_color=COLORS['secondary_bg'], border_color=COLORS['border'],
        command=lambda: switch_page(dashboardPage))
    dashboardButton.place(x=68, y=372)

    # Create dashboard frames
    Frame13 = customtkinter.CTkFrame(master=dashboardPage, width=280, height=800, 
                                   border_width=0, corner_radius=0, fg_color=COLORS['secondary_bg'])
    Frame13.place(x=0, y=0)

    Frame14 = customtkinter.CTkFrame(master=dashboardPage, width=1120, height=800, corner_radius=0)
    Frame14.place(x=280, y=0)

    Frame15 = customtkinter.CTkFrame(master=dashboardPage, width=1123, height=800, 
                                   border_width=0, fg_color=COLORS['frame_bg'], corner_radius=0)
    Frame15.place(x=280, y=0)

    # Main labels
    Label4 = customtkinter.CTkLabel(
        master=mainapp,
        font=customtkinter.CTkFont('impact', size=49, weight='bold', slant='italic'),
        height=0, text='FitPlus', bg_color=COLORS['secondary_bg'],
        text_color='#787878', padx=13, pady=2)
    Label4.place(x=50, y=18)

    Label5 = customtkinter.CTkLabel(master=dashboardPage, font=FONTS['section_title'],
                                  text='Dashboard', bg_color=COLORS['frame_bg'])
    Label5.place(x=783, y=16)

    Label7 = customtkinter.CTkLabel(master=progressPage, font=FONTS['section_title'],
                                  text='Progress', bg_color=COLORS['frame_bg'])
    Label7.place(x=783, y=16)

    nutritionTitle = customtkinter.CTkLabel(master=nutritionPage, font=FONTS['section_title'],
                                          text='Nutrition', bg_color=COLORS['frame_bg'])
    nutritionTitle.place(x=783, y=16)

    # Create meal and calorie counter frames
    MealsFrame = customtkinter.CTkFrame(master=nutritionPage, width=1123, height=800, 
                                      border_width=0, fg_color=COLORS['frame_bg'], corner_radius=0)
    MealsFrame.place(x=280, y=0)

    CalorieCounter_Frame = customtkinter.CTkFrame(master=nutritionPage, width=1123, height=800, 
                                                border_width=0, fg_color=COLORS['frame_bg'], corner_radius=0)
    CalorieCounter_Frame.place(x=280, y=0)

    # Enhanced workout section with better error handling
    def update_workouts_section():
        """Enhanced workout section with safe image loading"""
        try:
            for widget in workoutsframe.winfo_children():
                widget.destroy()
            
            # Video data with safe paths
            video_data = {
                'Cardio': {
                    'Beginner': [
                        ('https://www.youtube.com/watch?v=gX9SOYbfxeM', r'workoutimgs\CardioBeg1.jpg'), 
                        ('https://www.youtube.com/watch?v=PqqJBaE4srs', r'workoutimgs\CardioBeg2.jpg'), 
                        ('https://www.youtube.com/watch?v=_JUJ9647NbI', r'workoutimgs\CardioBeg3.jpg')
                    ],
                    'Intermediate': [
                        ('https://www.youtube.com/watch?v=wLYeRlyyncY', r'workoutimgs\CardioInt1.jpg'), 
                        ('https://www.youtube.com/watch?v=9lVBk1gS6qc', r'workoutimgs\CardioInt2.jpg'), 
                        ('https://www.youtube.com/watch?v=ZgPWjI-FG24', r'workoutimgs\CardioInt3.jpg')
                    ],
                    'Advanced': [
                        ('https://www.youtube.com/watch?v=LE67JPeJsUQ', r'workoutimgs\CardioAdv1.jpg'), 
                        ('https://www.youtube.com/watch?v=kZDvg92tTMc', r'workoutimgs\CardioAdv2.jpg'), 
                        ('https://www.youtube.com/watch?v=HzfHKN6rmpk', r'workoutimgs\CardioAdv3.jpg')
                    ],
                },
                'Strength': {
                    'Beginner': [
                        ('https://www.youtube.com/watch?v=tj0o8aH9vJw', r'workoutimgs\StrengthBeg1.jpg'), 
                        ('https://www.youtube.com/watch?v=eMjyvIQbn9M', r'workoutimgs\StrengthBeg2.jpg'), 
                        ('https://www.youtube.com/watch?v=Vxtr50cbX6c', r'workoutimgs\StrengthBeg3.jpg')
                    ],
                    'Intermediate': [
                        ('https://www.youtube.com/watch?v=XxuRSjER3Qk', r'workoutimgs\StrengthInt1.jpg'), 
                        ('https://www.youtube.com/watch?v=0hYDDsRjwks', r'workoutimgs\StrengthInt2.jpg'), 
                        ('https://www.youtube.com/watch?v=9FBIaqr7TjQ', r'workoutimgs\StrengthInt3.jpg')
                    ],
                    'Advanced': [
                        ('https://www.youtube.com/watch?v=588-C4bEL28', r'workoutimgs\StrengthAdv1.jpg'), 
                        ('https://www.youtube.com/watch?v=pHesd3IMTNI', r'workoutimgs\StrengthAdv2.jpg'), 
                        ('https://www.youtube.com/watch?v=IEyXbt_ZbF4', r'workoutimgs\StrengthAdv3.jpg')
                    ],
                },
                'Yoga': {
                    'Beginner': [
                        ('https://www.youtube.com/watch?v=v7AYKMP6rOE', r'workoutimgs\YogaBeg1.jpg'), 
                        ('https://www.youtube.com/watch?v=-wArTthypOo', r'workoutimgs\YogaBeg2.jpg'), 
                        ('https://www.youtube.com/watch?v=VzY6XuOSoHw', r'workoutimgs\YogaBeg3.jpg')
                    ],
                    'Intermediate': [
                        ('https://www.youtube.com/watch?v=52GAcwujm0k', r'workoutimgs\YogaInt1.jpg'), 
                        ('https://www.youtube.com/watch?v=vkZ-hRCpC-4', r'workoutimgs\YogaInt2.jpg'), 
                        ('https://www.youtube.com/watch?v=ZbtVVYBLCug', r'workoutimgs\YogaInt3.jpg')
                    ],
                    'Advanced': [
                        ('https://www.youtube.com/watch?v=OHNNfNHxapc', r'workoutimgs\YogaAdv1.jpg'), 
                        ('https://www.youtube.com/watch?v=JaCW9K_L_-8', r'workoutimgs\YogaAdv2.jpg'), 
                        ('https://www.youtube.com/watch?v=f7_zx1sPBj0', r'workoutimgs\YogaAdv3.jpg')
                    ],
                },
                'HIIT': {
                    'Beginner': [
                        ('https://www.youtube.com/watch?v=cbKkB3POqaY', r'workoutimgs\HIITBeg1.jpg'), 
                        ('https://www.youtube.com/watch?v=jWCm9piAwAU', r'workoutimgs\HIITBeg2.jpg'), 
                        ('https://www.youtube.com/watch?v=ebfBv6h3UFM', r'workoutimgs\HIITBeg3.jpg')
                    ],
                    'Intermediate': [
                        ('https://www.youtube.com/watch?v=H8vrfohV5e4', r'workoutimgs\HIITInt1.jpg'), 
                        ('https://www.youtube.com/watch?v=M5BhuRQ_FGk', r'workoutimgs\HIITInt2.jpg'), 
                        ('https://www.youtube.com/watch?v=M0uO8X3_tEA', r'workoutimgs\HIITInt3.jpg')
                    ],
                    'Advanced': [
                        ('https://www.youtube.com/watch?v=Amj0PAfhGIk', r'workoutimgs\HIITAdv1.jpg'), 
                        ('https://www.youtube.com/watch?v=WNUvx5y-1QE', r'workoutimgs\HIITAdv2.jpg'), 
                        ('https://www.youtube.com/watch?v=4nPKyvKmFi0', r'workoutimgs\HIITAdv3.jpg')
                    ],
                },
            }


            # Create categories frame
            categories_frame = customtkinter.CTkFrame(workoutsframe, width=1120, height=150, 
                                                    corner_radius=0, fg_color=COLORS['frame_bg'])
            categories_frame.place(x=0, y=0)
            
            categories = ['Cardio', 'Strength', 'Yoga', 'HIIT']
            x_pos = 145

            def show_category_details(category):
                """Enhanced category display with safe image loading"""
                try:
                    for widget in workoutsframe.winfo_children():
                        if widget != categories_frame:
                            widget.destroy()

                    category_title = customtkinter.CTkLabel(workoutsframe, text=category, font=('Impact', 19))
                    category_title.place(x=10, y=150)

                    levels = ['Beginner', 'Intermediate', 'Advanced']
                    colors = {'Beginner': 'green', 'Intermediate': 'yellow', 'Advanced': 'red'}
                    y_pos = 90

                    for level in levels:
                        level_frame = customtkinter.CTkFrame(workoutsframe, width=1100, height=240, 
                                                           corner_radius=0, fg_color='#2d2d2d')
                        level_frame.place(x=10, y=y_pos)
                        
                        level_label = customtkinter.CTkLabel(level_frame, text=f"{level} - {category}", 
                                                           font=('Impact', 16), text_color=colors[level])
                        level_label.place(x=30, y=7)

                        for i, (video_url, thumbnail_path) in enumerate(video_data[category][level]):
                            try:
                                # Safe image loading
                                img = safe_load_image(thumbnail_path, (315, 177))
                                photoImg = ImageTk.PhotoImage(img)

                                thumbnail_label = Label(level_frame, image=photoImg, cursor="hand2")
                                thumbnail_label.image = photoImg  # Keep reference
                                thumbnail_label.place(x=30 + (360 * i), y=40)
                                thumbnail_label.bind("<Button-1>", lambda e, url=video_url: open_youtube_video(url))
                                
                            except Exception as e:
                                logger.error(f"Error loading workout thumbnail {thumbnail_path}: {e}")
                                # Create placeholder label
                                placeholder_label = customtkinter.CTkLabel(level_frame, text="Video\nThumbnail", 
                                                                         width=315, height=177,
                                                                         fg_color="gray", cursor="hand2")
                                placeholder_label.place(x=30 + (360 * i), y=40)
                                placeholder_label.bind("<Button-1>", lambda e, url=video_url: open_youtube_video(url))

                        y_pos += 230
                        
                except Exception as e:
                    logger.error(f"Error showing category details: {e}")

            # Create category buttons
            for category in categories:
                try:
                    btn = customtkinter.CTkButton(categories_frame, text=category, 
                                                font=customtkinter.CTkFont('impact', size=17), 
                                                width=170, height=52, corner_radius=26, 
                                                fg_color=COLORS['button_bg'], hover_color=COLORS['button_hover'],
                                                command=lambda c=category: show_category_details(c))
                    btn.place(x=x_pos, y=20)
                    x_pos += 220
                except Exception as e:
                    logger.error(f"Error creating category button {category}: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating workouts section: {e}")

    # Enhanced dashboard section
    def update_dashboard_section():
        """Enhanced dashboard with safe image loading"""
        try:
            for widget in Frame15.winfo_children():
                widget.destroy()

            # Quote section
            quote_frame = customtkinter.CTkFrame(Frame15, width=1120, height=100, corner_radius=0)
            quote_frame.place(x=0, y=80)
            quote_label = customtkinter.CTkLabel(quote_frame, text="Quote of the day: 'Don't wish for it, work for it.'", 
                                            font=('Impact', 18))
            quote_label.place(x=10, y=10)

            # Featured workouts section
            featured_workouts_frame = customtkinter.CTkFrame(Frame15, width=1120, height=280, corner_radius=0)
            featured_workouts_frame.place(x=0, y=190)
            featured_label = customtkinter.CTkLabel(featured_workouts_frame, text="Featured Workouts:", 
                                                font=('Impact', 19))
            featured_label.place(x=10, y=10)

            # Dashboard workout videos with safe loading
            dashboard_workouts = [
                ('https://www.youtube.com/watch?v=J212vz33gU4', r"dashboardimgs\0.jpg"),
                ('https://www.youtube.com/watch?v=vr0g1-V6xec', r"dashboardimgs\1.jpg"),
                ('https://www.youtube.com/watch?v=sTANio_2E0Q', r"dashboardimgs\2.jpg")
            ]

            for i, (url, img_path) in enumerate(dashboard_workouts):
                try:
                    img = safe_load_image(img_path, (350, 196))
                    photoImg = ImageTk.PhotoImage(img)
                    
                    thumbnail_label = Label(featured_workouts_frame, image=photoImg, cursor="hand2")
                    thumbnail_label.image = photoImg
                    thumbnail_label.place(x=10 + (370 * i), y=40)
                    thumbnail_label.bind("<Button-1>", lambda e, video_url=url: open_youtube_video(video_url))
                    
                except Exception as e:
                    logger.error(f"Error loading dashboard workout image {img_path}: {e}")
                    # Create placeholder
                    placeholder = customtkinter.CTkLabel(featured_workouts_frame, text="Workout\nVideo", 
                                                    width=350, height=196, fg_color="gray", cursor="hand2")
                    placeholder.place(x=10 + (370 * i), y=40)
                    placeholder.bind("<Button-1>", lambda e, video_url=url: open_youtube_video(video_url))

            # Featured meals section
            featured_meals_frame = customtkinter.CTkFrame(Frame15, width=1120, height=280, corner_radius=0)
            featured_meals_frame.place(x=0, y=480)
            featured_meals_label = customtkinter.CTkLabel(featured_meals_frame, text="Featured Meals:", 
                                                    font=('Impact', 19))
            featured_meals_label.place(x=10, y=10)

            # Dashboard meal videos with safe loading
            dashboard_meals = [
                ('https://www.youtube.com/watch?v=1N6hbRbyAeQ', r"dashboardimgs\meal1.jpg"),
                ('https://www.youtube.com/watch?v=_f4ArgoSmoM', r"dashboardimgs\meal2.jpg"),
                ('https://www.youtube.com/watch?v=LzWb_P4lYgA', r"dashboardimgs\meal3.jpg")
            ]

            for i, (url, img_path) in enumerate(dashboard_meals):
                try:
                    img = safe_load_image(img_path, (350, 196))
                    photoImg = ImageTk.PhotoImage(img)
                    
                    thumbnail_label = Label(featured_meals_frame, image=photoImg, cursor="hand2")
                    thumbnail_label.image = photoImg
                    thumbnail_label.place(x=10 + (370 * i), y=40)
                    thumbnail_label.bind("<Button-1>", lambda e, video_url=url: open_youtube_video(video_url))
                    
                except Exception as e:
                    logger.error(f"Error loading dashboard meal image {img_path}: {e}")
                    # Create placeholder
                    placeholder = customtkinter.CTkLabel(featured_meals_frame, text="Meal\nVideo", 
                                                    width=350, height=196, fg_color="gray", cursor="hand2")
                    placeholder.place(x=10 + (370 * i), y=40)
                    placeholder.bind("<Button-1>", lambda e, video_url=url: open_youtube_video(video_url))
                
        except Exception as e:
            logger.error(f"Error updating dashboard section: {e}")

    # Enhanced meals section
    def update_meals_section():
        """Enhanced meals section with safe image loading"""
        try:
            for widget in MealsFrame.winfo_children():
                widget.destroy()
            MealsFrame.lift()
            
            MealsTitle = customtkinter.CTkLabel(master=MealsFrame, font=FONTS['section_title'],
                                              text='Meals', bg_color=COLORS['frame_bg'])
            MealsTitle.place(x=510, y=16)

            back_button = customtkinter.CTkButton(MealsFrame, text="Back", command=MealToNutrition, 
                                                fg_color="black", hover_color="grey", 
                                                font=FONTS['button'], width=30)
            back_button.place(x=1050, y=16)

            xy_frame = CTkXYFrame(MealsFrame, width=1075, height=700)
            xy_frame.place(x=15, y=75)
            
            # Meal data with safe loading
            meals_data = [
                ('https://www.bbcgoodfood.com/recipes/chicken-satay-salad', 
                 r"mealimages\meal1.jpeg",
                 "Try this no-fuss, midweek meal that's high in protein and big on flavour. Marinate chicken breasts, then drizzle with a punchy peanut satay sauce"),
                ('https://www.bbcgoodfood.com/recipes/double-bean-roasted-pepper-chilli', 
                 r"mealimages\meal2.jpeg",
                 "This warming vegetarian chilli is a low-fat, healthy option that packs in the veggies and flavour. Serve with Tabasco sauce, soured cream or yoghurt."),
                ('https://www.bbcgoodfood.com/recipes/chicken-noodle-soup', 
                 r"mealimages\meal3.jpeg",
                 "Mary Cadogan's aromatic broth will warm you up on a winter's evening - it contains ginger, which is particularly good for colds."),
                ('https://www.bbcgoodfood.com/recipes/classic-waffles', 
                 r"mealimages\meal4.jpeg",
                 "Make savoury or sweet waffles using this all-in-one batter mix. For even lighter waffles, whisk the egg white until fluffy, then fold through the batter"),
                ('https://www.bbcgoodfood.com/recipes/oat-biscuits-0', 
                 r"mealimages\meal5.jpeg",
                 "Nothing beats homemade cookies - make these easy oat biscuits for a sweet treat during the day when you need a break. They're perfect served with a cuppa"),
                ('https://www.bbcgoodfood.com/recipes/protein-balls', 
                 r"mealimages\meal6.jpeg",
                 "Make tasty protein balls using oats, protein powder, flaxseed and cinnamon to enjoy post-exercise and replenish your protein"),
                ('https://www.bbcgoodfood.com/recipes/creamy-salmon-pasta', 
                 r"mealimages\meal7.jpeg",
                 "Indulge in this creamy salmon dish for two. It's comforting and filling, and ready in just 30 minutes. Serve with a green salad")
            ]


            for i, (url, img_path, description) in enumerate(meals_data):
                try:
                    # Safe image loading
                    img = safe_load_image(img_path, (350, 196))
                    photoImg = ImageTk.PhotoImage(img)
                    
                    thumbnail_label = Label(xy_frame, image=photoImg, cursor="hand2")
                    thumbnail_label.image = photoImg
                    thumbnail_label.grid(row=i, column=0, padx=5, pady=20)
                    thumbnail_label.bind("<Button-1>", lambda e, recipe_url=url: open_recipe_link(recipe_url))

                    # Description label
                    description_label = customtkinter.CTkLabel(master=xy_frame, text=description, 
                                                             wraplength=500, font=FONTS['output'])
                    description_label.grid(row=i, column=1, padx=15, pady=0)
                    
                except Exception as e:
                    logger.error(f"Error loading meal {i}: {e}")
                    # Create placeholder
                    placeholder = customtkinter.CTkLabel(xy_frame, text="Recipe\nImage", 
                                                       width=350, height=196, fg_color="gray", cursor="hand2")
                    placeholder.grid(row=i, column=0, padx=5, pady=20)
                    placeholder.bind("<Button-1>", lambda e, recipe_url=url: open_recipe_link(recipe_url))
                    
                    description_label = customtkinter.CTkLabel(master=xy_frame, text=description, 
                                                             wraplength=500, font=FONTS['output'])
                    description_label.grid(row=i, column=1, padx=15, pady=0)
                    
        except Exception as e:
            logger.error(f"Error updating meals section: {e}")

    # Enhanced calorie counter section
    global update_calorie_counter_section
    def update_calorie_counter_section():
        """Enhanced calorie counter with better error handling"""
        global current_username, items, selected_food
        
        try:
            current_username = user_var.get().strip()
            if not current_username:
                logger.warning("No username available for calorie counter")
                return
                
            for widget in CalorieCounter_Frame.winfo_children():
                widget.destroy()
            CalorieCounter_Frame.lift()

            calorieTitle = customtkinter.CTkLabel(master=CalorieCounter_Frame, font=FONTS['section_title'],
                                                text='Calorie Counter', bg_color=COLORS['frame_bg'])
            calorieTitle.place(x=450, y=16)

            back_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Back", 
                                                command=CalorieToNutrition, fg_color="black", 
                                                hover_color="grey", font=FONTS['button'], width=30)
            back_button.place(x=1050, y=16)

            adjustcalorie_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Adjust calorie limit", 
                                                         command=open_calorie_settings, fg_color="black", 
                                                         hover_color="grey", font=FONTS['button'], width=200)
            adjustcalorie_button.place(x=900, y=80)

            # Enhanced food database
            items = [
                {"name": "Egg", "calories": 155, "fat": 11, "carbs": 1.1, "protein": 13, "sugars": 1.1},
                {"name": "Milk (1 cup)", "calories": 103, "fat": 2.4, "carbs": 12, "protein": 8, "sugars": 12},
                {"name": "Banana", "calories": 89, "fat": 0.3, "carbs": 23, "protein": 1.1, "sugars": 12},
                {"name": "Chicken Breast (100g)", "calories": 165, "fat": 3.6, "carbs": 0, "protein": 31, "sugars": 0},
                {"name": "Apple", "calories": 52, "fat": 0.2, "carbs": 14, "protein": 0.3, "sugars": 10},
                {"name": "Almonds (1 ounce)", "calories": 579, "fat": 49.9, "carbs": 21.6, "protein": 21.2, "sugars": 3.9},
                {"name": "Broccoli (1 cup)", "calories": 34, "fat": 0.4, "carbs": 6.6, "protein": 2.8, "sugars": 1.7},
                {"name": "Salmon (100g)", "calories": 208, "fat": 13, "carbs": 0, "protein": 20, "sugars": 0},
                {"name": "Sweet Potato", "calories": 86, "fat": 0.1, "carbs": 20, "protein": 1.6, "sugars": 4.2},
                {"name": "Oats (1 cup)", "calories": 389, "fat": 6.9, "carbs": 66, "protein": 17, "sugars": 0},
                {"name": "White Rice (1 cup)", "calories": 130, "fat": 0.3, "carbs": 28, "protein": 2.7, "sugars": 0.1},
                {"name": "Whole Wheat Bread (1 slice)", "calories": 247, "fat": 4.4, "carbs": 41, "protein": 13, "sugars": 6},
                {"name": "Avocado", "calories": 160, "fat": 15, "carbs": 9, "protein": 2, "sugars": 0.7},
                {"name": "Greek Yogurt (100g)", "calories": 59, "fat": 0.4, "carbs": 3.6, "protein": 10, "sugars": 3.2},
                {"name": "Spinach (1 cup)", "calories": 23, "fat": 0.4, "carbs": 3.6, "protein": 2.9, "sugars": 0.4},
                {"name": "Tomato", "calories": 18, "fat": 0.2, "carbs": 3.9, "protein": 0.9, "sugars": 2.6},
                {"name": "Beef (100g)", "calories": 254, "fat": 20, "carbs": 0, "protein": 17.2, "sugars": 0},
                {"name": "Peanut Butter (2 tablespoons)", "calories": 588, "fat": 50, "carbs": 20, "protein": 25, "sugars": 9},
                {"name": "Quinoa (1 cup)", "calories": 120, "fat": 1.9, "carbs": 21, "protein": 4.1, "sugars": 0.9},
                {"name": "Lentils (1 cup)", "calories": 116, "fat": 0.4, "carbs": 20, "protein": 9, "sugars": 1.8},
                {"name": "Cucumber", "calories": 16, "fat": 0.1, "carbs": 3.6, "protein": 0.7, "sugars": 1.7},
                {"name": "Cheddar Cheese (1 ounce)", "calories": 402, "fat": 33, "carbs": 1.3, "protein": 25, "sugars": 0.5},
                {"name": "Whole Wheat Pasta (1 cup)", "calories": 124, "fat": 0.8, "carbs": 26, "protein": 5, "sugars": 1.3},
                {"name": "Orange", "calories": 47, "fat": 0.1, "carbs": 12, "protein": 0.9, "sugars": 9},
                {"name": "Tofu (100g)", "calories": 76, "fat": 4.8, "carbs": 1.9, "protein": 8, "sugars": 0.3}
            ]

            item_names = [item["name"] for item in items]
            selected_food = ""

            button = customtkinter.CTkButton(CalorieCounter_Frame, text="Choose food item", width=400, 
                                           fg_color="black", hover_color="grey", font=("Impact", 17))
            button.place(x=360, y=400)

            def on_select(selected_item):
                """Enhanced food selection"""
                try:
                    global selected_food
                    selected_food = selected_item
                    button.configure(text=selected_item)
                    logger.info(f"Selected food item: {selected_item}")
                except Exception as e:
                    logger.error(f"Error selecting food item: {e}")

            CTkScrollableDropdown(button, values=item_names, height=200, resize=False, 
                                button_height=50, scrollbar=True, command=on_select)

            # Display calorie information with error handling
            try:
                daily_calorie_limit = get_user_calorie_limit(current_username)
                daily_calorie_intake = get_user_calorie_intake(current_username)
                remaining_calories = daily_calorie_limit - daily_calorie_intake
                
                intake_label = customtkinter.CTkLabel(CalorieCounter_Frame, 
                                                    text=f"Today's Calorie Intake: {daily_calorie_intake} kcal", 
                                                    font=("Impact", 20), bg_color=COLORS['frame_bg'])
                intake_label.place(x=290, y=170)
                
                remaining_label = customtkinter.CTkLabel(CalorieCounter_Frame, 
                                                       text=f"Remaining Calories: {remaining_calories} kcal", 
                                                       font=("Impact", 20), bg_color=COLORS['frame_bg'])
                remaining_label.place(x=590, y=170)

                # Get nutrition data
                nutrition_data = get_user_data(current_username, 
                                             ['daily_fat', 'daily_carbs', 'daily_protein', 'daily_sugars'])
                
                if nutrition_data:
                    daily_fat = nutrition_data.get('daily_fat', 0)
                    daily_carbs = nutrition_data.get('daily_carbs', 0)
                    daily_protein = nutrition_data.get('daily_protein', 0)
                    daily_sugars = nutrition_data.get('daily_sugars', 0)
                else:
                    daily_fat = daily_carbs = daily_protein = daily_sugars = 0

                # Display nutrition labels
                labels = [
                    ("Fats", daily_fat, "g"),
                    ("Carbohydrates", daily_carbs, "g"),
                    ("Proteins", daily_protein, "g"),
                    ("Sugars", daily_sugars, "g")
                ]

                y_pos = 220
                for label_text, value, unit in labels:
                    label = customtkinter.CTkLabel(CalorieCounter_Frame, 
                                                 text=f"{label_text}: {round(value, 1)} {unit}", 
                                                 font=("Impact", 18), bg_color=COLORS['frame_bg'])
                    label.place(x=290, y=y_pos)
                    y_pos += 35

            except Exception as e:
                logger.error(f"Error displaying calorie information: {e}")

            def reset_function():
                """Enhanced reset with user feedback"""
                try:
                    success1, msg1 = reset_daily_calorie_intake(current_username)
                    success2, msg2 = reset_nutrition(current_username)
                    
                    if success1 and success2:
                        update_calorie_counter_section()
                        CTkMessagebox(title="Success", message="Daily intake reset successfully", 
                                    icon="check", justify=CENTER, button_color="black")
                    else:
                        CTkMessagebox(title="Error", message="Error resetting daily intake", 
                                    icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error in reset function: {e}")
                    CTkMessagebox(title="Error", message="Error resetting data", 
                                icon="cancel", justify=CENTER, button_color="black")
            
            reset_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Reset", 
                                                 command=reset_function, fg_color="black", 
                                                 hover_color="grey", font=FONTS['button'], width=200)
            reset_button.place(x=900, y=120)

            def safe_add_food():
                """Enhanced food addition with validation"""
                try:
                    if not selected_food:
                        CTkMessagebox(title="Error", message="Please select a food item first", 
                                    icon="warning", justify=CENTER, button_color="black")
                        return
                    
                    success, message = add_food_to_intake(selected_food)
                    if success:
                        CTkMessagebox(title="Success", message=f"Added {selected_food} to your intake", 
                                    icon="check", justify=CENTER, button_color="black")
                    else:
                        CTkMessagebox(title="Error", message=message, 
                                    icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error adding food: {e}")
                    CTkMessagebox(title="Error", message="Error adding food item", 
                                icon="cancel", justify=CENTER, button_color="black")

            add_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Add", fg_color="black", 
                                               hover_color="grey", font=FONTS['button'], 
                                               command=safe_add_food)
            add_button.place(x=490, y=450)
            
        except Exception as e:
            logger.error(f"Error updating calorie counter section: {e}")

    # Enhanced settings section with safe pygame initialization
    def update_settings_section():
        """Enhanced settings with safe music handling"""
        try:
            # Safe pygame initialization
            music_available = False
            try:
                pygame.mixer.init()
                if os.path.exists("soundtrack.mp3"):
                    pygame.mixer.music.load("soundtrack.mp3")
                    pygame.mixer.music.set_volume(0.05)
                    pygame.mixer.music.play(-1)
                    music_available = True
                    logger.info("Background music loaded successfully")
                else:
                    logger.warning("Background music file not found: soundtrack.mp3")
            except Exception as e:
                logger.error(f"Error initializing music: {e}")
                music_available = False

            def toggle_music():
                """Safe music toggle"""
                try:
                    if not music_available:
                        return
                    
                    if musicCheckBox.get() == 1:
                        pygame.mixer.music.unpause()
                        logger.info("Music resumed")
                    else:
                        pygame.mixer.music.pause()
                        logger.info("Music paused")
                except Exception as e:
                    logger.error(f"Error toggling music: {e}")

            # Music checkbox (only if music is available)
            if music_available:
                musicCheckBox = customtkinter.CTkCheckBox(
                    master=settingsPage,
                    font=customtkinter.CTkFont('impact', size=20),
                    height=0, corner_radius=30, text='Music',
                    fg_color=COLORS['button_bg'], bg_color=COLORS['frame_bg'],
                    hover_color=COLORS['button_hover'], command=toggle_music,
                    variable=tkinter.IntVar(value=1))
                musicCheckBox.place(x=802, y=373)

            SettingsTitle = customtkinter.CTkLabel(master=settingsPage, font=FONTS['section_title'],
                                                 text='Settings', bg_color=COLORS['frame_bg'])
            SettingsTitle.place(x=783, y=16)

            Label1 = customtkinter.CTkLabel(master=settingsPage,
                                          font=customtkinter.CTkFont('Impact', size=28, underline=True),
                                          text='Your account', bg_color=COLORS['frame_bg'])
            Label1.place(x=766, y=107)

            def safe_logout():
                """Enhanced logout with cleanup"""
                try:
                    # Stop music if playing
                    if music_available:
                        pygame.mixer.music.stop()
                    
                    # Hide main app
                    mainapp.pack_forget()
                    
                    # Clear user data
                    global current_username
                    current_username = ""
                    user_var.set("")
                    pass_var.set("")
                    
                    # Show login screen
                    frame.pack(expand=True)
                    particle_frame.pack(expand=True, fill="both")
                    
                    logger.info("User logged out successfully")
                    
                except Exception as e:
                    logger.error(f"Error during logout: {e}")

            logoutButton = customtkinter.CTkButton(
                master=settingsPage,
                font=customtkinter.CTkFont('impact', size=19),
                width=133, height=50, corner_radius=25,
                text='Log Out',
                fg_color=COLORS['button_bg'], bg_color=COLORS['frame_bg'],
                hover_color=COLORS['button_hover'], command=safe_logout)
            logoutButton.place(x=775, y=686)

            Label2 = customtkinter.CTkLabel(master=settingsPage,
                                          font=customtkinter.CTkFont('Impact', size=28, underline=True),
                                          text='Miscellaneous', bg_color=COLORS['frame_bg'])
            Label2.place(x=760, y=321)

            def confirmDelete():
                """Enhanced account deletion confirmation"""
                try:
                    confirmdelete = CTkMessagebox(title="Delete Account", 
                                                message="Are you sure you want to delete your account? This action cannot be undone.", 
                                                icon="warning", justify=CENTER, button_color="black", 
                                                button_hover_color="grey", option_1="Yes", option_2="No")
                    response = confirmdelete.get()
                    
                    if response == "Yes":
                        success, message = delete_account()
                        if success:
                            CTkMessagebox(title="Account Deleted", message="Your account has been deleted successfully", 
                                        icon="check", justify=CENTER, button_color="black")
                        else:
                            CTkMessagebox(title="Error", message=message, 
                                        icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error confirming account deletion: {e}")
                    CTkMessagebox(title="Error", message="Error processing account deletion", 
                                icon="cancel", justify=CENTER, button_color="black")

            DeleteAccButton = customtkinter.CTkButton(
                master=settingsPage,
                font=customtkinter.CTkFont('impact', size=17),
                width=238, height=52, corner_radius=26,
                text='Delete Account',
                fg_color=COLORS['button_bg'], bg_color=COLORS['frame_bg'],
                command=confirmDelete, hover_color=COLORS['button_hover'])
            DeleteAccButton.place(x=723, y=162)
            
        except Exception as e:
            logger.error(f"Error updating settings section: {e}")

    # Enhanced progress section with better validation
    def update_progress_section():
        """Enhanced progress tracking with validation"""
        try:
            # Clear existing widgets
            for widget in Frame9.winfo_children():
                widget.destroy()

            # Get user data
            user_data = get_user_data(current_username, 
                                    ['current_weight', 'ideal_weight', 'bench_press_pr', 'squat_pr', 'deadlift_pr'])
            
            if not user_data:
                logger.warning(f"No user data found for {current_username}")
                return

            current_weight = user_data.get('current_weight', 0)
            ideal_weight = user_data.get('ideal_weight', 0)
            bench_press_pr = user_data.get('bench_press_pr', 0)
            squat_pr = user_data.get('squat_pr', 0)
            deadlift_pr = user_data.get('deadlift_pr', 0)
            
            weight_difference = ideal_weight - current_weight

            # Enhanced update functions with validation
            def on_update_current_weight_click():
                try:
                    new_weight = simpledialog.askfloat("Update Current Weight", 
                                                     f"Enter your new current weight (kg):\nCurrent: {current_weight} kg",
                                                     minvalue=0, maxvalue=MAX_WEIGHT)
                    if new_weight is not None:
                        success, message = update_current_weight(current_username, new_weight)
                        if success:
                            update_progress_section()
                            CTkMessagebox(title="Success", message="Current weight updated successfully", 
                                        icon="check", justify=CENTER, button_color="black")
                        else:
                            CTkMessagebox(title="Error", message=message, 
                                        icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error updating current weight: {e}")
                    CTkMessagebox(title="Error", message="Error updating weight", 
                                icon="cancel", justify=CENTER, button_color="black")

            def on_update_ideal_weight_click():
                try:
                    new_weight = simpledialog.askfloat("Update Ideal Weight", 
                                                     f"Enter your new ideal weight (kg):\nCurrent: {ideal_weight} kg",
                                                     minvalue=0, maxvalue=MAX_WEIGHT)
                    if new_weight is not None:
                        success, message = update_ideal_weight(current_username, new_weight)
                        if success:
                            update_progress_section()
                            CTkMessagebox(title="Success", message="Ideal weight updated successfully", 
                                        icon="check", justify=CENTER, button_color="black")
                        else:
                            CTkMessagebox(title="Error", message=message, 
                                        icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error updating ideal weight: {e}")
                    CTkMessagebox(title="Error", message="Error updating weight", 
                                icon="cancel", justify=CENTER, button_color="black")
            
            def on_update_bench_press_click():
                try:
                    new_pr = simpledialog.askfloat("Update Bench Press PR", 
                                                 f"Enter your new Bench Press PR (kg):\nCurrent: {bench_press_pr} kg",
                                                 minvalue=0, maxvalue=MAX_PR)
                    if new_pr is not None:
                        success, message = update_bench_press_pr(current_username, new_pr)
                        if success:
                            update_progress_section()
                            CTkMessagebox(title="Success", message="Bench Press PR updated successfully", 
                                        icon="check", justify=CENTER, button_color="black")
                        else:
                            CTkMessagebox(title="Error", message=message, 
                                        icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error updating bench press PR: {e}")
                    CTkMessagebox(title="Error", message="Error updating PR", 
                                icon="cancel", justify=CENTER, button_color="black")
            
            def on_update_squat_click():
                try:
                    new_pr = simpledialog.askfloat("Update Squat PR", 
                                                 f"Enter your new Squat PR (kg):\nCurrent: {squat_pr} kg",
                                                 minvalue=0, maxvalue=MAX_PR)
                    if new_pr is not None:
                        success, message = update_squat_pr(current_username, new_pr)
                        if success:
                            update_progress_section()
                            CTkMessagebox(title="Success", message="Squat PR updated successfully", 
                                        icon="check", justify=CENTER, button_color="black")
                        else:
                            CTkMessagebox(title="Error", message=message, 
                                        icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error updating squat PR: {e}")
                    CTkMessagebox(title="Error", message="Error updating PR", 
                                icon="cancel", justify=CENTER, button_color="black")

            def on_update_deadlift_click():
                try:
                    new_pr = simpledialog.askfloat("Update Deadlift PR", 
                                                 f"Enter your new Deadlift PR (kg):\nCurrent: {deadlift_pr} kg",
                                                 minvalue=0, maxvalue=MAX_PR)
                    if new_pr is not None:
                        success, message = update_deadlift_pr(current_username, new_pr)
                        if success:
                            update_progress_section()
                            CTkMessagebox(title="Success", message="Deadlift PR updated successfully", 
                                        icon="check", justify=CENTER, button_color="black")
                        else:
                            CTkMessagebox(title="Error", message=message, 
                                        icon="warning", justify=CENTER, button_color="black")
                except Exception as e:
                    logger.error(f"Error updating deadlift PR: {e}")
                    CTkMessagebox(title="Error", message="Error updating PR", 
                                icon="cancel", justify=CENTER, button_color="black")

            # Create achievement frame with scrolling
            achievementframe = CTkXYFrame(Frame9, width=1075, height=250)
            achievementframe.place(x=15, y=520)

            # Enhanced achievement system
            achievements = [
                ("Reach a 20kg bench press", bench_press_pr >= 20),
                ("Reach a 40kg bench press", bench_press_pr >= 40),
                ("Reach a 60kg bench press", bench_press_pr >= 60),
                ("Reach a 80kg bench press", bench_press_pr >= 80),
                ("Reach a 100kg bench press", bench_press_pr >= 100),
                ("Reach a 20kg squat", squat_pr >= 20),
                ("Reach a 40kg squat", squat_pr >= 40),
                ("Reach a 60kg squat", squat_pr >= 60),
                ("Reach a 80kg squat", squat_pr >= 80),
                ("Reach a 100kg squat", squat_pr >= 100),
                ("Reach a 60kg deadlift", deadlift_pr >= 60),
                ("Reach a 80kg deadlift", deadlift_pr >= 80),
                ("Reach a 100kg deadlift", deadlift_pr >= 100),
                ("Reach a 120kg deadlift", deadlift_pr >= 120),
                ("Reach a 140kg deadlift", deadlift_pr >= 140),
            ]

            def update_achievement_labels(frame, achievement_text, achieved, relx_position):
                """Enhanced achievement display"""
                try:
                    static_label = customtkinter.CTkLabel(master=frame, text=f"{achievement_text}: ", 
                                                        font=("Impact", 24))
                    static_label.place(relx=relx_position, rely=0.5, anchor='e')

                    status = "✓ Unlocked" if achieved else "✗ Locked"
                    status_color = "green" if achieved else "red"
                    status_label = customtkinter.CTkLabel(master=frame, text=status, font=("Impact", 24), 
                                                        text_color=status_color)
                    status_label.place(relx=relx_position, rely=0.5, anchor='w')
                except Exception as e:
                    logger.error(f"Error updating achievement label: {e}")

            # Create achievement frames
            for i, (achievement_text, achieved) in enumerate(achievements):
                try:
                    achievement_frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
                    achievement_frame.grid(row=i, column=0, padx=5, pady=20)
                    update_achievement_labels(achievement_frame, achievement_text, achieved, 0.3)
                except Exception as e:
                    logger.error(f"Error creating achievement frame {i}: {e}")

            # Weight tracking frame
            weightFrame = customtkinter.CTkFrame(Frame9, width=450, height=300)
            weightFrame.place(x=63, y=120)
            
            WeightTitle = customtkinter.CTkLabel(master=weightFrame, text="Weight Tracker", 
                                               font=("Calibri", 18, 'underline'))
            WeightTitle.place(relx=0.5, rely=0.1, anchor='center')
            
            current_weight_label = customtkinter.CTkLabel(master=weightFrame, 
                                                        text=f"Current Weight: {current_weight} kg", 
                                                        font=("Calibri", 16))
            current_weight_label.place(relx=0.5, rely=0.3, anchor='center')
            
            ideal_weight_label = customtkinter.CTkLabel(master=weightFrame, 
                                                      text=f"Ideal Weight: {ideal_weight} kg", 
                                                      font=("Calibri", 16))
            ideal_weight_label.place(relx=0.5, rely=0.4, anchor='center')
            
            diff_text = "Weight to Gain: " if weight_difference > 0 else "Weight to Lose: " if weight_difference < 0 else "At Ideal Weight: "
            weight_diff_label = customtkinter.CTkLabel(master=weightFrame, 
                                                     text=f"{diff_text} {abs(weight_difference)} kg", 
                                                     font=("Calibri", 16))
            weight_diff_label.place(relx=0.5, rely=0.5, anchor='center')
            
            UpdateCurrentWeight = customtkinter.CTkButton(weightFrame, text="Update Current Weight", 
                                                        width=180, fg_color="black", hover_color="grey", 
                                                        font=("Impact", 16), command=on_update_current_weight_click)
            UpdateCurrentWeight.place(relx=0.25, rely=0.75, anchor='center')
            
            UpdateIdealWeight = customtkinter.CTkButton(weightFrame, text="Update Ideal Weight", 
                                                      width=180, fg_color="black", hover_color="grey", 
                                                      font=("Impact", 16), command=on_update_ideal_weight_click)
            UpdateIdealWeight.place(relx=0.75, rely=0.75, anchor='center')

            # PR tracking frame
            prFrame = customtkinter.CTkFrame(Frame9, width=450, height=300)
            prFrame.place(x=606, y=120)
            
            prTitle = customtkinter.CTkLabel(master=prFrame, text="Personal Record Tracker", 
                                           font=("Calibri", 18, 'underline'))
            prTitle.place(relx=0.5, rely=0.1, anchor='center')
            
            bench_pr_label = customtkinter.CTkLabel(master=prFrame, text=f"Bench Press PR: {bench_press_pr} kg", 
                                                  font=("Calibri", 16))
            bench_pr_label.place(relx=0.5, rely=0.3, anchor='center')
            
            squat_pr_label = customtkinter.CTkLabel(master=prFrame, text=f"Squat PR: {squat_pr} kg", 
                                                  font=("Calibri", 16))
            squat_pr_label.place(relx=0.5, rely=0.4, anchor='center')
            
            deadlift_pr_label = customtkinter.CTkLabel(master=prFrame, text=f"Deadlift PR: {deadlift_pr} kg", 
                                                     font=("Calibri", 16))
            deadlift_pr_label.place(relx=0.5, rely=0.5, anchor='center')
            
            UpdateBench = customtkinter.CTkButton(prFrame, text="Update Bench Press", width=143, 
                                                fg_color="black", hover_color="grey", font=("Impact", 16), 
                                                command=on_update_bench_press_click)
            UpdateBench.place(relx=0.5, rely=0.75, anchor='center')
            
            UpdatesSquat = customtkinter.CTkButton(prFrame, text="Update Squat", width=140, 
                                                 fg_color="black", hover_color="grey", font=("Impact", 16), 
                                                 command=on_update_squat_click)
            UpdatesSquat.place(relx=0.17, rely=0.75, anchor='center')
            
            UpdateDeadlift = customtkinter.CTkButton(prFrame, text="Update Deadlift", width=140, 
                                                   fg_color="black", hover_color="grey", font=("Impact", 16), 
                                                   command=on_update_deadlift_click)
            UpdateDeadlift.place(relx=0.83, rely=0.75, anchor='center')

            achievementTitle = customtkinter.CTkLabel(master=Frame9, text="Achievements", font=("Impact", 20))
            achievementTitle.place(relx=0.5, rely=0.62, anchor='center')
            
        except Exception as e:
            logger.error(f"Error updating progress section: {e}")

    # Initialize all sections with error handling
    try:
        update_workouts_section()
        update_dashboard_section()
        update_meals_section()
        update_calorie_counter_section()
        update_settings_section()
        update_progress_section()
        logger.info("All sections initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing sections: {e}")

# Enhanced error handling for main execution
try:
    if __name__ == "__main__":
        logger.info("Starting FitPlus application")
        app.mainloop()
except KeyboardInterrupt:
    logger.info("Application interrupted by user")
except Exception as e:
    logger.error(f"Critical application error: {e}")
finally:
    try:
        # Cleanup on exit
        if 'pygame' in sys.modules:
            pygame.mixer.quit()
        logger.info("Application cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")