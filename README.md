# web3storage

## *Project under active deveopment - not production ready* 

---

A Python3 package to interact with [Web3.Storage](https://web3.storage/).

Already Implemented
----------
- `.upload()`: Store files using Web3.Storage. (limited to 100MB)
- `.retrieve()`: Retrieve a file from Web3.Storage
- `.metadata()`: Retrieve metadata about a specific file
- `.http_header()`: RetrieveHTTP header information
- `.user_uploads`: Lists all previous uploads for the account

Installation
----------
*This package is currently only installable via GitHub*

```sh
pip install -e git+https://github.com/lgloege/web3storage#egg=web3storage
```

Using the Package
----------
1. **Create an access token** by first logging into your account and clicking on your username in the top right corner. Navigate to "Applications" and then "+new token" under "Personal access tokens".  Keep this window open while you proceed to step 2 because **the token is only displayed once**.

2. **Store the token** in `~/.web3_storage_token` using the folowing command
```sh
 { echo 'ACCESS_TOKEN: your_access_token_here' } > ~/.web3_storage_token
```

1. **start using the ackage**
```python
import web3storage

# create a Client object
ws = web3storage.Client()

# upload a file
ws.upload("~/test.file.txt", filename="test-file")
```

Notes
----------
This project is under active development. Here is a list of improvements:
- **CAR**: right this only works with "small" files (<100MB). Need a way to create and upload a CAR 
- **improve retrive**: retrieve needs some work. I think there is an encoding issue?
- **tests!**: need to test uploading and downloading files, not sure how to mock this
- **documentation**: need to setup a readthedocs
- **asyncronous functions**: use `asyncio` and `aiohttp` to write async functions. This could improve speed
