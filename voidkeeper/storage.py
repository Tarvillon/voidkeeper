import copy
import hashlib
import json
import random
import shutil
import string

from voidkeeper.config import Defaults, Config


class Void(object):
    def __init__(self, record={}, need_id=True, need_password=False):
        self.username = record.get('username', '')
        self.email = record.get('email', '')
        self.service = record.get('service', '')
        self.secrets = record.get('secrets', [])

        self.id = record.get('id', '')
        if need_id and not self.id:
            self.generate_id()
        self.password = record.get('password', '')
        if need_password and not self.password:
            self.generate_password()

    def generate_password(self, length=13):
        main = [random.choice(string.ascii_letters)]
        [main.append(
            random.choice(string.printable)
        ) for i in range(length - 1)]
        self.password = ''.join(main)

    def generate_id(self):
        hash = hashlib.sha256("{}_{}_{}".format(self.username, self.email, self.service).encode('utf8'))
        self.id = hash.hexdigest()

    @property
    def dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'service': self.service,
            'secrets': self.secrets,
            'password': self.password,
        }

    @property
    def printable(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'service': self.service,
        }


class VoidHeader(object):
    @property
    def printable(self):
        return {
            'id': 'id',
            'username': 'username',
            'email': 'email',
            'service': 'service',
        }


class VoidSpawner(object):
    @staticmethod
    def create(username='', email='', service='', secrets=[], password=None):
        void = Void(need_id=True, need_password=password is None, record={
            'username': username,
            'email': email,
            'service': service,
            'password': password,
            'secrets': secrets
        })
        return void


class VoidList(object):
    def __init__(self, data=[], init_list=None):
        self.list = init_list if init_list else []
        for item in data:
            if type(item) is dict:
                self.list.append(Void(need_id=False, record=item))

    def __getitem__(self, desc):
        if type(desc) is int:
            return self.list[desc]

    def __len__(self):
        return len(self.list)

    def add(self, void):
        self.list.append(VoidSpawner.create(**void))

    def merge(self, voidlist):
        self.list.extend(voidlist.list)

    def update(self, void):
        for item in self.list:
            if item.id == void.id:
                place = self.list.index(item)
                self.list[place] = void
                break

    def filter(self, data={}):
        filtered = self.list
        for field, value in data.items():
            filtered = list(filter(lambda x: getattr(x, field, '') == value, filtered))
        return VoidList(init_list=copy.deepcopy(filtered))

    def by_id_fuzzy(self, hash):
        return self.target_fuzzy(data={'id': hash})

    def target_fuzzy(self, data={}):
        filtered = copy.deepcopy(self.list)
        for field, value in data.items():
            filtered = list(filter(lambda x: x.printable.get(field, '').startswith(value), filtered))
        return VoidList(init_list=filtered)

    @staticmethod
    def check_field_fuzzy(void, field):
        for value in void.printable.values():
            if field in value:
                return True
        return False

    def full_fuzzy(self, data=[]):
        result = VoidList(init_list=[], data=[])
        for field in data:
            result.merge(self.by_id_fuzzy(field))

        if len(result) > 0:
            return result

        for field in data:
            for void in self.list:
                if VoidList.check_field_fuzzy(void, field):
                    result.add(void)
        return result

    def find(self, data=None):
        if type(data) not in [tuple, list, dict]:
            return None

        if type(data) is list:
            return self.full_fuzzy(data)
        elif type(data) is tuple:
            return self.full_fuzzy(list(data))

        return self.target_fuzzy(data)

    @property
    def storing(self):
        return [void.dict for void in self.list]


class VoidKeeper(object):
    def build_config(self, config):
        if config:
            return config
        return Config()

    def __init__(self, config={}):
        self.config = self.build_config(config)
        try:
            with open(self.config.storage, 'r') as storage:
                self.data = json.load(storage)
        except json.decoder.JSONDecodeError:
            # log error about broken storage file
            pass
        except FileNotFoundError:
            # log error about missing storage file
            pass
        finally:
            if not hasattr(self, 'data'):
                self.data = {}

    def list(self):
        return VoidList(data=self.data.get('list', []))

    def store(self, voidlist):
        if self.config.backup:
            shutil.copy(self.config.storage, self.config.new_backup())

        with open(self.config.storage, 'w') as target:
            json.dump({'list': voidlist.storing}, target, ensure_ascii=False)
