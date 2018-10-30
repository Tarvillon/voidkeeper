import subprocess


class Clipboard(object):
    def clipboard(self):
        return subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, close_fds=True)
    
    def clear(self):
        clipboard = self.clipboard()
        clipboard.communicate(input=''.encode('utf-8'))

    def place(self, data): 
        clipboard = self.clipboard()
        clipboard.communicate(input=str(data).encode('utf-8'))
