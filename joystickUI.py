import customtkinter as ctk

class UI:
    def __init__(self, on_start, on_stop, on_refresh):
        """
        UI initializer.
        :param on_start: function(selected_joystick, calibration_dict)
        :param on_stop: function()
        :param on_refresh: function() -> list of joystick names
        """
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_refresh = on_refresh
        self.running = False

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.app = ctk.CTk()
        self.app.title("Joystick Calibrator")
        self.app.geometry("420x480")

        # Title
        ctk.CTkLabel(self.app, text="🎮 Joystick Calibrator",
                     font=("Segoe UI", 18, "bold")).pack(pady=10)

        # Joystick selection
        ctk.CTkLabel(self.app, text="Select Joystick:").pack()
        self.joystick_dropdown = ctk.CTkComboBox(self.app, values=["Click Refresh"])
        self.joystick_dropdown.pack(pady=10)
        ctk.CTkButton(self.app, text="Refresh Devices", command=self.refresh_joysticks).pack(pady=5)

        # Calibration frame
        frame = ctk.CTkFrame(self.app)
        frame.pack(pady=10)
        ctk.CTkLabel(frame, text="Axis Calibration", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=3, pady=5)

        self.entries = {}
        labels = ["Left Stick X", "Left Stick Y", "Right Stick X", "Right Stick Y"]
        default_mins = ["-1.0", "-1.0", "-0.32", "-1.0"]
        default_maxs = ["1.0", "1.0", "1.0", "1.0"]

        for i, label in enumerate(labels):
            ctk.CTkLabel(frame, text=label).grid(row=i+1, column=0, padx=5, pady=4, sticky="w")
            min_entry = ctk.CTkEntry(frame, width=80)
            min_entry.insert(0, default_mins[i])
            min_entry.grid(row=i+1, column=1, padx=3, pady=4)
            max_entry = ctk.CTkEntry(frame, width=80)
            max_entry.insert(0, default_maxs[i])
            max_entry.grid(row=i+1, column=2, padx=3, pady=4)
            self.entries[i] = (min_entry, max_entry)

        # Start/Stop toggle button
        self.toggle_btn = ctk.CTkButton(self.app, text="Start Virtual Joystick", command=self.toggle_mapper)
        self.toggle_btn.pack(pady=10)

        # Status label
        self.status_label = ctk.CTkLabel(self.app, text="Idle", text_color="gray")
        self.status_label.pack(pady=0)

        # Initial refresh
        self.refresh_joysticks()

    # ──────────── Event Handlers ──────────── #
    def refresh_joysticks(self):
        try:
            names = self.on_refresh()
            if not names:
                names = ["No Joystick Found"]
            self.joystick_dropdown.configure(values=names)
            self.joystick_dropdown.set(names[0])
            self.status_label.configure(text="Devices refreshed", text_color="lightblue")
        except Exception as e:
            self.status_label.configure(text=f"Error: {e}", text_color="red")

    def toggle_mapper(self):
        if not self.running:
            try:
                selected = self.joystick_dropdown.get()
                calibration = {
                    0: (float(self.entries[0][0].get()), float(self.entries[0][1].get())),  # LX
                    1: (float(self.entries[1][0].get()), float(self.entries[1][1].get())),  # LY
                    2: (float(self.entries[2][0].get()), float(self.entries[2][1].get())),  # RX
                    3: (float(self.entries[3][0].get()), float(self.entries[3][1].get())),  # RY
                }

                self.on_start(selected, calibration)
                self.running = True
                self.toggle_btn.configure(text="Stop Virtual Joystick")
                self.status_label.configure(text="Running...", text_color="green")

            except Exception as e:
                self.status_label.configure(text=f"Error: {e}", text_color="red")
        else:
            try:
                self.on_stop()
                self.running = False
                self.toggle_btn.configure(text="Start Virtual Joystick")
                self.status_label.configure(text="Stopped", text_color="gray")
            except Exception as e:
                self.status_label.configure(text=f"Error: {e}", text_color="red")

    def run(self):
        self.app.mainloop()
