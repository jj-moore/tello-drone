class User:
    name = ''
    type = ''
    organization = ''
    major = ''

    def __str__(self):
        return f'Name: {self.name} Type: {self.type} Org: {self.organization} Major: {self.major}'