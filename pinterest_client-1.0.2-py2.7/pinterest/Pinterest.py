# -*- coding: utf-8 -*-
import json
import mimetypes
import os
import uuid
import requests
import time
import requests.cookies
from requests.structures import CaseInsensitiveDict
from requests_toolbelt import MultipartEncoder
from pinterest.exceptions import PinterestLoginFailedException, PinterestLoginRequiredException, PinterestException
from pinterest import Registry
from pinterest.utils import url_encode

AGENT_STRING = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) " \
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"


class Pinterest:
    home_page = 'https://www.pinterest.com/'

    def __init__(self, username_or_email, password, proxies=None, agent_string=None):
        self.debug = False
        self.is_logged_in = False
        self.user = None
        self.http = requests.session()
        self.username_or_email = username_or_email
        self.password = password
        self.proxies = proxies
        self.data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data',
                                      self.username_or_email) + os.sep
        if not os.path.isdir(self.data_path):
            os.makedirs(self.data_path)
        self.registry = Registry('%sregistry.dat' % self.data_path)
        if agent_string:
            self.registry.set(Registry.Key.USER_AGENT, agent_string)
        elif not self.registry.get(Registry.Key.USER_AGENT):
            self.registry.set(Registry.Key.USER_AGENT, AGENT_STRING)
        old_cookies = self.registry.get(Registry.Key.COOKIES)
        if old_cookies:
            self.http.cookies.update(old_cookies)
        self.next_book_marks = {'pins': {}, 'boards': {}, 'people': {}}

    def request(self, method, url, params=None, data=None, files=None, headers=None, ajax=False, stream=None):
        """
        :rtype: requests.models.Response
        """
        _headers = CaseInsensitiveDict([
            ('Accept', 'text/html,image/webp,image/apng,*/*;q=0.8'),
            ('Accept-Encoding', 'gzip, deflate'),
            ('Accept-Language', 'en-US,en;q=0.8'),
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Cache-Control', 'no-cache'),
            ('Connection', 'keep-alive'),
            ('Host', 'www.pinterest.com'),
            ('Origin', 'https://www.pinterest.com'),
            ('Referer', self.home_page),
            ('User-Agent', self.registry.get(Registry.Key.USER_AGENT))])
        if method.upper() == 'POST':
            _headers.update([('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')])
        if ajax:
            _headers.update([('Accept', 'application/json')])
            csrftoken = self.http.cookies.get('csrftoken')
            if csrftoken:
                _headers.update([('X-CSRFToken', csrftoken)])
            _headers.update([('X-Requested-With', 'XMLHttpRequest')])
        if headers:
            _headers.update(headers)
        response = self.http.request(method, url, params=params, data=data, headers=_headers,
                                     files=files, timeout=60, proxies=self.proxies, stream=stream)
        response.raise_for_status()
        self.registry.update(Registry.Key.COOKIES, response.cookies)
        return response

    def get(self, url, params=None, headers=None, ajax=False, stream=None):
        """
        :rtype: requests.models.Response
        """
        return self.request('GET', url=url, params=params, headers=headers, ajax=ajax, stream=stream)

    def post(self, url, data=None, files=None, headers=None, ajax=False, stream=None):
        """
        :rtype: requests.models.Response
        """
        return self.request('POST', url=url, data=data, files=files, headers=headers, ajax=ajax, stream=stream)

    def extract_user_data(self, html_page=''):
        """
        Extract user data from html page if available otherwise return None
        :rtype: dict|None
        """
        if html_page:
            s = html_page[html_page.rfind('application/json'):]
            if s and s.rfind(self.username_or_email) > -1:
                s = s[s.find('{'): s.find('</script>')]
                s = json.loads(s)
                try:
                    user = s['context']['user']
                    return user
                except KeyError:
                    pass
        return None

    def login(self):
        """
        Login to pinterest site. If OK return True
        :rtype: bool
        """
        r = self.get(self.home_page)
        self.user = self.extract_user_data(r.content)
        if self.user:
            self.is_logged_in = True
        else:
            time.sleep(2)
            login_page = 'https://www.pinterest.com/login/?referrer=home_page'
            self.get(login_page)
            time.sleep(3)
            data = url_encode({
                'source_url': '/login/?referrer=home_page',
                'data': json.dumps({
                    'options': {'username_or_email': self.username_or_email, 'password': self.password},
                    "context": {}
                }).replace(' ', '')
            })
            url = 'https://www.pinterest.com/resource/UserSessionResource/create/'
            result = self.post(url=url, data=data, ajax=True).json()
            error = result['resource_response']['error']
            if error is None:
                self.user = self.extract_user_data(self.get(self.home_page).content)
                self.is_logged_in = True
            else:
                raise PinterestLoginFailedException('[%s Login failed] %s' % (error['http_status'], error['message']))
        return self.is_logged_in

    def login_required(self):
        if not self.is_logged_in:
            raise PinterestLoginRequiredException("Login is required")

    def boards(self):
        """
        Return all boards of logged in user
        :rtype: list
        """
        self.login_required()
        data = url_encode({
            'source_url': '/%s/pins/' % self.user['username'],
            'data': json.dumps({
                'options': {"filter": "all", "field_set_key": "board_picker", "allow_stale": "true", "from": "app"},
                "context": {}
            }).replace(' ', ''),
            '_': '%s' % int(time.time() * 1000)
        })
        url = 'https://www.pinterest.com/resource/BoardPickerBoardsResource/get/?%s' % data
        r = self.get(url=url, ajax=True)
        result = r.json()
        boards = []
        try:
            if result['resource_response']['data']['all_boards']:
                all_boards = result['resource_response']['data']['all_boards']
                for board in all_boards:
                    boards.append({
                        'id': board.get('id'),
                        'name': board.get('name'),
                        'privacy': board.get('privacy')
                    })
        except KeyError:
            pass
        return boards

    def create_board(self, name, description='', category='other', privacy='public', layout='default'):
        self.login_required()
        url = 'https://www.pinterest.com/resource/BoardResource/create/'
        data = url_encode({
            'source_url': '/%s/boards/' % self.user['username'],
            'data': json.dumps({
                'options': {
                    "name": name,
                    "description": description,
                    "category": category,
                    "privacy": privacy,
                    "layout": layout,
                    "collab_board_email": 'true',
                    "collaborator_invites_enabled": 'true'
                },
                "context": {}
            }).replace(' ', '')
        })
        r = self.post(url=url, data=data, ajax=True)
        result = r.json()
        if result['resource_response']['error'] is None:
            board = result['resource_response']['data']
            return board
        return None

    def follow_board(self, board_id, board_url):
        self.login_required()
        url = 'https://www.pinterest.com/resource/BoardFollowResource/create/'
        data = url_encode({
            'source_url': board_url,
            'data': json.dumps({
                'options': {"board_id": board_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def unfollow_board(self, board_id, board_url):
        self.login_required()
        url = 'https://www.pinterest.com/resource/BoardFollowResource/delete/'
        data = url_encode({
            'source_url': board_url,
            'data': json.dumps({
                'options': {"board_id": board_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def follow_user(self, user_id, username):
        self.login_required()
        url = 'https://www.pinterest.com/resource/UserFollowResource/create/'
        data = url_encode({
            'source_url': '/%s/' % username,
            'data': json.dumps({
                'options': {"user_id": user_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def unfollow_user(self, user_id, username):
        self.login_required()
        url = 'https://www.pinterest.com/resource/UserFollowResource/delete/'
        data = url_encode({
            'source_url': '/%s/' % username,
            'data': json.dumps({
                'options': {"user_id": user_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def pin(self, board_id, image_url, description='', link='', share_facebook=False, share_twitter=False):
        self.login_required()
        url = 'https://www.pinterest.com/resource/PinResource/create/'
        data = url_encode({
            'source_url': '/pin/find/?url=%s' % url_encode(image_url),
            'data': json.dumps({
                'options': {
                    "board_id": board_id,
                    "image_url": image_url,
                    "description": description,
                    "link": link if link else image_url,
                    "scrape_metric": {"source": "www_url_scrape"},
                    "method": "scraped",
                    "share_facebook": share_facebook,
                    "share_twitter": share_twitter},
                "context": {}
            })
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            pin = {'id': result['resource_response']['data']['id']}
            return pin
        return None

    def upload_pin(self, board_id, image_file, description='', share_facebook=False, share_twitter=False):
        self.login_required()
        url = 'https://www.pinterest.com/resource/PinResource/create/'
        uploaded_image = self.__upload_image(image_file)
        if uploaded_image['success'] is True:
            image_url = uploaded_image['image_url']
            data = url_encode({
                'source_url': '/%s/' % self.user['username'],
                'data': json.dumps({
                    'options': {
                        "board_id": board_id,
                        "image_url": image_url,
                        "description": description,
                        "upload_metric": {"source": "pinner_upload_standalone"},
                        "method": "uploaded",
                        "share_facebook": share_facebook,
                        "share_twitter": share_twitter},
                    "context": {}
                }).replace(' ', '')
            })
            result = self.post(url=url, data=data, ajax=True).json()
            if result['resource_response']['error'] is None:
                pin = {'id': result['resource_response']['data']['id']}
                return pin
        return None

    def __upload_image(self, image_file):
        self.login_required()
        file_name = os.path.basename(image_file)
        mime_type = mimetypes.guess_type(image_file)[0]
        if mime_type is None:
            extension = os.path.splitext(image_file)[1][1:]
            if extension == 'jpg':
                mime_type = 'image/jpeg'
            else:
                mime_type = 'image/%s' % extension
        m = MultipartEncoder(fields={
            'qquuid': '%s' % uuid.uuid4(),
            'qqfilename': file_name,
            'img': ('%s' % file_name, open(image_file, 'rb'), mime_type)
        })
        headers = {
            'Content-Length': '%s' % m.len,
            'Content-Type': m.content_type,
            'X-UPLOAD-SOURCE': 'pinner_uploader'
        }
        url = 'https://www.pinterest.com/upload-image/?img=%s' % url_encode(file_name)
        result = self.post(url=url, data=m, headers=headers, ajax=True).json()
        return result

    def repin(self, board_id, pin_id, link='', title='', description='', share_facebook=False, share_twitter=False):
        """
        Save this Pin to a Board. For 'save button'
        """
        self.login_required()
        url = 'https://www.pinterest.com/resource/RepinResource/create/'
        data = url_encode({
            'source_url': '/pin/%s/' % pin_id,
            'data': json.dumps({
                'options': {
                    "board_id": board_id,
                    "pin_id": pin_id,
                    "link": link,
                    "title": title,
                    "description": description,
                    "is_buyable_pin": False,
                    "share_facebook": share_facebook,
                    "share_twitter": share_twitter
                },
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            pin = {'id': result['resource_response']['data']['id']}
            return pin
        return None

    def like(self, pin_id):
        self.login_required()
        url = 'https://www.pinterest.com/resource/PinLikeResource/create/'
        data = url_encode({
            'source_url': '/pin/%s/' % pin_id,
            'data': json.dumps({
                'options': {"pin_id": pin_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def undo_like(self, pin_id):
        self.login_required()
        url = 'https://www.pinterest.com/resource/PinLikeResource/delete/'
        data = url_encode({
            'source_url': '/pin/%s/' % pin_id,
            'data': json.dumps({
                'options': {"pin_id": pin_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def delete_pin(self, pin_id):
        self.login_required()
        url = 'https://www.pinterest.com/resource/PinResource/delete/'
        data = url_encode({
            'source_url': '/pin/%s/' % pin_id,
            'data': json.dumps({
                'options': {"id": pin_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def comment(self, pin_id, text):
        self.login_required()
        url = 'https://www.pinterest.com/resource/PinCommentResource/create/'
        data = url_encode({
            'source_url': '/pin/%s/' % pin_id,
            'data': json.dumps({
                'options': {"pin_id": "657384876829999984", "text": text},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            comment = {
                'id': result['resource_response']['data']['id'],
                'text': result['resource_response']['data']['text'],
                'created_at': result['resource_response']['data']['created_at']
            }
            return comment
        return None

    def delete_comment(self, pin_id, comment_id):
        self.login_required()
        url = 'https://www.pinterest.com/resource/PinCommentResource/delete/'
        data = url_encode({
            'source_url': '/pin/%s/' % pin_id,
            'data': json.dumps({
                'options': {"pin_id": pin_id, "comment_id": comment_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def invite(self, board_id, board_url, user_id):
        self.login_required()
        url = 'https://www.pinterest.com/resource/BoardInviteResource/create/'
        data = url_encode({
            'source_url': board_url,
            'data': json.dumps({
                'options': {"board_id": board_id, "invited_user_ids": [user_id]},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def delete_invite(self, board_id, board_url, invited_user_id, also_block=False):
        self.login_required()
        url = 'https://www.pinterest.com/resource/BoardInviteResource/delete/'
        data = url_encode({
            'source_url': board_url,
            'data': json.dumps({
                'options': {
                    "ban": also_block,
                    "board_id": board_id,
                    "field_set_key": "boardEdit",
                    "invited_user_id": invited_user_id},
                "context": {}
            }).replace(' ', '')
        })
        result = self.post(url=url, data=data, ajax=True).json()
        if result['resource_response']['error'] is None:
            return True
        return False

    def search(self, scope, query, next_page=False):
        if next_page is True and self.next_book_marks[scope].get(query):
            return self.__search_next_page(scope, query)
        q = url_encode({
            'q': query,
            '_': '%s' % int(time.time() * 1000)
        })
        url = 'https://www.pinterest.com/search/%s/?%s' % (scope, q)
        r = self.get(url=url)
        html = r.content[r.content.find('application/json'):]
        html = html[html.find('{'):html.find('</script>')]
        search_result = json.loads(html)
        results = []
        try:
            if len(search_result['resources']['data']['BaseSearchResource']) > 0:
                search_resource = search_result['resources']['data']['BaseSearchResource'].values()[0]
                results = search_resource['data']['results']
                self.next_book_marks[scope][query] = search_resource['nextBookmark']
        except KeyError:
            pass
        return results

    def __search_next_page(self, scope, query):
        q = url_encode({
            'source_url': '/search/%s/?q=%s' % (scope, query),
            'data': json.dumps({
                'options': {
                    'bookmarks': [self.next_book_marks[scope][query]],
                    'query': query,
                    'scope': scope
                },
                "context": {}
            }).replace(' ', ''),
            '_': '%s' % int(time.time() * 1000)
        })
        url = 'https://www.pinterest.com/resource/SearchResource/get/?%s' % q
        r = self.get(url=url, ajax=True).json()
        results = []
        try:
            if r['resource_response']['error'] is not None:
                error = r['resource_response']['error']
                raise PinterestException('[%s] %s' % (error['http_status'], error['message']))
            results = r['resource_response']['data']
            bookmarks = r['resource']['options']['bookmarks']
            if isinstance(bookmarks, basestring):
                self.next_book_marks[scope][query] = bookmarks
            else:
                self.next_book_marks[scope][query] = bookmarks[0]
        except KeyError:
            pass
        return results

    def search_boards(self, query, next_page=False):
        results = self.search('boards', query, next_page=next_page)
        boards = []
        for result in results:
            if result['type'] == 'board':
                boards.append({
                    'id': result['id'],
                    'name': result['name'],
                    'url': result['url'],
                    'privacy': result['privacy'],
                    'layout': result['layout'],
                    'followed_by_me': result['followed_by_me'],
                    'owner': {
                        'id': result['owner']['id'],
                        'username': result['owner']['username'],
                        'full_name': result['owner']['full_name'],
                        'followed_by_me': result['owner']['explicitly_followed_by_me'],
                    },
                    'description': result['description'],
                    'pin_count': result['pin_count'],
                })
        return boards

    def search_pins(self, query, next_page=False):
        results = self.search('pins', query, next_page=next_page)
        pins = []
        for result in results:
            if result['type'] == 'pin':
                pins.append({
                    'id': result['id'],
                    'description': result['description'],
                    'img': result['images']['orig']['url'],
                    'like_count': result['like_count'],
                    'comment_count': result['comment_count'],
                    'repin_count': result['repin_count'],
                    'liked_by_me': result['liked_by_me'],
                    'link': result['link'],
                    'title': result['title'],
                    'is_video': result['is_video'],
                    'board': {
                        'id': result['board']['id'],
                        'name': result['board']['name'],
                        'url': result['board']['url'],
                        'privacy': result['board']['privacy'],
                        'followed_by_me': result['board']['followed_by_me'],
                        'owner': {'id': result['board']['owner']['id']},
                    },
                    'pinner': {
                        'id': result['pinner']['id'],
                        'username': result['pinner']['username'],
                    }
                })
        return pins

    def search_users(self, query, next_page=False):
        results = self.search('people', query, next_page=next_page)
        users = []
        for result in results:
            if result['type'] == 'user':
                users.append({
                    'id': result['id'],
                    'username': result['username'],
                    'full_name': result['full_name'],
                    'blocked_by_me': result['blocked_by_me'],
                    'image_medium_url': result['image_medium_url'],
                    'followed_by_me': result['explicitly_followed_by_me'],
                    'follower_count': result['follower_count'],
                    'pin_count': result['pin_count'],
                    'board_count': result['board_count'],
                })
        return users
