# Required dependencies
* Python3
* perl

## apt
`sudo apt install libffi-dev` (dependency of pysftp)
`sudo apt install imagemagick` (for creating a montage)
`sudo apt install libwww-perl` (for syncing the files on the piwigo server)

## through pip:
`pip3 install pysftp` (to upload securely to piwigo)

# Authentication
create a credentials.txt file with the following contents

sftpHost
sftpUsername
sftpPassword
piwigoBaseURL
piwigoAdminUserName
piwigoAdminPassword

# Memory

On Raspberry Pi 3B+, there wasn't enough memory available to render all overlays.
Configure these settings in `/boot/config.txt` to fix:

```
gpu_mem=256 # Bump GPU memory up a bit to use the below setting
dispmanx_offline=1 # off screen render buffers
```
