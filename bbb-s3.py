import os, glob, shutil, boto3, magic, logging, requests
from botocore.exceptions import NoCredentialsError, ClientError
mime = magic.Magic(mime=True)
## Configuration Part 
BUCKET_NAME = 'bbbrecordings'
DELETE_SERVER_FILES = True ## Set False (F should be capital) if you don't want to delete files from bbb-server

def create_presigned_post(bucket_name, object_name,
                          fields=None, conditions=None, expiration=3600):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return response

def upload_to_aws(local_file, bucket, s3_file):
    ctype = mime.from_file(local_file) 
    s3 = boto3.client('s3')
    response = create_presigned_post(bucket, s3_file, ExtraArgs={'ContentType': ctype})
    try:
        http_response = requests.post(response['url'], data=response['fields'], files=files)
        return True
    except OSError as e:
        if e.errno == errno.ENOENT:
            print("\nFile not found\n")
    except NoCredentialsError: 
        return False

def getListOfFiles(dirName): 
    listOfFile = os.listdir(dirName)
    allFiles = list() 
    for entry in listOfFile: 
        fullPath = os.path.join(dirName, entry) 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles     

def getListOfDirs(path):
    return [os.path.basename(x) for x in filter(
        os.path.isdir, glob.glob(os.path.join(path, '*')))]

def remove(path):
    """ param <path> could either be relative or absolute. """
    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)  # remove the file
    elif os.path.isdir(path):
        shutil.rmtree(path)  # remove dir and all contains
    else:
        raise ValueError("file {} is not a file or dir.".format(path))

def main():
    
    dirName = os.getcwd(); 
    listOfFiles = getListOfFiles(dirName) 
    listOfDirs = getListOfDirs(dirName)
    for elem in listOfFiles:
        listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk(dirName):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames]

    for elem in listOfFiles: 
        relative_path = elem.replace(dirName,'')[1:]
        if(relative_path!='bbb-s3.py'):
            print("\nUploading "+relative_path)    
            uploaded = upload_to_aws(elem, BUCKET_NAME, relative_path)
            if(uploaded and DELETE_SERVER_FILES):
                remove(elem)
            else:
                print("\nNot able to delete files from your bbb-server, check file if its uploaded")

    file_length = len(listOfFiles)
    if(file_length==1):
        for folder in listOfDirs:
            remove(folder)

        
        
        
        
if __name__ == '__main__':
    main()
