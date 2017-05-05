import json
import os
import secrets
import imghdr 
import gzip

from django.shortcuts import render
from django.http import HttpResponse
from wsgiref.util import FileWrapper

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
FILE_NOT_FOUND = Response("Image[s] not found on the server", status=status.HTTP_404_NOT_FOUND)
UNRECOGNIZED_FILE_TYPE = Response("Unrecognized file type", status=status.HTTP_406_NOT_ACCEPTABLE)

def path_exists(*args):
    return os.path.exists(os.path.join(DB_PATH, *args))


def validate_file(f):
    """
    imghdr.what returns None for non image types.
    """
    return imghdr.what('', next(f.chunks()))

def validate_token(token):
    """
    Token will be valid if corresponding directory exists in database.
    """
    return path_exists(token)


@api_view(['GET'])
def get_image(request, token, image_id):
    """
    Return image corresponding to <image_id>.
    """
    if not validate_token(token):
        return INVALID_TOKEN

    try:
        with open(os.path.join(DB_PATH, token, 'imagemap.json')) as F:
            imagemap = json.load(F)
        if not image_id in imagemap:
            return FILE_NOT_FOUND
        # Decompress image
        compressed_imagepath = os.path.join(DB_PATH, token, imagemap[image_id]+'.gz')
        image = gzip.open(compressed_imagepath)
        # Detect file type
        content_type = 'image/'+imghdr.what('', image.read())
        # Get file size
        image.seek(0, 2)
        size = image.tell()
        image.seek(0)
        # Create response
        response = HttpResponse(FileWrapper(image), content_type=content_type)
        response['Content-Length'] = size
        response['Content-Disposition'] = 'attatchement; filename='+imagemap[image_id]
        return response

    except FileNotFoundError:
        return FILE_NOT_FOUND

@api_view(['GET'])
def get_image_list(request, token):
    """
    Returns response consisting of all images associated with <token> and
    their corresponding access id.
    """
    if not validate_token(token):
        return INVALID_TOKEN

    try:
        with open(os.path.join(DB_PATH, token, 'imagemap.json')) as F:
            imagemap = json.load(F)
        if not imagemap:
            return FILE_NOT_FOUND
        response = {filename: fileid for fileid, filename in imagemap.items()}
        return Response(response, status=status.HTTP_200_OK)
    except FileNotFoundError:
        return FILE_NOT_FOUND


@api_view(['POST'])
@parser_classes((FormParser, MultiPartParser))
def put_image(request, token):
    """
    Compress and save the image provided.
    """
    if not validate_token(token):
        return INVALID_TOKEN

    if not request.data:
        return Response(status=status.HTTP_204_NO_CONTENT)

    uploaded_file = next(request.data.items())[1]        # Ignore multiple files, for now

    if not validate_file(uploaded_file):
        return UNRECOGNIZED_FILE_TYPE

    userdir = os.path.join(DB_PATH, token)
    
    if path_exists(token, uploaded_file.name+'.gz'):
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

    # Compress image
    with gzip.open(os.path.join(userdir, uploaded_file.name + '.gz'), 'wb') as F:
        for chunk in uploaded_file.chunks():
            F.write(chunk)

    return Response({"File ID": imageid}, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
def remove_image(request, token, image_id):
    """
    Deletes image specified by <image_id>.
    """
    if not validate_token(token):
        return INVALID_TOKEN

    try:
        with open(os.path.join(DB_PATH, token, 'imagemap.json')) as F:
            imagemap = json.load(F)
        if not image_id in imagemap:
            return FILE_NOT_FOUND
        # Delete the file
        os.remove(os.path.join(DB_PATH, token, imagemap[image_id]+'.gz'))
        # Update imagemap
        del imagemap[image_id]
        with open(os.path.join(DB_PATH, token, 'imagemap.json'), 'w') as F:
            json.dump(imagemap, F)
        return Response(status=status.HTTP_200_OK)
    except FileNotFoundError:
        return FILE_NOT_FOUND


@api_view(['PATCH'])
@parser_classes((FormParser, MultiPartParser))
def update_image(request, token, image_id):
    """
    Update image corresponding to <image_id> with new image data.
    """
    if not validate_token(token):
        return INVALID_TOKEN

    try:
        with open(os.path.join(DB_PATH, token, 'imagemap.json')) as F:
            imagemap = json.load(F)
        if not image_id in imagemap:
            return FILE_NOT_FOUND
    except FileNotFoundError:
        return FILE_NOT_FOUND

    uploaded_file = next(request.data.items())[1]
    if not validate_file(uploaded_file):
        return UNRECOGNIZED_FILE_TYPE

    # Delete existing file
    os.remove(os.path.join(DB_PATH, token, imagemap[image_id]+'.gz'))

    # Write new file
    if path_exists(token, uploaded_file.name+'.gz'):
        return Response("Cannot patch. File exists.", status=status.HTTP_409_CONFLICT)
    with gzip.open(os.path.join(DB_PATH, token, uploaded_file.name+'.gz'), 'wb') as F:
        for chunk in uploaded_file.chunks():
            F.write(chunk)

    # Update imagemap
    imagemap[image_id] = uploaded_file.name
    with open(os.path.join(DB_PATH, token, 'imagemap.json'), 'w') as F:
        json.dump(imagemap, F)

    return Response(status=status.HTTP_200_OK)


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

@api_view(['GET'])
def retrieve_token(request, username):
    try:
        with open(os.path.join(DB_PATH, 'tokens.json')) as F:
            TOKEN_DB = json.load(F)
        if username not in TOKEN_DB:
            return Response("User does not exists", status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({username: TOKEN_DB[username]}, status=status.HTTP_200_OK)
    except FileNotFoundError:
        return Response("User does not exists", status=status.HTTP_404_NOT_FOUND)
