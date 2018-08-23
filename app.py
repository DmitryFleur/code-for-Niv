from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import validates
from flask import jsonify, request, json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/temp_db.db'
db = SQLAlchemy(app)


class Friends(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friend_id = db.Column(db.Integer)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    friends = db.relationship('Friends', backref='user', lazy='dynamic')

    @validates('email')
    def validate_email(self, key, address):
        assert '@' in address
        return address

    def __repr__(self):
        return self.name


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    if not data:
        return jsonify({'status': 'error: provide some data'})
    if 'name' not in data or 'email' not in data:
        return jsonify({'status': 'error: some of the fields are missed'})

    if not User.query.filter_by(email=data['email']).first():
        try:
            user = User(name=data['name'],
                        email=data['email'])
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            return jsonify({'status': e})

    return jsonify({'status': 'user is created'})


@app.route('/user/<user_id>/', defaults={'optional_path': None})
@app.route('/user/<user_id>/<optional_path>')
def user(user_id, optional_path):
    user = User.query.get(user_id)
    if not optional_path and user:
        return jsonify({'name': user.name})
    if optional_path == 'friends' and user:
        return jsonify({'friends': [i.friend_id for i in user.friends]})
    if optional_path == 'suggestFriends':
        user_friends = [i.friend_id for i in user.friends]
        suggested = []
        for friend in user_friends:
            suggested = [i.friend_id for i in Friends.query.filter_by(user_id=friend) if i.friend_id != user.id]
        return jsonify({'friends': suggested})


@app.route('/friend/<first_id>/<second_id>')
def add_friends(first_id, second_id):

    def add_friend(first_user, second_user):
        friend = Friends(user_id=first_user, friend_id=second_user)
        db.session.add(friend)
        first_user.friends.append(friend)
        db.session.commit()

    first_user = User.query.filter_by(id=first_id).first()
    second_user = User.query.filter_by(id=second_id).first()

    if first_user and second_user:
        add_friend(first_user, second_user.id)
        add_friend(second_user, first_user.id)

        return jsonify({'status': 'friends added'})


if __name__ == '__main__':
    app.run()
