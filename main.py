import json
from pathlib import Path
import shutil
import tempfile


# import psycopg2
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

api_app = FastAPI(title="api app")

# New data
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@api_app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@api_app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@api_app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@api_app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@api_app.get("/items/", response_model=list[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@api_app.get("/locations/", response_model=list[schemas.Location])
def read_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.get_location(db, skip=skip, limit=limit)
    return items


@api_app.post("/locations/", response_model=schemas.Location)
def create_location(location: schemas.LocationCreate, db: Session = Depends(get_db)):
    return crud.create_location(db=db, location=location)


# Upload CSV file
def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
    finally:
        upload_file.file.close()
    return tmp_path


"""
Api endpoint to accept csv upload from user and save it to database for query later
"""


@api_app.post("/csv/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    # csvReader = csv.DictReader(codecs.iterdecode(file.file, "utf-8"))
    # background_tasks.add_task(file.file.close)
    # create a temporary directory using the context manager
    tmp_path = save_upload_file_tmp(file)

    try:
        data = crud.update_database(
            engine, tmp_path
        )  # Do something with the saved temp file
    finally:
        tmp_path.unlink()
    # look out for spaces in data
    # print(list(data))
    return "data Upload Seccessfull"


"""
api endpoint to retrieve cities data from database using SQL statement
and return data formated using created schema Cities
"""


@api_app.get("/uscities/", response_model=list[schemas.Cities])
def read_cities(limit: int = 100, db: Session = Depends(get_db)):
    query = f"""
    SELECT * FROM tmp43xjsy9o FETCH FIRST {limit} ROWS ONLY
    """
    cities = db.execute(query)
    results = cities.fetchall()
    print(results)
    return results


"""
api endpoint which receives geojson as geometry from data created by leaflet geoman
and use its geometry to query point in database table (location) that fall within the polygon with SQL PostGIS
"""


@api_app.post(
    "/query/"
)  # corresponds to the ajax request above $.get("../query/" + <geometry_string>)...
async def geometry_filter(geometry_string: dict, db: Session = Depends(get_db)):
    geometry_string = json.dumps(geometry_string)
    # Note: for testing purposes f-strings or string concatenation are fine but never to be used in production!
    # Always use parametrized queries instead!

    db_query = f"""
    SELECT * FROM location
    WHERE ST_Within(ST_SetSRID(ST_MakePoint(lon, lat),4326), -- creating a point from lat long in EPSG 4326
                        ST_SetSRID(ST_GeomFromGeoJSON('{geometry_string}'),4326)) -- creating the geometry from string EPSG 4326
        """

    dat = db.execute(db_query)  # execute the query safely # execute the query safely
    results = dat.fetchall()
    return results[
        0
    ]  # comes back as array, hence to be indexed with [0], return to frontend


# end here


app = FastAPI(title="main app")

app.mount("/api", api_app)
app.mount("/", StaticFiles(directory="ui", html=True), name="ui")

"""
To run the live server use
'uvicorn main:app --reload'
"""
