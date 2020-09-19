# WufooExtractor

WufooExtractor is an internal tool to extract Wufoo form data for Khan academy into language-sorted XLSX files.

### How to install

First, acquire the Wufoo API key (format: `XXXX-XXXX-XXXX-XXXX`) from Khan Academy and save it in `apikey.txt`.

Then,
```
pip3 install -r requirements.txt
```

After that, you can run the extractor:

```
python3 WufooCSVExport.py
```

That should generate all the XLSX files in the current directory.

We have a systemd timer & service that allows you to automatically run the update script periodically. In order to install, use
```
./install-systemd-service.sh
```

You might need to modify `/etc/systemd/system/WufooUpdate.service` and `/etc/systemd/system/WufooUpdate.timer` to fit your system configuration. After that `sudo systemctl daemon-reload`.

In order to run the service manually,
```
sudo systemctl start WufooUpdate.service
```
