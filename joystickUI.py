import customtkinter as ctk
import pygame

from joystickMapper import (
    create_virtual_joystick,
    destroy_virtual_joystick,
    start_mapping,
    stop_mapping,
)

class UI:
    def __init__(self, on_refresh):
        self.on_refresh = on_refresh

        self.preview_js = None
        self.selected_js = None
        self.running = False

        # FSM
        self.startup_state = "INIT"
        self.virtual_created = False
        self.hid_clear_ticks = 0

        # calibration
        self.auto_capture = False
        self.captured_min = [float("inf")] * 4
        self.captured_max = [float("-inf")] * 4

        # ───────── UI setup ─────────
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.app = ctk.CTk()
        self.app.title("Joystick Calibrator")
        self.app.geometry("460x760")
        self.app.resizable(False, False)
        self.app.minsize(460, 760)
        self.app.maxsize(460, 760)
        self.app.update_idletasks()
        self.app.geometry("460x700+0+0")

        ctk.CTkLabel(
            self.app,
            text="🎮 Joystick Calibrator",
            font=("Segoe UI", 18, "bold")
        ).pack(pady=10)

        ctk.CTkLabel(self.app, text="Select Physical Joystick:").pack()

        self.joystick_dropdown = ctk.CTkComboBox(self.app, values=["No Joystick"])
        self.joystick_dropdown.pack(pady=6)

        self.refresh_btn = ctk.CTkButton(
            self.app, text="Refresh Devices", command=self.refresh_joysticks
        )
        self.refresh_btn.pack(pady=4)

        # ───────── Calibration UI ─────────
        self.cal_frame = ctk.CTkFrame(self.app)
        self.cal_frame.pack(pady=10, padx=10, fill="x")

        # 🔥 CENTER GRID COLUMNS
        for col in range(4):
            self.cal_frame.columnconfigure(col, weight=1)

        ctk.CTkLabel(
            self.cal_frame,
            text="Axis Calibration (Min / Center / Max)",
            font=("Segoe UI", 13, "bold")
        ).grid(row=0, column=0, columnspan=4, pady=10, sticky="nsew")

        headers = ["Axis", "Min", "Center", "Max"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.cal_frame, text=h).grid(
                row=1, column=i, sticky="nsew"
            )

        self.entries = {}
        labels = ["Left X", "Left Y", "Right X", "Right Y"]

        for i, label in enumerate(labels):
            ctk.CTkLabel(
                self.cal_frame, text=label
            ).grid(row=i + 2, column=0, padx=6, pady=8, sticky="nsew")

            m = ctk.CTkEntry(self.cal_frame, width=50)
            c = ctk.CTkEntry(self.cal_frame, width=50)
            x = ctk.CTkEntry(self.cal_frame, width=50)

            m.insert(0, "-1.0")
            c.insert(0, "0.0")
            x.insert(0, "1.0")

            m.grid(row=i + 2, column=1, padx=12, pady=3, sticky="nsew")
            c.grid(row=i + 2, column=2, padx=12, pady=3, sticky="nsew")
            x.grid(row=i + 2, column=3, padx=12, pady=3, sticky="nsew")

            self.entries[i] = (m, c, x)

        # ───────── Tools ─────────
        tools = ctk.CTkFrame(self.app)
        tools.pack(pady=6)

        self.center_btn = ctk.CTkButton(tools, text="Set Center", command=self.set_center)
        self.center_btn.pack(side="left", padx=6)

        self.auto_btn = ctk.CTkButton(
            tools, text="Start Auto Min/Max", command=self.toggle_auto_capture
        )
        self.auto_btn.pack(side="left", padx=6)

        # ───────── Monitor ─────────
        monitor = ctk.CTkFrame(self.app)
        monitor.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(
            monitor,
            text="Live Axis Values",
            font=("Segoe UI", 13, "bold")
        ).pack(pady=6)

        self.axis_labels = {}
        for a in ["LX", "LY", "RX", "RY"]:
            lbl = ctk.CTkLabel(
                monitor, text=f"{a}: 0.000", font=("Consolas", 14)
            )
            lbl.pack(pady=2)  # 🔥 CENTERED (removed anchor="w")
            self.axis_labels[a] = lbl

        # ───────── Control ─────────
        self.toggle_btn = ctk.CTkButton(
            self.app, text="Start Mapping", command=self.toggle_mapping
        )
        self.toggle_btn.pack(pady=12)

        self.status_label = ctk.CTkLabel(self.app, text="", text_color="orange")
        self.status_label.pack(pady=4)

        # init
        self.refresh_joysticks()
        self._update_live_axes()
        self._fsm_tick()

        self.app.protocol("WM_DELETE_WINDOW", self._on_close)


    # ───────────────── FSM ─────────────────

    def _fsm_tick(self):
        names = self.on_refresh() or []
        device_count = len(names)
        physical_count = device_count - (1 if self.virtual_created else 0)

        # INIT → WAIT_DISCONNECT
        if self.startup_state == "INIT":
            if physical_count > 0:
                self.startup_state = "WAIT_DISCONNECT"
                self._set_ui_enabled(False)
                self.status_label.configure(
                    text="Disconnect physical joystick to free Slot 1"
                )

        # WAIT_DISCONNECT → WAIT_HID_CLEAR
        elif self.startup_state == "WAIT_DISCONNECT":
            if physical_count == 0:
                self.startup_state = "WAIT_HID_CLEAR"
                self.hid_clear_ticks = 0
                self.status_label.configure(
                    text="Waiting for system to release HID slots…"
                )

        # WAIT_HID_CLEAR → WAIT_RECONNECT
        elif self.startup_state == "WAIT_HID_CLEAR":
            if device_count == 0:
                self.hid_clear_ticks += 1
                if self.hid_clear_ticks >= 4:
                    create_virtual_joystick()
                    self.virtual_created = True
                    self.startup_state = "WAIT_RECONNECT"
                    self.status_label.configure(
                        text="Reconnect joystick (will become Slot 2)"
                    )

        # WAIT_RECONNECT → READY
        elif self.startup_state == "WAIT_RECONNECT":
            if physical_count > 0:
                self.startup_state = "READY"
                self._set_ui_enabled(True)
                self._bind_selected_joystick()
                self.status_label.configure(
                    text="Ready", text_color="lightgreen"
                )
            else:
                self.status_label.configure(
                    text="Reconnect joystick (will become Slot 2)"
                )

        self.app.after(300, self._fsm_tick)

    # ───────────────── Device handling ─────────────────

    def refresh_joysticks(self):
        names = self.on_refresh() or []
        self.joystick_dropdown.configure(
            values=names if names else ["No Joystick"]
        )

        # ONLY rebind if not already bound
        if not self.selected_js:
            self._bind_selected_joystick()


    def _bind_selected_joystick(self):
        self.preview_js = None
        self.selected_js = None

        for i in range(pygame.joystick.get_count()):
            js = pygame.joystick.Joystick(i)

            # skip virtual joystick
            if self.virtual_created and i == 0:
                continue

            js.init()  # ← CRITICAL
            self.preview_js = js
            self.selected_js = js
            self.joystick_dropdown.set(js.get_name())
            break


    # ───────────────── Misc ─────────────────

    def _set_ui_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for w in (
            self.joystick_dropdown,
            self.refresh_btn,
            self.toggle_btn,
            self.center_btn,
            self.auto_btn,
        ):
            w.configure(state=state)

        for e in self.entries.values():
            for x in e:
                x.configure(state=state)

    def _update_live_axes(self):
        if self.preview_js:
            pygame.event.pump()

            for i, key in enumerate(self.axis_labels):
                v = self.preview_js.get_axis(i)

                # update live display
                self.axis_labels[key].configure(
                    text=f"{key}: {v:+.3f}"
                )

                # auto min/max capture
                if self.auto_capture:
                    self.captured_min[i] = min(self.captured_min[i], v)
                    self.captured_max[i] = max(self.captured_max[i], v)

                    # 🔥 LIVE UI UPDATE
                    min_e, _, max_e = self.entries[i]

                    min_e.delete(0, "end")
                    min_e.insert(0, f"{self.captured_min[i]:.3f}")

                    max_e.delete(0, "end")
                    max_e.insert(0, f"{self.captured_max[i]:.3f}")

        self.app.after(50, self._update_live_axes)

    def set_center(self):
        if not self.preview_js:
            return
        pygame.event.pump()
        for i in range(4):
            e = self.entries[i][1]
            e.delete(0, "end")
            e.insert(0, f"{self.preview_js.get_axis(i):.3f}")

    def toggle_auto_capture(self):
        if not self.preview_js:
            return

        # START auto capture
        if not self.auto_capture:
            self.auto_capture = True
            self.captured_min = [float("inf")] * 4
            self.captured_max = [float("-inf")] * 4

            self.auto_btn.configure(text="Stop Auto Min/Max")
            self.toggle_btn.configure(state="disabled")  # 🔒 disable mapping

            self.status_label.configure(
                text="Move sticks to extremes…", text_color="orange"
            )

        # STOP auto capture → apply values
        else:
            self.auto_capture = False
            self.auto_btn.configure(text="Start Auto Min/Max")
            self.toggle_btn.configure(state="normal")  # 🔓 re-enable mapping

            for i in range(4):
                mn = self.captured_min[i]
                mx = self.captured_max[i]

                if mn == float("inf") or mx == float("-inf"):
                    continue

                min_e, _, max_e = self.entries[i]

                min_e.delete(0, "end")
                min_e.insert(0, f"{mn:.3f}")

                max_e.delete(0, "end")
                max_e.insert(0, f"{mx:.3f}")

            self.status_label.configure(
                text="Auto Min/Max captured", text_color="lightgreen"
            )

    def toggle_mapping(self):
        if not self.selected_js:
            self.status_label.configure(
                text="No physical joystick selected", text_color="orange"
            )
            return

        # START mapping
        if not self.running:
            calibration = {
                i: tuple(float(x.get()) for x in e)
                for i, e in self.entries.items()
            }
            start_mapping(self.selected_js, calibration)
            self.running = True
            self.toggle_btn.configure(text="Stop Mapping")
            self.status_label.configure(text="Mapping running", text_color="green")

        # STOP mapping → EXIT APP
        else:
            self._on_close()

    def _on_close(self):
        stop_mapping()
        if self.virtual_created:
            destroy_virtual_joystick()
        self.app.destroy()

    def run(self):
        self.app.mainloop()
