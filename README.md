# 🎨 Virtual Painter Web App

A web-based virtual painting application using hand tracking and computer vision.

## 🌟 Features

- **Hand Tracking**: Paint using your index finger in the air
- **Multi-Color Support**: Purple, Blue, Green, Red, Yellow, White
- **Eraser Function**: Remove drawings with black color
- **Real-time Canvas**: Live drawing on webcam feed
- **Web Interface**: Easy-to-use controls and color selection
- **Gesture Controls**:
  - ✋ All fingers up: Clear canvas
  - ✌️ Index + Middle finger: Selection mode  
  - 👆 Index finger only: Draw/Paint

## 🚀 Local Development

### Prerequisites
- Python 3.8+
- Webcam access
- Good lighting for hand detection

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd virtual_painter
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
streamlit run app.py
```

5. Open your browser and go to `http://localhost:8501`

## 🌐 Web Deployment (Render)

### Quick Deploy
1. Fork this repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Use these settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
   - **Environment**: Python 3

### Environment Variables (Optional)
- `PORT`: Automatically set by Render
- `STREAMLIT_SERVER_HEADLESS`: `true`

## 📁 Project Structure

```
virtual_painter/
├── app.py                 # Main Streamlit web app
├── main.py               # Original OpenCV desktop version
├── HandTrackingModule.py # Hand detection utilities
├── requirements.txt      # Python dependencies
├── .streamlit/           # Streamlit configuration
│   └── config.toml
├── header/               # UI header images
│   ├── brush.png
│   ├── colors.png
│   └── ...
└── README.md            # This file
```

## 🛠️ Technology Stack

- **Backend**: Python, OpenCV, MediaPipe
- **Frontend**: Streamlit, HTML5 Canvas
- **Video Processing**: WebRTC, streamlit-webrtc
- **Hand Tracking**: MediaPipe Hands
- **Deployment**: Render Cloud Platform

## 🎯 How It Works

1. **Camera Access**: WebRTC captures your webcam feed
2. **Hand Detection**: MediaPipe identifies hand landmarks
3. **Gesture Recognition**: Analyzes finger positions for drawing modes
4. **Canvas Overlay**: Combines drawing canvas with live video
5. **Web Interface**: Streamlit provides user-friendly controls

## 🐛 Troubleshooting

### Common Issues:

1. **Camera not working**:
   - Ensure browser permissions for camera access
   - Check if other applications are using the camera

2. **Hand tracking poor**:
   - Ensure good lighting
   - Keep hand clearly visible
   - Avoid cluttered backgrounds

3. **Performance issues**:
   - Close other browser tabs
   - Ensure stable internet connection
   - Try reducing video quality if needed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- MediaPipe by Google for hand tracking
- OpenCV community for computer vision tools
- Streamlit for the amazing web framework
