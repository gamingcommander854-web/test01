import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox





# -------- INVENTORY (GLOBAL) --------

class InventoryItem:
    def __init__(
        self,
        item,
        category,
        quantity,
        unit,
        per_person_per_day,
        last_updated
    ):
        self.item = item
        self.category = category
        self.quantity = quantity
        self.unit = unit
        self.per_person_per_day = per_person_per_day
        self.last_updated = last_updated

    def to_dict(self):
        return {
            "item": self.item,
            "category": self.category,
            "quantity": self.quantity,
            "unit": self.unit,
            "per_person_per_day": self.per_person_per_day,
            "last_updated": self.last_updated
        }



class InventoryManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(base_dir, "inventory.json")

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def add_or_update_item(self, item: InventoryItem):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []

        for existing in data:
            if existing["item"].lower() == item.item.lower():
                existing["quantity"] += item.quantity
                existing["last_updated"] = item.last_updated
                break
        else:
            data.append(item.to_dict())

        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)



    def distribute_item(self, item_name, quantity):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return False, "Inventory file error"

        for item in data:
            if item["item"].lower() == item_name.lower():
                if item["quantity"] < quantity:
                    return False, "Insufficient stock"

                item["quantity"] -= quantity
                item["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                with open(self.file_path, "w") as f:
                    json.dump(data, f, indent=4)

                return True, "Distribution successful"

        return False, "Item not found"



    def analyze_needs(self, total_people, safety_days=3):
        """
        Returns:
        - all_items (list)
        - critical_items (list)
        """

        try:
            with open(self.file_path, "r") as f:
                items = json.load(f)
        except:
            return [], []

        critical = []

        for item in items:
            qty = item.get("quantity", 0)
            rate = item.get("per_person_per_day", 0)

            if rate <= 0:
                continue  # cannot assess without consumption rate

            required = total_people * rate * safety_days

            if qty < required:
                item["required_quantity"] = round(required, 2)
                item["shortfall"] = round(required - qty, 2)
                critical.append(item)

        return items, critical






class Logger:
    @staticmethod
    def log(action, user="SYSTEM"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_file = os.path.join(base_dir, "logs.txt")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{timestamp} | {action} | {user}\n"

        with open(log_file, "a") as file:
            file.write(entry)




class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Shelter OMS – Secure Login")
        self.root.geometry("420x360")
        self.root.resizable(False, False)
        self.root.configure(bg="#111827")

        self.build_ui()

    def build_ui(self):
        container = tk.Frame(self.root, bg="#111827")
        container.pack(expand=True)

        card = tk.Frame(container, bg="#111827", width=400, height=320)
        card.pack()
        card.pack_propagate(False)

        tk.Label(
            card,
            text="Shelter OMS",
            bg="#111827",
            fg="#ffffff",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=(20, 5))

        tk.Label(
            card,
            text="Secure Access",
            bg="#111827",
            fg="#9ca3af",
            font=("Segoe UI", 11)
        ).pack(pady=(0, 20))

        self.username_entry = self.create_field(card, "Username")
        self.password_entry = self.create_field(card, "Password", show="*")

        tk.Button(
            card,
            text="Sign In",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            relief="flat",
            padx=10,
            pady=8,
            cursor="hand2",
            command=self.authenticate
        ).pack(pady=15, fill="x", padx=30)

    def create_field(self, parent, label, show=None):
        tk.Label(
            parent,
            text=label,
            bg="#111827",
            fg="#9ca3af",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=30)

        entry = tk.Entry(
            parent,
            show=show,
            font=("Segoe UI", 11),
            relief="flat"
        )
        entry.pack(fill="x", padx=30, pady=(2, 10))
        return entry

    def authenticate(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if self.check_credentials(username, password):
            Logger.log("LOGIN_SUCCESS", username)
            self.root.destroy()
            self.launch_app(username)
        else:
            Logger.log("LOGIN_FAILED", username or "UNKNOWN")
            messagebox.showerror("Login Failed", "Invalid username or password")


    def check_credentials(self, username, password):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            users_file = os.path.join(base_dir, "users.txt")

            with open(users_file, "r") as file:
                for line in file:
                    u, p = line.strip().split(",")
                    if u == username and p == password:
                        return True
        except FileNotFoundError:
            messagebox.showerror("Error", "users.txt not found in project folder")
        except ValueError:
            messagebox.showerror("Error", "Invalid format in users.txt")

        return False
    

    def launch_app(self, username):
        app_root = tk.Tk()
        ShelterApp(app_root, username)
        app_root.mainloop()



class Donation:
    def __init__(self, donor, dtype, amount, timestamp):
        self.donor = donor
        self.type = dtype
        self.amount = amount
        self.timestamp = timestamp

    def to_dict(self):
        return {
            "donor": self.donor,
            "type": self.type,
            "amount": self.amount,
            "timestamp": self.timestamp
        }



class DonationManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(base_dir, "donations.json")

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as file:
                json.dump([], file)

    def add_donation(self, donation: Donation):
        # Read existing data safely
        try:
            with open(self.file_path, "r") as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            data = []

    # Append new donation
        data.append(donation.to_dict())

    # Write back to file
        with open(self.file_path, "w") as file:
            json.dump(data, file, indent=4)



class Volunteer:
    def __init__(self, name, phone, role, joined):
        self.name = name
        self.phone = phone
        self.role = role
        self.joined = joined

    def to_dict(self):
        return {
            "name": self.name,
            "phone": self.phone,
            "role": self.role,
            "joined": self.joined
        }
    
class VolunteerManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(base_dir, "volunteers.json")

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def add_volunteer(self, volunteer: Volunteer):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except:
            data = []

        data.append(volunteer.to_dict())

        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def count(self):
        try:
            with open(self.file_path, "r") as f:
                return len(json.load(f))
        except:
            return 0


    def load_all(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except:
            return []




class ShelterLocation:
    def __init__(self, name, address, capacity, occupancy, created):
        self.name = name
        self.address = address
        self.capacity = capacity
        self.occupancy = occupancy
        self.created = created

    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            "capacity": self.capacity,
            "current_occupancy": self.occupancy,
            "created": self.created
        }




class ShelterLocationManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.file_path = os.path.join(base_dir, "shelters.json")

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def add_shelter(self, shelter: ShelterLocation):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except:
            data = []

        data.append(shelter.to_dict())

        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def count(self):
        try:
            with open(self.file_path, "r") as f:
                return len(json.load(f))
        except:
            return 0


    def total_population(self):
        try:
            with open(self.file_path, "r") as f:
                shelters = json.load(f)
        except:
            return 0

        return sum(s.get("occupancy", 0) for s in shelters)




# class ShelterApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Shelter Operations Management System")
#         self.root.geometry("900x600")

#         tk.Label(
#             root,
#             text="Welcome to Shelter Operations Management System",
#             font=("Segoe UI", 16, "bold")
#         ).pack(expand=True)



class ShelterApp:
    def __init__(self, root, username):
        self.user = username
        self.donation_manager = DonationManager()
        self.inventory_manager = InventoryManager()
        self.root = root
        self.root.title("Shelter Operations Management System")
        self.root.geometry("1350x750")
        self.root.minsize(1350, 750)
        self.root.configure(bg="#f5f7fa")
        self.volunteer_manager = VolunteerManager()
        self.shelter_manager = ShelterLocationManager()


        

        self.active_button = None
        self.build_layout()


    def show_volunteer_ui(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Volunteer Management",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        form = tk.Frame(self.activity, bg="#ffffff")
        form.pack(anchor="w", padx=20)

        self.vol_name = self.create_input(form, "Name")
        self.vol_phone = self.create_input(form, "Phone")
        self.vol_role = self.create_input(form, "Role")

        tk.Button(
            self.activity,
            text="Register Volunteer",
            font=("Segoe UI", 11, "bold"),
            bg="#7c3aed",
            fg="#ffffff",
            relief="flat",
            padx=15,
            pady=8,
            command=self.submit_volunteer
        ).pack(anchor="w", padx=20, pady=20)
        
        
        
        
        
    def submit_volunteer(self):
        name = self.vol_name.get().strip()
        phone = self.vol_phone.get().strip()
        role = self.vol_role.get().strip()

        if not name or not phone:
            messagebox.showerror("Error", "Name and phone required")
            return

        v = Volunteer(
            name=name,
            phone=phone,
            role=role or "General",
            joined=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self.volunteer_manager.add_volunteer(v)
        Logger.log("VOLUNTEER_REGISTERED", self.user)

        messagebox.showinfo("Success", "Volunteer registered")

        self.vol_name.delete(0, tk.END)
        self.vol_phone.delete(0, tk.END)
        self.vol_role.delete(0, tk.END)
        self.navigate("Dashboard", self.buttons["Dashboard"])





    def submit_inventory_item(self):
        item = self.inv_item_entry.get().strip()
        category = self.inv_category_entry.get().strip()
        quantity = self.inv_quantity_entry.get().strip()
        unit = self.inv_unit_entry.get().strip()
        rate = self.inv_rate_entry.get().strip()


        if (
            not item or
            not quantity.isdigit() or
            not rate.replace(".", "", 1).isdigit()
        ):
            messagebox.showerror(
                "Error",
                "Item name, numeric quantity, and numeric consumption rate are required"
            )
            return


        inventory_item = InventoryItem(
            item=item,
            category=category or "General",
            quantity=int(quantity),
            unit=unit or "units",
            per_person_per_day=float(rate),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )


        self.inventory_manager.add_or_update_item(inventory_item)
        Logger.log("INVENTORY_UPDATED", self.user)

        messagebox.showinfo("Success", "Inventory updated successfully")

        self.inv_item_entry.delete(0, tk.END)
        self.inv_category_entry.delete(0, tk.END)
        self.inv_quantity_entry.delete(0, tk.END)
        self.inv_unit_entry.delete(0, tk.END)
        self.inv_rate_entry.delete(0, tk.END)



    def build_layout(self):
        self.main_frame = tk.Frame(self.root, bg="#f5f7fa")
        self.main_frame.pack(fill="both", expand=True)

        self.build_sidebar()
        self.build_content_area()

        self.navigate("Dashboard", self.buttons["Dashboard"])

    # ---------------- Sidebar ----------------
    def build_sidebar(self):
        self.sidebar = tk.Frame(self.main_frame, bg="#111827", width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        title = tk.Label(
            self.sidebar,
            text="Shelter OMS",
            bg="#111827",
            fg="#ffffff",
            font=("Segoe UI", 20, "bold")
        )
        title.pack(pady=(30, 50))

        self.buttons = {}
        menu_items = [
            "Dashboard",
            "Donations & Funding",
            "Resource Inventory",
            "Aid Distribution",
            "Shelter Locations",
            "Volunteer Management",
            "Needs Assessment",
            "System Audit Logs",
            "Sign Out"
        ]

        for name in menu_items:
            btn = tk.Label(
                self.sidebar,
                text=name,
                bg="#111827",
                fg="#9ca3af",
                font=("Segoe UI", 11),
                padx=25,
                pady=12,
                anchor="w",
                cursor="hand2"
            )
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#1f2937", fg="#ffffff"))
            btn.bind("<Leave>", lambda e, b=btn: self.reset_button(b))
            btn.bind("<Button-1>", lambda e, n=name, b=btn: self.navigate(n, b))

            self.buttons[name] = btn

    def reset_button(self, button):
        # Only reset if this button is NOT active
        if self.active_button is None:
            button.config(bg="#111827", fg="#9ca3af")
        elif button != self.active_button:
            button.config(bg="#111827", fg="#9ca3af")



    def create_input(self, parent, label):
        tk.Label(
            parent,
            text=label,
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(5, 2))

        entry = tk.Entry(parent, font=("Segoe UI", 11), width=30)
        entry.pack(anchor="w", pady=(0, 10))
        return entry


    
    def submit_donation(self):
        print("DEBUG: submit_donation called")
        print("DEBUG: donation_manager =", self.donation_manager)

        donor = self.donor_entry.get().strip() or "Anonymous"
        dtype = self.type_entry.get().strip() or "General"
        amount = self.amount_entry.get().strip()

        if not amount.isdigit():
            messagebox.showerror("Error", "Amount must be a number")
            return


        donation = Donation(
            donor=donor,
            dtype=dtype,
            amount=int(amount),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        print("DEBUG: donation data =", donation.to_dict())

        self.donation_manager.add_donation(donation)
        Logger.log("DONATION_ADDED", self.user)

        messagebox.showinfo("Success", "Donation recorded successfully")

        self.donor_entry.delete(0, tk.END)
        self.type_entry.delete(0, tk.END)
        self.amount_entry.delete(0, tk.END)

        self.navigate("Dashboard", self.buttons["Dashboard"])



    # ---------------- Content ----------------
    def build_content_area(self):
        # CLEAN previous dashboard content if it exists
        if hasattr(self, "content"):
            self.content.destroy()

        self.content = tk.Frame(self.main_frame, bg="#f5f7fa")
        self.content.pack(side="left", fill="both", expand=True, padx=30, pady=30)

        self.header = tk.Label(
            self.content,
            text="Dashboard",
            bg="#f5f7fa",
            fg="#111827",
            font=("Segoe UI", 26, "bold")
        )
        self.header.pack(anchor="w", pady=(0, 20))

        self.cards_frame = tk.Frame(self.content, bg="#f5f7fa")
        self.cards_frame.pack(fill="x")
        self.cards_frame.columnconfigure((0, 1), weight=1)

        # ---- REAL DATA ----
        count = self.volunteer_manager.count()
        total = self.calculate_total_donations()
        population = self.shelter_manager.total_population()
        items, critical = self.inventory_manager.analyze_needs(population)
        total_items = len(items)


        # ---- CLICKABLE DASHBOARD CARDS ----
        self.create_card(
            "Total Donations",
            f"₹ {total}",
            "#2563eb",
            0, 0,
            on_click=lambda: self.show_donation_overview()
        )

        self.create_card(
            "Inventory Status",
            f"{total_items} items tracked",
            "#059669",
            0, 1,
            on_click=lambda: self.show_inventory_overview()
        )

        self.create_card(
            "Active Volunteers",
            f"{count} Registered",
            "#7c3aed",
            1, 0,
            on_click=lambda: self.show_volunteer_overview()
        )

        self.create_card(
            "Critical Needs",
            f"{len(critical)} critical items",
            "#dc2626",
            1, 1,
            on_click=lambda: self.show_needs_ui()
        )

        # ---- RECENT ACTIVITY PLACEHOLDER ----
        self.activity = tk.Label(
            self.content,
            text="Recent Activity\n\nNo activity logged yet.",
            bg="#ffffff",
            fg="#374151",
            font=("Segoe UI", 11),
            justify="left",
            padx=20,
            pady=20
        )
        self.activity.pack(fill="both", expand=True, pady=(30, 0))


    def create_card(self, title, value, accent, row, col, on_click=None):
        card = tk.Frame(
            self.cards_frame,
            bg="#ffffff",
            height=120,
            cursor="hand2" if on_click else "arrow"
        )
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

        title_lbl = tk.Label(
            card,
            text=title,
            bg="#ffffff",
            fg="#6b7280",
            font=("Segoe UI", 11)
        )
        title_lbl.pack(anchor="w", padx=20, pady=(20, 5))

        value_lbl = tk.Label(
            card,
            text=value,
            bg="#ffffff",
            fg=accent,
            font=("Segoe UI", 18, "bold")
        )
        value_lbl.pack(anchor="w", padx=20)

        if on_click:
            # Make entire card clickable
            for widget in (card, title_lbl, value_lbl):
                widget.bind("<Button-1>", lambda e: on_click())


    # ---------------- Navigation ----------------
    



    def navigate(self, name, button=None):
        # Reset previous active button
            if self.active_button:
                self.active_button.config(bg="#111827", fg="#9ca3af")

            # Set new active button
            if button:
                button.config(bg="#1f2937", fg="#ffffff")
                self.active_button = button

            # Update header
            self.header.config(text=name)

            # Clear previous content
            if hasattr(self, "activity"):
                self.activity.destroy()

            # ---- ROUTING ----
            if name == "Dashboard":
                self.build_content_area()
                return

            elif name == "Donations & Funding":
                self.show_donations_ui()
                return

            elif name == "Resource Inventory":
                self.show_inventory_ui()
                return

            elif name == "Aid Distribution":
                self.show_distribution_ui()
                return

            elif name == "Shelter Locations":
                self.show_shelter_locations_ui()
                return

            elif name == "Volunteer Management":
                self.show_volunteer_ui()
                return

            elif name == "System Audit Logs":
                self.show_logs_ui()
                return

            elif name == "Sign Out":
                Logger.log("LOGOUT", self.user)
                self.root.destroy()

                # Relaunch login window
                new_root = tk.Tk()
                LoginWindow(new_root)
                new_root.mainloop()
                return
            
            elif name == "Needs Assessment":
                self.show_needs_ui()
                return


            # ---- DEFAULT ----
            self.activity = tk.Label(
                self.content,
                text=f"{name}\n\nModule interface will appear here.",
                bg="#ffffff",
                fg="#374151",
                font=("Segoe UI", 11),
                justify="left",
                padx=20,
                pady=20
            )
            self.activity.pack(fill="both", expand=True, pady=(30, 0))







    def show_logs_ui(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="System Audit Logs",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        container = tk.Frame(self.activity, bg="#ffffff")
        container.pack(fill="both", expand=True, padx=20, pady=10)

        scrollbar = tk.Scrollbar(container)
        scrollbar.pack(side="right", fill="y")

        log_text = tk.Text(
            container,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            bg="#f9fafb",
            fg="#111827",
            relief="flat",
            padx=10,
            pady=10
        )
        log_text.pack(fill="both", expand=True)

        scrollbar.config(command=log_text.yview)

    # Load logs
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            log_path = os.path.join(base_dir, "logs.txt")

            with open(log_path, "r") as f:
                lines = f.readlines()

            for line in reversed(lines):
                log_text.insert(tk.END, line)

        except FileNotFoundError:
            log_text.insert(tk.END, "No logs available.")

        log_text.config(state="disabled")







    def show_donations_ui(self):
        # Clear activity area
        self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Add Donation",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        form = tk.Frame(self.activity, bg="#ffffff")
        form.pack(anchor="w", padx=20)

        self.donor_entry = self.create_input(form, "Donor Name")
        self.type_entry = self.create_input(form, "Donation Type")
        self.amount_entry = self.create_input(form, "Amount")

        tk.Button(
            self.activity,
            text="Submit Donation",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            relief="flat",
            padx=15,
            pady=8,
            command=self.submit_donation
        ).pack(anchor="w", padx=20, pady=20)




    def show_inventory_ui(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Inventory Management",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        form = tk.Frame(self.activity, bg="#ffffff")
        form.pack(anchor="w", padx=20)

        self.inv_item_entry = self.create_input(form, "Item Name")
        self.inv_category_entry = self.create_input(form, "Category (Food / Clothes / etc.)")
        self.inv_quantity_entry = self.create_input(form, "Quantity")
        self.inv_unit_entry = self.create_input(form, "Unit (kg / pcs / boxes)")
        self.inv_rate_entry = self.create_input(
            form,
            "Per Person Consumption / Day"
        )


        tk.Button(
            self.activity,
            text="Add / Update Item",
            font=("Segoe UI", 11, "bold"),
            bg="#059669",
            fg="#ffffff",
            relief="flat",
            padx=15,
            pady=8,
            command=self.submit_inventory_item
        ).pack(anchor="w", padx=20, pady=20)


    def show_distribution_ui(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Aid Distribution",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        form = tk.Frame(self.activity, bg="#ffffff")
        form.pack(anchor="w", padx=20)

        self.dist_item_entry = self.create_input(form, "Item Name")
        self.dist_quantity_entry = self.create_input(form, "Quantity to Distribute")

        tk.Button(
            self.activity,
            text="Distribute Aid",
            font=("Segoe UI", 11, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            relief="flat",
            padx=15,
            pady=8,
            command=self.submit_distribution
        ).pack(anchor="w", padx=20, pady=20)





    def submit_distribution(self):
        item = self.dist_item_entry.get().strip()
        quantity = self.dist_quantity_entry.get().strip()

        if not item or not quantity.isdigit():
            messagebox.showerror("Error", "Item name and numeric quantity required")
            return

        success, message = self.inventory_manager.distribute_item(
            item_name=item,
            quantity=int(quantity)
        )

        if success:
            Logger.log("AID_DISTRIBUTED", self.user)
            messagebox.showinfo("Success", message)
            self.dist_item_entry.delete(0, tk.END)
            self.dist_quantity_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Distribution Failed", message)




    def show_shelter_locations_ui(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Shelter Locations",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        form = tk.Frame(self.activity, bg="#ffffff")
        form.pack(anchor="w", padx=20)

        self.shelter_name = self.create_input(form, "Shelter Name")
        self.shelter_address = self.create_input(form, "Address")
        self.shelter_capacity = self.create_input(form, "Capacity")
        self.shelter_occupancy = self.create_input(form, "Current Occupancy")

        tk.Button(
            self.activity,
            text="Add Shelter Location",
            font=("Segoe UI", 11, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            relief="flat",
            padx=15,
            pady=8,
            command=self.submit_shelter
        ).pack(anchor="w", padx=20, pady=20)

        count = self.shelter_manager.count()
        tk.Label(
            self.activity,
            text=f"Total Shelters Registered: {count}",
            font=("Segoe UI", 11),
            bg="#ffffff",
            fg="#374151"
        ).pack(anchor="w", padx=20, pady=(10, 0))



    def submit_shelter(self):
        name = self.shelter_name.get().strip()
        address = self.shelter_address.get().strip()
        capacity = self.shelter_capacity.get().strip()
        occupancy = self.shelter_occupancy.get().strip()

        if not name or not capacity.isdigit() or not occupancy.isdigit():
            messagebox.showerror("Error", "Name, capacity, and occupancy must be valid")
            return

        shelter = ShelterLocation(
            name=name,
            address=address,
            capacity=int(capacity),
            occupancy=int(occupancy),
            created=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        self.shelter_manager.add_shelter(shelter)
        Logger.log("SHELTER_ADDED", self.user)

        messagebox.showinfo("Success", "Shelter location added")

        self.shelter_name.delete(0, tk.END)
        self.shelter_address.delete(0, tk.END)
        self.shelter_capacity.delete(0, tk.END)
        self.shelter_occupancy.delete(0, tk.END)

        self.navigate("Shelter Locations", self.buttons["Shelter Locations"])




    def calculate_total_donations(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, "donations.json")

            with open(path, "r") as f:
                data = json.load(f)

            total = 0
            for d in data:
                amount = d.get("amount")
                if isinstance(amount, int):
                    total += amount

            return total
        except:
            return 0


    def show_needs_ui(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Critical Needs Assessment",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        _, critical, low = self.inventory_manager.analyze_needs()

        if not critical:
            tk.Label(
                self.activity,
                text="No critical needs at the moment.",
                bg="#ffffff",
                fg="#059669",
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20)
            return

        for item in critical:
            text = f"{item['item']} ({item['category']}) — Qty: {item['quantity']}"
            tk.Label(
                self.activity,
                text=text,
                bg="#ffffff",
                fg="#dc2626",
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20, pady=4)




    def show_inventory_overview(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Inventory Overview",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        _, critical, low = self.inventory_manager.analyze_needs()

        try:
            items = self.inventory_manager.load_all()
        except:
            items = []

        if not items:
            tk.Label(
                self.activity,
                text="No inventory items found.",
                bg="#ffffff",
                fg="#6b7280",
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20)
            return

        for item in items:
            qty = item["quantity"]
            color = "#059669"
            if qty < 10:
                color = "#dc2626"
            elif qty < 25:
                color = "#f59e0b"

            text = f"{item['item']} ({item['category']}) — {qty} {item['unit']}"
            tk.Label(
                self.activity,
                text=text,
                bg="#ffffff",
                fg=color,
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20, pady=4)




    def show_donation_overview(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Donation Summary",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, "donations.json")
            with open(path, "r") as f:
                data = json.load(f)
        except:
            data = []

        if not data:
            tk.Label(
                self.activity,
                text="No donations recorded.",
                bg="#ffffff",
                fg="#6b7280",
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20)
            return

        total = 0
        for d in data:
            total += d.get("amount", 0)
            text = f"{d['timestamp']} — {d['donor']} — ₹{d['amount']}"
            tk.Label(
                self.activity,
                text=text,
                bg="#ffffff",
                fg="#374151",
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20, pady=3)

        tk.Label(
            self.activity,
            text=f"\nTotal Donations: ₹{total}",
            bg="#ffffff",
            fg="#2563eb",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", padx=20, pady=10)





    def show_volunteer_overview(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, pady=(30, 0), padx=5)

        tk.Label(
            self.activity,
            text="Volunteer Overview",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff",
            fg="#111827"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        volunteers = self.volunteer_manager.load_all()

        if not volunteers:
            tk.Label(
                self.activity,
                text="No volunteers registered.",
                bg="#ffffff",
                fg="#6b7280",
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20)
            return

        for v in volunteers:
            text = f"{v['name']} — {v['role']} — {v['phone']}"
            tk.Label(
                self.activity,
                text=text,
                bg="#ffffff",
                fg="#7c3aed",
                font=("Segoe UI", 11)
            ).pack(anchor="w", padx=20, pady=4)




    def show_inventory_overview(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            self.activity,
            text="Inventory Overview",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff"
        ).pack(anchor="w", padx=10, pady=10)

        columns = ("Item", "Category", "Quantity", "Unit", "Per Person/Day")
        tree = ttk.Treeview(self.activity, columns=columns, show="headings")
        tree.pack(fill="both", expand=True)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        items, _ = self.inventory_manager.analyze_needs(
            self.shelter_manager.total_population()
        )

        for item in items:
            tree.insert("", "end", values=(
                item["item"],
                item["category"],
                item["quantity"],
                item["unit"],
                item.get("per_person_per_day", "-")
            ))




    def show_needs_ui(self):
        if hasattr(self, "activity"):
            self.activity.destroy()

        self.activity = tk.Frame(self.content, bg="#ffffff")
        self.activity.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(
            self.activity,
            text="Critical Needs Assessment",
            font=("Segoe UI", 16, "bold"),
            bg="#ffffff"
        ).pack(anchor="w", padx=10, pady=10)

        columns = ("Item", "Available", "Required", "Shortfall")
        tree = ttk.Treeview(self.activity, columns=columns, show="headings")
        tree.pack(fill="both", expand=True)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        _, critical = self.inventory_manager.analyze_needs(
            self.shelter_manager.total_population()
        )

        for item in critical:
            tree.insert("", "end", values=(
                item["item"],
                item["quantity"],
                item["required_quantity"],
                item["shortfall"]
            ))





if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
