# Controller Stick Drift Calibrator

A Windows utility that detects, visualizes, and compensates for analog stick drift in game controllers by creating a calibrated virtual controller output.

## Download

📦 Download the latest release:

[Gumroad Download] https://maverick0071.gumroad.com/l/joystick-calibrator

No source code setup required. Simply download and run the packaged application.

## Overview

Controller stick drift is a common issue where analog sticks register movement even when untouched. This can make games difficult or impossible to play accurately.

This project provides a software-based solution that:

* Detects analog stick drift in real time
* Visualizes controller input
* Allows deadzone and calibration adjustments
* Maps corrected inputs to a virtual controller
* Extends the usable lifespan of affected controllers

---

## Demonstration

🎥 **YouTube Demo**

https://www.youtube.com/watch?v=7M7Xmpmnsno

---

## Features

* Real-time analog stick monitoring
* Drift detection and visualization
* Adjustable deadzone configuration
* Input remapping and correction
* Virtual controller output using ViGEm
* User-friendly graphical interface
* Works without requiring hardware modification

---

## How It Works

Physical Controller
        ↓
Input Capture
        ↓
Drift Detection
        ↓
Calibration & Deadzone Processing
        ↓
Virtual Controller Output
        ↓
Game/Application

The application continuously reads raw controller input, applies calibration and drift compensation algorithms, and forwards corrected values through a virtual controller interface.

---

## Technologies Used

* Python
* Tkinter
* ViGEm Virtual Gamepad Framework
* Pygame

---

## Use Cases

* Repairing stick drift without opening the controller
* Extending controller lifespan
* Improving gaming accuracy
* Testing controller behavior and input quality

---

## Installation

### Clone the repository

git clone https://github.com/Maverick572/controller-stick-drift-calibrator.git
cd controller-stick-drift-calibrator

### Install dependencies

pip install -r requirements.txt

### Run the application

python main.py

---

## Screenshots

<img width="573" height="985" alt="image" src="https://github.com/user-attachments/assets/6215993f-8c48-4a1c-b5e3-ce37b39f5f02" />

---

## Future Improvements

* Calibration profile saving
* Automatic drift detection
* Advanced response curve customization
* Multi-controller support
* Export/import calibration presets

---

## Project Motivation

Many controllers become unusable due to stick drift despite being otherwise functional. This project was developed as a software-first solution to reduce hardware waste and provide gamers with an accessible method of restoring controller usability.

---

## License

This project is licensed under the MIT License.
