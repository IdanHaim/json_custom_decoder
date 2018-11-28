from custom_decoder import JsonDecoder
import json


class Address:
    def __init__(self, street, city, state):
        self.street = street
        self.city = city
        self.state = state


class Owner:
    def __init__(self, name, address):
        self.name = name
        self.address = address


class Dog:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner


def get_dog(key, value):
    if key == "address":
        return Address(**value)
    elif key == "owner":
        return Owner(**value)


def get_owner(key, value):
    if key == "address":
        return Address(**value)


mappers = {Owner: get_owner, Dog: get_dog}


def json_default(obj):
    if getattr(obj, "__dict__"):
        return obj.__dict__


if __name__ == "__main__":
    address = Address("MyStreet", "MyCity", "Israel")
    owner = Owner("Idan", address)
    dog = Dog(name="Donald", owner=owner)
    json_string = json.dumps(dog, default=json_default)
    object_type = Dog

    # object_type property is the class we want to get from json.load
    # object_mapper property is a key, value method that uses to parse on the json object
    obj = json.loads(json_string, cls=JsonDecoder, object_type=object_type,
                     object_mapper=mappers.get(object_type, None))

    print(f"I am {obj.owner.name} I live in {obj.owner.address.street} with my dog {obj.name}")
