Prerequisites

FFmpeg: The project uses FFmpeg via the command line to embed subtitles in videos. Ensure it is installed and added to your PATH.

Conda: Recommended for managing AI and GPU dependencies.

=================================================================

Setup

Clone this repository or download the code.

Create the virtual environment using the provided whisper.yaml file:

====================================================================================

Bash

conda env create -f whisper.yaml

conda activate csi

Note: The environment includes support for PyTorch with CUDA 11.8 for GPU acceleration.

====================================================================================

Configuration

Open the main Python file and adjust the following variables in the configuration block:

WHISPER_MODEL: Defines the model size (e.g., "large", "medium").

FORCED_LANGUAGE: Set 'pt' for Portuguese or 'en' for English.

Paper_to_process: The path to the folder containing the original videos.

=========================================================================

Execution

Place your videos in the configured folder and run the script:

Bash

python your_script.py

The script will:

Transcribe the audio using the Whisper model.

Generate a temporary .srt file.

Create a new version of the video in the videos_subtitled folder with embedded subtitles.

Log the progress in videos_processed.json so that, in a future execution, the same files are not processed again.

====================


Jesus answered, ‘I am the way and the truth and the life. No-one comes to the Father except through me.

John 14:6 NIVUK

https://bible.com/bible/129/jhn.14.6.NVI

allancostans.blogspot.com 
