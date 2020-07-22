
## Install
#### pip
`pip install pgesmd_self_access`
#### source
`git clone https://github.com/JPHutchins/pgesmd_self_access`

`cd pgesmd_self_access`

Virtual environment is optional but suggested if you are fiddling around:

`python3 -m venv venv`

`source venv/bin/activate`

Install the dependencies:

`pip install -r requirements.txt`

## Access Your Data
In order to listen for message from the PGE server you will need to provide the path to the SSL certificate (or symlink) that you provided to PGE.  For example, the files (or symlinks) could be in `~/pgesmd_self_access/cert/cert.crt` and `~/pgesmd_self_access/cert/private.key`.

Create a file `~/pgesmd_self_access/auth/auth.json`.  The JSON needs these keys:
```
{
  "third_party_id" : string, from PGE
  "client_id" : string, from PGE after completing registration
  "client_secret" : string, from PGE after completing registration
  "cert_crt_path" : string, like above
  "cert_key_path" : string, like above
}
```
You may test some commands in the REPL to verify that everything is set up correctly.
```
from pgesmd_self_access.api import SelfAccessApi
pge_api = SelfAccessApi.auth( < full path to the auth.json > ) # for example, /home/jp/pgesmd_self_access/auth/auth.json
pge_api.get_service_status()
```
In order to listen for the messages from PGE you will need to forward port 443 to the server that this module runs at (default) port 7999.
Once it is open you can start the server.
```
from pgesmd_self_access.api import SelfAccessApi
from pgesmd_self_access.server import SelfAccessServer
from pgesmd_self_access.helpers import save_espi_xml
pge_api = SelfAccessApi.auth( < full path to the auth.json > )
SelfAccessServer(pge_api, save_file=save_espi_xml)
```
The PGE server usually takes between 10-40 seconds to package and send the message. The helper function will save the response XML in your current working directory.  You may like to see helpers.parse_espi_xml for more possibilities.


