from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: list[Item] = []

    class Config:
        orm_mode = True


class LocationBase(BaseModel):
    lat: float
    lon: float
    value: int


class LocationCreate(LocationBase):
    pass


class Location(LocationBase):
    id: int
    lat: float
    lon: float
    value: int

    class Config:
        orm_mode = True


class CitiesBase(BaseModel):
    index: int
    city: str
    state_name: str
    lat: float
    lng: float
    population: int
    density: float


class Cities(CitiesBase):
    index: int
    city: str
    state_name: str
    lat: float
    lng: float
    population: int
    density: float

    class Config:
        orm_mode = True
