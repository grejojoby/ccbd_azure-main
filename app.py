from flask import Flask, render_template, request, redirect
from azure.storage.blob import BlobServiceClient
import pandas as pd

app = Flask(__name__)

CONNECTION_STRING ="DefaultEndpointsProtocol=https;AccountName=ruvinassignment01;AccountKey=0Ms+MtwxLU/QJXxaNDKg1UteswsjNKlbBIWRcBG8Lt3SrZ/oQ229TOjFjPgiE0bKiaOAX9s1shUO+ASt+UYlQA==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(conn_str=CONNECTION_STRING)
container_photos = "photos"
container_data = "data"
try:
    container_client_photos = blob_service_client.get_container_client(container=container_photos) # get container client to interact with the container in which images will be stored
    container_client_photos.get_container_properties() # get properties of the container to force exception to be thrown if container does not exist
except Exception as e:
    print(e)
    print("Creating container...")
    container_client_photos = blob_service_client.create_container(container_photos) # create a container in the storage account if it does not exist

try:
    container_client_data = blob_service_client.get_container_client(container=container_data) # get container client to interact with the container in which images will be stored
    container_client_data.get_container_properties()
except Exception as e:
    print(e)
    print("Creating container...")
    container_client_data = blob_service_client.create_container(container_data)

def collect_data():
    blob_items = container_client_photos.list_blobs() # list all the blobs in the container
    people_data = pd.DataFrame()
    if container_client_data.get_blob_client(blob="people.csv").exists():
        people_data = container_client_data.get_blob_client(blob="people.csv")
        people_data = pd.read_csv(people_data.url)
        people_data = people_data.values.tolist()
    else:
        people_data = []
    imgs = {}
    for blob in blob_items:
        blob_client = container_client_photos.get_blob_client(blob=blob.name) # get blob client to interact with the blob and get blob url
        imgs[blob.name] = blob_client.url
    return people_data, imgs


@app.route('/')
def home():
    people_data, imgs = collect_data()

    return render_template('index.html', images= imgs, data=people_data)




@app.route('/upload-imgs' , methods=["POST"])
def uploadImages():
    for file in request.files.getlist("photos"):
        try:
            container_client_photos.upload_blob(file.filename, file, overwrite=True) # upload the file to the container using the filename as the blob name
        except Exception as e:
            print(e)
    return redirect('/')




@app.route('/upload-data' , methods=["POST"])
def uploadData():
    file = request.files.get("data")
    try:
        container_client_data.upload_blob(file.filename, file, overwrite=True) # upload the file to the container using the filename as the blob name
    except Exception as e:
        print(e)
    return redirect('/')





@app.route('/search', methods=["GET"])
def search():
    name = request.args.get('name')
    people_data, imgs = collect_data()
    person_data = []
    for index,data in enumerate(people_data):
        if name.lower() == data[0].lower():
            person_data = data
            break
    return render_template('search.html', person_data = person_data, images = imgs, index=index)


@app.route('/delete-image/<image_name>/<index>')
def delete_image(image_name,index):
    blob_client = container_client_photos.get_blob_client(blob=image_name)
    blob_client.delete_blob(delete_snapshots="include")
    people_data, imgs = collect_data()
    people_data[int(index)][6] = ""
    df = pd.DataFrame(people_data)
    csv_data = df.to_csv(index=False)
    container_client_data.upload_blob("people.csv", csv_data, overwrite=True)
    return redirect('/')

@app.route('/add_image/<index>', methods=["POST"])
def add_image(index):
    people_data, imgs = collect_data()
    file = request.files.get("photo")
    try:
        container_client_photos.upload_blob(file.filename, file, overwrite=True) # upload the file to the container using the filename as the blob name
        people_data[int(index)][6] = file.filename
        df = pd.DataFrame(people_data)
        csv_data = df.to_csv(index=False)
        container_client_data.upload_blob("people.csv", csv_data, overwrite=True)
    except Exception as e:
        print(e)
    return redirect('/')

@app.route('/change_keyword/<index>', methods=["POST"])
def change_keyword(index):
    people_data, imgs = collect_data()
    keyword = request.form.get('keywords')
    print(request.form)
    people_data[int(index)][7] = keyword

    try:
        df = pd.DataFrame(people_data)
        csv_data = df.to_csv(index=False)
        container_client_data.upload_blob("people.csv", csv_data, overwrite=True)
    except Exception as e:
        print(e)
    return redirect('/')

@app.route('/change_salary/<index>', methods=["POST"])
def change_salary(index):
    people_data, imgs = collect_data()
    salary = request.form.get('salary')
    print(request.form)
    people_data[int(index)][2] = salary

    try:
        df = pd.DataFrame(people_data)
        csv_data = df.to_csv(index=False)
        container_client_data.upload_blob("people.csv", csv_data, overwrite=True)
    except Exception as e:
        print(e)
    return redirect('/')


@app.route('/salary', methods=["GET"])
def salary():
    salary = request.args.get('salary')
    people_data, imgs = collect_data()
    data = []
    for person in people_data:
        try:
            if int(person[2]) < int(salary):
                data.append(person)
        except Exception as e:
            print(e)
    return render_template('salary.html', data = data, images = imgs)

@app.route('/delete-person/<image_name>/<index>')
def delete_person(image_name,index):
    try:
        blob_client = container_client_photos.get_blob_client(blob=image_name)
        blob_client.delete_blob(delete_snapshots="include")
    except Exception as e:
            print(e)
    people_data, imgs = collect_data()
    print(people_data.pop(int(index)))
    df = pd.DataFrame(people_data)
    csv_data = df.to_csv(index=False)
    container_client_data.upload_blob("people.csv", csv_data, overwrite=True)
    return redirect('/')


if __name__ == '__main__':
    app.debug=True
    app.run()
    