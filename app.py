# app.py - Web-based Virtual Painter using Streamlit
import streamlit as st
import cv2
import numpy as np
import av
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode
from HandTrackingModule import HandDetector

WINDOW_W, WINDOW_H = 1280, 720
HEADER_H = 125

# Color options
color_options = [
    {"name": "Purple", "bgr": (255, 0, 255)},
    {"name": "Green",  "bgr": (0, 255, 0)},
    {"name": "Red",    "bgr": (0, 0, 255)},
    {"name": "Yellow", "bgr": (0, 255, 255)},
    {"name": "Eraser", "bgr": (0, 0, 0)},
]

def create_color_header(selected_idx=0):
    """Create header with color swatches programmatically"""
    header = np.ones((HEADER_H, WINDOW_W, 3), np.uint8) * 50  # Dark gray background
    
    num_colors = len(color_options)
    region_width = WINDOW_W // num_colors
    
    for i, option in enumerate(color_options):
        left = i * region_width
        right = (i + 1) * region_width
        
        # Draw color rectangle
        color = option["bgr"]
        if option["name"] == "Eraser":
            # Draw eraser as light gray with diagonal lines
            cv2.rectangle(header, (left + 10, 10), (right - 10, HEADER_H - 10), (200, 200, 200), -1)
            cv2.line(header, (left + 10, 10), (right - 10, HEADER_H - 10), (100, 100, 100), 3)
            cv2.line(header, (right - 10, 10), (left + 10, HEADER_H - 10), (100, 100, 100), 3)
        else:
            cv2.rectangle(header, (left + 10, 10), (right - 10, HEADER_H - 10), color, -1)
        
        # Add text label
        text_color = (255, 255, 255) if option["name"] != "Eraser" else (0, 0, 0)
        cv2.putText(header, option["name"], (left + 30, HEADER_H - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        # Highlight selected color with a white border
        if i == selected_idx:
            cv2.rectangle(header, (left + 5, 5), (right - 5, HEADER_H - 5), (255, 255, 255), 5)
    
    return header

class VirtualPainterTransformer(VideoTransformerBase):
    def __init__(self):
        self.detector = HandDetector(detectionCon=0.85)
        self.brushThickness = 15
        self.eraserThickness = 50
        self.xp, self.yp = 0, 0
        
        # Initialize canvas
        self.imgCanvas = np.zeros((WINDOW_H, WINDOW_W, 3), np.uint8)
        
        # Initialize color selection
        self.current_color_idx = 0
        self.drawColor = color_options[self.current_color_idx]["bgr"]
        self.header = create_color_header(self.current_color_idx)

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Resize frame to match canvas
        img = cv2.resize(img, (WINDOW_W, WINDOW_H))
        img = cv2.flip(img, 1)
        
        # Hand detection
        img = self.detector.findHands(img)
        lmList = self.detector.findPosition(img)

        if lmList:
            x1, y1 = lmList[8][1:]  # Index finger tip
            x2, y2 = lmList[12][1:]  # Middle finger tip
            
            # Check which fingers are up
            fingers = []
            tip_ids = [4, 8, 12, 16, 20]
            # Thumb
            if lmList[tip_ids[0]][1] > lmList[tip_ids[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)
            # 4 Fingers
            for id in range(1, 5):
                if lmList[tip_ids[id]][2] < lmList[tip_ids[id] - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
            
            # Clear canvas if all 5 fingers are up
            if sum(fingers) == 5:
                self.imgCanvas = np.zeros((WINDOW_H, WINDOW_W, 3), np.uint8)
                self.xp, self.yp = 0, 0
            
            # Selection Mode: Index and Middle fingers are up, Ring finger is down
            if fingers[1] and fingers[2] and not fingers[3]:
                self.xp, self.yp = 0, 0
                cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), self.drawColor, cv2.FILLED)
                
                # If in the header area, select color
                if y1 < HEADER_H:
                    region_width = WINDOW_W // len(color_options)
                    for i, option in enumerate(color_options):
                        left = i * region_width
                        right = left + region_width
                        if left < x1 < right:
                            self.current_color_idx = i
                            self.drawColor = option["bgr"]
                            self.header = create_color_header(self.current_color_idx)
                            break

            # Drawing Mode: Only Index finger is up
            elif fingers[1] and not fingers[2]:
                cv2.circle(img, (x1, y1), 15, self.drawColor, cv2.FILLED)
                if self.xp == 0 and self.yp == 0:
                    self.xp, self.yp = x1, y1

                thickness = self.eraserThickness if self.drawColor == (0, 0, 0) else self.brushThickness
                cv2.line(img, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)
                cv2.line(self.imgCanvas, (self.xp, self.yp), (x1, y1), self.drawColor, thickness)

                self.xp, self.yp = x1, y1

        # Combine canvas with webcam feed
        imgGray = cv2.cvtColor(self.imgCanvas, cv2.COLOR_BGR2GRAY)
        _, imgInv = cv2.threshold(imgGray, 20, 255, cv2.THRESH_BINARY_INV)
        imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
        img = cv2.bitwise_and(img, imgInv)
        img = cv2.bitwise_or(img, self.imgCanvas)

        # Display header
        img[0:HEADER_H, 0:WINDOW_W] = self.header

        return av.VideoFrame.from_ndarray(img, format="bgr24")

def main():
    st.set_page_config(
        page_title="Virtual Painter",
        page_icon="🎨",
        layout="wide"
    )

    st.title("🎨 Virtual Painter - Hand Tracking")
    st.markdown("Draw in the air using your index finger! Use two fingers (index + middle) to select colors from the header.")

    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Camera source selection
        st.subheader("📹 Camera Source")
        camera_source = st.radio(
            "Select Camera",
            ["Webcam (Browser)", "Phone Camera (IP)"],
            help="For phone camera, install 'IP Webcam' app on your phone"
        )
        
        phone_ip = ""
        if camera_source == "Phone Camera (IP)":
            st.info("📱 **Phone Camera Setup:**\n1. Install 'IP Webcam' app from Play Store/App Store\n2. Open app and tap 'Start Server'\n3. Note the IP address shown (e.g., http://192.168.1.5:8080)\n4. Enter it below:")
            phone_ip = st.text_input("Phone Camera URL", placeholder="http://192.168.1.5:8080/video")
            
            if phone_ip and not phone_ip.startswith("http"):
                st.warning("⚠️ URL should start with http://")
        
        # Color info
        st.info("**Available Colors:**\n- Purple\n- Green\n- Red\n- Yellow\n- Eraser")

        # Brush size
        st.subheader("Brush Settings")
        brush_size = st.slider("Brush Size", 5, 50, 15)
        eraser_size = st.slider("Eraser Size", 20, 100, 50)
        
        # Instructions
        st.subheader("📋 Instructions")
        st.markdown("""
        **Hand Gestures:**
        - ✋ **All 5 fingers up**: Clear canvas
        - ✌️ **Index + Middle (ring down)**: Selection mode - move to header area to select color
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
        # WebRTC streamer for browser webcam
        if camera_source == "Webcam (Browser)":
            webrtc_ctx = webrtc_streamer(
                key="virtual-painter",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=VirtualPainterTransformer,
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
            )
            
            # Update transformer with UI values
            if webrtc_ctx.video_transformer:
                webrtc_ctx.video_transformer.brushThickness = brush_size
                webrtc_ctx.video_transformer.eraserThickness = eraser_size
        
        # Phone camera via IP
        else:
            if phone_ip:
                st.info("📱 Phone camera mode - Processing video from: " + phone_ip)
                
                # Create placeholder for video
                frame_placeholder = st.empty()
                stop_button = st.button("⏹️ Stop Camera")
                
                # Initialize phone camera processor
                if 'phone_running' not in st.session_state:
                    st.session_state.phone_running = False
                
                if not stop_button and phone_ip:
                    try:
                        # Format URL - ensure it ends with /video for mjpeg stream
                        camera_url = phone_ip if phone_ip.endswith('/video') else phone_ip.rstrip('/') + '/video'
                        
                        # Use CAP_FFMPEG backend for better MJPEG stream handling
                        cap = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)
                        
                        # Set buffer size to 1 to reduce latency
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        if cap.isOpened():
                            st.session_state.phone_running = True
                            
                            # Initialize processor
                            processor = VirtualPainterTransformer()
                            processor.brushThickness = brush_size
                            processor.eraserThickness = eraser_size
                            
                            while st.session_state.phone_running and not stop_button:
                                ret, frame = cap.read()
                                if not ret:
                                    st.error("❌ Failed to read from phone camera. Check the URL and connection.")
                                    break
                                
                                # Convert to av.VideoFrame and process
                                import av
                                av_frame = av.VideoFrame.from_ndarray(frame, format="bgr24")
                                processed_frame = processor.recv(av_frame)
                                
                                # Display processed frame
                                frame_placeholder.image(processed_frame.to_ndarray(format="bgr24"), channels="BGR", use_container_width=True)
                            
                            cap.release()
                        else:
                            st.error("❌ Could not connect to phone camera. Make sure:\n- Phone and computer are on same WiFi\n- IP Webcam app is running\n- URL is correct")
                    except Exception as e:
                        st.error(f"❌ Error connecting to phone camera: {str(e)}")
                else:
                    st.warning("⚠️ Enter phone camera URL to start")
            else:
                st.warning("⚠️ Please enter your phone camera URL above")

    with col2:
        st.subheader("🎯 Status")
        if camera_source == "Webcam (Browser)":
            if 'webrtc_ctx' in locals() and webrtc_ctx.state.playing:
                st.success("🔴 Camera Active")
                st.info("Ready to paint!")
            else:
                st.warning("📹 Camera Inactive")
                st.info("Click 'START' to begin")
        else:
            if phone_ip:
                st.success("📱 Phone Camera Mode")
                st.info("Streaming from phone")
            else:
                st.warning("⚠️ Enter phone URL")

        # Stats
        st.subheader("⚙️ Settings")
        st.write(f"**Brush Size:** {brush_size}px")
        st.write(f"**Eraser Size:** {eraser_size}px")

    # Footer
    st.markdown("---")
    st.markdown("Made with ❤️ using Streamlit & OpenCV | Virtual Painter v2.0")

if __name__ == "__main__":
    main()
