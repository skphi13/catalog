from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import asc, desc


Base = declarative_base()

engine = create_engine('sqlite:///gamescatalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# User functions
def create_user(login_session):
    new_user = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture']
        )

    session.add(new_user)
    session.commit()
    return new_user.id


def get_user(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250))
    picture = Column(String)


# Genres functions
def create_genre(name):
    new_genre = Genre(name=name)
    session.add(new_genre)
    session.commit()
    return new_genre.id


def get_gen(gen_id):
    gen = session.query(Genre).filter_by(id=gen_id).one()
    return gen


def get_gen_id(name):
    cat = session.query(Genre).filter_by(name=name).one()
    return gen.id


def get_titles_in_genre(genre_id):
    titles_list = session.query(MovieTitle).join(MovieTitle.genre).filter_by(id=genre_id)
    return titles_list


def get_all_genres():
    genres = session.query(Genre).order_by(asc(Genre.name))
    return genres


class Genre(Base):
    __tablename__ = 'genre'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name
        }


# MovieTitle functions
def create_title(name, plot, genre_id, user_id):
    new_title = MovieTitle(
        name=name,
        plot=plot,
        genre_id=genre_id,
        user_id=user_id
        )
    session.add(new_title)
    session.commit()
    return new_title


def get_title(title_id):
    title = session.query(MovieTitle).filter_by(id=title_id).one()
    return title


def delete_title(title):
    session.delete(title)
    session.commit()


def edit_title(title, name, plot, genre_id):
    title.name = name
    title.plot = plot
    title.genre_id = genre_id
    session.add(title)
    session.commit()
    return title


class MovieTitle(Base):
    __tablename__ = 'movie_title'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    plot = Column(Text)
    genre_id = Column(Integer, ForeignKey('genre.id'))
    genre = relationship(Genre)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'plot': self.plot,
            'genre': self.genre.name
        }

if __name__ == '__main__':
    Base.metadata.create_all(engine)
