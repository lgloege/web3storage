from pathlib import Path
import subprocess
import requests
import json
import os


def json_print(contents):
    """make JSON look good"""
    json_object = json.loads(contents)
    json_formatted_str = json.dumps(json_object, indent=2)
    print(json_formatted_str)


def create_car(source_dir, output_file):
    """creates a car file
    this requires ipfs-car command line tool
    (see https://web3.storage/docs/how-tos/work-with-car-files)

    install ipfs-caf:
     ```npm install -g ipfs-car```

     args:
     ------
     source_dir (str): the directory with files to upload
     output_file (str): the directory where car file will be stored

     returns:
     -----
     output_dict: dictionary with CID and output path
    """
    # make sure source directory exists
    source_dir = os.path.expanduser(source_dir)
    source_obj = Path(source_dir)
    if not source_obj.exists():
        raise FileNotFoundError(f"{source_dir} does not exist")

    # acceptable extensions for outputfile
    acceptable_extensions = ['.car']

    # use name of source_dir for output_file if none is included
    if not output_file:
        output_file = f"{source_obj.stem}.car"
        output_obj = Path(output_file)
    else:
        output_file = os.path.expanduser(output_file)
        output_obj = Path(output_file)
        # gets the file extentions
        extension = ''.join(output_obj.suffixes)

        # make sure extension is acceptable
        if extension not in acceptable_extensions:
            raise Exception(f"Extension must be in {acceptable_extensions}")

        # add an extension if not included
        if not extension:
            output_file = os.path.expanduser(output_file + '.car')
            output_obj = Path(output_file)

    # check to make sure outputfile doesn't already exist
    if output_obj.exists():
        raise Exception(f"{output_obj} already exists. Please chance the name")

    # create tar directory if does not exist
    if output_obj.parent.exists():
        # make car file
        command = f"ipfs-car --pack {source_dir} --output {output_file}"
        make_car = subprocess.run(command.split(' '), stdout=subprocess.PIPE)
        output = make_car.stdout.decode("utf-8").split('\n')
        output_dict = {output[0].split(':')[0].strip(): output[0].split(':')[1].strip(),
                       output[1].split(':')[0].strip(): output[1].split(':')[1].strip()}
    else:
        # create directory
        os.makedirs(output_obj.parent)
        # make car file
        command = f"ipfs-car --pack {source_dir} --output {output_file}"
        make_car = subprocess.run(command.split(' '), stdout=subprocess.PIPE)
        output = make_car.stdout.decode("utf-8").split('\n')
        output_dict = {output[0].split(':')[0].strip(): output[0].split(':')[1].strip(),
                       output[1].split(':')[0].strip(): output[1].split(':')[1].strip()}

    return output_dict


class BearerAuth(requests.auth.AuthBase):
    """Bearer Authentication"""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class Client(object):
    """Web3Storage Client Class
    This class is used to interact with web3.storage. 
    You can upload and retrieve files from your account

    Using this class
    -----------------------------------------------------
    1. Create an account with web3.storage
        https://web3.storage/

    2. Create an access token
        https://web3.storage/tokens/

    3. Best practice is to store this token in a configuration file.
        Use this code to create 
        { echo 'ACCESS_TOKEN: put_token_here' } > ~/.web3_storage_token

        Note: you can also initialize the Client() object with a token
            ws = Client(token='put_token_here')
    """

    def __init__(self, endpoint='https://api.web3.storage', token=None):
        self._endpoint = endpoint
        self._token = self._read_from_config if token is None else token
        self._bearer_auth = BearerAuth(self._token)

    # ---------------------------------------------
    # hidden methods, these could be pulled outside the class
    # ---------------------------------------------
    @staticmethod
    def _read_config(path=None):
        """reads the configuration file ~/.web3_storage_token

        Args:
            path (str): location of the file with ACCESS_TOKEN

        Returns:
            dict: dictionary with API ACCESS_TOKEN
        """

        if path is None:
            print("You need to supply a path")

        full_path = os.path.expanduser(path)
        if not Path(full_path).exists():
            print(f"{path} does not exist. Please check you entered the correct path")

        config = {}
        with open(path) as file:
            for line in file.readlines():
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    if key in ("ACCESS_TOKEN"):
                        config[key] = value.strip()
        return config

    @property
    def _read_from_config(self):
        """reads the web3.storage token from configuration file
        configuration file is ~/.web3_storage_token

        Returns:
            str: ACCESS_TOKEN to connect to web3 storage
        """
        dotrc = os.environ.get("ACCESS_TOKEN", os.path.expanduser("~/.web3_storage_token"))

        if os.path.exists(dotrc):
            config = self._read_config(dotrc)
            key = config.get("ACCESS_TOKEN")
            return key
        else:
            print(' ** No token was found, check your ~/.web3_storage_token file ** ')

    # ---------------------------------------------
    # user facing properties
    # ---------------------------------------------
    @property
    def user_uploads(self):
        """Lists all previous uploads for the account ordered by creation date, newest first. 
        Results can be paginated by specifying before and size parameters in the query string, 
        using the creation date associated with the oldest upload returned in each batch 
        as the value of before in subsequent calls.

        Note this endpoint returns all uploads for the account not just the API key in use.

        The information returned includes
            - the creation date
            - file size
            - details about how the network is storing your data. 

        With this you can identify peers on IPFS network that are pinning the data, 
        and Filecoin storage providers that have accepted deals to store the data.
        """
        return requests.get(self._endpoint + '/user/uploads/',
                            auth=self._bearer_auth)

    # ---------------------------------------------
    # user facing methods
    # ---------------------------------------------

    def upload(self, file_path=None, filename=None):
        """Store files using Web3.Storage. 
        You can upload either a single file or multiple files.

        Args:
            file_path (str): path to file to uploade
            filename (str): filename that will appear in web3.storage
        """
        if file_path is None:
            print("You need to supply a path")

        if not Path(os.path.expanduser(file_path)).exists():
            print(f"{file_path} does not exist. Please check you entered the correct path")
        else:
            #data = {"file": open(file_path, "rb")}

            # supply a filename
            headers = {"X-NAME": filename.encode(encoding='utf-8')}

            with open(file_path, "rb") as fp:
                r = requests.post(self._endpoint + '/upload',
                                  auth=self._bearer_auth,
                                  data=fp,
                                  headers=headers)
            print(f"{file_path} successfully uploaded!") if r.ok else print("Oh no! something went wrong")
            return r

    def upload_car(self, source_path=None, output_path=None, filename=None):
        """Store files using Web3.Storage. 
        You can upload either a single file or multiple files.

        Args:
            source_path (str): path to file to upload
            output_path (str): path to car file
            filename (str): filename that will appear in web3.storage
        """
        if source_path is None:
            print("You need to supply a path")

        if not Path(os.path.expanduser(source_path)).exists():
            print(f"{source_path} does not exist. Please check you entered the correct path")
        else:
            car_dict = create_car(source_path, output_path)

            # supply a filename
            headers = {"X-NAME": filename.encode(encoding='utf-8')}

            #data = {"file": open(file_path, "rb")}
            with open(car_dict['output'], "rb") as fp:
                r = requests.post(self._endpoint + '/car',
                                  auth=self._bearer_auth,
                                  data=fp,
                                  headers=headers)
            print(f"{output_path} successfully uploaded!") if r.ok else print("Oh no! something went wrong")
            return r

    def retrieve(self, cid=None):
        """Retrieve an IPFS DAG packaged in a CAR,
        supplying the CID of the data you are interested in.

        Args:
            cid(str): content id of data intersted in

        Returns:
            r(object): requests object
        """
        if cid is None:
            print("You need to supply a cid")
        else:
            return requests.get(self._endpoint + '/car/' + cid,
                                auth=self._bearer_auth)

    def metadata(self, cid=None):
        """Retrieve metadata about a specific file, 
        supplying the CID of the file you are interested in. 
        Metadata includes
            - the creation date
            - file size
            - details about how the network is storing your data. 

        With this you can identify peers on IPFS network that are pinning the data, 
        and Filecoin storage providers that have accepted deals to store the data.

        Args:
            cid(str): content id

        Returns:
            r(object): requests object
        """
        if cid is None:
            print("You need to supply a cid")
        else:
            return requests.get(self._endpoint + '/status/' + cid,
                                auth=self._bearer_auth)

    def http_header(self, cid=None):
        """Useful for doing a dry run of a call to /car/{cid}. 
        only returns HTTP header information, 
        lightweight and only gets the metadata about the given CAR file 
        without retrieving a whole payload in the body of the HTTP response.

        Args:
            cid(str): content id

        Returns:
            r(object): requests object
        """
        if cid is None:
            print("You need to supply a cid")
        else:
            return requests.head(self._endpoint + '/car/' + cid,
                                 auth=self._bearer_auth)
