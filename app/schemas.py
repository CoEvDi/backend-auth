from pydantic import BaseModel


class CurrentUser:
    is_auth = False
    
    def __init__(self, db_info = None, role=None):
        if db_info:
            self.is_auth = True
            self.account_id = db_info['account_id']
            self.session_id = db_info['id']
            self.role = role
            self.client = db_info['client']
            self.login_time = db_info['login_time']

    
    def jsonify(self):
        return {
            'account_id': self.account_id,
            'session_id': self.session_id,
            'role': self.role,
            'client': self.client,
            'login_time': self.login_time,
        }


    def auth_info(self):
        return {
            'ACCOUNT_ID': self.account_id,
            'SESSION_ID': self.session_id,
            'ACCOUNT_ROLE': self.role
        }


class Token(BaseModel):
    token: str


class AuthCredentials(BaseModel):
    login: str
    password: str


class Password(BaseModel):
    password: str


class Session(BaseModel):
    session: str
    user_id: int
