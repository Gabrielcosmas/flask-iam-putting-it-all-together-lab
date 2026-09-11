from config import db, bcrypt
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

try:
    from sqlalchemy_serializer import SerializerMixin
except ModuleNotFoundError:
    class SerializerMixin:
        serialize_only = ()
        serialize_rules = ()

        def to_dict(self, rules=(), only=(), exclude=()):
            excluded = set(exclude) if exclude else set()
            if hasattr(self, "serialize_rules") and self.serialize_rules:
                for r in self.serialize_rules:
                    if r.startswith("-"):
                        excluded.add(r[1:])
            res = {}
            if hasattr(self, "__table__"):
                for col in self.__table__.columns:
                    if col.name not in excluded:
                        res[col.name] = getattr(self, col.name)
            if hasattr(self, "__mapper__"):
                for rel in self.__mapper__.relationships:
                    name = rel.key
                    if name not in excluded:
                        val = getattr(self, name)
                        if val is None:
                            res[name] = None
                        elif isinstance(val, list):
                            res[name] = [item.to_dict() if hasattr(item, "to_dict") else str(item) for item in val]
                        else:
                            res[name] = val.to_dict() if hasattr(val, "to_dict") else str(val)
            return res

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String)
    bio = db.Column(db.String)
    image_url = db.Column(db.String)

    # Relationship to Recipe model
    recipes = db.relationship('Recipe', backref='user', cascade='all, delete-orphan')

    # Prevent recursion in JSON serialization
    serialize_rules = ('-recipes.user', '-_password_hash')

    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8')
        )
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8')
        )

    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError('User must have a username.')
        return username

    def __repr__(self):
        return f'<User {self.username}>'


class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Prevent recursion in JSON serialization
    serialize_rules = ('-user.recipes',)

    @validates('title')
    def validate_title(self, key, title):
        if not title:
            raise ValueError('Recipe must have a title.')
        return title

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions or len(instructions) < 50:
            raise ValueError('Instructions must be at least 50 characters long.')
        return instructions

    def __repr__(self):
        return f'<Recipe {self.title}>'