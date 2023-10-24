class RequestRHCreate(BaseModel):
    UserID: int
    Content: str
    RegistrationDate: NaiveDatetime
    Visibility: str
    Close: str
    LastAction: str
    ContentHistory: str


class RequestRHUpdate(BaseModel):
    UserID: int
    Content: str
    Visibility: str
    Close: str
    LastAction: str
    ContentHistory: str


class RequestRHRemove(BaseModel):
    UserID: int
    Content: str
    Visibility: str
    Close: str
    LastAction: str
    ContentHistory: str


class RequestRHGet(BaseModel):
    UserID: int
    Content: str
    Visibility: str
    Close: str
    LastAction: str
    ContentHistory: str
