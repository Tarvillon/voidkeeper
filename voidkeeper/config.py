import datetime
import os


class Defaults(object):
    @staticmethod
    def fields():
        return ['id', 'username', 'email', 'service']

    @staticmethod
    def editable_fields():
        return ['username', 'email', 'service', 'password']

    @staticmethod
    def template():
        return "{id} {username} {email} {service}"

    @staticmethod
    def header():
        return {'id': 'ID', 'username': 'Username', 'email': 'e-mail', 'service': 'Service'}


class Config(object):
    def __init__(self):
        home = os.environ.get('HOME')
        self.voidkeeper_home = os.environ.get('VOIDKEEPER_PATH')
        if not self.voidkeeper_home:
            self.voidkeeper_home = os.path.join(home, '.voidkeeper')
        self.voids_path = os.path.join(self.voidkeeper_home, 'voids/')
        self.config_path = os.path.join(self.voidkeeper_home, 'config')
        self.storage_name = 'default.json'
        self.storage = os.path.join(self.voids_path, self.storage_name) 
        self.backup = True
        self.backups_path = os.path.join(self.voids_path, 'backups/')
    
    def check_state(self):
        voids = os.path.exists(self.voids_path)
        backups = os.path.exists(self.backups_path)
        storage = os.path.exists(self.storage)
        return {
            'voids': voids,
            'backups': backups,
            'storage': storage
        }

    def make_voids_path(self):
        os.makedirs(self.voids_path, exist_ok=True)

    def make_backups_path(self):
        os.makedirs(self.backups_path, exist_ok=True)

    def make_storage(self): 
        with open(self.storage, 'w') as target:
            json.dump({}, target, ensure_ascii=False)
    
    def restore(self, state):
        if not state.get('voids', False):
            self.make_voids_path()
        if not state.get('backups', False):
            self.make_backups_path()
        if not state.get('storage', False):
            self.make_storage()

    def new_backup(self, prefix=datetime.datetime.now().isoformat()):
        return os.path.join(self.backups_path, "{}_{}".format(prefix, self.storage_name))
