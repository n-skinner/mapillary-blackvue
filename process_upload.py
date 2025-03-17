import os
import subprocess
import datetime
import keyring as kr

blackvue_video_path = r'.\data'
blackvue_img_path = f"{blackvue_video_path}\\mapillary_sampled_video_frames"

cred = kr.get_credential("Mapillary","")
mapillary_un = cred.username

try:
    for entry in os.listdir(blackvue_video_path):
        entryPath = f"{blackvue_video_path}\\{entry}"
        entryGPX = f"{entryPath[:-4]}.gpx"

        if entry[-3:] == 'mp4' or entry[-3:] == 'MP4':
            print(f"Processing: {entry}")
            filename = entry[:-7]
            cmd = f'exiftool -GPSDateTime -ee "{blackvue_video_path}\\{entry}"'
            output = subprocess.check_output(cmd, shell=True)
            if len(output) != 0:  # we have GPSDateTime
                fields = output.decode().split()
                date = fields[3].strip()
                hours = fields[4].strip()
                format = f"%Y:%m:%d%H:%M:%S{hours[-4:]}"  # this end characters were causing problems if it wasn't .00Z
                timestamp = datetime.datetime.strptime(date + hours, format)
                
                isoTime = timestamp.isoformat()
                formattedTime = timestamp.strftime('%Y_%m_%d_%H_%M_%S_%f')

                try:
                    cmd = f'exiftool -m -ee3 -p C:\exiftool\gpx_wpt.fmt "{entryPath}" > "{entryGPX}"'
                    os.system(cmd)
                    print('gpx Created')
                except ValueError:
                    continue

                cmd = f'mapillary_tools sample_video {entryPath} {blackvue_img_path} --video_sample_distance=-1 --video_sample_interval 1 --video_start_time {formattedTime}'
                os.system(cmd)
                print('Videos Sampled')

                photoFolder = f"{blackvue_img_path}\\{entry}"

                cmd = 'exiftool -geotag=' + entryGPX + ' "-geotime<${DateTimeOriginal}+00:00" ' + photoFolder
                os.system(cmd)

                cmd = f"mapillary_tools process_and_upload {photoFolder} --user_name {mapillary_un}"
                os.system(cmd)
                print(f"{entry} Uploaded Successfully\n\n")

except Exception as e:
    print(e.args[0])
    pass