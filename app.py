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

    def _get_fingers_up(self, lmList):
        """Helper function to determine which fingers are up."""
        fingers = []
        if not lmList:
            return fingers

        # Landmark IDs for the tips of the fingers
        tip_ids = [4, 8, 12, 16, 20]

        # Thumb: Check if the thumb tip is to the left (for a right hand) of the joint below it.
        # This logic assumes a horizontally flipped image of a right hand.
        if lmList[tip_ids[0]][1] < lmList[tip_ids[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Other 4 fingers: Check if the tip is above the joint below it.
        for id in range(1, 5):
            if lmList[tip_ids[id]][2] < lmList[tip_ids[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Resize frame to match canvas
        img = cv2.resize(img, (1280, 720))
        img = cv2.flip(img, 1)
        
        # Hand detection
        img = self.detector.findHands(img)
        lmList = self.detector.findPosition(img)

        if lmList:
            fingers = self._get_fingers_up(lmList)
            
            x1, y1 = lmList[8][1:]  # Index finger tip
            x2, y2 = lmList[12][1:] # Middle finger tip

            # Selection Mode: Index and Middle fingers are up, Ring finger is down.
            if fingers[1] and fingers[2] and not fingers[3]:
                self.xp, self.yp = 0, 0
                
                # If in the header area, select color
                if y1 < 125:
                    if 200 < x1 < 350:  # Purple
                        self.drawColor = (255, 0, 255)
                        self.header = self.overlayList[0] if len(self.overlayList) > 0 else self.header
                    elif 400 < x1 < 550:  # Blue
                        self.drawColor = (255, 0, 0)
                        self.header = self.overlayList[1] if len(self.overlayList) > 1 else self.header
                    elif 600 < x1 < 750:  # Green
                        self.drawColor = (0, 255, 0)
                        self.header = self.overlayList[2] if len(self.overlayList) > 2 else self.header
                    elif 800 < x1 < 950:  # Red
                        self.drawColor = (0, 0, 255)
                        self.header = self.overlayList[3] if len(self.overlayList) > 3 else self.header
                    elif 1000 < x1 < 1150:  # Eraser
                        self.drawColor = (0, 0, 0)
                        self.header = self.overlayList[4] if len(self.overlayList) > 4 else self.header

                cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), self.drawColor, cv2.FILLED)

            # Drawing Mode: Only Index finger is up.
            elif fingers[1] and not fingers[2]:
                cv2.circle(img, (x1, y1), 15, self.drawColor, cv2.FILLED)
                if self.xp == 0 and self.yp == 0:
                    self.xp, self.yp = x1, y1

                thickness = self.eraserThickness if self.drawColor == (0, 0, 0) else self.brushThickness
                cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)
                cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)

                self.xp, self.yp = x1, y1
            
            else:
                # Reset drawing point if not in a specific mode
                self.xp, self.yp = 0, 0

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
        
        # This part is now for display purposes, as gestures control the color
        st.info("Use hand gestures in the video feed to select colors.")

        # Brush size
        st.subheader("Brush Settings")
        brush_size = st.slider("Brush Size", 5, 50, 15)
        eraser_size = st.slider("Eraser Size", 20, 100, 50)
        
        # Instructions
        st.subheader("📋 Instructions")
        st.markdown("""
        **Hand Gestures:**
        - ✌️ **Index + Middle**: Selection mode (move into the header to select a color)
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
    
    if webrtc_ctx.video_transformer:
        webrtc_ctx.video_transformer.brushThickness = brush_size
        webrtc_ctx.video_transformer.eraserThickness = eraser_size

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
        st.write(f"**Brush Size:** {brush_size}px")
        st.write(f"**Eraser Size:** {eraser_size}px")

    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit & OpenCV | Virtual Painter v2.0")

if __name__ == "__main__":
    main()
