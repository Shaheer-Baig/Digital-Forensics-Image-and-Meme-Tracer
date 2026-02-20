# Digital Forensic Image Tracer

A tool to trace the origin of memes and images on Reddit and Pinterest using OCR and Reverse Image Search.

## Features
- **Hybrid Search**: Uses OCR (Text) and Visual Search (Reverse Image) to find matches.
- **Forensic Timeline**: Identifies the earliest known upload date.
- **Modern GUI**: Dark-mode interface built with CustomTkinter.
- **Metadata Extraction**: Automatically fetches upload dates and usernames.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs PyTorch and EasyOCR, which may take a few minutes.*

2.  **Run the Application**:
    ```bash
    python gui.py
    ```

## Usage
1.  Click **Select Image** to upload a meme or photo.
2.  Click **Start Trace**.
3.  Wait for the tool to scan Reddit, Pinterest, and the Web.
4.  Review the **Trace Results** list. The earliest match is highlighted in green.
5.  Click **Open Link** to verify the source.

## Troubleshooting
- **No matches found?** Try an image with clearer text or a more distinct subject.
- **Slow search?** The tool scrapes Google, which can be slow. Please be patient.
