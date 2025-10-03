import os, requests, zipfile

def validate_dataset():
    # Test if dataset exists in expected path
    if os.path.exists("dataset/SMSSpamCollection"):
        print("Dataset found")
        return True
    else:
        print("Dataset not found, downloading from source")
        url = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"
        filename = "smsspamcollection.zip"
        try:
            with requests.get(url) as r:
                r.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"'{filename}' downloaded successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file: {e}")
            return False
        with zipfile.ZipFile("smsspamcollection.zip", 'r') as zip:
            zip.extractall('dataset')
        print("Extracted zip into dataset folder")
        os.remove("smsspamcollection.zip")
        return True
