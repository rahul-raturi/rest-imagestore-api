# Simple REST API for managing files over the server

### Requirements

* Django (Tested on version 1.11)
* Django Rest Framework
* Python3

### Basics

The API allows posting, retrieving, updating images on to the server. Images are stored in a compressed format. No database is required at the server.

#### Authentication

Authentication is pretty basic. A unique token is generated for each unique username. This token would be required in the URL for accessing the resources (images) on the server.

* **Generating token [GET]**:

	(shell) http http://localhost:8000/imageapi/generate-token/<username>/`

* **Retrieving lost token [GET]**:
	
	(shell) http http://localhost:8000/imageapi/retrieve-token/<username>/

*Note*: It's a requirement that username must be remembered. As it's a test only API, password authentication is skipped.

---

#### Uploading a single image [POST]

Only images could be uploaded at the image. Python's *imghdr* module is used to verify that. Otherwise *HTTP 406* would be thrown. Also, a single file can be uploaded at an instance. In case of multiple files, only first one would be saved, ignoring others.

If the operation was successful, a unique 4 characters long image id will be replied to the client. This image id must be stored for future retrieval.

	(shell) http -f POST http://localhost:8000/imageapi/token/<10 char long token>/upload-image/ <somename>@<somefile>

---

#### Retrieving  a single image [GET]

	(shell) http http://localhost:8000/imageapi/token/<10 char long token>/get-image/<4 char long image id>/

---

#### Retrieving list of all images of corresponding user [GET]

A list is returned to the client containing information about the available images, and their corresponding access id.

	(shell) http http://localhost:8000/imageapi/token/<10 char long token>/get-image-list/

---

#### Removing an image from the server [DELETE]

	(shell) http -f DELETE http://localhost:8000/imageapi/token/<10 char long token>/delete-image/<4 char long image id>/

---

#### Updating image on the server [PATCH]

Updation in this API's context means linking the new image provided, with the image id, thereby deleting the existing one.

	(shell) http -f PATCH http://localhost:8000/imageapi/token/<10 char long token>/update-image/<4 char long image id>/ <somename>@<somefile>

---

### Important notes

* For posting or patching an image, it's important that the name of the file is unique. As the names are stored on the server, and the same is transferred back on a GET request. Otherwise an *HTTP 409* would be thrown.
* A simple file database (directory structure) would be created in the same parent directory where this application resides. It must be ensured that the user has write permissions there.
* The authentication system is a bit lame. One can retrieve token by guessing the username. For more robust authentication, DRF's or Django's authentication classes should be used.
* Compression is done with Python's **gzip** module.
* For token and image id generation, Python's **secrets** module is used. 
