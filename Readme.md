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
