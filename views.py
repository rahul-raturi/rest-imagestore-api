import json
import os
import secrets
import imghdr 

from django.shortcuts import render
from django.http import HttpResponse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import parser_classes
from rest_framework.parsers import FormParser, MultiPartParser


# Database path 
DB_PATH = os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), os.pardir), 'lamedb'))
if not os.path.exists(DB_PATH):
    os.makedirs(DB_PATH)

# Frequent responses
INVALID_TOKEN = Response("Token not recognized", status=status.HTTP_401_UNAUTHORIZED)


def path_exists(location):
    return os.path.exists(os.path.join(DB_PATH, location))

def generate_file_id(filename, token):
    """
    Generates another file name if provided one exists.
    Uses incremental update,
    e.g. filename_1 or filename_2 if filename_1 also exists.
    """
    pass

def validate_file(f):
    """
    Support for only JPEG, PNG, and GIF file types
    """
    return imghdr.what('', next(f.chunks()))


@api_view(['GET'])
def get_image(request, token, image_id):
    print(token)
    print(image_id)


@api_view(['POST'])
@parser_classes((FormParser, MultiPartParser))
def put_image(request, token):
    """
    Compress and save the image provided.
    """
    if not path_exists(token):
        # If location <token> doesn't exists, means token is invalid
        return INVALID_TOKEN

    if not request.data:
        return Response(status=status.HTTP_204_NO_CONTENT)

    uploaded_file = next(request.data.items())[1]        # Ignore multiple files, for now

    if not validate_file(uploaded_file):
        return Response("Unrecognized file type", status=status.HTTP_406_NOT_ACCEPTABLE)

    userdir = os.path.join(DB_PATH, token)
    
    if os.path.exists(os.path.join(userdir, uploaded_file.name)):
        return Response("File exists", status=status.HTTP_409_CONFLICT)

    try:
        with open(os.path.join(userdir, 'imagemap.json')) as F:
            imagemap = json.load(F)
    except FileNotFoundError:
        imagemap = {}

    imageid = secrets.token_urlsafe(4)[:4]
    while imageid in imagemap:
        imageid = secrets.token_urlsafe(4)[:4]

    imagemap[imageid] = uploaded_file.name
    with open(os.path.join(userdir, 'imagemap.json'), 'w') as F:
        json.dump(imagemap, F)

    print("ABOUT TO SAVE")
    with open(os.path.join(userdir, uploaded_file.name), 'wb') as F:
        for chunk in uploaded_file.chunks():
            F.write(chunk)

    return Response({"File ID": imageid}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def generate_token(request, username):
    """
    Generate new token for <username> if doesn't exists.
    Else do nothing.
    """
    try:
        with open(os.path.join(DB_PATH, 'tokens.json')) as F:
            TOKEN_DB = json.load(F)
    except FileNotFoundError:
        TOKEN_DB = {}
    if username in TOKEN_DB:
        return Response("User exists", status=status.HTTP_409_CONFLICT)

    else:

        # Generate new unique token
        token = secrets.token_urlsafe(10)[:10] 
        while token in TOKEN_DB:
            token = secrets.token_urlsafe(10)[:10] 
        TOKEN_DB[username] = token
        with open(os.path.join(DB_PATH, 'tokens.json'), 'w') as F:
            json.dump(TOKEN_DB, F)

        # Create new folder for user
        os.makedirs(os.path.join(DB_PATH, token))
        return Response({'token': TOKEN_DB[username]}, status=status.HTTP_201_CREATED)
