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

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#
# Here I have code which has been sourced from github that creates a cool particle effect in the background of frames

class Particle:
    def __init__(self, canvas):
        self.canvas = canvas
        self.radius = self.canvas.size
        self.x = random.randint(self.radius, self.canvas.winfo_screenwidth() - self.radius)
        self.y = random.randint(self.radius, self.canvas.winfo_screenheight()  - self.radius)
        self.dx = random.uniform(-1, 1)
        self.dy = random.uniform(-1, 1)

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.canvas.move(self.id, self.dx, self.dy)

class ParticleFrame(tkinter.Canvas):
    def __init__(self,
                 master,
                 fg_color="black",
                 particle_color="white",
                 particle_size=3,
                 particle_count=100,
                 respawn=15,
                 **kwargs):

        super().__init__(master, bg=fg_color,
                         highlightthickness=0,
                         borderwidth=0, **kwargs)
        
        self.color = particle_color
        self.size = particle_size
        self.particles = []
        self.num_particles = particle_count
        self.respawn = respawn
        self.after(200, self.start)
        self._stop = False
        self.bind("<Destroy>", lambda e: self.stop())
        
    def stop(self):
        self._stop = True
        
    def create_particles(self):
        if self._stop:
            return
        for _ in range(self.num_particles):
            particle = Particle(self)
            particle.id = self.create_oval(
                particle.x - self.size,
                particle.y - self.size,
                particle.x + self.size,
                particle.y + self.size,
                fill=self.color, outline=self.color
            )
            self.particles.append(particle)
        self.after(self.respawn*1000, self.create_particles)
        
    def move_particles(self):
        for particle in self.particles:
            particle.move()

    def start(self):
        self.create_particles()
        self.after(10, self.update_simulation)
        self._stop = False
        
    def update_simulation(self):
        if self._stop:
            return
        #self.update()
        self.move_particles()
        self.after(10, self.update_simulation)

dropdown_theme_created = False
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def setup_database():
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            security_question TEXT NOT NULL,
            security_answer TEXT NOT NULL,
            daily_calorie_limit INTEGER DEFAULT 2000,
            daily_calorie_intake INTEGER DEFAULT 0,
            daily_fat INTEGER DEFAULT 0,
            daily_carbs INTEGER DEFAULT 0,
            daily_protein INTEGER DEFAULT 0,
            daily_sugars INTEGER DEFAULT 0,
            current_weight INTEGER DEFAULT 0,
            ideal_weight INTEGER DEFAULT 0,
            bench_press_pr INTEGER DEFAULT 0,
            squat_pr INTEGER DEFAULT 0,
            deadlift_pr INTEGER DEFAULT 0,
            last_update DATE DEFAULT (DATE('now'))
        )
    ''')
    connection.commit()
    connection.close()

def register_user(username, password, security_question, security_answer):
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, password, security_question, security_answer)
            VALUES (?, ?, ?, ?)
        ''', (username, password, security_question, security_answer))
        connection.commit()
        return True
    except sqlite3.IntegrityError:
        print("Username already exists.")
        return False
    finally:
        connection.close()

def login_user(username, password):
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    cursor.execute('''
        SELECT password FROM users WHERE username = ?
    ''', (username,))
    result = cursor.fetchone()
    connection.close()
    return bool(result and result[0] == password)

def forgot_password(username, security_answer):
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    cursor.execute('''
        SELECT password FROM users WHERE username = ? AND security_answer = ?
    ''', (username, security_answer))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

def delete_account():
    username = user_var.get()  
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    # Delete the user's account from the database
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    connection.commit()
    connection.close()
    
    # Hide the main app frame and show the login screen
    mainapp.pack_forget()  # Hide the main application
    frame.pack(expand=True)  # Show the login frame
    particle_frame.pack(expand=True, fill="both")  # Ensure particle effect is visible
    
    # clear the username and password fields
    user_var.set("")
    pass_var.set("")


def update_current_weight(username, new_weight):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    c.execute("UPDATE users SET current_weight = ? WHERE username = ?", (new_weight, username))
    conn.commit()
    conn.close()
    print("Current weight updated.")

def update_ideal_weight(username, new_weight):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    c.execute("UPDATE users SET ideal_weight = ? WHERE username = ?", (new_weight, username))
    conn.commit()
    conn.close()
    print("Ideal weight updated.")

def update_bench_press_pr(username, new_pr):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    c.execute("UPDATE users SET bench_press_pr = ? WHERE username = ?", (new_pr, username))
    conn.commit()
    conn.close()

def update_squat_pr(username, new_pr):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    c.execute("UPDATE users SET squat_pr = ? WHERE username = ?", (new_pr, username))
    conn.commit()
    conn.close()

def update_deadlift_pr(username, new_pr):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    c.execute("UPDATE users SET deadlift_pr = ? WHERE username = ?", (new_pr, username))
    conn.commit()
    conn.close()

def get_user_calorie_limit(username):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    c.execute("SELECT daily_calorie_limit FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 2000

def get_user_calorie_intake(username):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    # check and reset calorie data if the date has changed
    check_and_reset_calorie_data(username)
    c.execute("SELECT daily_calorie_intake FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def check_and_reset_calorie_data(username):
    conn = sqlite3.connect('fitplus.db')
    c = conn.cursor()
    c.execute("SELECT last_update FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    last_update = result[0] if result else None
    today = datetime.date.today().isoformat()
    
    if not last_update or last_update < today:
        c.execute("UPDATE users SET daily_calorie_intake = 0, last_update = ? WHERE username = ?", (today, username))
        conn.commit()
    conn.close()

def reset_daily_calorie_intake(username):
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE users
        SET daily_calorie_intake = 0
        WHERE username = ?
    ''', (username,))
    connection.commit()
    connection.close()

def reset_nutrition(username):
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE users
        SET daily_fat = 0,
            daily_carbs = 0,
            daily_protein = 0,
            daily_sugars = 0
        WHERE username = ?
    ''', (username,))
    connection.commit()
    connection.close()

def save_new_calorie_limit(username, new_limit):
    connection = sqlite3.connect('fitplus.db')
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE users
        SET daily_calorie_limit = ?
        WHERE username = ?
    ''', (new_limit, username))
    connection.commit()
    connection.close()


def add_food_to_intake(selected_item_name):
    global items, current_username
    selected_item = next((item for item in items if item["name"] == selected_item_name), None)
    if selected_item:
        # Fetches current intake from the database
        conn = sqlite3.connect('fitplus.db')
        c = conn.cursor()
        c.execute("SELECT daily_calorie_intake, daily_fat, daily_carbs, daily_protein, daily_sugars FROM users WHERE username = ?", (current_username,))
        result = c.fetchone()
        current_intake, current_fats, current_carbs, current_protein, current_sugars = result if result else (0, 0, 0, 0, 0)

        # Update the intake with selected item's values
        new_intake = current_intake + selected_item["calories"]
        new_fats = current_fats + selected_item["fat"]
        new_carbs = current_carbs + selected_item["carbs"]
        new_protein = current_protein + selected_item["protein"]
        new_sugars = current_sugars + selected_item["sugars"]

        c.execute("UPDATE users SET daily_calorie_intake = ?, daily_fat = ?, daily_carbs = ?, daily_protein = ?, daily_sugars = ? WHERE username = ?", (new_intake, new_fats, new_carbs, new_protein, new_sugars, current_username))
        conn.commit()
        conn.close()

        # Refresh the UI to show updated values
        update_calorie_counter_section()

setup_database()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

current_theme = {"theme": "dark"}

app = customtkinter.CTk()  # Create the base window
app.configure(bg="#242424")  # Set background colour to #242424
app.title("FitPlus")
app.resizable(False, False)
app.iconbitmap("fitplus_smallicon.ico")
window_height = 800
window_width = 1400

# Calculate screen dimensions to display the window in the middle of the user's screen
screen_width = app.winfo_screenwidth()
screen_height = app.winfo_screenheight()
x_cordinate = int((screen_width / 2) - (window_width / 2))
y_cordinate = int((screen_height / 2) - (window_height / 2))
app.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

particle_frame = ParticleFrame(app)
particle_frame.pack(expand=True, fill="both")

frame = customtkinter.CTkFrame(particle_frame, corner_radius=10)
frame.pack(expand=True)
pywinstyles.set_opacity(frame, 0.9) # blur background content


fitplus_data = Image.open("fitplus.png")
fitplus_icon_data = Image.open("fitplus_smallicon.ico")

fitplus_img = CTkImage(dark_image=fitplus_data, light_image=fitplus_data, size=(213, 164))
fitplus_smallicon = CTkImage(dark_image=fitplus_icon_data, light_image=fitplus_icon_data, size=(96, 96))

# Define security_questions globally (used in registration and forgotpassword functions later on)
security_questions = ["Where were you born?", "What is your pet's name?", "What is your mother's name?", "Your favourite colour?"]

# Assigning fonts (used throughout the code later on)
title_font = ("Impact", 36)
subtitle_font = ("Impact", 16)
input_font = ("Calibri", 16)
dropdown_font = ("Impact", 12)
button_font = ("Impact", 14)
output_font = ("Calibri", 18)
                     
title = customtkinter.CTkLabel(frame, text="FitPlus Authentication", font=title_font)
title.pack(padx=20, pady=10)

userTitle = customtkinter.CTkLabel(frame, text="Username", font=subtitle_font)
userTitle.pack(padx=18, pady=12)

user_var = tkinter.StringVar()
username = customtkinter.CTkEntry(frame, width=350, height=40, textvariable=user_var, border_color="white", font=input_font) # Input box
username.pack(padx=18, pady=0)

passTitle = customtkinter.CTkLabel(frame, text="Password", font=subtitle_font)
passTitle.pack(padx=18, pady=12)

pass_var = tkinter.StringVar()
password = customtkinter.CTkEntry(frame, width=350, height=40, textvariable=pass_var, border_color="white", font=input_font) # Input box
password.pack(padx=18, pady=0)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def loginClick(): # function for when "login" button is clicked on by the user
    if login_user(user_var.get(), pass_var.get()):
        CTkMessagebox(title="Login successful", message="You have been logged in", icon="check", justify=CENTER, button_color="black")
        frame.pack_forget()
        particle_frame.pack_forget()
        FitPlusApp()  # Proceed to the main application
    else:
        # Login unsuccessful
        CTkMessagebox(title="Login failed", message="Incorrect username or password.", icon="cancel", justify=CENTER, button_color="black")

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

# Function to hide the registration frame and show the login interface
def hide_registration_show_login():
    registration_frame.lower()  

# Registration Frame Setup
registration_frame = customtkinter.CTkFrame(app, width=800, height=475)
registration_frame.place(x=0, y=0, relwidth=1, relheight=1)
registration_particle_frame = ParticleFrame(registration_frame)
registration_particle_frame.pack(expand=True, fill="both")
registration_inner_frame = customtkinter.CTkFrame(registration_particle_frame, corner_radius=10) 
registration_inner_frame.pack(expand=True)
pywinstyles.set_opacity(registration_inner_frame, 0.9)  # blur background content
registration_frame.lower()  # Initially keeps the registration frame hidden

def show_registration():
    registration_frame.lift() 
    for widget in registration_inner_frame.winfo_children():
        widget.destroy()

    title = customtkinter.CTkLabel(registration_inner_frame, text="Registration", font=title_font, text_color='white')
    title.pack(padx=20, pady=3)

    back_button = customtkinter.CTkButton(registration_inner_frame, text="Back", command=hide_registration_show_login, fg_color="black", hover_color="grey", font=button_font, width=30)
    back_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

    userTitle = customtkinter.CTkLabel(registration_inner_frame, text="Username", font=subtitle_font).pack(pady=3)
    userReg_var = tkinter.StringVar()
    userInp = customtkinter.CTkEntry(registration_inner_frame, width=350, height=40, textvariable=userReg_var, border_color="white", font=input_font).pack(padx=40)

    passTitle = customtkinter.CTkLabel(registration_inner_frame, text="Password", font=subtitle_font).pack(pady=6)
    passReg_var = tkinter.StringVar()
    passInp = customtkinter.CTkEntry(registration_inner_frame, width=350, height=40, textvariable=passReg_var, border_color="white", font=input_font).pack()

    securityTitle = customtkinter.CTkLabel(registration_inner_frame, text="Security Question", font=subtitle_font).pack(pady=6)
    securityQ_var = tkinter.StringVar()

    # dropdown menu with security questions
    security_dropdown = ttk.Combobox(registration_inner_frame, textvariable=securityQ_var, values=security_questions, state="readonly", font=dropdown_font, width=25)
    security_dropdown.pack()


    # Code sourced from GitHub - Akascape
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
    security_dropdown.option_add("*TCombobox*Listbox*Background", registration_inner_frame.cget("fg_color")[1])
    security_dropdown.option_add("*TCombobox*Listbox*selectBackground", "white")
    security_dropdown.option_add("*TCombobox*Listbox*selectForeground", "black")

    securityAnsTitle = customtkinter.CTkLabel(registration_inner_frame, text="Security Answer", font=subtitle_font).pack(pady=6)
    securityAns_var = tkinter.StringVar()
    securityAnsInp = customtkinter.CTkEntry(registration_inner_frame, width=350, height=40, textvariable=securityAns_var, border_color="white", font=input_font).pack()

    def regValidation():
        username = userReg_var.get().strip()  
        password = passReg_var.get().strip()
        security_question = securityQ_var.get().strip()
        security_answer = securityAns_var.get().strip()

        # Check if any of the fields are empty
        if not username or not password or not security_question or not security_answer:
            CTkMessagebox(title="Error", message="Registration Failed, All fields are required.", icon="cancel", justify=CENTER, button_color="black")
            return  # Exit the function early if any field is empty

        if register_user(username, password, security_question, security_answer):
            # Registration successful
            CTkMessagebox(title="Success", message="Registration Successful, You are now registered.", icon="check", justify=CENTER, button_color="black")
        else:
            # Registration failed (due to existing username)
            CTkMessagebox(title="Registration failed", message="Username already exists.", icon="warning", justify=CENTER, button_color="black")
    regConfirm = customtkinter.CTkButton(registration_inner_frame, command=regValidation, text="Confirm", fg_color="black", hover_color="grey", font=button_font)
    regConfirm.pack(padx=18, pady=18)


def retrieve_security_question(username):
    connection = sqlite3.connect('fitplus.db')  
    cursor = connection.cursor()
    cursor.execute("SELECT security_question FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    connection.close()
    if result:
        return result[0]
    else:
        return None


def hide_forgot_password_show_login():
    forgot_password_frame.lower()

forgot_password_frame = customtkinter.CTkFrame(app, width=800, height=475)
forgot_password_frame.place(x=0, y=0, relwidth=1, relheight=1)
forgot_password_particle_frame = ParticleFrame(forgot_password_frame)
forgot_password_particle_frame.pack(expand=True, fill="both")
forgot_password_inner_frame = customtkinter.CTkFrame(forgot_password_particle_frame, corner_radius=10) 
forgot_password_inner_frame.pack(expand=True)
pywinstyles.set_opacity(forgot_password_inner_frame, 0.9)  # blur background content
forgot_password_frame.lower()  # Initially keeps the forgot password frame hidden

def show_forgot_password():
    forgot_password_frame.lift() 
    for widget in forgot_password_inner_frame.winfo_children():
        widget.destroy()

    title = customtkinter.CTkLabel(forgot_password_inner_frame, text="Forgot Password", font=title_font, text_color='white')
    title.pack(padx=20, pady=10)

    back_button = customtkinter.CTkButton(forgot_password_inner_frame, text="Back", command=hide_forgot_password_show_login, fg_color="black", hover_color="grey", font=button_font, width=30)
    back_button.place(relx=1.0, rely=0.0, x=-10, y=10, anchor="ne")

    userTitle = customtkinter.CTkLabel(forgot_password_inner_frame, text="Username", font=subtitle_font)
    userTitle.pack(pady=6)
    user_var = tkinter.StringVar()
    username_entry = customtkinter.CTkEntry(forgot_password_inner_frame, width=350, height=40, textvariable=user_var, border_color="white", font=input_font)
    username_entry.pack(padx=40)

    securityQTitle = customtkinter.CTkLabel(forgot_password_inner_frame, text="Security Question", font=subtitle_font)
    securityQTitle.pack(pady=6)
    securityQ_var = tkinter.StringVar()
    security_dropdown = ttk.Combobox(forgot_password_inner_frame, textvariable=securityQ_var, values=security_questions, state="readonly", width=25, font=dropdown_font)
    security_dropdown.pack()

    # Code sourced from GitHub - Akascape
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
    security_dropdown.option_add("*TCombobox*Listbox*Background", forgot_password_inner_frame.cget("fg_color")[1])
    security_dropdown.option_add("*TCombobox*Listbox*selectBackground", "white")
    security_dropdown.option_add("*TCombobox*Listbox*selectForeground", "black")

    securityAnsTitle = customtkinter.CTkLabel(forgot_password_inner_frame, text="Security Answer", font=subtitle_font)
    securityAnsTitle.pack(pady=6)
    securityAns_var = tkinter.StringVar()
    securityAnsInp = customtkinter.CTkEntry(forgot_password_inner_frame, width=350, height=40, textvariable=securityAns_var, border_color="white", font=input_font)
    securityAnsInp.pack()

    def validate_answer():
        username = user_var.get()
        security_answer = securityAns_var.get()
        password = forgot_password(username, security_answer)
        if password:
            # Display the password
            CTkMessagebox(title="Success", message=f"Your Password: {password}", icon="check", justify=CENTER, button_color="black")
        else:
            # Failed to retrieve password
            CTkMessagebox(title="Failed", message="Incorrect username or answer.", icon="cancel", justify=CENTER, button_color="black")
    validate_button = customtkinter.CTkButton(forgot_password_inner_frame, command=validate_answer, text="Validate Answer", fg_color="black", hover_color="grey", font=button_font)
    validate_button.pack(padx=18, pady=18)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

loginButton = customtkinter.CTkButton(frame, text="Login", command=loginClick, fg_color="black", hover_color="grey", font=button_font)
loginButton.pack(padx=18, pady=16)

RegisterButton = customtkinter.CTkButton(frame, text="Register", command=show_registration, fg_color="black", hover_color="grey", font=button_font)
RegisterButton.pack(padx=18, pady=0)

forgot_password_button = customtkinter.CTkButton(frame, text="Forgot Password", command=show_forgot_password, fg_color="black", hover_color="grey", font=button_font)
forgot_password_button.pack(padx=18, pady=16)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def FitPlusApp():
    def switch_page(page):
        pages = [workoutPage, nutritionPage, progressPage, settingsPage, dashboardPage]
        for i in pages:
            i.pack_forget()
        page.pack(expand=True, fill='both')

        fixed_widgets = [workoutButton, progressButton, nutritionButton, settingsButton, dashboardButton]
        for widget in fixed_widgets:
            widget.lift()
            widget.place(x=widget.winfo_x(), y=widget.winfo_y())
    
    
    def MealToNutrition():
        MealsFrame.lower()
        Frame6.lift()
        nutritionTitle.lift()
        

    def CalorieToNutrition():
        CalorieCounter_Frame.lower()
        Frame6.lift()
        nutritionTitle.lift()


    def open_calorie_settings():
        current_username = user_var.get()  # Fetches the username from the global user_var

        # settings frame within CalorieCounter_Frame
        calorie_settings_frame = customtkinter.CTkFrame(CalorieCounter_Frame, width=400, height=200, fg_color="#3c3c3c", border_color="white",border_width=2)
        calorie_settings_frame.place(relx=0.5, rely=0.8, anchor='center')

        calorie_limit_label = customtkinter.CTkLabel(calorie_settings_frame, text="Set your daily calorie limit:", font=("Calibri", 15))
        calorie_limit_label.place(relx=0.5, rely=0.2, anchor='center')

        daily_calorie_limit = get_user_calorie_limit(current_username)
        current_limit = customtkinter.CTkLabel(calorie_settings_frame, text=f"Current Calorie limit: {daily_calorie_limit}", font=("Calibri", 15))
        current_limit.place(relx=0.5, rely=0.8, anchor='center')

        new_calorie_limit_var = tkinter.StringVar()
        new_calorie_limit_entry = customtkinter.CTkEntry(calorie_settings_frame, textvariable=new_calorie_limit_var, width=100)
        new_calorie_limit_entry.place(relx=0.5, rely=0.4, anchor='center')

        def close_calorie_settings():
            calorie_settings_frame.destroy()

        close_button = customtkinter.CTkButton(calorie_settings_frame, text="Close", command=close_calorie_settings, fg_color="black", hover_color="grey", font=button_font, width=30)
        close_button.place(relx=0.9, rely=0.15, anchor='center')
       
        def save_and_close():
            new_limit = new_calorie_limit_var.get()
            if new_limit.isdigit():  # Ensure that the new limit is a digit before saving
                save_new_calorie_limit(current_username, new_limit)
                reset_daily_calorie_intake(current_username)  # Reset daily calorie intake to 0
                reset_nutrition(current_username)
                calorie_settings_frame.destroy()  # Destroys the settings frame after saving
                update_calorie_counter_section()  # Refreshes calorie counter display
            else:
                CTkMessagebox.error(title="Error", message="Please enter a valid number for the calorie limit.")

        save_button = customtkinter.CTkButton(calorie_settings_frame, text="Save", command=save_and_close, fg_color="black", hover_color="grey", font=button_font)
        save_button.place(relx=0.5, rely=0.6, anchor='center')

    global mainapp
    mainapp = customtkinter.CTkFrame(app, width=1400, height=800)  
    mainapp.pack(expand=True, fill='both')

    workoutPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    nutritionPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    progressPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    settingsPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    dashboardPage = customtkinter.CTkFrame(mainapp, fg_color='transparent', corner_radius=0, border_width=0)
    dashboardPage.pack(expand=True, fill='both')  

    Frame1 = customtkinter.CTkFrame(
        master=workoutPage,
        width=280,
        height=800,
        border_width=0,
        border_color='#ffffff',
        corner_radius=0,
        fg_color='#313131')
    Frame1.place(x=0, y=0)

    Frame2 = customtkinter.CTkFrame(master=workoutPage, width=1120, height=800, corner_radius=0)
    Frame2.place(x=280, y=0)

    workoutButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont(
            'Impact',
            size=23),
        width=238,
        height=46,
        corner_radius=23,
        border_width=1,
        text='Workouts',
        fg_color='#000000',
        bg_color='#313131',
        hover_color='#313131',
        border_color='#ffffff',
        command=lambda: switch_page(workoutPage))
    workoutButton.place(x=22, y=153)

    def progressSwitch():
        switch_page(progressPage)
        update_progress_section
    progressButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont(
            'Impact',
            size=23),
        width=238,
        height=46,
        corner_radius=23,
        border_width=1,
        text='Progress',
        fg_color='#000000',
        bg_color='#313131',
        hover_color='#313131',
        border_color='#ffffff',
        command=lambda: progressSwitch())
    progressButton.place(x=22, y=299)


    def nutrition_switchpage():
        switch_page(nutritionPage)
        Frame6.lift()
        nutritionTitle.lift()


    nutritionButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont(
            'Impact',
            size=23),
        width=238,
        height=46,
        corner_radius=23,
        border_width=1,
        text='Nutrition',
        fg_color='#000000',
        bg_color='#313131',
        hover_color='#313131',
        border_color='#ffffff',
        command=lambda: nutrition_switchpage())
    nutritionButton.place(x=22, y=226)

    workoutsframe = customtkinter.CTkFrame(
        master=workoutPage,
        width=1123,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#3c3c3c',
        bg_color='#414141',
        corner_radius=0)
    workoutsframe.place(x=280, y=0)

    Frame4 = customtkinter.CTkFrame(
        master=nutritionPage,
        width=280,
        height=800,
        border_width=0,
        border_color='#ffffff',
        corner_radius=0,
        fg_color='#313131')
    Frame4.place(x=0, y=0)

    Frame5 = customtkinter.CTkFrame(master=nutritionPage, width=1123, height=800, corner_radius=0)
    Frame5.place(x=280, y=0)

    Frame6 = customtkinter.CTkFrame(
        master=nutritionPage,
        width=1123,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#3c3c3c',
        bg_color='#414141',
        corner_radius=0)
    Frame6.place(x=280, y=0)

    ButtonMeals = customtkinter.CTkButton(
        master=Frame6,  
        text="Meals",
        command=lambda: update_meals_section(), 
        font=("Roboto Medium", -40),  
        fg_color="black",  
        hover_color="grey",  
        width=400,  
        height=400,  
        corner_radius=20
    )
    ButtonMeals.place(x=110, y=180)  

    ButtonCalorieCounter = customtkinter.CTkButton(
        master=Frame6, 
        text="Calorie Counter",
        command=lambda: update_calorie_counter_section(), 
        font=("Roboto Medium", -40),
        fg_color="black", 
        hover_color="grey",
        width=400,  
        height=400,  
        corner_radius=20 
    )
    ButtonCalorieCounter.place(x=610, y=180) 

    Frame7 = customtkinter.CTkFrame(
        master=progressPage,
        width=280,
        height=800,
        border_width=0,
        border_color='#ffffff',
        corner_radius=0,
        fg_color='#313131')
    Frame7.place(x=0, y=0)

    Frame8 = customtkinter.CTkFrame(master=progressPage, width=1120, height=800, corner_radius=0)
    Frame8.place(x=280, y=0)

    Frame9 = customtkinter.CTkFrame(
        master=progressPage,
        width=1123,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#3c3c3c',
        corner_radius=0)
    Frame9.place(x=280, y=0)

    Frame10 = customtkinter.CTkFrame(
        master=settingsPage,
        width=280,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#313131',
        corner_radius=0)
    Frame10.place(x=0, y=0)

    Frame11 = customtkinter.CTkFrame(master=settingsPage, width=1120, height=800, corner_radius=0, fg_color='#2b2b2b')
    Frame11.place(x=280, y=0)

    Frame12 = customtkinter.CTkFrame(
        master=settingsPage,
        width=1123,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#3c3c3c',
        corner_radius=0)
    Frame12.place(x=280, y=0)

    settingsButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont(
            'Impact',
            size=23),
        width=147,
        height=46,
        corner_radius=23,
        border_width=1,
        text='Settings',
        fg_color='#000000',
        bg_color='#313131',
        hover_color='#313131',
        border_color='#ffffff',
        command=lambda: clicksettings())
    settingsButton.place(x=66, y=732)

    def clicksettings():
        switch_page(settingsPage)
        update_settings_section()

    dashboardButton = customtkinter.CTkButton(
        master=mainapp,
        font=customtkinter.CTkFont(
            'Impact',
            size=23),
        width=126,
        height=46,
        corner_radius=23,
        border_width=1,
        text='Dashboard',
        fg_color='#000000',
        bg_color='#313131',
        hover_color='#313131',
        border_color='#ffffff',
        command=lambda: switch_page(dashboardPage))
    dashboardButton.place(x=68, y=372)

    Frame13 = customtkinter.CTkFrame(
        master=dashboardPage,
        width=280,
        height=800,
        border_width=0,
        border_color='#ffffff',
        corner_radius=0,
        fg_color='#313131')
    Frame13.place(x=0, y=0)

    Frame14 = customtkinter.CTkFrame(master=dashboardPage, width=1120, height=800, corner_radius=0)
    Frame14.place(x=280, y=0)

    Frame15 = customtkinter.CTkFrame(
        master=dashboardPage,
        width=1123,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#3c3c3c',
        corner_radius=0)
    Frame15.place(x=280, y=0)

    Label4 = customtkinter.CTkLabel(
        master=mainapp,
        font=customtkinter.CTkFont(
            'impact',
            size=49,
            weight='bold',
            slant='italic'),
        height=0,
        text='FitPlus',
        bg_color='#313131',
        text_color='#787878',
        padx=13,
        pady=2,
        text_color_disabled='#787878')
    Label4.place(x=50, y=18)

    Label5 = customtkinter.CTkLabel(
        master=dashboardPage,
        font=customtkinter.CTkFont(
            'Impact',
            size=35),
        text='Dashboard',
        bg_color='#3c3c3c')
    Label5.place(x=783, y=16)

    Label7 = customtkinter.CTkLabel(
        master=progressPage,
        font=customtkinter.CTkFont(
            'impact',
            size=35),
        text='Progress',
        bg_color='#3c3c3c')
    Label7.place(x=783, y=16)

    nutritionTitle = customtkinter.CTkLabel(
        master=nutritionPage,
        font=customtkinter.CTkFont(
            'impact',
            size=35),
        text='Nutrition',
        bg_color='#3c3c3c')
    nutritionTitle.place(x=783, y=16)


    MealsFrame = customtkinter.CTkFrame(
        master=nutritionPage,
        width=1123,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#3c3c3c',
        bg_color='#414141',
        corner_radius=0
    )
    MealsFrame.place(x=280, y=0)


    CalorieCounter_Frame = customtkinter.CTkFrame(
        master=nutritionPage,
        width=1123,
        height=800,
        border_width=0,
        border_color='#ffffff',
        fg_color='#3c3c3c',
        bg_color='#414141',
        corner_radius=0
    )
    CalorieCounter_Frame.place(x=280, y=0)

    def update_workouts_section():
        for widget in workoutsframe.winfo_children():
            widget.destroy()
        
        video_data = {
            'Cardio': {
                'Beginner': [('https://www.youtube.com/watch?v=gX9SOYbfxeM', r'workoutimgs\CardioBeg1.jpg'), ('https://www.youtube.com/watch?v=PqqJBaE4srs', r'workoutimgs\CardioBeg2.jpg'), ('https://www.youtube.com/watch?v=_JUJ9647NbI', r'workoutimgs\CardioBeg3.jpg')],
                'Intermediate': [('https://www.youtube.com/watch?v=wLYeRlyyncY', r'workoutimgs\CardioInt1.jpg'), ('https://www.youtube.com/watch?v=9lVBk1gS6qc', r'workoutimgs\CardioInt2.jpg'), ('https://www.youtube.com/watch?v=ZgPWjI-FG24', r'workoutimgs\CardioInt3.jpg')],
                'Advanced': [('https://www.youtube.com/watch?v=LE67JPeJsUQ', r'workoutimgs\CardioAdv1.jpg'), ('https://www.youtube.com/watch?v=kZDvg92tTMc', r'workoutimgs\CardioAdv2.jpg'), ('https://www.youtube.com/watch?v=HzfHKN6rmpk', r'workoutimgs\CardioAdv3.jpg')],
            },
            'Strength': {
                'Beginner': [('https://www.youtube.com/watch?v=tj0o8aH9vJw', r'workoutimgs\StrengthBeg1.jpg'), ('https://www.youtube.com/watch?v=eMjyvIQbn9M', r'workoutimgs\StrengthBeg2.jpg'), ('https://www.youtube.com/watch?v=Vxtr50cbX6c', r'workoutimgs\StrengthBeg3.jpg')],
                'Intermediate': [('https://www.youtube.com/watch?v=XxuRSjER3Qk', r'workoutimgs\StrengthInt1.jpg'), ('https://www.youtube.com/watch?v=0hYDDsRjwks', r'workoutimgs\StrengthInt2.jpg'), ('https://www.youtube.com/watch?v=9FBIaqr7TjQ', r'workoutimgs\StrengthInt3.jpg')],
                'Advanced': [('https://www.youtube.com/watch?v=588-C4bEL28', r'workoutimgs\StrengthAdv1.jpg'), ('https://www.youtube.com/watch?v=pHesd3IMTNI', r'workoutimgs\StrengthAdv2.jpg'), ('https://www.youtube.com/watch?v=IEyXbt_ZbF4', r'workoutimgs\StrengthAdv3.jpg')],
            },
            'Yoga': {
                'Beginner': [('https://www.youtube.com/watch?v=v7AYKMP6rOE', r'workoutimgs\YogaBeg1.jpg'), ('https://www.youtube.com/watch?v=-wArTthypOo', r'workoutimgs\YogaBeg2.jpg'), ('https://www.youtube.com/watch?v=VzY6XuOSoHw', r'workoutimgs\YogaBeg3.jpg')],
                'Intermediate': [('https://www.youtube.com/watch?v=52GAcwujm0k', r'workoutimgs\YogaInt1.jpg'), ('https://www.youtube.com/watch?v=vkZ-hRCpC-4', r'workoutimgs\YogaInt2.jpg'), ('https://www.youtube.com/watch?v=ZbtVVYBLCug', r'workoutimgs\YogaInt3.jpg')],
                'Advanced': [('https://www.youtube.com/watch?v=OHNNfNHxapc', r'workoutimgs\YogaAdv1.jpg'), ('https://www.youtube.com/watch?v=JaCW9K_L_-8', r'workoutimgs\YogaAdv2.jpg'), ('https://www.youtube.com/watch?v=f7_zx1sPBj0', r'workoutimgs\YogaAdv3.jpg')],
            },
            'HIIT': {
                'Beginner': [('https://www.youtube.com/watch?v=cbKkB3POqaY', r'workoutimgs\HIITBeg1.jpg'), ('https://www.youtube.com/watch?v=jWCm9piAwAU', r'workoutimgs\HIITBeg2.jpg'), ('https://www.youtube.com/watch?v=ebfBv6h3UFM', r'workoutimgs\HIITBeg3.jpg')],
                'Intermediate': [('https://www.youtube.com/watch?v=H8vrfohV5e4', r'workoutimgs\HIITInt1.jpg'), ('https://www.youtube.com/watch?v=M5BhuRQ_FGk', r'workoutimgs\HIITInt2.jpg'), ('https://www.youtube.com/watch?v=M0uO8X3_tEA', r'workoutimgs\HIITInt3.jpg')],
                'Advanced': [('https://www.youtube.com/watch?v=Amj0PAfhGIk', r'workoutimgs\HIITAdv1.jpg'), ('https://www.youtube.com/watch?v=WNUvx5y-1QE', r'workoutimgs\HIITAdv2.jpg'), ('https://www.youtube.com/watch?v=4nPKyvKmFi0', r'workoutimgs\HIITAdv3.jpg')],
            },
        }

        # Function to open a YouTube video
        def open_youtube_video(url):
            webbrowser.open(url)

        categories_frame = customtkinter.CTkFrame(workoutsframe, width=1120, height=150, corner_radius=0, fg_color='#3c3c3c', bg_color='#414141')
        categories_frame.place(x=0, y=0)
        categories = ['Cardio', 'Strength', 'Yoga', 'HIIT']
        x_pos = 145  # Starting position for the first category button

        def show_category_details(category):
            for widget in workoutsframe.winfo_children():
                if widget != categories_frame:
                    widget.destroy()

            category_title = customtkinter.CTkLabel(workoutsframe, text=category, font=('Impact', 19))
            category_title.place(x=10, y=150)

            levels = ['Beginner', 'Intermediate', 'Advanced']
            colors = {'Beginner': 'green', 'Intermediate': 'yellow', 'Advanced': 'red'}  # Colour mapping for each level
            y_pos = 90  # Starting y position for the first level frame

            for level in levels:
                level_frame = customtkinter.CTkFrame(workoutsframe, width=1100, height=240, corner_radius=0, fg_color='#2d2d2d', bg_color='#414141')
                level_frame.place(x=10, y=y_pos)
                # Change the level_label colour according to the level
                level_label = customtkinter.CTkLabel(level_frame, text=f"{level} - {category}", font=('Impact', 16), text_color=colors[level])
                level_label.place(x=30, y=7)

                for i, (video_url, thumbnail_path) in enumerate(video_data[category][level]):
                    img = Image.open(thumbnail_path)
                    img = img.resize((315, 177))
                    photoImg = ImageTk.PhotoImage(img)

                    thumbnail_label = Label(level_frame, image=photoImg, cursor="hand2")
                    thumbnail_label.image = photoImg  
                    thumbnail_label.place(x=30 + (360 * i), y=40) 
                    thumbnail_label.bind("<Button-1>", lambda e, url=video_url: open_youtube_video(url))

                y_pos += 230  # Adjust y position for the next level frame

        for category in categories:
            btn = customtkinter.CTkButton(categories_frame, text=category, font=customtkinter.CTkFont('impact', size=17), width=170, height=52, corner_radius=26, fg_color='#000000', bg_color='#3c3c3c', hover_color='#1a1a1a', command=lambda c=category: show_category_details(c))
            btn.place(x=x_pos, y=20)
            x_pos += 220

        def setup_category_frames(Frame3, categories_frame):
            def show_category_details(category):
                for widget in Frame3.winfo_children():
                    if widget != categories_frame:
                        widget.destroy()

                category_title = customtkinter.CTkLabel(Frame3, text=category, font=('Impact', 19), fg_color='white', bg_color='transparent')
                category_title.place(x=10, y=190)

                levels = ['Beginner', 'Intermediate', 'Advanced']
                y_pos = 210

                for level in levels:
                    level_frame = customtkinter.CTkFrame(Frame3, width=1100, height=300, corner_radius=0, fg_color='#2d2d2d', bg_color='#414141')
                    level_frame.place(x=10, y=y_pos)
                    level_label = customtkinter.CTkLabel(level_frame, text=f"{level} - {category}", font=('Impact', 16), fg_color='white', bg_color='#414141')
                    level_label.place(x=10, y=10)

                    for i, (video_url, thumbnail_path) in enumerate(video_data[category][level]):
                        img = Image.open(thumbnail_path)
                        img = img.resize((350, 196))
                        photoImg = ImageTk.PhotoImage(img)

                        thumbnail_label = Label(level_frame, image=photoImg, cursor="hand2")
                        thumbnail_label.image = photoImg
                        thumbnail_label.place(x=10 + (360 * i), y=40)
                        thumbnail_label.bind("<Button-1>", lambda e, url=video_url: open_youtube_video(url))

                    y_pos += 310
    update_workouts_section()


    def update_dashboard_section():
        for widget in Frame15.winfo_children():
            widget.destroy()

        quote_frame = customtkinter.CTkFrame(Frame15, width=1120, height=100, corner_radius=0)
        quote_frame.place(x=0, y=80) 
        quote_label = customtkinter.CTkLabel(quote_frame, text="Quote of the day: 'Don't wish for it, work for it.'", font=('Impact', 18))
        quote_label.place(x=10, y=10)

        featured_workouts_frame = customtkinter.CTkFrame(Frame15, width=1120, height=280, corner_radius=0)
        featured_workouts_frame.place(x=0, y=190)
        featured_label = customtkinter.CTkLabel(featured_workouts_frame, text="Featured Workouts:", font=('Impact', 19))
        featured_label.place(x=10, y=10)

        def open_first_youtube_video():
            webbrowser.open('https://www.youtube.com/watch?v=J212vz33gU4')

        thumbnail_path_first = r"dashboardimgs\0.jpg"
        img_first = Image.open(thumbnail_path_first)
        img_first = img_first.resize((350, 196))
        photoImg_first = ImageTk.PhotoImage(img_first)
        
        thumbnail_label_first = Label(featured_workouts_frame, image=photoImg_first, cursor="hand2")
        thumbnail_label_first.image = photoImg_first
        thumbnail_label_first.place(x=10, y=40)
        thumbnail_label_first.bind("<Button-1>", lambda e: open_first_youtube_video())

        def open_second_youtube_video():
            webbrowser.open('https://www.youtube.com/watch?v=vr0g1-V6xec')

        thumbnail_path_second = r"dashboardimgs\1.jpg"
        img_second = Image.open(thumbnail_path_second)
        img_second = img_second.resize((350, 196))
        photoImg_second = ImageTk.PhotoImage(img_second)
        
        thumbnail_label_second = Label(featured_workouts_frame, image=photoImg_second, cursor="hand2")
        thumbnail_label_second.image = photoImg_second
        thumbnail_label_second.place(x=380, y=40)
        thumbnail_label_second.bind("<Button-1>", lambda e: open_second_youtube_video())

        def open_third_youtube_video():
            webbrowser.open('https://www.youtube.com/watch?v=sTANio_2E0Q')

        thumbnail_path_third = r"dashboardimgs\2.jpg"
        img_third = Image.open(thumbnail_path_third)
        img_third = img_third.resize((350, 196))
        photoImg_third = ImageTk.PhotoImage(img_third)
        
        thumbnail_label_third = Label(featured_workouts_frame, image=photoImg_third, cursor="hand2")
        thumbnail_label_third.image = photoImg_third
        thumbnail_label_third.place(x=755, y=40)
        thumbnail_label_third.bind("<Button-1>", lambda e: open_third_youtube_video())


        featured_meals_frame = customtkinter.CTkFrame(Frame15, width=1120, height=280, corner_radius=0)
        featured_meals_frame.place(x=0, y=480)
        featured_meals_label = customtkinter.CTkLabel(featured_meals_frame, text="Featured Meals:", font=('Impact', 19))
        featured_meals_label.place(x=10, y=10)

        def open_first_meal_video():
            webbrowser.open('https://www.youtube.com/watch?v=1N6hbRbyAeQ')

        meal_thumbnail_path_first = r"dashboardimgs\meal1.jpg"
        img_meal_first = Image.open(meal_thumbnail_path_first)
        img_meal_first = img_meal_first.resize((350, 196))
        photoImg_meal_first = ImageTk.PhotoImage(img_meal_first)
        
        thumbnail_meal_label_first = Label(featured_meals_frame, image=photoImg_meal_first, cursor="hand2")
        thumbnail_meal_label_first.image = photoImg_meal_first
        thumbnail_meal_label_first.place(x=10, y=40)
        thumbnail_meal_label_first.bind("<Button-1>", lambda e: open_first_meal_video())

        def open_second_meal_video():
            webbrowser.open('https://www.youtube.com/watch?v=_f4ArgoSmoM')

        meal_thumbnail_path_second = r"dashboardimgs\meal2.jpg"
        img_meal_second = Image.open(meal_thumbnail_path_second)
        img_meal_second = img_meal_second.resize((350, 196))
        photoImg_meal_second = ImageTk.PhotoImage(img_meal_second)
        
        thumbnail_meal_label_second = Label(featured_meals_frame, image=photoImg_meal_second, cursor="hand2")
        thumbnail_meal_label_second.image = photoImg_meal_second
        thumbnail_meal_label_second.place(x=380, y=40)
        thumbnail_meal_label_second.bind("<Button-1>", lambda e: open_second_meal_video())

        def open_third_meal_video():
            webbrowser.open('https://www.youtube.com/watch?v=LzWb_P4lYgA')

        meal_thumbnail_path_third = r"dashboardimgs\meal3.jpg"
        img_meal_third = Image.open(meal_thumbnail_path_third)
        img_meal_third = img_meal_third.resize((350, 196))
        photoImg_meal_third = ImageTk.PhotoImage(img_meal_third)
        
        thumbnail_meal_label_third = Label(featured_meals_frame, image=photoImg_meal_third, cursor="hand2")
        thumbnail_meal_label_third.image = photoImg_meal_third
        thumbnail_meal_label_third.place(x=755, y=40)
        thumbnail_meal_label_third.bind("<Button-1>", lambda e: open_third_meal_video())
    update_dashboard_section()


    def update_meals_section():
        for widget in MealsFrame.winfo_children():
            widget.destroy()
        MealsFrame.lift()
        MealsTitle = customtkinter.CTkLabel(
        master=MealsFrame,
        font=customtkinter.CTkFont(
            'impact',
            size=35),
        text='Meals',
        bg_color='#3c3c3c')
        MealsTitle.place(x=510, y=16)

        back_button = customtkinter.CTkButton(MealsFrame, text="Back", command=MealToNutrition, fg_color="black", hover_color="grey", font=button_font, width=30)
        back_button.place(x=1050, y=16)

        xy_frame = CTkXYFrame(MealsFrame, width=1075, height=700)
        xy_frame.place(x=15, y=75)
        descriptionFont = ("Calibri", 18)

        def open_first_link():
            webbrowser.open('https://www.bbcgoodfood.com/recipes/chicken-satay-salad')

        thumbnail_path_first = r"mealimages\meal1.jpeg"
        img_first = Image.open(thumbnail_path_first)
        img_first = img_first.resize((350, 196))
        photoImg_first = ImageTk.PhotoImage(img_first)
        
        thumbnail_label_first = Label(xy_frame, image=photoImg_first, cursor="hand2")
        thumbnail_label_first.image = photoImg_first
        thumbnail_label_first.grid(row=0, column=0, padx=5, pady=20)
        thumbnail_label_first.bind("<Button-1>", lambda e: open_first_link())

        # Description for the first meal
        description_first = "Try this no-fuss, midweek meal that's high in protein and big on flavour. Marinate chicken breasts, then drizzle with a punchy peanut satay sauce"
        description_label_first = customtkinter.CTkLabel(master=xy_frame, text=description_first, wraplength=500, font=descriptionFont)
        description_label_first.grid(row=0, column=1, padx=15, pady=0)


        def open_second_link():
            webbrowser.open('https://www.bbcgoodfood.com/recipes/double-bean-roasted-pepper-chilli')

        thumbnail_path_second = r"mealimages\meal2.jpeg"  # Second thumbnail path
        img_second = Image.open(thumbnail_path_second)
        img_second = img_second.resize((350, 196))
        photoImg_second = ImageTk.PhotoImage(img_second)
        
        thumbnail_label_second = Label(xy_frame, image=photoImg_second, cursor="hand2")
        thumbnail_label_second.image = photoImg_second
        thumbnail_label_second.grid(row=1, column=0, padx=5, pady=20)  # Adjusted x position to place it to the right of the first thumbnail
        thumbnail_label_second.bind("<Button-1>", lambda e: open_second_link())

        # Description for the second meal
        description_second = "This warming vegetarian chilli is a low-fat, healthy option that packs in the veggies and flavour. Serve with Tabasco sauce, soured cream or yoghurt."
        description_label_second = customtkinter.CTkLabel(master=xy_frame, text=description_second, wraplength=500, font=descriptionFont)
        description_label_second.grid(row=1, column=1, padx=5, pady=20)

        def open_third_link():
            webbrowser.open('https://www.bbcgoodfood.com/recipes/chicken-noodle-soup')


        thumbnail_path_third = r"mealimages\meal3.jpeg" 
        img_third = Image.open(thumbnail_path_third)
        img_third = img_third.resize((350, 196))
        photoImg_third = ImageTk.PhotoImage(img_third)
        
        thumbnail_label_third = Label(xy_frame, image=photoImg_third, cursor="hand2")
        thumbnail_label_third.image = photoImg_third
        thumbnail_label_third.grid(row=2, column=0, padx=5, pady=20)
        thumbnail_label_third.bind("<Button-1>", lambda e: open_third_link())

        # Description for the third meal
        description_third = "Mary Cadogan's aromatic broth will warm you up on a winter's evening - it contains ginger, which is particularly good for colds."
        description_label_third = customtkinter.CTkLabel(master=xy_frame, text=description_third, wraplength=500, font=descriptionFont)
        description_label_third.grid(row=2, column=1, padx=5, pady=20)


        def open_fourth_link():
            webbrowser.open('https://www.bbcgoodfood.com/recipes/classic-waffles')


        thumbnail_path_fourth = r"mealimages\meal4.jpeg" 
        img_fourth = Image.open(thumbnail_path_fourth)
        img_fourth = img_fourth.resize((350, 196))
        photoImg_fourth = ImageTk.PhotoImage(img_fourth)
        
        thumbnail_label_fourth = Label(xy_frame, image=photoImg_fourth, cursor="hand2")
        thumbnail_label_fourth.image = photoImg_fourth
        thumbnail_label_fourth.grid(row=3, column=0, padx=5, pady=20) 
        thumbnail_label_fourth.bind("<Button-1>", lambda e: open_fourth_link())

        # Description for the fourth meal
        description_fourth = "Make savoury or sweet waffles using this all-in-one batter mix. For even lighter waffles, whisk the egg white until fluffy, then fold through the batter"
        description_label_fourth = customtkinter.CTkLabel(master=xy_frame, text=description_fourth, wraplength=500, font=descriptionFont)
        description_label_fourth.grid(row=3, column=1, padx=5, pady=20)


        def open_fifth_link():
            webbrowser.open('https://www.bbcgoodfood.com/recipes/oat-biscuits-0')


        thumbnail_path_fifth = r"mealimages\meal5.jpeg" 
        img_fifth = Image.open(thumbnail_path_fifth)
        img_fifth = img_fifth.resize((350, 196))
        photoImg_fifth = ImageTk.PhotoImage(img_fifth)
        
        thumbnail_label_fifth = Label(xy_frame, image=photoImg_fifth, cursor="hand2")
        thumbnail_label_fifth.image = photoImg_fifth
        thumbnail_label_fifth.grid(row=4, column=0, padx=5, pady=20)  
        thumbnail_label_fifth.bind("<Button-1>", lambda e: open_fifth_link())

        # Description for the fifth meal
        description_fifth = "Nothing beats homemade cookies - make these easy oat biscuits for a sweet treat during the day when you need a break. They're perfect served with a cuppa"
        description_label_fifth = customtkinter.CTkLabel(master=xy_frame, text=description_fifth, wraplength=500, font=descriptionFont)
        description_label_fifth.grid(row=4, column=1, padx=5, pady=20)


        def open_sixth_link():
            webbrowser.open('https://www.bbcgoodfood.com/recipes/protein-balls')


        thumbnail_path_sixth = r"mealimages\meal6.jpeg" 
        img_sixth = Image.open(thumbnail_path_sixth)
        img_sixth = img_sixth.resize((350, 196))
        photoImg_sixth = ImageTk.PhotoImage(img_sixth)
        
        thumbnail_label_sixth = Label(xy_frame, image=photoImg_sixth, cursor="hand2")
        thumbnail_label_sixth.image = photoImg_sixth
        thumbnail_label_sixth.grid(row=5, column=0, padx=5, pady=20) 
        thumbnail_label_sixth.bind("<Button-1>", lambda e: open_sixth_link())

        # Description for the sixth meal
        description_sixth = "Make tasty protein balls using oats, protein powder, flaxseed and cinnamon to enjoy post-exercise and replenish your protein"
        description_label_sixth = customtkinter.CTkLabel(master=xy_frame, text=description_sixth, wraplength=500, font=descriptionFont)
        description_label_sixth.grid(row=5, column=1, padx=5, pady=20)


        def open_seventh_link():
            webbrowser.open('https://www.bbcgoodfood.com/recipes/creamy-salmon-pasta')


        thumbnail_path_seventh = r"mealimages\meal7.jpeg"
        img_seventh = Image.open(thumbnail_path_seventh)
        img_seventh = img_seventh.resize((350, 196))
        photoImg_seventh = ImageTk.PhotoImage(img_seventh)
        
        thumbnail_label_seventh = Label(xy_frame, image=photoImg_seventh, cursor="hand2")
        thumbnail_label_seventh.image = photoImg_seventh
        thumbnail_label_seventh.grid(row=6, column=0, padx=5, pady=20)
        thumbnail_label_seventh.bind("<Button-1>", lambda e: open_seventh_link())

        # Description for the seventh meal
        description_seventh = "Indulge in this creamy salmon dish for two. It's comforting and filling, and ready in just 30 minutes. Serve with a green salad"
        description_label_seventh = customtkinter.CTkLabel(master=xy_frame, text=description_seventh, wraplength=500, font=descriptionFont)
        description_label_seventh.grid(row=6, column=1, padx=5, pady=20)
    update_meals_section()

    global update_calorie_counter_section
    def update_calorie_counter_section():
        global current_username
        current_username = user_var.get()
        for widget in CalorieCounter_Frame.winfo_children():
            widget.destroy()
        CalorieCounter_Frame.lift()

        calorieTitle = customtkinter.CTkLabel(
            master=CalorieCounter_Frame,
            font=customtkinter.CTkFont('impact', size=35),
            text='Calorie Counter',
            bg_color='#3c3c3c')
        calorieTitle.place(x=450, y=16)

        back_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Back", command=CalorieToNutrition, fg_color="black", hover_color="grey", font=button_font, width=30)
        back_button.place(x=1050, y=16)

        adjustcalorie_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Adjust calorie limit", command=lambda: open_calorie_settings(), fg_color="black", hover_color="grey", font=button_font, width=200)
        adjustcalorie_button.place(x=900, y=80)

        global items
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
        {"name": "Tofu (100g)", "calories": 76, "fat": 4.8, "carbs": 1.9, "protein": 8, "sugars": 0.3}]

        # Extracting item names for the dropdown
        item_names = [item["name"] for item in items]

        button = customtkinter.CTkButton(CalorieCounter_Frame, text="Choose food item", width=400, fg_color="black", hover_color="grey", font=("Impact", 17))
        button.place(x=360, y=400)

        # Function to handle item selection
        def on_select(e):
            global selected_food
            selected_food = e
            button.configure(text=e)  # Also update the button text with the selected item

        CTkScrollableDropdown(button, values=item_names, height=200, resize=False, button_height=50,
                            scrollbar=True, command=on_select)

        # Displaying today's calorie intake and remaining calories
        daily_calorie_limit = get_user_calorie_limit(current_username)
        daily_calorie_intake = get_user_calorie_intake(current_username)
        remaining_calories = daily_calorie_limit - daily_calorie_intake
        intake_label = customtkinter.CTkLabel(CalorieCounter_Frame, text=f"Today's Calorie Intake: {daily_calorie_intake} kcal", font=("Impact", 20), bg_color='#3c3c3c')
        intake_label.place(x=290, y=170)
        remaining_label = customtkinter.CTkLabel(CalorieCounter_Frame, text=f"Remaining Calories: {remaining_calories} kcal", font=("Impact", 20), bg_color='#3c3c3c')
        remaining_label.place(x=590, y=170)

        # Fetch current nutrition data from the database
        conn = sqlite3.connect('fitplus.db')
        c = conn.cursor()
        c.execute("SELECT daily_fat, daily_carbs, daily_protein, daily_sugars FROM users WHERE username = ?", (current_username,))
        result = c.fetchone()
        conn.close()

        if result:
                daily_fat, daily_carbs, daily_protein, daily_sugars = result
        else:
                daily_fat, daily_carbs, daily_protein, daily_sugars = 0, 0, 0, 0, 0

        # Labels for displaying daily intake of calories, fats, carbs, proteins, and sugars
        labels = [
            ("Fats", daily_fat, "g"),
            ("Carbohydrates", daily_carbs, "g"),
            ("Proteins", daily_protein, "g"),
            ("Sugars", daily_sugars, "g")
        ]

        y_pos = 220  # Initial y position for the first label
        for label_text, value, unit in labels:
            label = customtkinter.CTkLabel(CalorieCounter_Frame, text=f"{label_text}: {value} {unit}", font=("Impact", 18), bg_color='#3c3c3c')
            label.place(x=290, y=y_pos)
            y_pos += 35  # Increment y position for the next label

        def reset_function():
                reset_daily_calorie_intake(current_username)  # Reset daily calorie intake to 0
                reset_nutrition(current_username)
                update_calorie_counter_section()  # Refresh calorie counter display
        
        reset_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Reset", command=lambda: reset_function(), fg_color="black", hover_color="grey", font=button_font, width=200)
        reset_button.place(x=900, y=120)

        add_button = customtkinter.CTkButton(CalorieCounter_Frame, text="Add", fg_color="black", hover_color="grey", font=button_font, command=lambda: add_food_to_intake(selected_food))
        add_button.place(x=490, y=450)
    update_calorie_counter_section()


    def update_settings_section():
        # Initialization for pygame to handle music playback
        pygame.mixer.init()
        pygame.mixer.music.load("soundtrack.mp3")
        pygame.mixer.music.set_volume(0.05)
        pygame.mixer.music.play(-1)  # loops the music playback
        
        # Function to toggle music playback
        global toggle_music
        def toggle_music():
            if musicCheckBox.get() == 1:  # If the checkbox is checked
                pygame.mixer.music.unpause()  # Resume the music
            else:
                pygame.mixer.music.pause()  # Pause the music

        musicCheckBox = customtkinter.CTkCheckBox(
            master=settingsPage,
            font=customtkinter.CTkFont('impact', size=20),
            height=0,
            corner_radius=30,
            text='Music',
            fg_color='#000000',
            bg_color='#3c3c3c',
            hover_color='#1a1a1a',
            command=toggle_music,
            variable=tkinter.IntVar(value=1)  # Checkbox is checked by default
        )
        musicCheckBox.place(x=802, y=373)

        SettingsTitle = customtkinter.CTkLabel(
        master=settingsPage,
        font=customtkinter.CTkFont(
            'impact',
            size=35),
        text='Settings',
        bg_color='#3c3c3c')
        SettingsTitle.place(x=783, y=16)

        Label1 = customtkinter.CTkLabel(
        master=settingsPage,
        font=customtkinter.CTkFont(
            'Impact',
            size=28,
            underline=1),
        text='Your account',
        bg_color='#3c3c3c')
        Label1.place(x=766, y=107)

        def logout():
            # Hide the main app frame
            mainapp.pack_forget()
            
            # reset the user input fields
            user_var.set("")
            pass_var.set("")
            
            # Show the initial app screen (login screen)
            frame.pack(expand=True)
            particle_frame.pack(expand=True, fill="both")

        logoutButton = customtkinter.CTkButton(
            master=settingsPage,
            font=customtkinter.CTkFont('impact', size=19),
            width=133,
            height=50,
            corner_radius=25,
            text='Log Out',
            fg_color='#000000',
            bg_color='#3c3c3c',
            hover_color='#1b1b1b',
            command=logout
        )
        logoutButton.place(x=775, y=686)

        Label2 = customtkinter.CTkLabel(
            master=settingsPage,
            font=customtkinter.CTkFont(
                'Impact',
                size=28,
                underline=1),
            text='Miscellaneous',
            bg_color='#3c3c3c')
        Label2.place(x=760, y=321)

        def confirmDelete():
            confirmdelete = CTkMessagebox(title="Delete Account", message="Are you sure you want to delete your account?", icon="warning", justify=CENTER, button_color="black", button_hover_color="grey", option_1= "Yes", option_2= "No")
            response = confirmdelete.get()
            if response=="Yes":
                delete_account()       

        DeleteAccButton = customtkinter.CTkButton(
            master=settingsPage,
            font=customtkinter.CTkFont(
                'impact',
                size=17),
            width=238,
            height=52,
            corner_radius=26,
            text='Delete Account',
            fg_color='#000000',
            bg_color='#3c3c3c',
            command=confirmDelete,
            hover_color='#1a1a1a')
        DeleteAccButton.place(x=723, y=162)
    update_settings_section()
    toggle_music()

    def update_progress_section():
        # Fetch user's weight details and PRs from the database
        conn = sqlite3.connect('fitplus.db')
        c = conn.cursor()
        c.execute("""
            SELECT current_weight, ideal_weight, bench_press_pr, squat_pr, deadlift_pr
            FROM users WHERE username = ?
        """, (current_username,))
        result = c.fetchone()
        conn.close()

        # Function called when "Update current weight" button is clicked
        def on_update_current_weight_click():
            new_weight = simpledialog.askfloat("Update Current Weight", "Enter your new current weight (kg):")
            if new_weight is not None:
                update_current_weight(current_username, new_weight)
            weightFrame.destroy()
            update_progress_section()

        # Function called when "Update ideal weight" button is clicked
        def on_update_ideal_weight_click():
            new_weight = simpledialog.askfloat("Update Ideal Weight", "Enter your new ideal weight (kg):")
            if new_weight is not None:
                update_ideal_weight(current_username, new_weight)
            weightFrame.destroy()
            update_progress_section()
        
        def on_update_bench_press_click():
            new_pr = simpledialog.askfloat("Update Bench Press PR", "Enter your new Bench Press PR (kg):")
            if new_pr is not None:
                update_bench_press_pr(current_username, new_pr)
                prFrame.destroy()
                update_progress_section()
        
        def on_update_squat_click():
            new_pr = simpledialog.askfloat("Update Squat PR", "Enter your new Squat PR (kg):")
            if new_pr is not None:
                update_squat_pr(current_username, new_pr)
                prFrame.destroy()
                update_progress_section()

        def on_update_deadlift_click():
            new_pr = simpledialog.askfloat("Update Deadlift PR", "Enter your new Deadlift PR (kg):")
            if new_pr is not None:
                update_deadlift_pr(current_username, new_pr)
                prFrame.destroy()
                update_progress_section()

            
        current_weight, ideal_weight, bench_press_pr, squat_pr, deadlift_pr = result if result else (0, 0, 0, 0, 0)
        weight_difference = ideal_weight - current_weight
        
        achievementframe = CTkXYFrame(Frame9, width=1075, height=250)
        achievementframe.place(x=15, y=520)

        bench20frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        bench20frame.grid(row=0, column=0, padx=5, pady=20)
        bench40frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        bench40frame.grid(row=1, column=0, padx=5, pady=20)
        bench60frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        bench60frame.grid(row=2, column=0, padx=5, pady=20)
        bench80frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        bench80frame.grid(row=3, column=0, padx=5, pady=20)
        bench100frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        bench100frame.grid(row=4, column=0, padx=5, pady=20)

        squat20frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        squat20frame.grid(row=5, column=0, padx=5, pady=20)
        squat40frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        squat40frame.grid(row=6, column=0, padx=5, pady=20)
        squat60frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        squat60frame.grid(row=7, column=0, padx=5, pady=20)
        squat80frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        squat80frame.grid(row=8, column=0, padx=5, pady=20)
        squat100frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        squat100frame.grid(row=9, column=0, padx=5, pady=20)

        deadlift60frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        deadlift60frame.grid(row=10, column=0, padx=5, pady=20)
        deadlift80frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        deadlift80frame.grid(row=11, column=0, padx=5, pady=20)
        deadlift100frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        deadlift100frame.grid(row=12, column=0, padx=5, pady=20)
        deadlift120frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        deadlift120frame.grid(row=13, column=0, padx=5, pady=20)
        deadlift140frame = customtkinter.CTkFrame(achievementframe, width=1060, height=100)
        deadlift140frame.grid(row=14, column=0, padx=5, pady=20)

        def update_achievement_labels(frame, achievement_text, achieved, relx_position):
            # Static part of the label
            static_label = customtkinter.CTkLabel(master=frame, text=achievement_text, font=("Impact", 24))
            static_label.place(relx=relx_position, rely=0.5, anchor='e')

            # Dynamic status part of the label
            status = "Unlocked" if achieved else "Locked"
            status_color = "green" if achieved else "red"
            status_label = customtkinter.CTkLabel(master=frame, text=status, font=("Impact", 24), text_color=status_color)
            status_label.place(relx=relx_position, rely=0.5, anchor='w')

        bench20_achieved = bench_press_pr >= 20
        bench40_achieved = bench_press_pr >= 40
        bench60_achieved = bench_press_pr >= 60
        bench80_achieved = bench_press_pr >= 80
        bench100_achieved = bench_press_pr >= 100
        squat20_achieved = squat_pr >= 20
        squat40_achieved = squat_pr >= 40
        squat60_achieved = squat_pr >= 60
        squat80_achieved = squat_pr >= 80
        squat100_achieved = squat_pr >= 100
        deadlift60_achieved = deadlift_pr >= 60
        deadlift80_achieved = deadlift_pr >= 80
        deadlift100_achieved = deadlift_pr >= 100
        deadlift120_achieved = deadlift_pr >= 120
        deadlift140_achieved = deadlift_pr >= 140

        update_achievement_labels(bench20frame, "Reach a 20kg bench press: ", bench20_achieved, 0.3)
        update_achievement_labels(bench40frame, "Reach a 40kg bench press: ", bench40_achieved, 0.3)
        update_achievement_labels(bench60frame, "Reach a 60kg bench press: ", bench60_achieved, 0.3)
        update_achievement_labels(bench80frame, "Reach a 80kg bench press: ", bench80_achieved, 0.3)
        update_achievement_labels(bench100frame, "Reach a 100kg bench press: ", bench100_achieved, 0.3)
        update_achievement_labels(squat20frame, "Reach a 20kg squat: ", squat20_achieved, 0.3)
        update_achievement_labels(squat40frame, "Reach a 40kg squat: ", squat40_achieved, 0.3)
        update_achievement_labels(squat60frame, "Reach a 60kg squat: ", squat60_achieved, 0.3)
        update_achievement_labels(squat80frame, "Reach a 80kg squat: ", squat80_achieved, 0.3)
        update_achievement_labels(squat100frame, "Reach a 100kg squat: ", squat100_achieved, 0.3)
        update_achievement_labels(deadlift60frame, "Reach a 60kg deadlift: ", deadlift60_achieved, 0.3)
        update_achievement_labels(deadlift80frame, "Reach a 80kg deadlift: ", deadlift80_achieved, 0.3)
        update_achievement_labels(deadlift100frame, "Reach a 100kg deadlift: ", deadlift100_achieved, 0.3)
        update_achievement_labels(deadlift120frame, "Reach a 120kg deadlift: ", deadlift120_achieved, 0.3)
        update_achievement_labels(deadlift140frame, "Reach a 140kg deadlift: ", deadlift140_achieved, 0.3)

        weightFrame = customtkinter.CTkFrame(Frame9, width=450, height=300)
        weightFrame.place(x=63, y=120)
        WeightTitle = customtkinter.CTkLabel(master=weightFrame, text="Weight tracker", font=("Calibri", 18, 'underline'))
        WeightTitle.place(relx=0.5, rely=0.1, anchor='center')
        current_weight_label = customtkinter.CTkLabel(master=weightFrame, text=f"Current Weight: {current_weight} kg", font=("Calibri", 16))
        current_weight_label.place(relx=0.5, rely=0.3, anchor='center')
        ideal_weight_label = customtkinter.CTkLabel(master=weightFrame, text=f"Ideal Weight: {ideal_weight} kg", font=("Calibri", 16))
        ideal_weight_label.place(relx=0.5, rely=0.4, anchor='center')
        diff_text = "Weight to Gain: " if weight_difference > 0 else "Weight to Lose: "
        weight_diff_label = customtkinter.CTkLabel(master=weightFrame, text=f"{diff_text} {abs(weight_difference)} kg", font=("Calibri", 16))
        weight_diff_label.place(relx=0.5, rely=0.5, anchor='center')
        UpdateCurrentWeight = customtkinter.CTkButton(weightFrame, text="Update current weight", width=180, fg_color="black", hover_color="grey", font=("Impact", 16), command=on_update_current_weight_click)
        UpdateCurrentWeight.place(relx=0.25, rely=0.75, anchor='center')
        UpdateIdealWeight = customtkinter.CTkButton(weightFrame, text="Update ideal weight", width=180, fg_color="black", hover_color="grey", font=("Impact", 16), command=on_update_ideal_weight_click)
        UpdateIdealWeight.place(relx=0.75, rely=0.75, anchor='center')

        prFrame = customtkinter.CTkFrame(Frame9, width=450, height=300)
        prFrame.place(x=606, y=120)
        prTitle = customtkinter.CTkLabel(master=prFrame, text="Personal Record Tracker", font=("Calibri", 18, 'underline'))
        prTitle.place(relx=0.5, rely=0.1, anchor='center')
        bench_pr_label = customtkinter.CTkLabel(master=prFrame, text=f"Bench Press PR: {bench_press_pr} kg", font=("Calibri", 16))
        bench_pr_label.place(relx=0.5, rely=0.3, anchor='center')
        squat_pr_label = customtkinter.CTkLabel(master=prFrame, text=f"Squat PR: {squat_pr} kg", font=("Calibri", 16))
        squat_pr_label.place(relx=0.5, rely=0.4, anchor='center')
        deadlift_pr_label = customtkinter.CTkLabel(master=prFrame, text=f"Deadlift PR: {deadlift_pr} kg", font=("Calibri", 16))
        deadlift_pr_label.place(relx=0.5, rely=0.5, anchor='center')
        UpdateBench = customtkinter.CTkButton(prFrame, text="Update Bench Press", width=143, fg_color="black", hover_color="grey", font=("Impact", 16), command=on_update_bench_press_click)
        UpdateBench.place(relx=0.5, rely=0.75, anchor='center')
        UpdatesSquat = customtkinter.CTkButton(prFrame, text="Update Squat", width=140, fg_color="black", hover_color="grey", font=("Impact", 16), command=on_update_squat_click)
        UpdatesSquat.place(relx=0.17, rely=0.75, anchor='center')
        UpdateDeadlift = customtkinter.CTkButton(prFrame, text="Update Deadlift", width=140, fg_color="black", hover_color="grey", font=("Impact", 16), command=on_update_deadlift_click)
        UpdateDeadlift.place(relx=0.83, rely=0.75, anchor='center')


        achievementTitle = customtkinter.CTkLabel(master=Frame9, text="Achievements", font=("Impact", 20))
        achievementTitle.place(relx = 0.5, rely = 0.62, anchor='center')
    update_progress_section()
app.mainloop()