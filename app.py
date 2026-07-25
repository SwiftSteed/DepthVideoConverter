"""
HuggingFace Spaces entry point.

Push this repo to a Space with the Gradio SDK and it just works.
Free Spaces are CPU-only — Small model runs ~5 min for a 15s clip.
"""

from depth_video_converter import create_ui

demo = create_ui()

if __name__ == "__main__":
    demo.launch()
