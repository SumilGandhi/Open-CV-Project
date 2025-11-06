# 🎨 Virtual Painter - User Guide

Welcome to the Virtual Painter! This guide will walk you through how to use the application and its features.

## 🚀 Getting Started

1.  **Launch the App**: Open your terminal, navigate to the project folder, and run the following command:
    ```bash
    streamlit run app.py
    ```
2.  **Open in Browser**: The application will open in your web browser. Make sure to grant it permission to access your webcam.
3.  **Start the Stream**: Click the "START" button in the video feed to begin.

## 👉 Hand Gestures - The Core Controls

The application is controlled primarily through hand gestures. Make sure your hand is well-lit and clearly visible to the camera.

---

### 👆 Drawing Mode

**Gesture**: Raise **only your index finger**.

**Action**:
- Move your finger around to draw on the screen.
- The line will be drawn in the currently selected color.
- If the "Eraser" is active, this gesture will erase parts of the drawing.

![Drawing Gesture](https://i.imgur.com/3j6YJmE.png)

---

### ✌️ Selection Mode

**Gesture**: Raise your **index and middle fingers**, and keep your other fingers down.

**Action**:
- This mode allows you to change colors or select the eraser.
- A colored rectangle will appear around your fingertips.
- Move your hand into the header area at the top of the screen.
- Hover over one of the color swatches or the eraser icon to select it. The `header` image will change to indicate your selection.

![Selection Gesture](https://i.imgur.com/O8lS9aM.png)

---

## 🎛️ Sidebar Controls

The sidebar on the left provides additional controls to customize your drawing experience.

### Brush and Eraser Size
- **Brush Size**: Use the slider to adjust the thickness of the drawing line.
- **Eraser Size**: Use this slider to change the size of the eraser.

### Clear Canvas
- **🗑️ Clear Canvas**: Click this button to instantly wipe the entire canvas clean and start fresh.

## ✨ Tips for the Best Experience

-   **Good Lighting is Key**: The hand tracking works best in a well-lit environment. Avoid having a bright light source (like a window) behind you.
-   **Clear Background**: A simple, non-cluttered background helps the camera focus on your hand.
-   **Slow and Steady**: Move your hand smoothly and not too quickly for the most accurate tracking.
-   **Hand Position**: Keep your hand at a comfortable distance from the camera—not too close and not too far.

Enjoy painting in the air!
