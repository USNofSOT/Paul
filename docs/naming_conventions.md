# Naming conventions
Function names, variable names, and filenames should be descriptive; avoid abbreviation. In particular, do not use abbreviations that are ambiguous or unfamiliar to readers outside your project, and do not abbreviate by deleting letters within a word [1].
Furthermore, ubiquitous Language should be applied throughout the project to ensure clear and consistent communication among team members and stakeholders. This means using the same terms and definitions across all documentation, code, and discussions [2].

## Guidelines derived from [Guido’s](https://en.wikipedia.org/wiki/Guido_van_Rossum) Recommendations
| Type                       | Public               | Internal                           |
|----------------------------|----------------------|------------------------------------|
| Packages                   | lower\_with\_under   |                                    |
| Modules                    | lower\_with\_under   | \_lower\_with\_under               |
| Classes                    | CapWords             | \_CapWords                         |
| Exceptions                 | CapWords             |                                    |
| Functions                  | lower\_with\_under() | \_lower\_with\_under()             |
| Global/Class Constants     | CAPS\_WITH\_UNDER    | \_CAPS\_WITH\_UNDER                |
| Global/Class Variables     | lower\_with\_under   | \_lower\_with\_under               |
| Instance Variables         | lower\_with\_under   | \_lower\_with\_under (protected)   |
| Method Names               | lower\_with\_under() | \_lower\_with\_under() (protected) |
| Function/Method Parameters | lower\_with\_under   |                                    |
| Local Variables            | lower\_with\_under   |                                    |

## Examples
When writing a function that returns a ship object by its role ID you may write it as follows:

### Bad 
This is an example of how not to name functions and variables. 
1. Notice how it is not clear what the function does due to the name `getShip`. And what does `id` refer to?
   1. You could assume this function returns a ship object by its ID. Which in this case it does not.
2. The variable `s` is not descriptive what is s? And what does `shps` refer to in the context of the code?

```python
def getShip(id):
    for s in shps:
        if s.role_id == id: 
            return s
    return None
```

### Good
By following the naming conventions and using a descriptive name, the function becomes more readable and understandable.
1. It is immediately clear what the function does getting a ship dictionary by its role ID.
2. The variable `ship` is descriptive and makes it clear what the variable represents.
    1. Let's say this code is longer, you don't have to go back and forth to understand what ship represents, it is clear from the name.
3. Notice how our configuration variable `SHIPS` is in all caps, this is global and should be treated as such.
```python
def get_ship_by_role_id(role_id: int) -> dict or None:
    """
    Get the ship object by role ID.
    
    Args:
        role_id (int): The role ID of the ship.
    Returns:
        dict or None: The ship object if found, otherwise None.
    """
    for ship in SHIPS:
        if ship.role_id == role_id:
            return ship
    return None
```


## Resources
[1] Google, “Google Python Style Guide,” Styleguide. https://google.github.io/styleguide/pyguide.html (accessed Dec. 19, 2024).

[2] Dremio, “Ubiquitous Language,” Dremio, May 24, 2024. https://www.dremio.com/wiki/ubiquitous-language/ (accessed Dec. 19, 2024).