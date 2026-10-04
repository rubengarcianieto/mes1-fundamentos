from pydantic import BaseModel, ValidationError

class Post(BaseModel):
    userId: int
    id: int
    title: str
    body: str

wrong_data = {
    "userId": "not a number",
    "id": 1,
    "body": "content"
}

try:
    post = Post(**wrong_data)
except ValidationError as e:
    print("The validation has failed:")
    print(e)

