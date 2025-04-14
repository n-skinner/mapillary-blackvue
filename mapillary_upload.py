import os
import subprocess
import datetime
import keyring as kr
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

blackvue_video_path = Path(r".\data")
blackvue_img_path = f"{blackvue_video_path}\\mapillary_sampled_video_frames"

cred = kr.get_credential("Mapillary", "")
mapillary_un = cred.username

try:
    for entry in blackvue_video_path.iterdir():
        entryPath = entry
        entryGPX = entryPath.with_suffix(".gpx")

        if entry.suffix.lower() == ".mp4":
            logging.info(f"Processing: {entry.name}")
            # Create GPX
            cmd = [
                "exiftool",
                "-GPSDateTime",
                "-ee",
                str(entryPath),
            ]
            output = subprocess.run(cmd, capture_output=True, text=True).stdout
            if output:  # we have GPSDateTime
                fields = output.split()
                date = fields[3].strip()
                hours = fields[4].strip()
                format = f"%Y:%m:%d%H:%M:%S{hours[-4:]}"  # catch errors
                timestamp = datetime.datetime.strptime(date + hours, format)

                isoTime = timestamp.isoformat()
                formattedTime = timestamp.strftime("%Y_%m_%d_%H_%M_%S_%f")

                try:
                    # Run ExifTool to create GPX
                    cmd = [
                        "exiftool",
                        "-m",
                        "-ee3",
                        "-p",
                        "C:/exiftool/gpx_wpt.fmt",
                        str(entryPath),
                    ]

                    # Run command
                    with open(entryGPX, "w") as gpx_file:
                        subprocess.run(cmd, stdout=gpx_file)
                    logging.info("GPX Created")

                except ValueError:
                    continue

                # Run Mapillary Tools to sample video
                cmd = [
                    "mapillary_tools",
                    "sample_video",
                    str(entryPath),
                    str(blackvue_img_path),
                    "--video_sample_distance=-1",
                    "--video_sample_interval",
                    "1",
                    "--video_start_time",
                    formattedTime,
                ]

                # Run command
                subprocess.run(cmd)
                logging.info("Videos Sampled")

                photoFolder = f"{blackvue_img_path}\\{entry.name}"

                # Run Exiftool to assign corrected GPX info to each image
                cmd = [
                    "exiftool",
                    f"-geotag={entryGPX}",
                    "-geotime<${DateTimeOriginal}+00:00",
                    str(photoFolder),
                ]

                # Run command
                result = subprocess.run(cmd, capture_output=True, text=True)

                # Add check for geotagging, upload fails without
                if result.returncode != 0:
                    logging.error(f"Geotagging failed: {result.stderr}")
                    raise RuntimeError("Geotagging failed, stopping script.")
                else:
                    logging.info("Geotagging successful")

                # Run Mapillary tools to upload images
                cmd = [
                    "mapillary_tools",
                    "process_and_upload",
                    str(photoFolder),
                    "--user_name",
                    mapillary_un,
                ]
                subprocess.run(cmd)
                logging.info(f"{entry.name} Uploaded Successfully\n\n")

except Exception as e:
    logging.error(e)
    raise
