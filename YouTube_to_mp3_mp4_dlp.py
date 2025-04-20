import yt_dlp
import os
import shutil
from pathlib import Path
import time
import subprocess
import re

def download_video_or_audio(url, mode, convert):
    try:
        print(f"Downloading: {url}")

        downloads_path = str(Path.home() / "Downloads")
        working_dir = os.getcwd()
        ffmpeg_folder = os.path.join(working_dir, "PATH_Program")  # Path to ffmpeg folder

        # MP3 download options
        if mode == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'ffmpeg_location': ffmpeg_folder,
                'quiet': False,
                'noplaylist': True,
                'outtmpl': os.path.join(working_dir, '%(title)s.%(ext)s'),
            }

        # MP4 download options
        else:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'ffmpeg_location': ffmpeg_folder,
                'quiet': False,
                'noplaylist': True,
                'outtmpl': os.path.join(working_dir, '%(title)s.%(ext)s'),
            }

        # Download using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if mode == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'
            elif info.get('ext') and not filename.endswith(info['ext']):
                filename += f".{info['ext']}"

        target_path = filename

        # Optionally re-encode MP4 from non-H.264 codecs
        if mode == 'mp4' and convert:
            ffmpeg_path = os.path.join(ffmpeg_folder, 'ffmpeg.exe')
            probe_cmd = f'"{ffmpeg_path}" -hide_banner -i "{target_path}" 2>&1'
            probe_output = os.popen(probe_cmd).read()

            if 'Video: h264' not in probe_output:
                print("Non-H.264 codec detected. Converting to H.264 for compatibility...")

                temp_output = os.path.join(working_dir, "temp_output.mp4")

                # Get duration
                duration_cmd = f'"{ffmpeg_path}" -i "{target_path}" 2>&1'
                duration_output = os.popen(duration_cmd).read()
                match = re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)', duration_output)
                if match:
                    h, m, s = map(float, match.groups())
                    total_seconds = h * 3600 + m * 60 + s
                else:
                    total_seconds = None

                convert_cmd = [
                    ffmpeg_path,
                    "-y",
                    "-i", target_path,
                    "-c:v", "libx264",
                    "-preset", "slow",
                    "-crf", "18",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    temp_output
                ]

                process = subprocess.Popen(convert_cmd, stderr=subprocess.PIPE, universal_newlines=True)

                for line in process.stderr:
                    if "time=" in line:
                        match = re.search(r'time=(\d+):(\d+):(\d+\.\d+)', line)
                        if match and total_seconds:
                            ch, cm, cs = map(float, match.groups())
                            current = ch * 3600 + cm * 60 + cs
                            percent = (current / total_seconds) * 100
                            print(f"\rConverting to H.264... {percent:.2f}% complete", end='')

                process.wait()
                print("\rConverting to H.264... 100.00% complete")

                if process.returncode == 0:
                    os.remove(target_path)
                    os.rename(temp_output, target_path)
                    print("Conversion complete.")
                else:
                    print("Conversion failed.")
                    print(process.stderr.read())
                    return

        # Move to Downloads
        final_path = os.path.join(downloads_path, os.path.basename(target_path))
        shutil.move(target_path, final_path)

        # Touch timestamp
        current_time = time.time()
        os.utime(final_path, (current_time, current_time))

        print(f"\nMoved to: {final_path}")
        print("Download complete!\n")

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    while True:
        video_url = input("Enter the YouTube video URL (or type 'exit' to quit): ").strip()
        if video_url.lower() in ['exit', 'quit', 'q']:
            break
        elif video_url:
            mode = ''
            while mode not in ['mp3', 'mp4', '3', '4']:
                mode = input("Do you want to download it as an MP3 or MP4 file? (type 'mp3', 'mp4', '3' or '4'): ").strip().lower()
            final_mode = 'mp3' if mode in ['mp3', '3'] else 'mp4'

            convert = False
            if final_mode == 'mp4':
                ask_convert = ''
                while ask_convert not in ['yes', 'no', 'y', 'n']:
                    ask_convert = input("Do you want to convert the video to H.264 for better compatibility? (yes/no): ").strip().lower()
                convert = ask_convert in ['yes', 'y']

            download_video_or_audio(video_url, final_mode, convert)
        else:
            print("Please enter a valid URL.")