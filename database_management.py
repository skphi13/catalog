from sqlalchemy.orm import sessionmaker
from database_setup_catalog import Base, User, Genre, MovieTitle, engine


Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# User functions
def create_user(name, email, picture):
    new_user = User(
        name=name,
        email=email,
        picture=picture
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


# def del_user(user_id):
#     user = session.query(User).filter_by(id=user_id).one()
#     session.delete(user)
#     session.commit()


# Genre functions
def create_genre(name):
    new_genre = Genre(name=name)
    session.add(new_genre)
    session.commit()
    return new_genre.id


def get_gen_id(name):
    gen = session.query(Genre).filter_by(name=name).one()
    return gen.id


def get_titles_in_genre(genre_name):
    titles_list = session.query(MovieTitle).join(MovieTitle.genre).filter_by(name=genre_name)
    return titles_list


# MovieTitle functions
def create_title(name, plot, genre_id, user_id):
    new_title = Title(
        name=name,
        plot=plot,
        genre_id=genre_id,
        user_id=user_id
        )
    session.add(new_title)
    session.commit()
    return new_title.id


# set up functions:

def add_users():
    user_list = [
        ['John Doe', 'John.Doe@email.com', 'http://picture_url.com']
    ]

    for user in user_list:
        create_user(user[0], user[1], user[2])


def fill_genres():
    gen_list = [
        'Action',
        'Adventure',
        'Comedy',
        'Dramas',
        'Horror',
        'Romance',
        'Sports',
        'Western'
    ]

    for gen in gen_list:
        create_genre(gen)


def fill_titles():

    movie_tuples = [
        (
            'The Avengers',
            'Team of superheroes band together to save the world',
            'Action'
            ),
        (
            'Black Panther',
            'Story about T\'Challa quest to become king and save his hometown',
            'Adventure'
            ),
        (
            'Superbad',
            'Highschool students using a fake id to buy alcohol and throw a party',
            'Comedy'
            ),
        (
            'The Greatest Showman',
            'Story about how the most famous circus came to be',
            'Dramas'
            ),
        (
            'It',
            'Story about a killer clown terrorizing little kids',
            'Horror'
            ),
        (
            'A Walk to Remember',
            'Dying girl changes boys life by falling love with him',
            'Romance'
            ),
        (
            'Miracle',
            'Story about USA hockey team beating Russia for gold in the olympics',
            'Sports'
            ),
        (
            '3:10 to Yuma',
            'Father escorting a fugitive to trial',
            'Western'
            ),
    ]

    for tup in movie_tuples:
        create_titles(
            tup[0],
            tup[1],
            get_gen_id(tup[2]),
            1
            )


if __name__ == '__main__':
    add_users()
    fill_genres()
    fill_titles()
