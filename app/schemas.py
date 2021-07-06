from pydantic import BaseModel


class CurrentUser:
    is_auth = False
    
    def __init__(self, db_info = None, role=None):
        if db_info:
            self.is_auth = True
            self.session_id = db_info['id']
            self.role = role
            self.account_id = db_info['account_id']
            self.client = db_info['client']
            self.login_time = db_info['login_time']

    
    def jsonify(self):
        return {
            'session_id': self.session_id,
            'role': self.role,
            'account_id': self.account_id,
            'client': self.client,
            'login_time': self.login_time,
        }


class AuthCredentials(BaseModel):
    login: str
    password: str


class Password(BaseModel):
    password: str


class Session(BaseModel):
    session: str
    user_id: int
