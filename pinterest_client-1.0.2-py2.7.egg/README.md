## pinterest-client
A simple python client for Pinterest that support user interact with Pinterest such as simple browser.

Support operations: login, pin, save pin, delete pin, boards, create board, delete board, follow board, follow user, comment, search pins, search users, search boards.

## Installation
[This package is in pypi](https://pypi.python.org/pypi/pinterest-client) so you can install it easily using pip command:
```sh
pip install pinterest-client
```
or install from source code if you downloaded it from [this GitHub repository](https://github.com/cvhau/pinterest-client) by using command:
```sh 
python setup.py install
```

## Dependencies
This package depends on some other Python packages:

- [requests](http://docs.python-requests.org)
- [requests_toolbelt](https://pypi.python.org/pypi/requests-toolbelt)

They are included in the requirements of this package so you won't have to manually install them.

## Usage
After installation was successful, you can initialize a new pinterest object: 
```python
from pinterest import Pinterest

pinterest = Pinterest(username_or_email='your_username_or_email', password='your_password')
```

#### With proxies
If you need to use a proxy, you can pass <i>proxies</i> argument to constructor
```python
from pinterest import Pinterest

proxies = {
    'http': 'http://10.10.1.10:3128',
    'https': 'http://10.10.1.10:1080',
}

pinterest = Pinterest(
    username_or_email='your_username_or_email', 
    password='your_password', 
    proxies=proxies)
```

#### Custom User-Agent
You can also use your custom User-Agent string for each pinterest-client object 
```python
from pinterest import Pinterest

agent_string='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0'

pinterest = Pinterest(
    username_or_email='your_username_or_email', 
    password='your_password', 
    agent_string=agent_string)
```

#### Operations
```python
from pinterest import Pinterest

pinterest = Pinterest(username_or_email='your_username_or_email', password='your_password')

# Login to pinterest site, if 'ok' return True otherwise return False
logged_in = pinterest.login()

# Get all boards of logged in user
boards = pinterest.boards()

# Create new board, it also return new board data if creation was successful
pinterest.create_board(name='Board name', description='Description')

# Follow a board
pinterest.follow_board(board_id='657384945546806337', board_url='/cvhautt/animal/')

# Follow a user
pinterest.follow_user(user_id='657385014266199005', username='cvhautt')

# Create pin from an image url
pin = pinterest.pin(
    board_id='657384945546806337', 
    image_url='your_image_url', 
    description='your_description (*optional)', 
    link='your_link (*optional)')

# Create pin by uploading an image from your computer
uploaded_pin = pinterest.upload_pin(
    board_id='657384945546806337', 
    image_file='full_path_to_your_image', 
    description='your_description (*optional)')

# Save a pin to your board (known as Save button on Pinterest site)
pinterest.repin(board_id='657385014266199005', pin_id='pin_id')

# Delete a pin
pinterest.delete_pin(pin_id='your_pin_id')

# Comment on a pin
cmt = pinterest.comment(pin_id='your_pin_id', text='your_comment_text')

# Delete a comment from pin
pinterest.delete_comment(pin_id='your_pin_id', comment_id='your_comment_id')

# Invite a person to join to your board
pinterest.invite(board_id='your_board_id', board_url='your_board_url', user_id='user_id')

# Search data on Pinterest site
boards = pinterest.search_boards(query='Some query')
pins = pinterest.search_pins(query='Some query')
users = pinterest.search_users(query='Some query')

# You can also get next page from search result by passing next_page=True to search operations above.
# Exp:
boards = pinterest.search_boards(query='Some query', next_page=True)
pins = pinterest.search_pins(query='Some query',next_page=True)
```
