import os
import requests
import streamlit as st


API_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")


DEMO_MOVIES = [
    {
        "title": "Interstellar",
        "description": "A science fiction film about space, time, gravity, and human survival.",
        "genres": ["Sci-Fi", "Drama", "Adventure"],
        "year": 2014,
        "director": "Christopher Nolan",
        "poster_url": "https://example.com/interstellar.jpg",
    },
    {
        "title": "Inception",
        "description": "A thief enters people's dreams to steal secrets and plant ideas.",
        "genres": ["Sci-Fi", "Thriller", "Action"],
        "year": 2010,
        "director": "Christopher Nolan",
        "poster_url": "https://example.com/inception.jpg",
    },
    {
        "title": "The Matrix",
        "description": "A hacker discovers that reality is a simulation controlled by machines.",
        "genres": ["Sci-Fi", "Action"],
        "year": 1999,
        "director": "The Wachowskis",
        "poster_url": "https://example.com/matrix.jpg",
    },
    {
        "title": "Arrival",
        "description": "A linguist works with the military to communicate with alien visitors.",
        "genres": ["Sci-Fi", "Drama"],
        "year": 2016,
        "director": "Denis Villeneuve",
        "poster_url": "https://example.com/arrival.jpg",
    },
    {
        "title": "Blade Runner 2049",
        "description": "A young blade runner uncovers a secret that could destabilize society.",
        "genres": ["Sci-Fi", "Drama", "Cyberpunk"],
        "year": 2017,
        "director": "Denis Villeneuve",
        "poster_url": "https://example.com/blade-runner-2049.jpg",
    },
    {
        "title": "Dune",
        "description": "A noble family becomes involved in a war for control of the desert planet Arrakis.",
        "genres": ["Sci-Fi", "Adventure", "Drama"],
        "year": 2021,
        "director": "Denis Villeneuve",
        "poster_url": "https://example.com/dune.jpg",
    },
    {
        "title": "The Dark Knight",
        "description": "Batman faces the Joker, a criminal mastermind who wants to create chaos in Gotham.",
        "genres": ["Action", "Crime", "Drama"],
        "year": 2008,
        "director": "Christopher Nolan",
        "poster_url": "https://example.com/dark-knight.jpg",
    },
    {
        "title": "Whiplash",
        "description": "A young drummer pushes himself to the limit under a ruthless music instructor.",
        "genres": ["Drama", "Music"],
        "year": 2014,
        "director": "Damien Chazelle",
        "poster_url": "https://example.com/whiplash.jpg",
    },
    {
        "title": "Parasite",
        "description": "A poor family infiltrates a wealthy household with unexpected consequences.",
        "genres": ["Drama", "Thriller", "Comedy"],
        "year": 2019,
        "director": "Bong Joon-ho",
        "poster_url": "https://example.com/parasite.jpg",
    },
    {
        "title": "The Grand Budapest Hotel",
        "description": "A hotel concierge and a lobby boy become involved in a theft and family conflict.",
        "genres": ["Comedy", "Drama", "Adventure"],
        "year": 2014,
        "director": "Wes Anderson",
        "poster_url": "https://example.com/grand-budapest.jpg",
    },
    {
        "title": "Mad Max: Fury Road",
        "description": "In a post-apocalyptic wasteland, rebels flee across the desert from a tyrant.",
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "year": 2015,
        "director": "George Miller",
        "poster_url": "https://example.com/mad-max.jpg",
    },
    {
        "title": "The Social Network",
        "description": "A drama about the creation of Facebook and the conflicts around it.",
        "genres": ["Drama", "Biography"],
        "year": 2010,
        "director": "David Fincher",
        "poster_url": "https://example.com/social-network.jpg",
    },
]


DEMO_USERS = [
    {"username": "sasha", "email": "sasha@example.com", "password": "123456"},
    {"username": "moviefan", "email": "moviefan@example.com", "password": "123456"},
    {"username": "cinephile", "email": "cinephile@example.com", "password": "123456"},
    {"username": "nolanlover", "email": "nolan@example.com", "password": "123456"},
    {"username": "scifi_queen", "email": "scifi@example.com", "password": "123456"},
    {"username": "filmcritic", "email": "critic@example.com", "password": "123456"},
]


DEMO_REVIEW_TEXTS = [
    "A powerful movie with great atmosphere and emotional depth.",
    "The visual style is impressive, and the story keeps you engaged.",
    "One of those films that stays in your head after watching.",
    "Strong direction, memorable scenes, and a great soundtrack.",
    "Not perfect, but definitely worth watching.",
    "The pacing is excellent, and the characters feel meaningful.",
    "A very cinematic experience with strong worldbuilding.",
    "The concept is fascinating and executed with confidence.",
    "Great movie for people who enjoy thoughtful storytelling.",
    "The ending makes the whole film even stronger.",
    "A solid film with a strong emotional core.",
    "The performances make the story feel alive and believable.",
]


st.set_page_config(
    page_title="Movie Review Platform",
    page_icon="🎬",
    layout="wide",
)


def css():
    st.markdown(
        """
        <style>
        .stApp {
            background: #080b12;
            color: #f8fafc;
        }

        .hero {
            padding: 28px 32px;
            border-radius: 28px;
            background: linear-gradient(135deg, #172033, #111827 45%, #3b0764);
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 26px;
        }

        .hero h1 {
            font-size: 46px;
            margin-bottom: 4px;
        }

        .hero p {
            color: #cbd5e1;
            font-size: 17px;
        }

        .card {
            padding: 20px;
            border-radius: 22px;
            background: rgba(15, 23, 42, 0.94);
            border: 1px solid rgba(148, 163, 184, 0.18);
            margin-bottom: 16px;
        }

        .review {
            padding: 18px;
            border-radius: 20px;
            background: rgba(17, 24, 39, 0.95);
            border-left: 5px solid #8b5cf6;
            margin-bottom: 14px;
        }

        .tag {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 999px;
            background: rgba(139, 92, 246, 0.20);
            color: #ddd6fe;
            font-size: 12px;
            margin-right: 6px;
            margin-top: 5px;
        }

        .muted {
            color: #94a3b8;
            font-size: 13px;
        }

        .good {
            color: #86efac;
        }

        .bad {
            color: #fca5a5;
        }

        .stButton > button {
            border-radius: 14px;
            font-weight: 700;
        }

        div[data-testid="stSidebar"] {
            background: #020617;
            border-right: 1px solid rgba(148, 163, 184, 0.15);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def init_state():
    defaults = {
        "token": None,
        "user": None,
        "selected_movie": None,
        "nav_page": "Catalog",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def api(method, path, payload=None, token=None):
    headers = {}

    if token is None:
        token = st.session_state.get("token")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{API_URL}{path}"

    if method == "GET":
        response = requests.get(url, headers=headers, timeout=20)
    elif method == "POST":
        response = requests.post(url, json=payload, headers=headers, timeout=20)
    else:
        raise ValueError("Unsupported method")

    if response.status_code >= 400:
        raise Exception(response.text)

    return response.json()


def get(path, token=None):
    return api("GET", path, token=token)


def post(path, payload=None, token=None):
    return api("POST", path, payload=payload, token=token)


def get_users_map():
    try:
        users = get("/auth/users")
        return {user["id"]: user["username"] for user in users}
    except Exception:
        return {}


def get_movies_map():
    try:
        movies = get("/catalog")
        return {movie["id"]: movie for movie in movies}
    except Exception:
        return {}


def get_user_by_username(username):
    return get(f"/auth/users/by-username/{username}")


def save_session_to_url():
    return


def restore_session_from_url():
    return


def hero():
    st.markdown(
        """
        <div class="hero">
            <h1>🎬 Movie Review Platform</h1>
            <p>
            A real microservices movie review app with authentication, catalog, reviews,
            social feed, Kafka events, Redis sessions, MongoDB Replica Set and Neo4j graph.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def auth_gate():
    st.markdown("## Welcome back")

    left, right = st.columns(2)

    with left:
        st.markdown("### Login")
        email = st.text_input("Email", value="gateway@example.com")
        password = st.text_input("Password", type="password", value="123456")

        if st.button("Login", use_container_width=True):
            try:
                login = post("/auth/login", {"email": email, "password": password})
                token = login["access_token"]
                profile = get("/auth/me", token=token)

                st.session_state.token = token
                st.session_state.user = profile
                save_session_to_url()
                st.success(f"Logged in as @{profile['username']}")
                st.rerun()
            except Exception as error:
                st.error(error)

    with right:
        st.markdown("### Create account")
        username = st.text_input("Username", key="register_username")
        reg_email = st.text_input("Email", key="register_email")
        reg_password = st.text_input("Password", type="password", key="register_password")

        if st.button("Register and login", use_container_width=True):
            try:
                post(
                    "/auth/register",
                    {
                        "email": reg_email,
                        "username": username,
                        "password": reg_password,
                    },
                )

                login = post(
                    "/auth/login",
                    {
                        "email": reg_email,
                        "password": reg_password,
                    },
                )

                token = login["access_token"]
                profile = get("/auth/me", token=token)

                st.session_state.token = token
                st.session_state.user = profile
                save_session_to_url()
                st.success(f"Created account and logged in as @{profile['username']}")
                st.rerun()

            except Exception as error:
                st.error(error)

    st.info("You must register or login before using the platform.")


def sidebar():
    user = st.session_state.user

    with st.sidebar:
        st.title("🎬 Platform")

        st.caption("API Gateway")
        st.code(API_URL)

        st.success(f"Logged in as @{user['username']}")
        st.caption(f"Email: {user['email']}")
        st.caption(f"User ID: {user['id']}")

        if st.session_state.selected_movie:
            st.info(f"Selected movie:\n{st.session_state.selected_movie['title']}")

        st.markdown("### Navigation")

        pages = [
            "Catalog",
            "Reviews",
            "Feed",
            "Users",
            "System",
            "Profile",
        ]

        for page in pages:
            button_label = f"● {page}" if st.session_state.nav_page == page else page

            if st.button(button_label, key=f"nav_btn_{page}", use_container_width=True):
                st.session_state.nav_page = page
                st.rerun()

        st.divider()

        if st.button("Logout", use_container_width=True):
            try:
                post("/auth/logout", token=st.session_state.token)
            except Exception:
                pass

            st.session_state.token = None
            st.session_state.user = None
            st.session_state.selected_movie = None
            st.session_state.nav_page = "Catalog"
            st.query_params.clear()
            st.rerun()


def seed_movies():
    existing = get("/catalog")
    existing_titles = {movie["title"].lower() for movie in existing}

    created = 0
    skipped = 0

    for movie in DEMO_MOVIES:
        if movie["title"].lower() in existing_titles:
            skipped += 1
            continue

        post("/catalog", movie)
        created += 1

    return created, skipped


def ensure_demo_users():
    existing_users = get("/auth/users")
    existing_usernames = {user["username"] for user in existing_users}

    created = 0
    skipped = 0

    for user in DEMO_USERS:
        if user["username"] in existing_usernames:
            skipped += 1
            continue

        try:
            post(
                "/auth/register",
                {
                    "email": user["email"],
                    "username": user["username"],
                    "password": user["password"],
                },
            )
            created += 1
        except Exception:
            skipped += 1

    users = get("/auth/users")
    return users, created, skipped


def ensure_demo_movies():
    existing = get("/catalog")
    existing_titles = {movie["title"].lower() for movie in existing}

    created = 0
    skipped = 0

    for movie in DEMO_MOVIES:
        if movie["title"].lower() in existing_titles:
            skipped += 1
            continue

        post("/catalog", movie)
        created += 1

    movies = get("/catalog")
    return movies, created, skipped


def get_demo_token(username):
    demo_user = next(
        (user for user in DEMO_USERS if user["username"] == username),
        None,
    )
    if not demo_user:
        return st.session_state.token

    login = post(
        "/auth/login",
        {
            "email": demo_user["email"],
            "password": demo_user["password"],
        },
        token=None,
    )
    return login["access_token"]


def seed_demo_reviews(users, movies):
    if not users or not movies:
        return 0

    try:
        existing_reviews = get("/reviews")
    except Exception:
        existing_reviews = []

    existing_keys = {
        (
            review.get("user_id"),
            review.get("item_id"),
            review.get("text"),
        )
        for review in existing_reviews
    }

    created = 0

    demo_usernames = {user["username"] for user in DEMO_USERS}
    demo_users = [user for user in users if user["username"] in demo_usernames]

    if not demo_users:
        demo_users = users

    max_reviews = min(36, len(movies) * 3)

    for index in range(max_reviews):
        user = demo_users[index % len(demo_users)]
        movie = movies[index % len(movies)]
        text = DEMO_REVIEW_TEXTS[index % len(DEMO_REVIEW_TEXTS)]

        key = (user["id"], movie["id"], text)
        if key in existing_keys:
            continue

        payload = {
            "item_id": movie["id"],
            "text": text,
            "rating": 7 + (index % 4),
        }

        try:
            token = get_demo_token(user["username"])
            post("/reviews", payload, token=token)
            existing_keys.add(key)
            created += 1
        except Exception:
            pass

    return created


def seed_demo_follows(users):
    username_to_user = {user["username"]: user for user in users}

    follow_pairs = [
        ("sasha", "moviefan"),
        ("sasha", "cinephile"),
        ("sasha", "nolanlover"),
        ("moviefan", "nolanlover"),
        ("cinephile", "scifi_queen"),
        ("scifi_queen", "sasha"),
        ("nolanlover", "scifi_queen"),
        ("filmcritic", "sasha"),
        ("filmcritic", "moviefan"),
    ]

    current_user = st.session_state.get("user")
    if current_user:
        for demo_user in DEMO_USERS:
            if demo_user["username"] != current_user["username"]:
                follow_pairs.append((current_user["username"], demo_user["username"]))

    created = 0

    for follower_username, following_username in follow_pairs:
        follower = username_to_user.get(follower_username)
        following = username_to_user.get(following_username)

        if not follower or not following:
            continue

        if follower["id"] == following["id"]:
            continue

        try:
            token = (
                st.session_state.token
                if current_user and current_user["username"] == follower_username
                else get_demo_token(follower_username)
            )
            post(f"/feed/follow/{following['id']}", token=token)
            created += 1
        except Exception:
            pass

    return created


def seed_demo_world():
    users, users_created, users_skipped = ensure_demo_users()
    movies, movies_created, movies_skipped = ensure_demo_movies()

    reviews_created = seed_demo_reviews(users, movies)
    follows_created = seed_demo_follows(users)

    return {
        "users_created": users_created,
        "users_skipped": users_skipped,
        "movies_created": movies_created,
        "movies_skipped": movies_skipped,
        "reviews_created": reviews_created,
        "follows_created": follows_created,
    }


def movie_card(movie):
    genres = "".join(
        [f"<span class='tag'>{genre}</span>" for genre in movie.get("genres", [])]
    )

    st.markdown(
        f"""
        <div class="card">
            <h3>{movie["title"]} <span class="muted">({movie["year"]})</span></h3>
            <p>{movie["description"]}</p>
            <p class="muted"><b>Director:</b> {movie["director"]}</p>
            <div>{genres}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Write review", key=f"write_{movie['id']}", use_container_width=True):
            st.session_state.selected_movie = movie
            st.session_state.nav_page = "Reviews"
            st.rerun()

    with col2:
        if st.button("Read reviews", key=f"read_{movie['id']}", use_container_width=True):
            st.session_state.selected_movie = movie
            st.session_state.nav_page = "Reviews"
            st.rerun()

def page_catalog():
    st.subheader("Movie catalog")

    st.markdown("### Demo data")

    if st.button("Seed Demo World", use_container_width=True):
        try:
            result = seed_demo_world()
            st.success("Demo world created successfully.")
            st.json(result)
            st.info(
                "Created demo users, movies, reviews, follows, Kafka events and Neo4j graph data."
            )
        except Exception as error:
            st.error(error)

    st.divider()

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Seed demo movies only", use_container_width=True):
            try:
                created, skipped = seed_movies()
                st.success(f"Created {created}, skipped {skipped}.")
            except Exception as error:
                st.error(error)

    with col2:
        if st.button("Refresh catalog", use_container_width=True):
            st.rerun()

    st.divider()

    search = st.text_input("Search by title")
    genre = st.text_input("Filter by genre")

    try:
        if search or genre:
            query = []
            if search:
                query.append(f"title={search}")
            if genre:
                query.append(f"genre={genre}")

            movies = get("/catalog/search?" + "&".join(query))
        else:
            movies = get("/catalog")

        if not movies:
            st.warning("No movies yet. Click Seed Demo World.")

        for movie in movies:
            movie_card(movie)

    except Exception as error:
        st.error(error)


def review_card(review, users_map=None, movies_map=None, show_open_button=True):
    users_map = users_map or {}
    movies_map = movies_map or {}

    username = review.get("username") or users_map.get(review["user_id"], f"user-{review['user_id']}")
    movie = review.get("movie") or movies_map.get(review["item_id"])

    movie_title = movie["title"] if movie else f"Movie {review['item_id']}"
    movie_year = movie["year"] if movie else ""
    stars = "⭐" * int(review["rating"])
    review_id = review.get("id", review.get("review_id", "?"))

    st.markdown(
        f"""
        <div class="review">
            <h3>{stars}</h3>
            <p>{review["text"]}</p>
            <p class="muted">
                by <b>@{username}</b> · review #{review_id} · {review["created_at"]}
            </p>
            <p class="muted">
                Movie: <b>{movie_title}</b> {f"({movie_year})" if movie_year else ""}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if show_open_button and movie:
        if st.button(
            f"Open reviews for {movie_title}",
            key=f"open_reviews_{review_id}_{review['item_id']}",
            use_container_width=True,
        ):
            st.session_state.selected_movie = movie
            st.session_state.nav_page = "Reviews"
            st.rerun()


def page_reviews():
    users_map = get_users_map()
    movies_map = get_movies_map()
    movie = st.session_state.selected_movie

    st.subheader("Reviews")

    all_movies = list(movies_map.values())

    if not movie:
        st.warning("Choose a movie from Catalog or select it here.")

        if all_movies:
            movie_titles = [f"{movie['title']} ({movie['year']})" for movie in all_movies]
            selected_title = st.selectbox("Choose movie", movie_titles)
            selected_index = movie_titles.index(selected_title)

            if st.button("Select movie", use_container_width=True):
                st.session_state.selected_movie = all_movies[selected_index]
                st.rerun()
        else:
            st.info("No movies yet. Go to Catalog and click Seed Demo World.")

        st.divider()

    movie = st.session_state.selected_movie

    if movie:
        st.markdown(
            f"""
            <div class="card">
                <h2>{movie["title"]} <span class="muted">({movie["year"]})</span></h2>
                <p>{movie["description"]}</p>
                <p class="muted">Director: {movie["director"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### Reviews for this movie")

        try:
            movie_reviews = get(f"/reviews/enriched?item_id={movie['id']}")

            if not movie_reviews:
                st.info("No reviews for this movie yet.")

            for review in movie_reviews:
                review_card(
                    review,
                    users_map=users_map,
                    movies_map=movies_map,
                    show_open_button=False,
                )

        except Exception as error:
            st.error(error)

        st.divider()

        st.markdown("### Write review")

        st.caption(f"You are writing as @{st.session_state.user['username']}")

        text = st.text_area(
            "Your review",
            height=150,
            value="This movie has strong atmosphere, story and visual style.",
        )
        rating = st.slider("Rating", 1, 10, 9)

        if st.button("Publish review", use_container_width=True):
            try:
                result = post(
                    "/reviews",
                    {
                        "item_id": movie["id"],
                        "text": text,
                        "rating": int(rating),
                    },
                )

                st.success("Review published. Kafka event sent to Feed Service.")
                st.json(result)
            except Exception as error:
                st.error(error)

        st.divider()

    st.markdown("### All reviews")

    try:
        reviews = get("/reviews/enriched")

        if not reviews:
            st.info("No reviews yet.")

        for review in reviews:
            review_card(
                review,
                users_map=users_map,
                movies_map=movies_map,
                show_open_button=True,
            )

    except Exception as error:
        st.error(error)

def page_feed():
    st.subheader("Social feed")

    users = get("/auth/users")
    users_map = get_users_map()
    movies_map = get_movies_map()

    usernames = [
        user["username"]
        for user in users
        if user["id"] != st.session_state.user["id"]
    ]

    tab_follow, tab_feed = st.tabs(["Follow people", "My feed"])

    with tab_follow:
        if not usernames:
            st.info("No other users yet. Use Seed Demo World or register another account.")
        else:
            selected_username = st.selectbox("Choose user to follow", usernames)

            if st.button("Follow", use_container_width=True):
                try:
                    selected_user = get_user_by_username(selected_username)

                    post(
                        f"/feed/follow/{selected_user['id']}"
                    )

                    st.success(f"You now follow @{selected_username}")
                except Exception as error:
                    st.error(error)

    with tab_feed:
        if st.button("Refresh feed", use_container_width=True):
            st.rerun()

        try:
            feed = get("/feed/enriched")

            if not feed:
                st.info("Your feed is empty. Follow someone who has written reviews.")

            for item in feed:
                review_card(
                    item,
                    users_map=users_map,
                    movies_map=movies_map,
                    show_open_button=True,
                )

        except Exception as error:
            st.error(error)


def page_users():
    st.subheader("Users")

    try:
        users = get("/auth/users")

        for user in users:
            marker = "you" if user["id"] == st.session_state.user["id"] else ""

            st.markdown(
                f"""
                <div class="card">
                    <h3>@{user["username"]} <span class="muted">{marker}</span></h3>
                    <p class="muted">{user["email"]}</p>
                    <p class="muted">User ID: {user["id"]}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    except Exception as error:
        st.error(error)


def page_system():
    st.subheader("System health")

    services = {
        "API Gateway": "/health",
        "Auth": "/auth/health",
        "Catalog": "/catalog/health",
        "Reviews": "/reviews/health",
        "Feed": "/feed/health",
    }

    cols = st.columns(5)

    for col, (name, path) in zip(cols, services.items()):
        with col:
            try:
                result = get(path)
                st.success(name)
                st.caption(result.get("service", "ok"))
            except Exception:
                st.error(name)


def page_profile():
    st.subheader("Profile")

    st.json(st.session_state.user)

    if st.button("Verify token", use_container_width=True):
        try:
            st.json(get("/auth/verify", token=st.session_state.token))
        except Exception as error:
            st.error(error)


def main():
    css()
    init_state()
    restore_session_from_url()
    hero()

    if not st.session_state.token or not st.session_state.user:
        auth_gate()
        return
    
    sidebar()

    page = st.session_state.nav_page

    if page == "Catalog":
        page_catalog()
    elif page == "Reviews":
        page_reviews()
    elif page == "Feed":
        page_feed()
    elif page == "Users":
        page_users()
    elif page == "System":
        page_system()
    elif page == "Profile":
        page_profile()


if __name__ == "__main__":
    main()
