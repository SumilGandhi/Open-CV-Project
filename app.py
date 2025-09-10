# app.py - Web-based Virtual Painter using Streamlit
import streamlit as st
import cv2
import numpy as np
import os
import av
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
from HandTrackingModule import HandDetector

class VirtualPainterTransformer(VideoTransformerBase):
    def __init__(self):
        self.detector = HandDetector(detectionCon=0.85)
        self.drawColor = (255, 0, 255)  # Purple
        self.brushThickness = 15
        self.eraserThickness = 50
        self.xp, self.yp = 0, 0
        
        # Initialize canvas
        self.imgCanvas = np.zeros((720, 1280, 3), np.uint8)
        
        # Load header images
        self.load_header_images()
        
        # Initialize session state for color selection
        if 'selected_color' not in st.session_state:
            st.session_state.selected_color = (255, 0, 255)  # Purple default
        if 'brush_size' not in st.session_state:
            st.session_state.brush_size = 15
        if 'eraser_size' not in st.session_state:
            st.session_state.eraser_size = 50

    def load_header_images(self):
        folderPath = "header"
        self.overlayList = []
        if os.path.exists(folderPath):
            for img in os.listdir(folderPath):
                if img.endswith(('.png', '.jpg', '.jpeg')):
                    loaded_img = cv2.imread(f'{folderPath}/{img}')
                    if loaded_img is not None:
                        resized_img = cv2.resize(loaded_img, (1280, 125))
                        self.overlayList.append(resized_img)
        
        self.header = self.overlayList[0] if self.overlayList else np.zeros((125, 1280, 3), np.uint8)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Resize frame to match canvas
        img = cv2.resize(img, (1280, 720))
        img = cv2.flip(img, 1)
        
        # Update colors from session state
        self.drawColor = st.session_state.selected_color
        self.brushThickness = st.session_state.brush_size
        self.eraserThickness = st.session_state.eraser_size
        
        # Hand detection
        img = self.detector.findHands(img)
        lmList = self.detector.findPosition(img)

        if lmList:
            x1, y1 = lmList[8][1:]  # Index finger
            x2, y2 = lmList[12][1:]  # Middle finger

            # Check which fingers are up
            fingers = []
            # Check for each fingertip
            if len(lmList) > 20:
                # Thumb
                if lmList[4][1] > lmList[3][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)
                
                # Other fingers
                for tip in [8, 12, 16, 20]:
                    if lmList[tip][2] < lmList[tip - 2][2]:
                        fingers.append(1)
                    else:
                        fingers.append(0)
            else:
                fingers = [0] * 5

            # Clear canvas - All fingers up
            if len(fingers) >= 4 and all(fingers[:4]):
                self.imgCanvas = np.zeros((720, 1280, 3), np.uint8)
                self.xp, self.yp = 0, 0

            # Selection Mode – 2 fingers up (index and middle)
            if len(fingers) >= 3 and fingers[1] and fingers[2] and not fingers[3]:
                self.xp, self.yp = 0, 0
                cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), self.drawColor, cv2.FILLED)

            # Drawing Mode – Index finger up only
            elif len(fingers) >= 2 and fingers[1] and not fingers[2]:
                cv2.circle(img, (x1, y1), 15, self.drawColor, cv2.FILLED)
                if self.xp == 0 and self.yp == 0:
                    self.xp, self.yp = x1, y1

                if self.drawColor == (0, 0, 0):  # Eraser mode
                    cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, self.eraserThickness)
                    cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, self.eraserThickness)
                else:
                    cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, self.brushThickness)
                    cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, self.brushThickness)

                self.xp, self.yp = x1, y1

        # Combine canvas with webcam feed
        imgGray = cv2.cvtColor(self.imgCanvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(imgGray, 20, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, imgInv)
        img = cv2.bitwise_or(img, self.imgCanvas)

        # Display header if available
        if len(self.overlayList) > 0:
            img[0:125, 0:1280] = self.header

        return av.VideoFrame.from_ndarray(img, format="bgr24")

def main():
    st.set_page_config(
        page_title="Virtual Painter",
        page_icon="🎨",
        layout="wide"
    )

    st.title("🎨 Virtual Painter - Hand Tracking")
    st.markdown("Draw in the air using your index finger! Raise two fingers to enter selection mode.")

    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Color selection
        st.subheader("Colors")
        color_options = {
            "Purple": (255, 0, 255),
            "Blue": (255, 0, 0),
            "Green": (0, 255, 0),
            "Red": (0, 0, 255),
            "Yellow": (0, 255, 255),
            "White": (255, 255, 255),
            "Eraser": (0, 0, 0)
        }
        
        selected_color_name = st.selectbox("Select Color", list(color_options.keys()))
        st.session_state.selected_color = color_options[selected_color_name]
        
        # Color preview
        color_preview = np.full((50, 200, 3), st.session_state.selected_color, dtype=np.uint8)
        if selected_color_name == "Eraser":
            color_preview = np.full((50, 200, 3), (128, 128, 128), dtype=np.uint8)
            cv2.putText(color_preview, "ERASER", (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        st.image(color_preview, caption=f"Selected: {selected_color_name}")
        
        # Brush size
        st.subheader("Brush Settings")
        st.session_state.brush_size = st.slider("Brush Size", 5, 50, 15)
        st.session_state.eraser_size = st.slider("Eraser Size", 20, 100, 50)
        
        # Instructions
        st.subheader("📋 Instructions")
        st.markdown("""
        **Hand Gestures:**
        - ✋ **All fingers up**: Clear canvas
        - ✌️ **Index + Middle**: Selection mode
        - 👆 **Index only**: Draw/Paint
        
        **Tips:**
        - Keep your hand clearly visible
        - Use good lighting
        - Move slowly for better tracking
        """)
        
        # Clear canvas button
        if st.button("🗑️ Clear Canvas"):
            st.rerun()

    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # WebRTC streamer
        webrtc_ctx = webrtc_streamer(
            key="virtual-painter",
            mode=WebRtcMode.SENDRECV,
            video_transformer_factory=VirtualPainterTransformer,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
        )

    with col2:
        st.subheader("🎯 Status")
        if webrtc_ctx.state.playing:
            st.success("🔴 Camera Active")
            st.info("Ready to paint!")
        else:
            st.warning("📹 Camera Inactive")
            st.info("Click 'START' to begin")

        # Stats
        st.subheader("⚙️ Settings Summary")
        st.write(f"**Color:** {selected_color_name}")
        st.write(f"**Brush Size:** {st.session_state.brush_size}px")
        st.write(f"**Eraser Size:** {st.session_state.eraser_size}px")

    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit & OpenCV | Virtual Painter v2.0")

if __name__ == "__main__":
    main()
