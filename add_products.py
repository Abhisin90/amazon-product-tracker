
import json

def add_product():
    product_name = input("Enter product name: ") 
    product_link = input("Enter product link: ")
    product_price = input("Enter maximum product price: ")

    new_product = {
        "name": product_name,
        "url": product_link,
        "threshold_inr": product_price
    }

    data = {}

    with open('products.json') as f:
        data = json.load(f)

    data.setdefault("products", []).append(new_product)

    with open("products.json", "w") as f:
        json.dump(data, f, indent = 2)

def remove_product(): 
    product_name = input("Enter the product name which you want to remove: ")

    data = {}

    with open("products.json") as f:
        data = json.load(f)
    
    data["products"] = [product for product in data["products"] if product.get("name") != product_name]
    print(data["products"][0]["name"])
    print(product_name)
    print(data)

    with open("products.json", "w") as f:
        json.dump(data, f, indent=2)
            
if __name__ == "__main__":
    action_type = input('Do you want to add or remove a product, reply either "add" or "remove": ')
    if action_type == "add":
        add_product()
    elif action_type == "remove":
        remove_product()