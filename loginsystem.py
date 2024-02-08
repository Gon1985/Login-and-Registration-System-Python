import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import sqlite3
from datetime import datetime
import re
import secrets
import pygame
import os
from PIL import Image, ImageTk
import time
import tkinter.filedialog as filedialog
import tkinter.font as tkFont
import calendar
import datetime
import datetime as dt




pygame.mixer.init()


def play_sound(sound_file):
    pygame.mixer.music.load(os.path.join("sounds", sound_file))
    pygame.mixer.music.play()


play_sound("welcome.mp3")  


def validate_password(password):
    if re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$', password):
        return True
    else:
        return False
    


def validate_email(email):
    
    if re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email) and '.' in email and '@' in email:
        return True
    else:
        return False



def check_and_validate_email(email):
    
    if not email.strip():
        messagebox.showerror("Error", "Please enter a valid email address.")
        
        play_sound("invalidemail.mp3")
        return False
   
    elif not validate_email(email):
        messagebox.showerror("Error", "Please enter a valid email address.")
        
        play_sound("invalidemail.mp3")
        return False
    else:
        return True
    



def generate_token():
    return secrets.token_hex(5) 


db_file_path = 'user_database.db'


if not os.path.exists(db_file_path):
    print("The database does not exist. Creating a new base...")
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            token TEXT NOT NULL,
            registration_date TEXT NOT NULL,
            login_attempts INTEGER DEFAULT 0,
            blocked INTEGER DEFAULT 0
        )
    ''')

    
    cursor.execute("PRAGMA table_info(users_backup)")
    if not cursor.fetchall():
        
        cursor.execute('''
            CREATE TABLE users_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                token TEXT NOT NULL,
                registration_date TEXT NOT NULL,
                login_attempts INTEGER DEFAULT 0,
                blocked INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

    
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("INSERT INTO users_backup SELECT id, username, '', '', token, registration_date, login_attempts, blocked FROM users")
        cursor.execute("DROP TABLE users")
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, email TEXT NOT NULL, password TEXT NOT NULL, token TEXT NOT NULL, registration_date TEXT NOT NULL, login_attempts INTEGER DEFAULT 0, blocked INTEGER DEFAULT 0)")
    cursor.execute("INSERT INTO users SELECT id, username, email, '', token, registration_date, login_attempts, blocked FROM users_backup")
    cursor.execute("DROP TABLE users_backup")

    conn.commit()
    conn.close()


conn = sqlite3.connect(db_file_path)
cursor = conn.cursor()


def register_user():
    username = entry_username.get()
    email = entry_email.get()
    password = entry_password.get()

    
    if not username:
        messagebox.showerror("Error", "Please complete the username.")
        play_sound("completetheusername.mp3")
        return

    
    if not email:
        messagebox.showerror("Error", "Please complete the email.")
        play_sound("pleasecompleteemail.mp3")
        return
    elif not validate_email(email):
        messagebox.showerror("Error", "Please enter a valid email address.")
        play_sound("invalidemail.mp3")
        return

    
    if not password:
        messagebox.showerror("Error", "Please complete the password.")
        play_sound("pleasecompletepassword.mp3")
        return

    
    if not validate_password(password):
        error_sound = pygame.mixer.Sound("sounds/passwordexplanation.mp3")
        error_sound.play()
        messagebox.showerror("Error", "Password must contain at least one uppercase letter, one lowercase letter, one digit, and one special character.")
        return

    
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        messagebox.showerror("Error", "Username already in use.")
        play_sound("usernamealreadyinuse.mp3")
    else:
        
        token = generate_token()

        
        current_time = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        cursor.execute("INSERT INTO users (username, email, password, token, registration_date) VALUES (?, ?, ?, ?, ?)",
                   (username, email, password, token, current_time))
        conn.commit()
        messagebox.showinfo("Successful Registration", "User registered successfully. Token: {}".format(token))
        play_sound("usercreation.mp3")  

        


def log_in():
    if not entry_username.get() or not entry_email.get() or not entry_password.get():
        messagebox.showerror("Error", "Please complete all required fields.")
        play_sound("pleasecompleteall.mp3")
        return

    username = entry_username.get()
    email = entry_email.get()
    password = entry_password.get()

    cursor.execute("SELECT blocked FROM users WHERE username=? AND email=? AND password=?", (username, email, password))
    result = cursor.fetchone()
    if result:
        blocked = result[0]
        if blocked:
            messagebox.showinfo("User Blocked", "Your account is blocked. Please contact the administrator.")
            play_sound("userblocked.mp3")
            return  
        else:
            messagebox.showinfo("Success", "Login successful!")
            play_sound("loginsuccess.mp3")
            
            return
    else:
        messagebox.showinfo("User Not Found", "User not registered.")
        play_sound("usernotfound.mp3")
        


def confirm_exit():
    result = messagebox.askquestion("Exit Confirmation", "Are you sure you want to close the application?")
    if result == "yes":
        play_sound("exit.mp3")
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10) 
        root.destroy()
        
    
    



def refresh_user_list():
    user_tree.delete(*user_tree.get_children())
    cursor.execute("SELECT username, email, blocked FROM users")
    users = cursor.fetchall()
    for user in users:
        user_tree.insert("", "end", values=user)


def block_user():
    selected_item = user_tree.selection()
    if selected_item:
        username = user_tree.item(selected_item, "values")[0]
        cursor.execute("UPDATE users SET blocked=1 WHERE username=?", (username,))
        conn.commit()
        refresh_user_list()  
        play_sound("userblock.mp3")
        messagebox.showinfo("User Blocked", f"User {username} has been blocked.")



admin_window_open = False

def admin_override():
    global admin_window, admin_window_open, user_tree 

    if admin_window_open:
        messagebox.showinfo("Admin Window", "Admin window is already open.")
        return

    password = simpledialog.askstring("Admin Override", "Enter password:")
    if password == "admin admin":

        play_sound("adminaccess.mp3")

        admin_window = tk.Toplevel(root)
        admin_window.title("Admin Access")
        admin_window.iconbitmap("images/icon.ico")

        admin_window_open = True

        def on_admin_window_close():
            global admin_window_open
            admin_window_open = False
            admin_window.destroy()

        admin_window.protocol("WM_DELETE_WINDOW", on_admin_window_close)

        user_tree = ttk.Treeview(admin_window, columns=("Username", "Email", "Blocked"), show="headings")
        user_tree.heading("Username", text="Username")
        user_tree.heading("Email", text="Email")
        user_tree.heading("Blocked", text="Blocked")

        cursor.execute("SELECT username, email, blocked FROM users")
        users = cursor.fetchall()
        for user in users:
            user_tree.insert("", "end", values=user)

        user_tree.pack(padx=10, pady=10)

        block_button = tk.Button(admin_window, text="Block User", command=block_user, bg="#086105", fg="white")
        block_button.pack(pady=10)

        def unblock_user():
            selected_item = user_tree.selection()
            if selected_item:
                username = user_tree.item(selected_item, "values")[0]
                cursor.execute("UPDATE users SET blocked=0 WHERE username=?", (username,))
                conn.commit()
                refresh_user_list()
                play_sound("userunblocked.mp3")
                messagebox.showinfo("User Unblocked", f"User {username} has been unblocked.")

        unblock_button = tk.Button(admin_window, text="Unblock User", command=unblock_user, bg="#086105", fg="white")
        unblock_button.pack(pady=10)

        def delete_user():
            selected_item = user_tree.selection()
            if selected_item:
                username = user_tree.item(selected_item, "values")[0]
                cursor.execute("DELETE FROM users WHERE username=?", (username,))
                conn.commit()
                refresh_user_list()
                play_sound("userdeleted.mp3")
                messagebox.showinfo("User Deleted", f"User {username} has been deleted.")

        delete_button = tk.Button(admin_window, text="Delete User", command=delete_user, bg="#086105", fg="white")
        delete_button.pack(pady=10)
    else:
        messagebox.showerror("Error", "Incorrect password.")
    
    
    
help_window = None
    

def show_help():
    
    global help_window

    
    if help_window and help_window.winfo_exists():
        return

    
    help_window_open[0] = True

    
    def close_help():
        global help_window
        if help_window and help_window.winfo_exists():
            help_window.destroy()
            pygame.mixer.music.stop()
            help_window = None 


    global help_bg_image 

    
    help_window = tk.Toplevel(root)
    help_window.title("Help")
    help_window.geometry("300x400")  
    help_window.resizable(False, False)  
    
    help_window.iconbitmap("images/icon.ico")
    

   
    help_img_path = "images/backgroundhelp.png" 
    if os.path.exists(help_img_path):
        img = Image.open(help_img_path)
        help_bg_image = ImageTk.PhotoImage(img)
        help_bg_label = tk.Label(help_window, image=help_bg_image)
        help_bg_label.place(relwidth=1, relheight=1)  

    
    play_sound("help.mp3")  
    

    help_window.protocol("WM_DELETE_WINDOW", close_help)


help_window_open = [False]
help_bg_image = None  



def validate_and_open_workspace():
    username = entry_username.get()
    email = entry_email.get()
    password = entry_password.get()

    if not username or not email or not password:
        messagebox.showerror("Error", "Please complete all required fields.")
        play_sound("pleasecompleteall.mp3")
        return

    cursor.execute("SELECT * FROM users WHERE username=? AND email=? AND password=?", (username, email, password))
    user = cursor.fetchone()
    if user:
        if user[7] == 1:  
            messagebox.showinfo("User Blocked", "Your account is blocked. Please contact the administrator.")
            play_sound("userblocked.mp3")
        else:
            open_user_workspace()
    else:
        messagebox.showinfo("User Not Found", "User not registered.")
        play_sound("usernotfound.mp3")


text_area = None        


workspace_window = None  

def open_user_workspace():
    global workspace_window, text_area 
    
    
    if workspace_window and workspace_window.winfo_exists():
        
        workspace_window.lift()
        return

    workspace_window = tk.Toplevel(root)
    workspace_window.title("User Workspace")
    workspace_window.geometry("800x600") 
    workspace_window.resizable(False, False)  
    
    workspace_window.iconbitmap("images/icon.ico")

    
    workspace_img_path = "images/background4.png"  
    if os.path.exists(workspace_img_path):
        workspace_img = Image.open(workspace_img_path)
        global workspace_bg_image
        workspace_bg_image = ImageTk.PhotoImage(workspace_img)
        workspace_bg_label = tk.Label(workspace_window, image=workspace_bg_image)
        workspace_bg_label.place(relwidth=1, relheight=1)  

    
    text_area = tk.Text(workspace_window, wrap="word", highlightthickness=0, borderwidth=0, fg='#09ff00', font=('pixelmix', 10))
    text_area.configure(bg='#086105', insertbackground='#19fffb', selectbackground='#19fffb')
    text_area.pack(expand=True, fill="both", padx=20, pady=20)
    
    
    play_sound("workspaceentry.mp3")  


    menu_bar = tk.Menu(workspace_window)
    workspace_window.config(menu=menu_bar)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)

   
    def new_file():
        
        pass

    
    def load_file():
        file_path = filedialog.askopenfilename(title="Open File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                
                with open(file_path, "r", encoding="utf-8") as file:
                    file_content = file.read()

                
                text_area.delete("1.0", tk.END)

                
                text_area.insert("1.0", file_content)

                messagebox.showinfo("Load Successful", "File loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while loading the file: {e}")

    
    def save_file():
        file_path = filedialog.asksaveasfilename(title="Save File", defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            try:
                
                text_content = text_area.get("1.0", tk.END)

                
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(text_content)

                messagebox.showinfo("Save Successful", "File saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while saving the file: {e}")

    
    def show_user_token():
        
        username = entry_username.get()
        email = entry_email.get()
        password = entry_password.get()
        
        
      
        if not username or not email or not password:
            messagebox.showerror("Error", "Please complete all required fields.")
            play_sound("pleasecompleteall.mp3")
            return

    
        cursor.execute("SELECT token FROM users WHERE username=? AND email=? AND password=?", (username, email, password))
        user_data = cursor.fetchone()

        if user_data:
            user_token = user_data[0]
            messagebox.showinfo("User Token", f"Your token is: {user_token}")
        else:
            messagebox.showinfo("User Not Found", "User not registered.")
            play_sound("usernotfound.mp3")  
        

    file_menu.add_command(label="New File", command=new_file)
    file_menu.add_command(label="Load File", command=load_file)
    file_menu.add_command(label="Save File", command=save_file)
    file_menu.add_command(label="Show User Token", command=show_user_token)
    file_menu.add_command(label="Exit", command=workspace_window.destroy)

    
    workspace_window.protocol("WM_DELETE_WINDOW", on_workspace_close)


def on_workspace_close():
    global workspace_window
    
    workspace_window.destroy()




root = tk.Tk()
root.title("Login and Registration System")
root.geometry("500x380")  


icon_path = "images/icon.ico"



if os.path.exists(icon_path):
    
    root.iconbitmap(icon_path)



img_path = "images/background1.png"
if os.path.exists(img_path):
    img = Image.open(img_path)
    bg_image = ImageTk.PhotoImage(img)
    bg_label = tk.Label(root, image=bg_image)
    bg_label.place(relwidth=1, relheight=1)


root.resizable(False, False)

label_username = tk.Label(root, text="Username:")
label_username.grid(row=0, column=0, padx=10, pady=5, sticky="e")


label_username = tk.Label(root, text="Username:")
label_username.grid(row=0, column=0, padx=10, pady=5, sticky="e")
entry_username = tk.Entry(root)
entry_username.grid(row=0, column=1, padx=10, pady=5, sticky="w")


label_email = tk.Label(root, text="Email:")
label_email.grid(row=1, column=0, padx=10, pady=5, sticky="e")
entry_email = tk.Entry(root)
entry_email.grid(row=1, column=1, padx=10, pady=5, sticky="w")

label_password = tk.Label(root, text="Password:")
label_password.grid(row=2, column=0, padx=10, pady=5, sticky="e")
entry_password = tk.Entry(root, show="*")
entry_password.grid(row=2, column=1, padx=10, pady=5, sticky="w")


button_color = "#09ff00"
button_text_color = "white"

btn_register = tk.Button(root, text="Create User", command=register_user, bg="#086105", fg="#FFFFFF")
btn_register.grid(row=3, column=0, columnspan=2, pady=5)


btn_log_in = tk.Button(root, text="Log In", command=validate_and_open_workspace, bg="#086105", fg="#FFFFFF")
btn_log_in.grid(row=4, column=0, columnspan=2, pady=5)  


btn_help = tk.Button(root, text="Help", command=show_help, bg="#086105", fg="#FFFFFF")
btn_help.grid(row=5, column=0, columnspan=2, pady=5)  


btn_admin_override = tk.Button(root, text="Admin Override", command=admin_override, bg="#086105", fg="#FFFFFF")
btn_admin_override.grid(row=6, column=0, columnspan=2, pady=5)  



btn_exit = tk.Button(root, text="Exit Program", command=confirm_exit, bg="#086105", fg="#FFFFFF")
btn_exit.grid(row=7, column=0, columnspan=2, pady=5) 


root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
root.rowconfigure(3, weight=1)
root.rowconfigure(4, weight=1)
root.rowconfigure(5, weight=1)
root.rowconfigure(6, weight=1)
root.rowconfigure(7, weight=1)



about_window = None

def show_about():
    global about_window
    
    
    pygame.mixer.init()

    
    sound_path = "sounds/logo.wav"  
    if os.path.exists(sound_path):
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()

    
    if about_window and about_window.winfo_exists():
        
        about_window.lift()
    else:
        
        about_window = tk.Toplevel(root)
        about_window.title("About")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        
        about_window.iconbitmap("images/icon.ico")

        
        about_bg_path = "images/about.png"
        if os.path.exists(about_bg_path):
            about_img = Image.open(about_bg_path)
            global about_bg_image
            about_bg_image = ImageTk.PhotoImage(about_img)
            about_bg_label = tk.Label(about_window, image=about_bg_image)
            about_bg_label.place(relwidth=1, relheight=1)  


def show_date_and_time():
    global date_time_window
    
    
    if hasattr(show_date_and_time, 'date_time_window') and show_date_and_time.date_time_window and show_date_and_time.date_time_window.winfo_exists():
        
        show_date_and_time.date_time_window.lift()
    else:
        
        
        sound_path = "sounds/clock.wav"  
        if os.path.exists(sound_path):
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
        
        date_time_window = tk.Toplevel(root)
        date_time_window.title("Date and Time")
        date_time_window.geometry("300x80")
        date_time_window.resizable(False, False)
        
        date_time_window.iconbitmap("images/icon.ico")
        

        
        date_time_window.configure(bg="#086105")

        
        pixel_font = tk.font.Font(family="pixelmix", size=15)

        
        date_time_label = tk.Label(date_time_window, text="", font=pixel_font, bg="#086105", fg="#09ff00")
        date_time_label.pack(pady=20)

        
        def update_date_time():
            current_date_time = time.strftime("%Y-%m-%d %H:%M:%S")
            date_time_label.config(text=current_date_time)
            date_time_window.after(1000, update_date_time) 

        
        update_date_time()

        
        show_date_and_time.date_time_window = date_time_window
    
    

date_time_window_opened = False
calendar_window_opened = False

    
    
def show_calendar():
    global calendar_window
    
    
    if hasattr(show_calendar, 'calendar_window') and show_calendar.calendar_window and show_calendar.calendar_window.winfo_exists():
        
        show_calendar.calendar_window.lift()
    else:
        
        sound_path = "sounds/calendar.wav"  
        if os.path.exists(sound_path):
            pygame.mixer.init()
            pygame.mixer.music.load(sound_path)
            pygame.mixer.music.play()
            
            
    
    if hasattr(show_calendar, 'calendar_window') and show_calendar.calendar_window and show_calendar.calendar_window.winfo_exists():
       
        show_calendar.calendar_window.lift()
    else:
        
        def update_calendar():
            calendar_text.config(state="normal")  
            calendar_text.delete("1.0", "end")

            
            current_month = datetime.datetime.now().month
            current_year = datetime.datetime.now().year
            
            
            cal_text = cal.formatmonth(current_year, current_month)
            calendar_text.insert("end", cal_text)

            
            today = datetime.datetime.now().day
            tag_start = f"{today:2d} "
            tag_end = f"{today + 1:2d} "
            start_index = calendar_text.search(tag_start, "1.0", stopindex="end")
            end_index = calendar_text.search(tag_end, "1.0", stopindex="end")
            calendar_text.tag_add("highlight", start_index, end_index)
            calendar_text.tag_config("highlight", foreground="red")

            calendar_text.config(state="disabled")  

        calendar_window = tk.Toplevel(root)
        calendar_window.title("Calendar")
        calendar_window.geometry("190x190")
        calendar_window.resizable(False, False)
        
        
        calendar_window.iconbitmap("images/icon.ico")
        
        
        
        def load_background_image():
            bg_img_path = "images/background5.png" 
            if os.path.exists(bg_img_path):
                bg_img = Image.open(bg_img_path)
                bg_img = bg_img.resize((190, 190), Image.LANCZOS)  
                bg_photo = ImageTk.PhotoImage(bg_img)
                bg_label = tk.Label(calendar_window, image=bg_photo)
                bg_label.image = bg_photo  
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)  

        
        load_background_image()


        
        cal = calendar.TextCalendar(calendar.SUNDAY)
        
        
        calendar_text = tk.Text(
            calendar_window,
            wrap="none",
            height=10,
            width=20,
            bg="#086105",
            fg="#09ff00",
            insertbackground="black",  
            selectbackground="#086105",  
            selectforeground="#171717",  
            state="disabled"  
        )
        calendar_text.pack(pady=10)
        
       
        calendar_window.configure(bg="#101f10")

        
        update_calendar()

        
        show_calendar.calendar_window = calendar_window
        
    


context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="About", command=show_about)
context_menu.add_command(label="Date and Time", command=show_date_and_time)


context_menu.add_command(label="Calendar", command=show_calendar)


def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)


root.bind("<Button-3>", show_context_menu)


root.mainloop()


conn.close()
