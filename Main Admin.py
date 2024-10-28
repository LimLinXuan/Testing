import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import END
from datetime import datetime
import sqlite3

root = tk.Tk()
root.title("Admin Inbox")
root.state("zoomed")

Unit = tk.StringVar()
Inbox = tk.StringVar(value="Inbox")
SearchText = tk.StringVar()
Subject = tk.StringVar()
AttachmentPath = tk.StringVar()
SendToAll = tk.BooleanVar()

# List of available units and inbox categories
unit_set = ['Unit 101', 'Unit 202', 'Unit 303', 'Unit 304', 'Unit 305', 'Unit 306', 'Unit 401', 'Unit 402']
inbox_set = ['Inbox', 'Read', 'Sent']

##FIXME: Placeholder for current user - replace with actual login system in production
current_user = "Admin"  # This line resolves the 'current_user' warnings


def create_database():
	conn = sqlite3.connect('db_messages.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS db_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT NOT NULL,
                  recipient TEXT NOT NULL,
                  subject TEXT NOT NULL,
                  message TEXT NOT NULL,
                  attachment TEXT,
                  timestamp DATETIME NOT NULL,
                  status TEXT NOT NULL)''')
	conn.commit()
	conn.close()


# Call this function at the start of your program
create_database()


def filter_units(event):
	typed_text = Unit.get().lower()
	filtered_units = [u for u in unit_set if typed_text in u.lower()]
	unit_combo['values'] = filtered_units


def filter_inbox(event):
	typed_text = Inbox.get().lower()
	filtered_inbox = [i for i in inbox_set if typed_text in i.lower()]
	inbox_combo['values'] = filtered_inbox


def search_units():
	search_text = SearchText.get().lower()
	filtered_units = [u for u in unit_set if search_text in u.lower()]
	result_label.config(text="Results: " + ", ".join(filtered_units))


def browse_file(window):
	file_path = filedialog.askopenfilename(title="Select file", parent=window)
	if file_path:
		AttachmentPath.set(file_path)


def insert_message(sender, recipient, subject, message, attachment, status):
	conn = sqlite3.connect('db_messages.db')
	c = conn.cursor()
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	c.execute(
		"INSERT INTO db_messages (sender, recipient, subject, message, attachment, timestamp, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
		(sender, recipient, subject, message, attachment, timestamp, status))
	conn.commit()
	conn.close()

def send_message():
    # Determine the unit based on the "Send to All" checkbox
    unit = "All Units" if SendToAll.get() else Unit.get()
    subject = Subject.get()
    message = message_text.get("1.0", tk.END).strip()  # Using proper string index
    attachment = AttachmentPath.get()

    # Check if the selected unit is in the valid units set
    if unit not in unit_set:  # Changed this line to check the actual unit
        messagebox.showerror("Invalid Unit", "This is not a valid unit.")
        return

    # Check if the subject and message are provided
    if not subject or not message:
        messagebox.showwarning("Missing Information", "Please enter both subject and message!")
        return

    sender = current_user  # Assuming current_user is defined elsewhere

    # Send the message to all or the specified unit
    if SendToAll.get():
        for recipient in unit_set:  # Assuming unit_set contains recipient units
            insert_message(sender, recipient, subject, message, attachment, "Inbox")
        # Store a single copy in the sender's "Sent" folder
        insert_message(sender, "All Units", subject, message, attachment, "Sent")
    else:
        insert_message(sender, unit, subject, message, attachment, "Inbox")
        insert_message(sender, unit, subject, message, attachment, "Sent")

    update_message_display()  # Assuming this function refreshes the message display
    messagebox.showinfo("Message Sent", "Message sent successfully!")
    compose_win.destroy()  # Close the compose window

def get_messages(user, category):
    conn = sqlite3.connect('db_messages.db')
    c = conn.cursor()
    if category == "Sent":
        c.execute("SELECT * FROM db_messages WHERE sender = ? AND status = ? ORDER BY timestamp DESC", (user, category))
    else:
        c.execute("SELECT * FROM db_messages WHERE recipient = ? AND status = ? ORDER BY timestamp DESC", (user, category))
    messages = c.fetchall()
    conn.close()
    return messages

def update_message_display():
    message_listbox.delete(0, tk.END)
    selected_category = Inbox.get()
    messages = get_messages(current_user, selected_category)

    for message in messages:
        if selected_category == "Sent":
            record_text = f"To: {message[2]} | Subject: {message[3]} | Date: {message[6]}"
        else:
            record_text = f"From: {message[1]} | Subject: {message[3]} | Date: {message[6]}"
        message_listbox.insert(tk.END, record_text)


def show_full_message(event):
    selection = message_listbox.curselection()
    if not selection:
        return

    selected_index = selection[0]
    selected_category = Inbox.get()
    messages = get_messages(current_user, selected_category)
    selected_message = messages[selected_index]

    # Unpack the message details
    message_id, sender, recipient, subject, message, attachment, timestamp, status = selected_message

    # Clear previous content
    for widget in full_message_frame.winfo_children():
        widget.destroy()

    # Create a new frame for message details
    details_frame = tk.Frame(full_message_frame, bg="#F5F5F5")
    details_frame.pack(fill=tk.X, padx=10, pady=10)

    # Add message details
    tk.Label(details_frame, text=f"From: {sender}", font=("Helvetica", 12, "bold"), bg="#F5F5F5", anchor="w").pack(fill=tk.X)
    tk.Label(details_frame, text=f"To: {recipient}", font=("Helvetica", 12), bg="#F5F5F5", anchor="w").pack(fill=tk.X)
    tk.Label(details_frame, text=f"Subject: {subject}", font=("Helvetica", 12, "bold"), bg="#F5F5F5", anchor="w").pack(fill=tk.X)
    tk.Label(details_frame, text=f"Date: {timestamp}", font=("Helvetica", 10), bg="#F5F5F5", anchor="w").pack(fill=tk.X)

    if attachment:
        tk.Label(details_frame, text=f"Attachment: {attachment}", font=("Helvetica", 10), bg="#F5F5F5", anchor="w").pack(fill=tk.X)

    # Create a frame for the message body
    message_body_frame = tk.Frame(full_message_frame)
    message_body_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

    # Add message body with scrollbar
    message_body = tk.Text(message_body_frame, font=("Helvetica", 12), wrap=tk.WORD, padx=10, pady=10)
    message_body.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    message_body.insert(tk.END, message)
    message_body.config(state=tk.DISABLED)

    scrollbar = tk.Scrollbar(message_body_frame, orient=tk.VERTICAL, command=message_body.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    message_body.config(yscrollcommand=scrollbar.set)

    # Add Reply button
    reply_button = tk.Button(full_message_frame, text="Reply", font=("Helvetica", 12), bg="#ff8210", fg="white",
                             command=lambda: reply_message(sender, subject, message))
    reply_button.pack(side=tk.BOTTOM, pady=10)

    if status == "Inbox":
        mark_message_as_read(message_id)



def mark_message_as_read(message_id):
	conn = sqlite3.connect('db_messages.db')
	c = conn.cursor()
	c.execute("UPDATE db_messages SET status = 'Read' WHERE id = ?", (message_id,))
	conn.commit()
	conn.close()
	update_message_display()

def delete_message():
    selected_index = message_listbox.curselection()
    if selected_index:
        selected_index = selected_index[0]
        selected_category = Inbox.get()
        messages = get_messages(current_user, selected_category)

        if selected_index < len(messages):
            message_to_delete = messages[selected_index]
            message_id = message_to_delete[0]  # Assuming the ID is the first element in the tuple
            recipient = message_to_delete[2]  # Assuming the recipient is the third element in the tuple

            # Confirm deletion
            if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this message?"):
                conn = sqlite3.connect('db_messages.db')
                c = conn.cursor()
                try:
                    # If the message is a group message, delete it based on the subject and recipient
                    if recipient == "All Units":  # Adjust based on your criteria for group messages
                        c.execute("DELETE FROM db_messages WHERE subject = ? AND recipient = 'All Units'", (message_to_delete[3],))
                    else:
                        c.execute("DELETE FROM db_messages WHERE id = ?", (message_id,))

                    conn.commit()
                    messagebox.showinfo("Success", "Message deleted successfully.")
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"An error occurred: {e}")
                finally:
                    conn.close()

                # Update the display
                update_message_display()
        else:
            messagebox.showwarning("Error", "Invalid selection.")
    else:
        messagebox.showwarning("Selection Error", "Please select a message to delete.")


def compose_message():
    global compose_win, message_text
    compose_win = tk.Toplevel(root)
    compose_win.title("Compose Message")
    compose_win.geometry("800x600")
    compose_win.config(bg="#D3D3D3")

    main_frame = tk.Frame(compose_win, bg="#D3D3D3")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    main_frame.grid_columnconfigure(1, weight=1)

    tk.Label(main_frame, text="Unit", font=("helvetica", 16), bg="#D3D3D3").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    unit_combo = tk.Entry(main_frame, textvariable=Unit, font=("helvetica", 16))
    unit_combo.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    tk.Checkbutton(main_frame, text="Send to All", variable=SendToAll, bg="#D3D3D3", font=("helvetica", 16)).grid(row=0, column=2, padx=10, pady=10)

    tk.Label(main_frame, text="Subject", font=("helvetica", 16), bg="#D3D3D3").grid(row=1, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=Subject, font=("helvetica", 16)).grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")

    tk.Label(main_frame, text="Message", font=("helvetica", 16), bg="#D3D3D3").grid(row=2, column=0, padx=10, pady=10, sticky="nw")
    message_text = tk.Text(main_frame, font=("helvetica", 16), width=50, height=10)
    message_text.grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="nsew")

    main_frame.grid_rowconfigure(2, weight=1)

    tk.Label(main_frame, text="Attachment", font=("helvetica", 16), bg="#D3D3D3").grid(row=3, column=0, padx=10, pady=10, sticky="w")
    tk.Entry(main_frame, textvariable=AttachmentPath, font=("helvetica", 16), state='readonly').grid(row=3, column=1, padx=10, pady=10, sticky="ew")
    tk.Button(main_frame, text="Browse", font=("helvetica", 16), command=lambda: browse_file(compose_win)).grid(row=3, column=2, padx=10, pady=10, sticky="e")

    tk.Button(main_frame, text="Send", font=("helvetica", 16), bg="#ff8210", fg="white", command=send_message).grid(row=4, column=1, padx=10, pady=20, sticky="ew")


def reply_message(original_sender, original_subject, original_message):
    reply_win = tk.Toplevel(root)
    reply_win.title("Reply Message")
    reply_win.geometry("800x600")
    reply_win.config(bg="#D3D3D3")

    # Create main frame
    main_frame = tk.Frame(reply_win, bg="#D3D3D3")
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    # Recipient and Subject display
    tk.Label(main_frame, text=f"To: {original_sender}", font=("Helvetica", 14), bg="#D3D3D3").pack(anchor="w")
    tk.Label(main_frame, text=f"Subject: Re: {original_subject}", font=("Helvetica", 14, "bold"), bg="#D3D3D3").pack(anchor="w")

    # Frame for previous messages
    previous_messages_frame = tk.Frame(main_frame)
    previous_messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    # Scrollable text area for previous messages
    previous_messages = tk.Text(previous_messages_frame, font=("Helvetica", 12), wrap=tk.WORD, padx=10, pady=10)
    previous_messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    previous_messages.insert(tk.END, f"From: {original_sender}\nSubject: {original_subject}\n\n{original_message}\n\n")
    previous_messages.config(state=tk.DISABLED)  # Disable editing

    # Scrollbar for previous messages
    scrollbar = tk.Scrollbar(previous_messages_frame, command=previous_messages.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    previous_messages.config(yscrollcommand=scrollbar.set)

    # Frame for new message
    new_message_frame = tk.Frame(main_frame)
    new_message_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))

    tk.Label(new_message_frame, text="Your Reply:", font=("Helvetica", 14), bg="#D3D3D3").pack(anchor="w")

    # Text area for user reply
    reply_text = tk.Text(new_message_frame, font=("Helvetica", 12), wrap=tk.WORD, height=5)
    reply_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Send button for sending the reply
    send_reply_button = tk.Button(main_frame, text="Send Reply", font=("Helvetica", 12), bg="#ff8210", fg="white",
                                  command=lambda: send_reply(original_sender, f"Re: {original_subject}",
                                                             reply_text.get(1.0, tk.END).strip(), reply_win))
    send_reply_button.pack(pady=10)


def send_reply(original_sender, subject, reply_message, window):
    if not reply_message.strip():
        messagebox.showwarning("Missing Reply", "Please enter your reply message!")
        return

    # Insert reply into the database
    insert_message(current_user, original_sender, subject, reply_message, None, "Sent")

    messagebox.showinfo("Reply Sent", "Your reply has been sent successfully!")

    # Close the reply window after sending
    window.destroy()

    # Update the message display after sending the reply
    update_message_display()



# Main UI setup
entries_frame = tk.Frame(root, bg="#F5F5F5")
entries_frame.pack(side=tk.TOP, fill=tk.X)

for i in range(7):
	entries_frame.grid_columnconfigure(i, weight=1)

tk.Label(entries_frame, text="Admin - INBOX", font=("helvetica", 30, "bold"), bg="#F5F5F5").grid(row=0, column=0, columnspan=7,
                                                                                         padx=10, pady=20,
                                                                                         sticky="nsew")

tk.Label(entries_frame, text="Unit:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=0, padx=10, pady=10,
                                                                                 sticky="nsew")
unit_combo = ttk.Combobox(entries_frame, textvariable=Unit, font=("helvetica", 16), width=30, values=unit_set)
unit_combo.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
unit_combo.bind("<KeyRelease>", filter_units)

tk.Label(entries_frame, text="Category:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=2, padx=10, pady=10,
                                                                                     sticky="nsew")
inbox_combo = ttk.Combobox(entries_frame, textvariable=Inbox, font=("helvetica", 16), width=30, values=inbox_set)
inbox_combo.grid(row=1, column=3, padx=10, pady=10, sticky="nsew")
inbox_combo.bind("<KeyRelease>", filter_inbox)
inbox_combo.bind("<<ComboboxSelected>>", lambda e: update_message_display())

tk.Label(entries_frame, text="Search Unit:", font=("helvetica", 16), bg="#F5F5F5").grid(row=1, column=4, padx=10, pady=10, sticky="nsew")
tk.Entry(entries_frame, textvariable=SearchText, font=("helvetica", 16), width=30).grid(row=1, column=5, padx=10, pady=10, sticky="nsew")
tk.Button(entries_frame, text="Search", font=("helvetica", 16), fg="white", bg="#ff8210", command=search_units).grid(row=1, column=6, padx=10, pady=10, sticky="nsew")

# Create a frame for the buttons
button_frame = tk.Frame(entries_frame, bg="#F5F5F5")
button_frame.grid(row=4, column=2, columnspan=3, padx=10, pady=10, sticky="ew")

# Configure the button frame columns
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)
button_frame.columnconfigure(2, weight=1)

# Add the buttons to the button frame
tk.Button(button_frame, text="Compose Message", font=("helvetica", 16), bg="#ff8210", fg="white", command=compose_message).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
tk.Button(button_frame, text="Delete Message", font=("helvetica", 16), bg="#ff8210", fg="white", command=delete_message).grid(row=0, column=1, padx=5, pady=5, sticky="ew")


# Adjust the results label row if needed
result_label = tk.Label(entries_frame, text="Results: ", font=("helvetica", 16), bg="#F5F5F5")
result_label.grid(row=5, column=0, columnspan=7, padx=10, pady=10, sticky="w")

# Message display setup
lower_frame = tk.Frame(root)
lower_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

message_frame = tk.Frame(lower_frame)
message_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

message_listbox = tk.Listbox(message_frame, font=("helvetica", 12))
message_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

message_scrollbar = tk.Scrollbar(message_frame, orient=tk.VERTICAL, command=message_listbox.yview)
message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
message_listbox.config(yscrollcommand=message_scrollbar.set)

message_listbox.bind("<<ListboxSelect>>", show_full_message)

full_message_frame = tk.Frame(lower_frame)
full_message_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

full_message_text = tk.Text(full_message_frame, font=("helvetica", 12), wrap=tk.WORD)
full_message_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

full_message_scrollbar = tk.Scrollbar(full_message_frame, orient=tk.VERTICAL, command=full_message_text.yview)
full_message_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
full_message_text.config(yscrollcommand=full_message_scrollbar.set)

# Initialize the message display
update_message_display()


root.mainloop()
