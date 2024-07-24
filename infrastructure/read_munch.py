from munch import Munch

def read_munch(munch_obj, parent_key=''):
    """
    Recursively reads a Munch object and returns a list of tuples containing the keys and values.

    Parameters:
    munch_obj (Munch): The Munch object to read.
    parent_key (str, optional): The parent key for nested objects. Defaults to an empty string.

    Returns:
    list: A list of tuples, where each tuple contains a key and its corresponding value.
    """
    items = []
    for key, value in munch_obj.items():
        new_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, Munch):
            items.extend(read_munch(value, new_key))
        elif isinstance(value, dict):
            items.extend(read_munch(Munch(value), new_key))
        else:
            items.append((new_key, value))
    return items    
